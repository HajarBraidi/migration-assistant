from pydantic import ValidationError

from app.llm import LLMError, generate_json
from app.prompt import build_plan_prompt, build_revision_prompt
from app.schemas import ApplicationDescription, MigrationPlan

MAX_TENTATIVES = 2


def _generer_plan_valide(prompt: str) -> MigrationPlan:
    """Envoie le prompt au LLM et vérifie que la réponse est un plan valide."""
    derniere_erreur: ValidationError | None = None
    for _ in range(MAX_TENTATIVES):
        reponse = generate_json(prompt)
        try:
            return MigrationPlan.model_validate_json(reponse)
        except ValidationError as exc:
            derniere_erreur = exc

    raise LLMError(
        f"Le LLM n'a pas produit un plan valide après {MAX_TENTATIVES} tentatives : "
        f"{derniere_erreur}"
    )


def generate_plan(description: ApplicationDescription) -> MigrationPlan:
    """Génère un plan de migration à partir de la description."""
    return _generer_plan_valide(build_plan_prompt(description))


def revise_plan(
    description: ApplicationDescription, plan: MigrationPlan, demande: str
) -> MigrationPlan:
    """Produit une nouvelle version du plan qui applique la demande de l'utilisateur."""
    return _generer_plan_valide(build_revision_prompt(description, plan, demande))
