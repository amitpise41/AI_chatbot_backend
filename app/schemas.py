from datetime import datetime
from sqlmodel import SQLModel
from pydantic import BaseModel, EmailStr


class UserBase(SQLModel):

    user_name: str


class UserView(UserBase):

    user_id: int


class UserLogin(BaseModel):
    
    user_name: EmailStr
    password: str


class ChatBase(SQLModel):

    chat_path: str


class TokenData(UserBase):
    pass


class ChatRequest(BaseModel):
    user_input: str


class Token(BaseModel):
    access_token: str
    token_type: str