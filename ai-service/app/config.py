from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration du service, lue depuis les variables d'environnement."""

    gemini_api_key: str
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_fallback_model: str | None = "gemini-3.1-flash-lite"
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 3


settings = Settings()