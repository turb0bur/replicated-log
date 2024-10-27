from abc import ABC, abstractmethod
from .log_entry import LogEntry


class StorageStrategy(ABC):
    @abstractmethod
    def log_message(self, message: LogEntry) -> None:
        pass

    @abstractmethod
    def retrieve_logs(self) -> list[LogEntry]:
        pass

    @abstractmethod
    def count_logs(self) -> int:
        pass

    @abstractmethod
    def clear_storage(self) -> None:
        pass


class BaseStorageStrategy(StorageStrategy):
    def __init__(self):
        self.logs = []
        self.count = 0
        self.sequence_tracker = set()

    def log_message(self, message: LogEntry) -> None:
        if message.sequence_number in self.sequence_tracker:
            return

        self.logs.append(message)
        self.sequence_tracker.add(message.sequence_number)
        self.count += 1

    def retrieve_logs(self) -> list[LogEntry]:
        return self.logs

    def count_logs(self) -> int:
        return self.count

    def clear_storage(self) -> None:
        self.logs = []
        self.count = 0
        self.sequence_tracker.clear()


class MasterStorageStrategy(BaseStorageStrategy):
    pass


class SecondaryStorageStrategy(BaseStorageStrategy):
    pass
