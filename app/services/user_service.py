from sqlmodel import Session, select
from fastapi import HTTPException, status
from pwdlib import PasswordHash
import app.models as m
import app.schemas as s

class UserService:
    def __init__(self, session: Session, password_hash: PasswordHash):
        self.session = session
        self.password_hash = password_hash

    def get_user(self, user_name: str) -> m.User | None:
        statement = select(m.User).where(m.User.user_name == user_name)
        return self.session.exec(statement).first()

    def create_user(self, user: s.UserLogin) -> m.User:
        user_in_db = self.get_user(user_name=user.user_name)
        if user_in_db:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        hashed_password = self.password_hash.hash(user.password)
        new_user = m.User(user_name=user.user_name, password=hashed_password)
        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)
        return new_user
