import httpx

from app.config import settings
from app.schemas import ApplicationDescription, MigrationPlan


class AIServiceError(Exception):
    """Erreur lors de l'appel à ai-service."""


def _appeler(route: str, donnees: dict) -> MigrationPlan:
    """Appelle une route d'ai-service et renvoie le plan obtenu."""
    try:
        response = httpx.post(
            f"{settings.ai_service_url}{route}",
            json=donnees,
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


def demander_plan(description: ApplicationDescription) -> MigrationPlan:
    """Demande à ai-service de générer le plan de migration."""
    return _appeler("/generate-plan", description.model_dump(mode="json"))


def demander_revision(
    description: ApplicationDescription, plan: MigrationPlan, demande: str
) -> MigrationPlan:
    """Demande à ai-service une nouvelle version du plan."""
    return _appeler(
        "/revise-plan",
        {
            "description": description.model_dump(mode="json"),
            "plan": plan.model_dump(mode="json"),
            "demande": demande,
        },
    )
