from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.llm import LLMError, generate_text

app = FastAPI(
    title="ai-service",
    description="Génère le plan de migration à l'aide d'un LLM.",
    version="0.1.0",
)


class LLMTestRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class LLMTestResponse(BaseModel):
    answer: str


@app.get("/health")
def health() -> dict:
    """Vérifie que le service fonctionne."""
    return {"status": "ok", "service": "ai-service"}


@app.post("/llm-test", response_model=LLMTestResponse)
def llm_test(request: LLMTestRequest) -> LLMTestResponse:
    """Route temporaire : vérifie la connexion au LLM."""
    try:
        answer = generate_text(request.question)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return LLMTestResponse(answer=answer)