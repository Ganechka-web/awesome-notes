from redis.asyncio import Redis

from src.logger import logger


class AsyncRedis:
    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        self.r = Redis(
            host=host,
            port=port,
            username=username,
            password=password,
            decode_responses=True,
        )
        logger.info("Redis has connected successfully")

    async def shutdown(self):
        await self.r.aclose()
        logger.info("Redis has disconnected successfully")
