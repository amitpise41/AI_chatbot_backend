import os
import json
from typing import Dict, List
from filelock import FileLock
from app.interfaces.storage import StorageProvider

CHAT_HISTORY_PATH = "chat_history"

class FileStorageProvider(StorageProvider):
    def __init__(self, base_path: str = CHAT_HISTORY_PATH):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def _ensure_user_dir(self, user_id: str) -> str:
        user_dir = os.path.join(self.base_path, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        return user_dir

    def create_thread(self, user_id: str, thread_id: str) -> Dict:
        user_dir = self._ensure_user_dir(user_id)
        thread_path = os.path.join(user_dir, f"{thread_id}.json")

        if os.path.exists(thread_path):
            raise Exception("Thread ID collision")

        data = {
            "thread_id": str(thread_id),
            "messages": [],
            "heading": ""
        }

        lock = FileLock(f"{thread_path}.lock")
        with lock:
            with open(thread_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        return data

    def load_thread(self, user_id: str, thread_id: str) -> Dict | None:
        user_dir = os.path.join(self.base_path, str(user_id))
        thread_path = os.path.join(user_dir, f"{thread_id}.json")

        if not os.path.exists(thread_path):
            return None

        lock = FileLock(f"{thread_path}.lock")
        with lock:
            try:
                with open(thread_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return None

    def save_thread(self, user_id: str, thread_id: str, data: Dict) -> None:
        user_dir = self._ensure_user_dir(user_id)
        thread_path = os.path.join(user_dir, f"{thread_id}.json")

        lock = FileLock(f"{thread_path}.lock")
        with lock:
            with open(thread_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
