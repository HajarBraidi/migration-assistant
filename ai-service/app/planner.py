from pydantic import ValidationError

from app.llm import LLMError, generate_json
from app.prompt import build_plan_prompt
from app.schemas import ApplicationDescription, MigrationPlan

MAX_TENTATIVES = 2


def generate_plan(description: ApplicationDescription) -> MigrationPlan:
    """Génère un plan de migration et vérifie qu'il respecte le format attendu."""
    prompt = build_plan_prompt(description)

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