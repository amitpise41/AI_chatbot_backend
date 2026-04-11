import uuid
from datetime import datetime
from typing import Dict, List
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from sqlmodel import Session, select

import app.models as m
from app.interfaces.storage import StorageProvider
from app.interfaces.llm import LLMProvider

IST = ZoneInfo("Asia/Kolkata")

class ChatService:
    def __init__(self, storage: StorageProvider, llm: LLMProvider, session: Session):
        self.storage = storage
        self.llm = llm
        self.session = session

    def list_chats(self, user_id: int) -> List[Dict]:
        try:
            statement = (
                select(m.Chat)
                .join(m.UserChatLinkTable, m.Chat.chat_id == m.UserChatLinkTable.chat_id_fk)
                .where(m.UserChatLinkTable.user_id_fk == user_id)
            )
            results = self.session.exec(statement).all()
        except Exception:
            raise HTTPException(status_code=500, detail="Unable to find files")

        thread_ids = [
            {"thread_id": r.chat_id, "heading": r.heading}
            for r in results
        ]
        thread_ids.sort(key=lambda x: x["thread_id"], reverse=True)
        return thread_ids

    def create_chat(self, user_id: int) -> Dict:
        thread_id = f"{datetime.now(IST).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}"
        
        chat = m.Chat(chat_id=thread_id, chat_path=f"{thread_id}.json", heading="")
        user_chat_link = m.UserChatLinkTable(
            user_id_fk=user_id,
            chat_id_fk=thread_id
        )
        
        self.session.add(chat)
        self.session.add(user_chat_link)

        try:
            data = self.storage.create_thread(str(user_id), thread_id)
        except Exception as e:
            self.session.rollback()
            raise HTTPException(status_code=500, detail="Failed to create new chat thread") from e

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise HTTPException(status_code=500, detail="Failed to save chat to database")

        return data

    def get_messages(self, user_id: int, thread_id: str) -> List[Dict]:
        data = self.storage.load_thread(str(user_id), thread_id)
        if data is None:
            raise HTTPException(status_code=404, detail="Chat thread not found or corrupted")
        if "messages" not in data:
            raise HTTPException(status_code=500, detail="Chat thread format is invalid")
        return data["messages"]

    async def send_message(self, user_id: int, thread_id: str, user_input: str) -> Dict:
        data = self.storage.load_thread(str(user_id), thread_id)
        if data is None:
            raise HTTPException(status_code=404, detail="Chat thread not found")

        messages = data.get("messages", [])
        messages_for_llm = [{"role": m["role"], "content": m["content"]} for m in messages]
        messages_for_llm.append({"role": "user", "content": user_input})

        try:
            graph_result = await self.llm.chat(messages=messages_for_llm, thread_id=thread_id)
            assistant_content = graph_result["messages"][-1].content
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": assistant_content})

            chat_heading = data.get("heading", "")
            if not chat_heading:
                chat_heading = await self.llm.generate_heading(messages)
                statement = select(m.Chat).where(m.Chat.chat_id == thread_id)
                chat = self.session.exec(statement).one()
                chat.heading = chat_heading
                self.session.add(chat)
                self.session.commit()
                self.session.refresh(chat)

            data["messages"] = messages
            data["heading"] = chat_heading
            self.storage.save_thread(str(user_id), thread_id, data)

            return {
                "thread_id": thread_id,
                "heading": chat_heading,
                "message": assistant_content
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail="Assistant failed to generate response") from e
