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
    database_schema: str = Field(
        default="talenthub_v2", pattern=r"^[a-z][a-z0-9_]{0,62}$"
    )
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    trusted_origins: str = "*"

    @property
    def allowed_origins(self) -> list[str]:
        return [
            v.strip().rstrip("/") for v in self.trusted_origins.split(",") if v.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
