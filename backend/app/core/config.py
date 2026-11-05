from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "TalentHub"
    api_prefix: str = "/api/v1"
    database_url: str
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 8
    auth_cookie_name: str = "talenthub_session"
    cookie_secure: bool = False
    trusted_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    frontend_dist_path: Path = Path("../frontend/dist")

    demo_student_password: str | None = None
    demo_institution_password: str | None = None
    demo_company_password: str | None = None
    mock_data_password: str | None = None

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.trusted_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
