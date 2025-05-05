from fastapi import FastAPI

from api.endpoints.user import users_router


app = FastAPI()

app.include_router(users_router)