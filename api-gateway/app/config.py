from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration de l'api-gateway."""

    project_service_url: str = "http://project-service:8000"
    auth_service_url: str = "http://auth-service:8000"
    analysis_service_url: str = "http://analysis-service:8000"
    cost_service_url: str = "http://cost-service:8000"
    deploy_service_url: str = "http://deploy-service:8000"
    request_timeout_seconds: int = 200
    cors_origins: list[str] = ["http://localhost:5173"]
    jwt_secret: str
    jwt_algorithm: str = "HS256"


settings = Settings()
