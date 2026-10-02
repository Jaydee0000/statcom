from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env", extra="ignore"
    )
    video_storage_path: Path = Path(__file__).resolve().parents[2] / "storage/videos"
    video_max_upload_bytes: int = 5 * 1024 * 1024 * 1024
    ffprobe_path: str = "ffprobe"
    database_url: str
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("database_url")
    @classmethod
    def postgresql_only(cls, value: str) -> str:
        url = make_url(value)
        if url.get_backend_name() != "postgresql":
            raise ValueError("DATABASE_URL must reference PostgreSQL")
        return url.set(drivername="postgresql+psycopg").render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
