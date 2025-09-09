import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


BASE_DIR = Path(__file__).parent.parent


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, "..", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field("127.0.0.1", alias="POSTGRES_HOST")
    port: int = Field(5432, alias="POSTGRES_PORT")
    user: str = Field("postgres", alias="POSTGRES_USER")
    password: str = Field("postgres", alias="POSTGRES_PASSWORD")
    db: str = Field("postgres", alias="POSTGRES_DB")


postgres_settings = PostgresSettings()


class RabbitMQSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, "..", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field("127.0.0.1", alias="RABBITMQ_HOST")
    port: int = Field(5672, alias="RABBITMQ_PORT")
    user: str = Field("guest", alias="RABBITMQ_USER")
    password: str = Field("guest", alias="RABBITMQ_PASSWORD")


USER_CREATION_QUEUE_NAME = "user_creation_queue"
rabbitmq_settings = RabbitMQSettings()

# security

SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = os.getenv("ALGORITHM", "")
