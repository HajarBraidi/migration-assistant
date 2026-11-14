import json

from app.llm import LLMError


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ai-service"}


def test_generate_plan_renvoie_le_plan(client, monkeypatch, description, plan_valide):
    # On remplace l'appel à Gemini par une fausse réponse
    monkeypatch.setattr("app.planner.generate_json", lambda prompt: json.dumps(plan_valide))

    response = client.post("/generate-plan", json=description)

    assert response.status_code == 200
    assert response.json()["strategie"]["strategie"] == "Replatform"


def test_generate_plan_refuse_une_valeur_invalide(client, description):
    description["budget"] = "Pas cher"

    response = client.post("/generate-plan", json=description)

    assert response.status_code == 422


def test_generate_plan_refuse_un_champ_manquant(client, description):
    del description["nom"]

    response = client.post("/generate-plan", json=description)

    assert response.status_code == 422


def test_generate_plan_renvoie_502_si_le_llm_echoue(client, monkeypatch, description):
    def llm_en_panne(prompt):
        raise LLMError("Gemini indisponible")

    monkeypatch.setattr("app.planner.generate_json", llm_en_panne)

    response = client.post("/generate-plan", json=description)

    assert response.status_code == 502
    assert "Gemini indisponible" in response.json()["detail"]