from abc import ABC, abstractmethod
from .log_entry import LogEntry

class StorageStrategy(ABC):
    @abstractmethod
    def log_message(self, message: LogEntry) -> None:
        pass

    @abstractmethod
    def retrieve_logs(self) -> list[LogEntry]:
        pass

    def count_logs(self) -> int:
        pass

class MasterStorageStrategy(StorageStrategy):
    def __init__(self):
        self.logs = []
        self.count = 0

    def log_message(self, message: LogEntry) -> None:
        self.logs.append(message)
        self.count += 1

    def retrieve_logs(self) -> list[LogEntry]:
        return self.logs

    def count_logs(self) -> int:
        return self.count

class SecondaryStorageStrategy(StorageStrategy):
    def __init__(self):
        self.logs = []
        self.count = 0

    def log_message(self, message: LogEntry) -> None:
        self.logs.append(message)
        self.count += 1

    def retrieve_logs(self) -> list[LogEntry]:
        return self.logs

    def count_logs(self) -> int:
        return self.count
