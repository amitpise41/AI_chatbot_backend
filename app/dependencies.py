from fastapi import Depends
from app.db import get_session
from app.interfaces.storage import StorageProvider
from app.interfaces.llm import LLMProvider
from app.services.file_storage import FileStorageProvider
from bot.llm_service import LangGraphLLMProvider
from app.services.chat_service import ChatService
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from sqlmodel import Session
from pwdlib import PasswordHash

# Global instances for providers
file_storage_provider = FileStorageProvider()
lang_graph_llm_provider = LangGraphLLMProvider()
password_hash = PasswordHash.recommended()

def get_storage_provider() -> StorageProvider:
    return file_storage_provider

def get_llm_provider() -> LLMProvider:
    return lang_graph_llm_provider

def get_password_hash() -> PasswordHash:
    return password_hash

def get_user_service(
    session: Session = Depends(get_session),
    password_hash: PasswordHash = Depends(get_password_hash)
) -> UserService:
    return UserService(session=session, password_hash=password_hash)

def get_auth_service(
    user_service: UserService = Depends(get_user_service),
    password_hash: PasswordHash = Depends(get_password_hash)
) -> AuthService:
    return AuthService(user_service=user_service, password_hash=password_hash)

def get_chat_service(
    storage: StorageProvider = Depends(get_storage_provider),
    llm: LLMProvider = Depends(get_llm_provider),
    session: Session = Depends(get_session)
) -> ChatService:
    return ChatService(storage=storage, llm=llm, session=session)
