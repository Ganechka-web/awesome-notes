import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from core.database import main as healthcheck
from api.endpoints.user import users_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(healthcheck())
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(users_router)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
