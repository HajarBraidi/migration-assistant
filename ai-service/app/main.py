from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.llm import LLMError
from app.planner import discuter, generate_plan
from app.schemas import ApplicationDescription, MessageChat, MigrationPlan, ReponseAssistant

app = FastAPI(
    title="ai-service",
    description="Génère le plan de migration et dialogue avec l'utilisateur à l'aide d'un LLM.",
    version="0.4.0",
)


class ChatRequest(BaseModel):
    description: ApplicationDescription
    plan: MigrationPlan
    historique: list[MessageChat] = []
    message: str = Field(min_length=1, max_length=1000)


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


@app.post("/chat", response_model=ReponseAssistant)
def chat_route(requete: ChatRequest) -> ReponseAssistant:
    """Un tour de conversation avec l'assistant à propos du plan."""
    try:
        return discuter(requete.description, requete.plan, requete.historique, requete.message)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
