from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.llm import LLMError
from app.planner import generate_plan, revise_plan
from app.schemas import ApplicationDescription, MigrationPlan

app = FastAPI(
    title="ai-service",
    description="Génère et ajuste le plan de migration à l'aide d'un LLM.",
    version="0.3.0",
)


class RevisionRequest(BaseModel):
    description: ApplicationDescription
    plan: MigrationPlan
    demande: str = Field(min_length=3, max_length=500)


@app.get("/health")
def health() -> dict:
    """Vérifie que le service fonctionne."""
    return {"status": "ok", "service": "ai-service"}


@app.post("/generate-plan", response_model=MigrationPlan)
def generate_plan_route(description: ApplicationDescription) -> MigrationPlan:
    """Génère un plan de migration à partir de la description de l'application."""
    try:
        return generate_plan(description)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/revise-plan", response_model=MigrationPlan)
def revise_plan_route(requete: RevisionRequest) -> MigrationPlan:
    """Produit une nouvelle version du plan selon la demande de l'utilisateur."""
    try:
        return revise_plan(requete.description, requete.plan, requete.demande)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
