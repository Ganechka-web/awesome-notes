from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.container import Container
from src.core.settings import (
    postgres_settings,
    rabbitmq_settings,
    USER_CREATION_QUEUE_NAME,
)
from src.api.endpoints.user import users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await app.container.user_broker().consume(
        queue_name=USER_CREATION_QUEUE_NAME,
        callback=app.container.create_user_callback(),
    )
    yield
    await app.container.user_broker().shutdown()
    await app.container.user_database().shutdown()


def create_app() -> FastAPI:
    dep_container = Container()
    dep_container.config.from_dict(
        {
            "postgres_settings": postgres_settings.model_dump(),
            "rabbitmq_settings": rabbitmq_settings.model_dump(),
        }
    )
    app = FastAPI(title="User service", version="0.0.0 alpha", lifespan=lifespan)
    app.container = dep_container


app = create_app()
app.include_router(users_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
