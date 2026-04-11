import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db import create_db_and_tables
from app.routers import auth, chats, users

CHAT_HISTORY_PATH = "chat_history"

def create_folder(path: str) -> None:
    os.makedirs(path, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    create_folder(CHAT_HISTORY_PATH)
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(users.router)

@app.get("/")
def check_run():
    return {"message": "The API is running fine!"}