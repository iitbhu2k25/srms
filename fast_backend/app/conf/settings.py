from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

BASE_DIR = Path(__file__).resolve().parents[2]  # fast_backend/


def get_db_url(drivername: str, settings: "Settings") -> str:
    return URL.create(
        drivername=drivername,
        username=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_DB,
    ).render_as_string(hide_password=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".fastdb.env", extra="ignore")

    # postgres
    POSTGRES_DB: str = "srms"
    POSTGRES_USER: str = "srms"
    POSTGRES_PASSWORD: str = "srms"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433

    CORS_ORIGINS: list[str] = [
        "http://localhost:3010",
        "http://127.0.0.1:3010",
    ]
    ENABLE_API_DOCS: bool = True

    # Dummy-data simulator: keeps appending 15-min readings for active stations so the dashboard stays live.
    # Turn off once real IoT devices push data through POST /api/ingest/readings.
    SIMULATE_LIVE: bool = True
    SIMULATOR_TICK_SECONDS: int = 60

    # A station is shown "offline" when its last reading is older than this.
    OFFLINE_AFTER_MINUTES: int = 60

    # media/: source (seed) data loaded into the database by script/load_database.py
    MEDIA_DIR: Path = BASE_DIR / "media"

    @property
    def DATABASE_URL(self) -> str:
        """Async URL used by the API."""
        return get_db_url("postgresql+asyncpg", self)

    @property
    def DATABASE_SYNC_URL(self) -> str:
        """Sync URL used by Alembic."""
        return get_db_url("postgresql+psycopg2", self)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
