from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
import jwt
from jwt.exceptions import InvalidTokenError
from zoneinfo import ZoneInfo
import os

from app.db import get_session
from sqlmodel import Session
import app.schemas as s
import app.models as m
from pwdlib import PasswordHash
from app.services.user_service import UserService

ALGORITHM = os.getenv("ALGORITHM", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Ensure password hash is available here if needed or inject everywhere
password_hash = PasswordHash.recommended()

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Session = Depends(get_session)
) -> m.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_name = payload.get("sub")
        if user_name is None:
            raise credentials_exception
        token_data = s.TokenData(user_name=user_name)
    except InvalidTokenError:
        raise credentials_exception
    
    # We construct UserService manually here since we just need simple lookup
    user_service = UserService(session, password_hash)
    user = user_service.get_user(user_name=token_data.user_name)
    if user is None:
        raise credentials_exception
    
    return user