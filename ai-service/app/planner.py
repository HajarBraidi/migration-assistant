from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.llm import LLMError, generate_json
from app.prompt import build_chat_prompt, build_plan_prompt
from app.schemas import ApplicationDescription, MessageChat, MigrationPlan, ReponseAssistant

MAX_TENTATIVES = 2

Modele = TypeVar("Modele", bound=BaseModel)


def _generer_valide(prompt: str, modele: type[Modele]) -> Modele:
    """Envoie le prompt au LLM et vérifie que la réponse respecte le format attendu."""
    derniere_erreur: ValidationError | None = None
    for _ in range(MAX_TENTATIVES):
        reponse = generate_json(prompt)
        try:
            return modele.model_validate_json(reponse)
        except ValidationError as exc:
            derniere_erreur = exc

    raise LLMError(
        f"Le LLM n'a pas produit une réponse valide après {MAX_TENTATIVES} tentatives : "
        f"{derniere_erreur}"
    )


def generate_plan(description: ApplicationDescription) -> MigrationPlan:
    """Génère un plan de migration à partir de la description."""
    return _generer_valide(build_plan_prompt(description), MigrationPlan)


def discuter(
    description: ApplicationDescription,
    plan: MigrationPlan,
    historique: list[MessageChat],
    message: str,
) -> ReponseAssistant:
    """Un tour de conversation : question, explication ou modification du plan."""
    reponse = _generer_valide(
        build_chat_prompt(description, plan, historique, message), ReponseAssistant
    )
    # Garde-fou : un « nouveau » plan identique à l'actuel n'est pas une modification
    if reponse.type == "modification" and reponse.plan == plan:
        return ReponseAssistant(type="reponse", message=reponse.message)
    return reponse
