import pytest
from fastapi.testclient import TestClient

from app.main import app

DEMANDE = {
    "nom": "RH Portal",
    "langage": "Java",
    "framework_backend": "Spring Boot 2.3",
    "type_base_donnees": "Oracle",
    "base_cible": "PostgreSQL",
    "fournisseur": "AWS",
    "nombre_utilisateurs": "100 à 1 000",
    "volume_donnees": "10 à 100 Go",
    "haute_disponibilite": False,
}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def generer(client: TestClient, **modifications) -> dict:
    reponse = client.post("/kits", json={**DEMANDE, **modifications})
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


def fichier(kit: dict, chemin: str) -> str:
    return next(f["contenu"] for f in kit["fichiers"] if f["chemin"] == chemin)


def chemins(kit: dict) -> set[str]:
    return {f["chemin"] for f in kit["fichiers"]}
