from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from api.endpoints.note import notes_router
from core.settings import postgres_settings, rabbitmq_settings, DELETE_NOTES_QUEUE_NAME
from container import Container


@asynccontextmanager
async def lifespan(app: FastAPI):
    dep_container = Container()
    dep_container.config.from_dict(
        {
            "postgres_settings": postgres_settings.model_dump(),
            "rabbitmq_settings": rabbitmq_settings.model_dump(),
        }
    )
    app.container = dep_container
    await app.container.note_broker().consume(
        queue_name=DELETE_NOTES_QUEUE_NAME,
        callback=app.container.delete_all_user_notes_callback(),
    )
    yield
    await app.container.note_broker().shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(notes_router)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8001, reload=True)
