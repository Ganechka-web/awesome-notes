from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from asgi_correlation_id import CorrelationIdMiddleware

from src.api.endpoints.note import notes_router
from src.core.settings import (
    postgres_settings,
    rabbitmq_settings,
    DELETE_NOTES_QUEUE_NAME,
)
from src.middlewares import log_request_middleware
from src.logger import configure_logging, logger
from src.monitoring import instrumentator
from src.container import Container


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    await app.container.note_broker().consume(
        queue_name=DELETE_NOTES_QUEUE_NAME,
        callback=app.container.delete_all_user_notes_callback(),
    )
    yield
    await app.container.note_broker().shutdown()

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
        root_path="/note"
    )
    app.container = dep_container

    # setting up Prometheus metrics
    instrumentator.instrument(app).expose(app)

    return app


app = create_app()

app.middleware("http")(log_request_middleware)
app.add_middleware(CorrelationIdMiddleware)

app.include_router(notes_router)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8003, reload=True, access_log=False)
