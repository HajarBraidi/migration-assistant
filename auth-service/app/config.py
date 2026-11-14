from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration d'auth-service."""

    database_url: str = "postgresql+psycopg://auth:auth@auth-db:5432/auth"
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_duree_minutes: int = 60 * 8  # une journée de travail


settings = Settings()
