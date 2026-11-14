from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.ai_client import AIServiceError, demander_plan
from app.rules import verifier_coherence
from app.schemas import ApplicationDescription, MigrationPlan

app = FastAPI(
    title="project-service",
    description="Gère les projets de migration : validation, règles de cohérence, plans.",
    version="0.1.0",
)


class ProjectResponse(BaseModel):
    plan: MigrationPlan
    avertissements: list[str]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "project-service"}


@app.post("/projects", response_model=ProjectResponse)
def creer_projet(description: ApplicationDescription) -> ProjectResponse:
    """Génère le plan de migration d'une application et vérifie sa cohérence."""
    try:
        plan = demander_plan(description)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    avertissements = verifier_coherence(description, plan)
    return ProjectResponse(plan=plan, avertissements=avertissements)