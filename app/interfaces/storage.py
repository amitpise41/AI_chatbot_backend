from abc import ABC, abstractmethod
from typing import Dict

class StorageProvider(ABC):
    @abstractmethod
    def create_thread(self, user_id: str, thread_id: str) -> Dict:
        pass

    @abstractmethod
    def load_thread(self, user_id: str, thread_id: str) -> Dict | None:
        pass

    @abstractmethod
    def save_thread(self, user_id: str, thread_id: str, data: Dict) -> None:
        pass
