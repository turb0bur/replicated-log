from common import LogEntry
from common.storage_strategy import StorageStrategy

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class LogStorage(metaclass=SingletonMeta):
    def __init__(self, storage_strategy: StorageStrategy):
        self.storage_strategy = storage_strategy

    def append(self, message: LogEntry) -> None:
        self.storage_strategy.log_message(message)

    def list(self) -> list[LogEntry]:
        return self.storage_strategy.retrieve_logs()

    def count(self) -> int:
        return self.storage_strategy.count_logs()

    def reset(self):
        self.storage_strategy.clear_storage()
