import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from core.database import main as healthcheck


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.create_task(healthcheck())
    yield


app = FastAPI(lifespan=lifespan)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8002, reload=True)
