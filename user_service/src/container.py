from dependency_injector import containers, providers

from core.broker import AsyncBroker
from core.database import AsyncDatabase
from repositories.user import UserRepository
from services.user import UserService
from broker.callbacks import CreateUserCallback
from core.settings import DELETE_NOTES_QUEUE_NAME


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=["api.endpoints.user", "broker.callbacks"]
    )
    config = providers.Configuration()

    user_database = providers.Singleton(
        AsyncDatabase,
        host=config.postgres_settings.host,
        port=config.postgres_settings.port,
        username=config.postgres_settings.user,
        password=config.postgres_settings.password,
        db=config.postgres_settings.db,
    )
    user_repository = providers.Factory(UserRepository, database=user_database)
    user_broker = providers.Singleton(
        AsyncBroker,
        host=config.rabbitmq_settings.host,
        port=config.rabbitmq_settings.port,
        login=config.rabbitmq_settings.user,
        password=config.rabbitmq_settings.password,
    )
    user_service = providers.Factory(
        UserService,
        repository=user_repository,
        broker=user_broker,
        delete_notes_quque_name=DELETE_NOTES_QUEUE_NAME,
    )
    create_user_callback = providers.Factory(
        CreateUserCallback, user_service=user_service
    )
