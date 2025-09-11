from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.api.endpoints.note import notes_router
from src.core.settings import postgres_settings, rabbitmq_settings, DELETE_NOTES_QUEUE_NAME
from src.container import Container


@asynccontextmanager
async def lifespan(app: FastAPI):
    await app.container.note_broker().consume(
        queue_name=DELETE_NOTES_QUEUE_NAME,
        callback=app.container.delete_all_user_notes_callback(),
    )
    yield
    await app.container.note_broker().shutdown()


def create_app() -> FastAPI:
    dep_container = Container()
    dep_container.config.from_dict(
        {
            "postgres_settings": postgres_settings.model_dump(),
            "rabbitmq_settings": rabbitmq_settings.model_dump(),
        }
    )
    app = FastAPI(lifespan=lifespan, root_path="note/")
    app.container = dep_container
    return app


app = create_app()
app.include_router(notes_router)

if __name__ == "__main__":
    uvicorn.run("src.main:app", port=8001, reload=True)
