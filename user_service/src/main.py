from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from asgi_correlation_id import CorrelationIdMiddleware

from src.core.settings import (
    postgres_settings,
    rabbitmq_settings,
    USER_CREATION_QUEUE_NAME,
)
from src.api.endpoints.user import users_router
from src.middlewares import log_request_middleware
from src.logger import configure_logging, logger
from src.monitoring import instrumentator
from src.container import Container


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    # starting to consume messages from user_creation_queue
    await app.container.user_broker().consume(
        queue_name=USER_CREATION_QUEUE_NAME,
        callback=app.container.create_user_callback(),
    )
    yield
    # shutting down broker and database
    await app.container.user_broker().shutdown()
    await app.container.user_database().shutdown()
    await logger.complete()


def create_app() -> FastAPI:
    dep_container = Container()
    dep_container.config.from_dict(
        {
            "postgres_settings": postgres_settings.model_dump(),
            "rabbitmq_settings": rabbitmq_settings.model_dump(),
        }
    )
    app = FastAPI(
        title="User service",
        version="0.0.0 alpha",
        lifespan=lifespan,
        root_path="/user",
    )
    app.container = dep_container

    # setting up Prometheus metrics
    instrumentator.instrument(app).expose(app)

    return app


app = create_app()

app.middleware("http")(log_request_middleware)
app.add_middleware(CorrelationIdMiddleware)

app.include_router(users_router)

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app", host="0.0.0.0", port=8001, reload=True, access_log=False
    )
