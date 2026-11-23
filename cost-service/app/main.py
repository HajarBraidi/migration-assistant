from fastapi import FastAPI

from app.calcul import TARIFS, estimer
from app.schemas import DemandeEstimation, Estimation

app = FastAPI(
    title="cost-service",
    description="Estime le coût mensuel d'hébergement chez AWS, Azure, Google Cloud et OVHcloud.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "cost-service"}


@app.post("/estimations", response_model=Estimation)
def creer_estimation(demande: DemandeEstimation) -> Estimation:
    """Compare les fournisseurs pour les besoins indiqués (tarifs dans app/tarifs.json)."""
    return estimer(demande)


@app.get("/tarifs")
def tarifs() -> dict:
    """Les tarifs utilisés, pour la transparence (date du relevé incluse)."""
    return TARIFS
