from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.container import Container
from src.core.settings import USER_CREATION_QUEUE_NAME, postgres_settings, rabbitmq_settings
from src.api.v1.auth import auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await app.container.auth_broker().shutdown()
    await app.container.auth_database().shutdown()


def create_app() -> FastAPI:
    dep_container = Container()
    dep_container.config.from_dict(
        {
            "postgres_settings": postgres_settings.model_dump(),
            "rabbitmq_settings": rabbitmq_settings.model_dump(),
            "queue_names": {"user_creation_queue_name": USER_CREATION_QUEUE_NAME},
        }
    )
    app = FastAPI(lifespan=lifespan)
    app.container = dep_container
    return app


app = create_app()
app.include_router(auth_router)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8002, reload=True)
