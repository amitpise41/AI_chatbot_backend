from fastapi import APIRouter, Depends
import app.schemas as s
from app.services.user_service import UserService
from app.dependencies import get_user_service

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=s.UserView)
def create_user(
    user: s.UserLogin,
    user_service: UserService = Depends(get_user_service)
):
    return user_service.create_user(user)
