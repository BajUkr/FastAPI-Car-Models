from app.api.v1.endpoints import item, user
from fastapi import APIRouter

api_v1_router = APIRouter()

api_v1_router.include_router(user.router, prefix="/users", tags=["users"])
api_v1_router.include_router(item.router, prefix="/items", tags=["items"])
