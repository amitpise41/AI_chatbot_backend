from fastapi import APIRouter

from app.routers import auth, chats, users

# We leave empty init, or build a combined router if preferred.
