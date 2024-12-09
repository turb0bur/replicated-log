import json
import os

from abc import ABC, abstractmethod
from .log_entry import LogEntry


class StorageStrategy(ABC):
    def __init__(self, file_path: str):
        self.file_path = file_path

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
    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.log_set = set()
        self._load_existing_logs()

    def _load_existing_logs(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                for line in file:
                    log_entry = LogEntry.model_validate_json(line.strip())
                    self.log_set.add(log_entry.sequence_number)

    def log_message(self, message: LogEntry) -> None:
        if message.sequence_number not in self.log_set:
            self.log_set.add(message.sequence_number)
            with open(self.file_path, 'a') as file:
                file.write(json.dumps(message.__dict__) + '\n')

    def retrieve_logs(self) -> list[LogEntry]:
        logs = []
        try:
            with open(self.file_path, 'r') as file:
                for line in file:
                    log_data = json.loads(line)
                    logs.append(LogEntry(**log_data))
        except FileNotFoundError:
            pass
        return logs

    def count_logs(self) -> int:
        try:
            with open(self.file_path, 'r') as file:
                return sum(1 for _ in file)
        except FileNotFoundError:
            return 0

    def clear_storage(self) -> None:
        open(self.file_path, 'w').close()


class MasterStorageStrategy(BaseStorageStrategy):
    pass


class SecondaryStorageStrategy(BaseStorageStrategy):
    pass
