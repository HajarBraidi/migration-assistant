import httpx

from app.config import settings
from app.schemas import ApplicationDescription, MigrationPlan


class AIServiceError(Exception):
    """Erreur lors de l'appel à ai-service."""


def demander_plan(description: ApplicationDescription) -> MigrationPlan:
    """Demande à ai-service de générer le plan de migration."""
    try:
        response = httpx.post(
            f"{settings.ai_service_url}/generate-plan",
            json=description.model_dump(mode="json"),
            timeout=settings.ai_service_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise AIServiceError(f"ai-service est injoignable : {exc}") from exc

    if response.status_code != 200:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise AIServiceError(f"ai-service a renvoyé l'erreur {response.status_code} : {detail}")

    return MigrationPlan.model_validate(response.json())