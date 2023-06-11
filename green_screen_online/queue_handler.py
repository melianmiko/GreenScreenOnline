import logging
import math
import subprocess
from datetime import datetime

import ffmpeg
from threading import Thread

from green_screen_online.queue_managment import PendingTask

log = logging.getLogger("QueueHandler")


def process_task(task: PendingTask):
    color = "#00FF00" if "color" not in task.data else task.data["color"]
    color = color.replace("#", "0x")

    # Выясняем продолжительность файлов
    bv_length = get_length(task.temp_dir / "base_video")
    ov_length = get_length(task.temp_dir / "overlay_video")

    # Время для запуска оверлея (под конец основного видео)
    overlay_delay = max(0, math.floor(bv_length-ov_length))

    # Загружаем видео
    base_file = ffmpeg.input(task.temp_dir / "base_video")
    overlay_file = ffmpeg.input(task.temp_dir / "overlay_video")

    # Отматываем overlay, добавляя задержку в overlay_delay
    overlay_video = overlay_file.video.filter("setpts", f"PTS-STARTPTS+{overlay_delay}/TB")
    overlay_audio = overlay_file.audio.filter('adelay', f"{overlay_delay}s", all="true")

    # Масштабируем оверлей под базовое видео
    videos = ffmpeg.filter_multi_output([
        overlay_video,
        base_file.video
    ], "scale2ref", "oh*mdar", "ih")

    # Заменяем выбранный цвет фона на прозрачность
    overlay = videos[0].filter("colorkey", color, "0.3", "0.2")
    base = videos[1]

    # Выполняем наложение
    out_video = ffmpeg.filter([base, overlay], "overlay", "(main_w-overlay_w)/2", "(main_h-overlay_h)/2",
                              enable=f"gt(t,{overlay_delay})")
    out_audio = ffmpeg.filter([base_file, overlay_audio], "amerge", inputs=2)
    out = ffmpeg.output(out_video, out_audio, filename=task.temp_dir / "output.mp4")
    out.run()


def get_length(input_video):
    result = subprocess.run(['ffprobe',
                             '-v',
                             'error',
                             '-show_entries',
                             'format=duration',
                             '-of',
                             'default=noprint_wrappers=1:nokey=1', input_video],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return float(result.stdout)


def start():
    Thread(target=thread_func, name="QueueHandler0").start()


def thread_func():
    """
    Основная функция потока работы с очередью
    """
    while True:
        task_id = PendingTask.queue.get(True)
        if task_id not in PendingTask.all_tasks:
            continue
        task = PendingTask.all_tasks[task_id]
        log.info(f"Accept {task_id}")

        # noinspection PyBroadException
        task.status = "processing"
        try:
            process_task(task)
            task.status = "ready"
            task.finished_at = datetime.now()
        except Exception as e:
            task.status = "failure"
            log.error(f"Failed to process task {task_id}")
            log.exception(e)
