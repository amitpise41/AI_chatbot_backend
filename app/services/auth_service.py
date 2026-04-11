import os
import jwt
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pwdlib import PasswordHash
from fastapi import HTTPException, status
import app.schemas as s
import app.models as m
from app.services.user_service import UserService

IST = ZoneInfo("Asia/Kolkata")
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = os.getenv("ALGORITHM", "")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "")
ACCESS_TOKEN_EXPIRE_MINUTES = int(ACCESS_TOKEN_EXPIRE_MINUTES) if ACCESS_TOKEN_EXPIRE_MINUTES else 0

class AuthService:
    def __init__(self, user_service: UserService, password_hash: PasswordHash):
        self.user_service = user_service
        self.password_hash = password_hash

    def authenticate(self, username: str, password: str) -> m.User:
        user = self.user_service.get_user(user_name=username)
        check_password = False
        if user:
            check_password = self.password_hash.verify(password, user.password)

        if not user or not check_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    def create_token(self, user: m.User) -> s.Token:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode = {"sub": user.user_name}
        expire = datetime.now(IST) + access_token_expires
            
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        return s.Token(access_token=encoded_jwt, token_type="bearer")
