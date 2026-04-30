from typing import Callable

from fastapi import Request, Response

from src.logger import logger


async def log_request_middleware(request: Request, call_next: Callable) -> Response:
    """
    Repleced standart uvicorn access_log, logs method, path and status code of each HTTP request
    """
    response: Response = await call_next(request)
    logger.info(f"{request.method.upper()} {request.url} {response.status_code}")
    return response
