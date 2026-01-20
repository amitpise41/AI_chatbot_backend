from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime

from contextlib import asynccontextmanager

from sqlmodel import Field, Session, SQLModel, select
import app.models as m
import app.schemas as s
from app.db import get_session, create_db_and_tables
import app.functions as f

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel, EmailStr
from typing import Annotated, List, Dict
import os
from bot.chat_bot import run_graph
import uuid
import json
import security
from filelock import FileLock
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
load_dotenv()


IST = ZoneInfo("Asia/Kolkata")
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = os.getenv("ALGORITHM", "")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "")
ACCESS_TOKEN_EXPIRE_MINUTES = int(ACCESS_TOKEN_EXPIRE_MINUTES) if ACCESS_TOKEN_EXPIRE_MINUTES else 0
CHAT_HISTORY_PATH = "chat_history"

def create_folder(path: str) -> None:
    os.makedirs(path, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    create_folder(CHAT_HISTORY_PATH)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def check_run():
    return {"message": "The API is running fine!"}


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> s.Token:
    
    user = f.get_user(user_name=form_data.username)

    check_password = False
    if user:
        check_password = security.verify_password(form_data.password, user.password)

    if not user or not check_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.user_name}, expires_delta=access_token_expires
    )

    return s.Token(access_token=access_token, token_type="bearer")


@app.get("/chats")
async def chats(
    user: Annotated[s.UserView, Depends(security.get_current_user)]
) -> List[str]:
    
    user_dir = os.path.join(CHAT_HISTORY_PATH, str(user.user_id))

    if not os.path.exists(user_dir):
        return []

    try:
        files = os.listdir(user_dir)
    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Unable to find files"
        )

    thread_ids = [
        f.replace(".json", "")
        for f in files
        if f.endswith(".json")
    ]
    thread_ids.sort(reverse=True)

    return thread_ids


@app.post("/chats")
async def chats(
    user: Annotated[s.UserView, Depends(security.get_current_user)],
    session: Session = Depends(get_session)
) -> Dict[str, str]:
    
    user_dir = f.ensure_user_dir(CHAT_HISTORY_PATH, str(user.user_id))

    thread_id = f"{datetime.now(IST).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}"
    thread_path = os.path.join(user_dir, f"{thread_id}.json")

    if os.path.exists(thread_path):
        raise HTTPException(
            status_code=500,
            detail="Thread ID collision"
        )

    lock = FileLock(f"{thread_path}.lock")

    with lock:
        data = f.new_thread(thread_path, thread_id)

        if not data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create new chat thread"
            )
    

    chat = m.Chat(chat_id=thread_id, chat_path=thread_path)

    session.add(chat)
    session.commit()
    session.refresh(chat)

    user_chat_link = m.UserChatLinkTable(
        user_id_fk=user.user_id,
        chat_id_fk=chat.chat_id
    )

    session.add(user_chat_link)
    session.commit()
    session.refresh(user_chat_link)

    return data


@app.get("/chats/{thread_id}")
async def chat(
    thread_id: str,
    user: Annotated[s.UserBase, Depends(security.get_current_user)]
) -> List[Dict]:
    user_dir = f.ensure_user_dir(CHAT_HISTORY_PATH, str(user.user_id))
    thread_path = os.path.join(user_dir, f"{thread_id}.json")

    if not os.path.exists(thread_path):
        raise HTTPException(
            status_code=404,
            detail="Chat thread not found"
        )

    lock = FileLock(f"{thread_path}.lock")

    with lock:
        data = f.safe_load_json(thread_path)

        if data is None:
            raise HTTPException(
                status_code=500,
                detail="Chat thread is corrupted"
            )

        if "messages" not in data:
            raise HTTPException(
                status_code=500,
                detail="Chat thread format is invalid"
            )

        return data["messages"]


@app.post("/chats/{thread_id}")
async def chat(
    thread_id: str,
    body: s.ChatRequest,
    user: Annotated[s.UserBase, Depends(security.get_current_user)]
):
    if "/" in thread_id or ".." in thread_id:
        raise HTTPException(status_code=400, detail="Invalid thread ID")

    user_dir = f.ensure_user_dir(CHAT_HISTORY_PATH, str(user.user_id))
    thread_path = os.path.join(user_dir, f"{thread_id}.json")

    messages = await run_in_threadpool(
        f.append_message,
        thread_path,
        thread_id,
        "user",
        body.user_input
    )

    if not messages:
        raise HTTPException(
            status_code=500,
            detail="Failed to append user message"
        )

    try:
        messages = f.messages_for_llm(messages)
        graph_result = await run_graph(
            messages=messages,
            thread_id=thread_id
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Assistant failed to generate response"
        )

    assistant_content = graph_result["messages"][-1].content

    messages = await run_in_threadpool(
        f.append_message,
        thread_path,
        thread_id,
        "assistant",
        assistant_content
    )

    return {
        "thread_id": thread_id,
        "message": messages[-1]
    }


@app.post("/users/", response_model=s.UserView)
def create_user(user: s.UserLogin, session: Session = Depends(get_session)):

    user_in_db = f.get_user(user_name=user.user_name)
    if user_in_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    hashed_password = security.password_hash.hash(user.password)
    new_user = m.User(user_name=user.user_name, password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user




# if for some reason the chat fails then the user_input should not be added to the dictionary