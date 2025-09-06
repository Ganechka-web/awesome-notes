from dependency_injector import containers, providers

from src.core.database import AsyncDatabase
from src.core.broker import AsyncBroker
from src.services.auth import AuthService
from src.services.security import SecurityPasswordService
from src.repositories.auth import AuthRepository
from src.broker.rpc_clients import UserCreationRPCClient


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=["src.api.v1.auth"])

    config = providers.Configuration()

    auth_database = providers.Singleton(
        AsyncDatabase,
        host=config.postgres_settings.host,
        port=config.postgres_settings.port,
        username=config.postgres_settings.user,
        password=config.postgres_settings.password,
        db=config.postgres_settings.db,
    )
    auth_broker = providers.Singleton(
        AsyncBroker,
        host=config.rabbitmq_settings.host,
        port=config.rabbitmq_settings.port,
        login=config.rabbitmq_settings.user,
        password=config.rabbitmq_settings.password,
    )
    user_creation_rpc_client = providers.Singleton(
        UserCreationRPCClient,
        broker=auth_broker,
    )
    password_service = providers.Singleton(SecurityPasswordService)
    auth_repository = providers.Factory(AuthRepository, database=auth_database)
    auth_service = providers.Factory(
        AuthService,
        repository=auth_repository,
        rpc_client=user_creation_rpc_client,
        password_service=password_service,
        user_creation_queue_name=config.queue_names.user_creation_queue_name,
    )
