import sys
from typing import TYPE_CHECKING

from loguru import logger
from asgi_correlation_id import correlation_id

if TYPE_CHECKING:
    from loguru import Record


def configure_logging() -> None:
    def correlation_id_filter(record: "Record") -> bool:
        record["extra"]["correlation_id"] = correlation_id.get()
        return True

    logger.remove()
    logger.add(
        sys.stdout,
        level="DEBUG",
        format="<green>{time:DD-MM-YYYY HH:mm:ss}</> | "
        "<lvl>{level}</> | [{extra[correlation_id]}] | <blue>{module}:{function}</> | "
        "<lvl>{message}</> {exception}",
        filter=correlation_id_filter,
        serialize=True,
        enqueue=True,
    )  # type: ignore
