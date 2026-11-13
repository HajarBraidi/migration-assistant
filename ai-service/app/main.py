from fastapi import FastAPI, HTTPException

from app.llm import LLMError
from app.planner import generate_plan
from app.schemas import ApplicationDescription, MigrationPlan

app = FastAPI(
    title="ai-service",
    description="Génère le plan de migration à l'aide d'un LLM.",
    version="0.2.0",
)


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