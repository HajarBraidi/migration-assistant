from fastapi import FastAPI

app = FastAPI(
    title="ai-service",
    description="Génère le plan de migration à l'aide d'un LLM.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict:
    """Vérifie que le service fonctionne."""
    return {"status": "ok", "service": "ai-service"}