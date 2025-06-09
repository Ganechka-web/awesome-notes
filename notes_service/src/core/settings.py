import os
import dotenv
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent
dotenv.load_dotenv(os.path.join(BASE_DIR, '..', '.env'))


class PostgresSettings:
    host: str = os.getenv('POSTGRES_HOST', '127.0.0.1')
    port: int = os.getenv('POSTGRES_PORT', 5432)
    user: str = os.getenv('POSTGRES_USER', 'postgres')
    password: str = os.getenv('POSTGRES_PASSWORD', 'postgres')
    db: str = os.getenv('POSTGRES_DB', 'postgres')


postgres_settings = PostgresSettings()


class RabbitMQSettings:
    host: str = os.getenv('RABBITMQ_HOST', '127.0.0.1')
    port: int = int(os.getenv('RABBITMQ_PORT', 5672))
    user: str = os.getenv('RABBITMG_USER', 'guest')
    password: str = os.getenv('RABBITMQ_PASSWORD', 'guest')


DELETE_NOTES_QUEUE_NAME = 'delete_notes_queue'
rabbitmq_settings = RabbitMQSettings()
