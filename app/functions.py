from app.db import engine
import app.models as m
from sqlmodel import Session, select
import os
import json
from datetime import datetime
from typing import List, Dict, Any
from filelock import FileLock
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")


def get_user(user_name) -> m.User | None:

    with Session(engine) as session:
        statement = select(m.User).where(m.User.user_name == user_name)
        results = session.exec(statement).first()
        if results:
            return results
        else:
            None


def safe_load_json(path: str) -> Any | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def ensure_user_dir(chat_path: str, user_id: str) -> str:

    user_dir = os.path.join(chat_path, user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    return user_dir


def new_thread(
    thread_path: str,
    thread_id: str,
) -> Dict:

    data = {
        "thread_id": str(thread_id),
        "messages": []
    }

    with open(thread_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"thread_id": thread_id}


def append_message(
    thread_path: str,
    thread_id: str,
    role: str,
    content: str
) -> List[Dict]:
    lock = FileLock(f"{thread_path}.lock")

    with lock:
        data = safe_load_json(thread_path)

        if not data:
            data = {
                "thread_id": thread_id,
                "messages": []
            }

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(IST).isoformat()
        }

        data.setdefault("messages", []).append(message)

        with open(thread_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return data["messages"]
