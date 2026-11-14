from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration de project-service."""

    ai_service_url: str = "http://ai-service:8000"
    ai_service_timeout_seconds: int = 180


settings = Settings()