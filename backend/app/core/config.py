from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"), env_file_encoding="utf-8", extra="ignore"
    )
    app_name: str = "TalentHub"
    api_prefix: str = "/api/v1"
    database_url: str
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    trusted_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def allowed_origins(self) -> list[str]:
        return [
            v.strip().rstrip("/") for v in self.trusted_origins.split(",") if v.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
