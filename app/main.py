from contextlib import asynccontextmanager

from app.api.v1.routers import car_model_router, user_router
from app.core.database import create_tables_car_models, create_tables_users
from fastapi import FastAPI


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    create_tables_car_models()
    create_tables_users()
    yield

app = FastAPI(lifespan=app_lifespan)

app.include_router(user_router)
app.include_router(car_model_router)
