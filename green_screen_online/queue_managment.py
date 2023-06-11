import random
import shutil
import string
from datetime import datetime, timedelta
from pathlib import Path
from queue import Queue

TASK_STORE_TIME = timedelta(minutes=10)
TASK_TEMP_DIR = Path("/tmp")


class PendingTask:
    queue = Queue()
    all_tasks = {}                  # type: dict[str, PendingTask]

    def __init__(self, ident, data):
        self.finished_at = None     # type: datetime | None
        self.ident = ident
        self.data = data
        self.temp_dir = TASK_TEMP_DIR / ident
        self.temp_dir.mkdir()
        self.status = "queue"

    def cleanup(self):
        """
        Удаляет задачу и всё что с ней связано
        """
        shutil.rmtree(self.temp_dir)
        del PendingTask.all_tasks[self.ident]
        del self

    @staticmethod
    def register(data):
        """
        Создаёт задачу, добавляет её в очередь
        :param data:
        :return:
        """
        entry_id = None
        while entry_id in PendingTask.all_tasks or entry_id is None:
            entry_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

        entry = PendingTask(entry_id, data)
        PendingTask.queue.put(entry_id)
        PendingTask.all_tasks[entry_id] = entry
        return entry

    @staticmethod
    def get_status(ident):
        """
        Возвращает статус задачи
        """
        if ident not in PendingTask.all_tasks:
            return "none"
        return PendingTask.all_tasks[ident].status
