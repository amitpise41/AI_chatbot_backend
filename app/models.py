import app.schemas as s
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


class UserChatLinkTable(SQLModel, table=True):
    __tablename__ = "user_chat"

    user_chat_id: int | None = Field(default=None, primary_key=True)
    user_id_fk: int = Field(foreign_key="users.user_id", index=True)
    chat_id_fk: str = Field(foreign_key="chats.chat_id", index=True)
    modified_at: datetime = Field(default_factory=lambda: datetime.now(IST).replace(microsecond=0))


class User(s.UserBase, table=True):
    __tablename__ = "users"

    user_id: int | None = Field(default=None, primary_key=True)
    password: str
    modified_at: datetime = Field(default_factory=lambda: datetime.now(IST).replace(microsecond=0))

    chats: "Chat" = Relationship(back_populates="users", link_model=UserChatLinkTable)


class Chat(s.ChatBase, table=True):
    __tablename__ = "chats"

    chat_id: str = Field(default=None, primary_key=True)
    modified_at: datetime = Field(default_factory=lambda: datetime.now(IST).replace(microsecond=0))

    users: User = Relationship(back_populates="chats", link_model=UserChatLinkTable)
