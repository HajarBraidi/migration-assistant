import httpx
import pytest
from fastapi.testclient import TestClient

import app.main as gateway
from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)
    gateway._transport = None


def faux_service(gestionnaire):
    """Remplace le réseau par une fonction qui simule project-service."""
    gateway._transport = httpx.MockTransport(gestionnaire)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "service": "api-gateway"}


def test_transmet_la_creation_et_garde_le_code(client):
    requetes = []

    def gestionnaire(request: httpx.Request) -> httpx.Response:
        requetes.append(request)
        return httpx.Response(201, json={"id": 1, "nom": "StockPro"})

    faux_service(gestionnaire)
    reponse = client.post("/api/projects", json={"nom": "StockPro"})

    assert reponse.status_code == 201
    assert reponse.json()["id"] == 1
    assert requetes[0].method == "POST"
    assert requetes[0].url.path == "/projects"


def test_transmet_les_erreurs_du_service(client):
    faux_service(lambda request: httpx.Response(404, json={"detail": "Projet introuvable."}))

    reponse = client.get("/api/projects/999")

    assert reponse.status_code == 404
    assert reponse.json()["detail"] == "Projet introuvable."


def test_503_si_le_service_ne_repond_pas(client):
    def en_panne(request):
        raise httpx.ConnectError("connexion refusée")

    faux_service(en_panne)
    reponse = client.get("/api/projects")

    assert reponse.status_code == 503