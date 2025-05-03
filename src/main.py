from fastapi import FastAPI

from core.database import async_engine
from repositories.user import UserRepository
from api.endpoints.user import users_router


app = FastAPI()

app.include_router(users_router)