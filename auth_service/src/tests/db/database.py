from testcontainers.postgres import PostgresContainer

from src.core.database import AsyncDatabase, Base


class TestDatabase:
    def __init__(self, db_image: str = "postgres:latest") -> None:
        # launching postgres test container in docker
        self.__postgres_test_container = PostgresContainer(
            image=db_image,
            username="auth_test",
            password="auth_test",
            dbname="test_auth_db",
            driver="asyncpg",
        )
        self.__postgres_test_container.start()
        # creating async db
        self.async_database = AsyncDatabase(
            host=self.__postgres_test_container.get_container_host_ip(),
            port=self.__postgres_test_container.get_exposed_port(5432),
            username=self.__postgres_test_container.username,
            password=self.__postgres_test_container.password,
            db=self.__postgres_test_container.dbname,
        )

    async def create_test_tables(self) -> None:
        async with self.async_database.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def shutdown(self) -> None:
        async with self.async_database.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.async_database.shutdown()
        self.__postgres_test_container.stop()
