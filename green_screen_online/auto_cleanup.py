import logging
import time
from datetime import datetime
from threading import Thread
from green_screen_online.queue_managment import PendingTask, TASK_STORE_TIME

log = logging.getLogger("Cleanup")


def cleanup_loop():
    while True:
        for task_id in PendingTask.all_tasks:
            task = PendingTask.all_tasks[task_id]
            if task.finished_at is not None and\
                    task.finished_at + TASK_STORE_TIME < datetime.now():
                log.info(f"DELETE {task_id}")
                task.cleanup()
        time.sleep(60)


def start():
    Thread(target=cleanup_loop).start()
