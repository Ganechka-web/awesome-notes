import os
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


BASE_DIR = Path(__file__).parent.parent

# class ModelConfigMixin:
#     model_config = SettingsConfigDict(
#         env_file=os.path.join(BASE_DIR, "..", ".env"),
#         env_file_encoding="utf-8",
#         extra="ignore",
#     )


class PortAlwaysIntegerMixin:
    @field_validator("port", mode="before")
    @classmethod
    def convert_port_to_int(cls, value: str | int) -> int:
        if isinstance(value, int):
            return value
        return int(value)


class PostgresSettings(BaseSettings, PortAlwaysIntegerMixin):
    host: str = Field("127.0.0.1", alias="POSTGRES_HOST")
    port: int = Field(5432, alias="POSTGRES_PORT")
    user: str = Field("postgres", alias="POSTGRES_USER")
    password: str = Field("postgres", alias="POSTGRES_PASSWORD")
    db: str = Field("postgres", alias="POSTGRES_DB")


postgres_settings = PostgresSettings()


class RabbitMQSettings(BaseSettings, PortAlwaysIntegerMixin):
    host: str = Field("127.0.0.1", alias="RABBITMQ_HOST")
    port: int = Field(5672, alias="RABBITMQ_PORT")
    user: str = Field("guest", alias="RABBITMQ_USER")
    password: str = Field("guest", alias="RABBITMQ_PASSWORD")


USER_CREATION_QUEUE_NAME = "user_creation_queue"
rabbitmq_settings = RabbitMQSettings()


class RedisSettings(BaseSettings, PortAlwaysIntegerMixin):
    host: str = Field("127.0.0.1", alias="REDIS_HOST")
    port: int = Field(6379, alias="REDIS_PORT")
    user: str = Field("default", alias="REDIS_USER")
    password: str = Field("", alias="REDIS_USER_PASSWORD")


redis_settings = RedisSettings()

# security

SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = os.getenv("ALGORITHM", "")
