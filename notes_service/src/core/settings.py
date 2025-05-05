import os
import dotenv
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent
dotenv.load_dotenv(os.path.join(BASE_DIR, "..", ".env"))


class PostgresSettings:
    host: str = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port: int = os.getenv("POSTGRES_PORT", 5432)
    user: str = os.getenv("POSTGRES_USER", "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    db: str = os.getenv("POSTGRES_NAME", "postgres")


postgres_settings = PostgresSettings()
