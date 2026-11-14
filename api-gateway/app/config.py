from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration de l'api-gateway."""

    project_service_url: str = "http://project-service:8000"
    request_timeout_seconds: int = 200
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()