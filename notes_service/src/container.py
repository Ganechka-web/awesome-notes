from dependency_injector import containers, providers

from core.database import AsyncDatabase
from repositories.note import NoteRepository
from services.note import NoteService
from core.broker import AsyncBroker
from broker.callbacks import DeleteAllUserNotesCallback


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=["api.endpoints.note"])
    config = providers.Configuration()

    note_database = providers.Singleton(
        AsyncDatabase,
        host=config.postgres_settings.host,
        port=config.postgres_settings.port,
        username=config.postgres_settings.user,
        password=config.postgres_settings.password,
        db=config.postgres_settings.db,
    )
    note_repository = providers.Factory(NoteRepository, database=note_database)
    note_service = providers.Factory(NoteService, repository=note_repository)
    note_broker = providers.Singleton(
        AsyncBroker,
        host=config.rabbitmq_settings.host,
        port=config.rabbitmq_settings.port,
        login=config.rabbitmq_settings.user,
        password=config.rabbitmq_settings.password,
    )
    delete_all_user_notes_callback = providers.Factory(
        DeleteAllUserNotesCallback, note_service=note_service
    )
