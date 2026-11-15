import httpx

from app.config import settings
from app.schemas import ApplicationDescription, MessageChat, MigrationPlan, ReponseAssistant


class AIServiceError(Exception):
    """Erreur lors de l'appel à ai-service."""


def _appeler(route: str, donnees: dict) -> dict:
    """Appelle une route d'ai-service et renvoie sa réponse JSON."""
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

    return response.json()


def demander_plan(description: ApplicationDescription) -> MigrationPlan:
    """Demande à ai-service de générer le plan de migration."""
    return MigrationPlan.model_validate(
        _appeler("/generate-plan", description.model_dump(mode="json"))
    )


def discuter(
    description: ApplicationDescription,
    plan: MigrationPlan,
    historique: list[MessageChat],
    message: str,
) -> ReponseAssistant:
    """Envoie un message à l'assistant et renvoie sa réponse."""
    return ReponseAssistant.model_validate(
        _appeler(
            "/chat",
            {
                "description": description.model_dump(mode="json"),
                "plan": plan.model_dump(mode="json"),
                "historique": [m.model_dump() for m in historique],
                "message": message,
            },
        )
    )
