import asyncio 
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.endpoints.note import notes_router
from broker.connection import (
    connect_to_broker,
    close_connection_to_broker
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(connect_to_broker())
    yield
    await asyncio.create_task(close_connection_to_broker()) 


app = FastAPI(lifespan=lifespan)

app.include_router(notes_router)
