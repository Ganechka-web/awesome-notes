import asyncio 
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from api.endpoints.note import notes_router
from core.database import main as healthcheck
from broker.connection import (
    connect_to_broker,
    close_connection_to_broker
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    connection = asyncio.create_task(connect_to_broker())
    asyncio.create_task(healthcheck())
    yield
    await asyncio.create_task(
        close_connection_to_broker(await connection)
    )


app = FastAPI(lifespan=lifespan)

app.include_router(notes_router)

if __name__ == '__main__':
     uvicorn.run('main:app', port=8001, reload=True)
