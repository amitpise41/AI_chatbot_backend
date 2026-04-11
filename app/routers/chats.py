from typing import Annotated, List, Dict
from fastapi import APIRouter, Depends
import app.schemas as s
from app.services.chat_service import ChatService
from app.dependencies import get_chat_service
from security import get_current_user

router = APIRouter(prefix="/chats", tags=["chats"])

@router.get("", response_model=List[Dict])
def get_all_chats(
    user: Annotated[s.UserView, Depends(get_current_user)],
    chat_service: ChatService = Depends(get_chat_service)
):
    return chat_service.list_chats(user.user_id)

@router.post("", response_model=Dict)
def create_new_chat(
    user: Annotated[s.UserView, Depends(get_current_user)],
    chat_service: ChatService = Depends(get_chat_service)
):
    return chat_service.create_chat(user.user_id)

@router.get("/{thread_id}", response_model=List[Dict])
def get_chat_messages(
    thread_id: str,
    user: Annotated[s.UserBase, Depends(get_current_user)],
    chat_service: ChatService = Depends(get_chat_service)
):
    # Depending on token scope, user might just be UserBase or UserView, need ID 
    # Usually it's the User model but let's assume it has user_id
    # From security.py we return m.User which has user_id
    return chat_service.get_messages(user.user_id, thread_id)

@router.post("/{thread_id}", response_model=Dict)
async def post_chat_message(
    thread_id: str,
    body: s.ChatRequest,
    user: Annotated[s.UserBase, Depends(get_current_user)],
    chat_service: ChatService = Depends(get_chat_service)
):
    return await chat_service.send_message(user.user_id, thread_id, body.user_input)
