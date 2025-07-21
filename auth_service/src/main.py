from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from container import Container
from core.settings import USER_CREATION_QUEUE_NAME, postgres_settings, rabbitmq_settings
from api.endpoints.auth import auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    dep_container = Container()
    dep_container.config.from_dict(
        {
            "postgres_settings": postgres_settings.model_dump(),
            "rabbitmq_settings": rabbitmq_settings.model_dump(),
            "queue_names": {"user_creation_queue_name": USER_CREATION_QUEUE_NAME},
        }
    )
    app.container = dep_container
    yield
    await app.container.auth_broker().shutdown()
    await app.container.auth_database().shutdown()


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8002, reload=True)
