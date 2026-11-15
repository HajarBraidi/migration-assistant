import json

import pytest
from pydantic import ValidationError

from app.prompt import build_chat_prompt
from app.schemas import ApplicationDescription, MessageChat, MigrationPlan, ReponseAssistant


def requete(description, plan, message, historique=None):
    return {"description": description, "plan": plan, "message": message, "historique": historique or []}


def faux_llm(monkeypatch, reponse: dict, prompts: list | None = None):
    def llm(prompt):
        if prompts is not None:
            prompts.append(prompt)
        return json.dumps(reponse)

    monkeypatch.setattr("app.planner.generate_json", llm)


def test_message_incomprehensible_donne_une_question(client, monkeypatch, description, plan_valide):
    faux_llm(monkeypatch, {"type": "question", "message": "Je n'ai pas compris, pouvez-vous préciser ?"})

    reponse = client.post("/chat", json=requete(description, plan_valide, "bhjhbjbj"))

    assert reponse.status_code == 200
    assert reponse.json()["type"] == "question"
    assert reponse.json()["plan"] is None


def test_modification_renvoie_le_nouveau_plan(client, monkeypatch, description, plan_valide):
    nouveau = {**plan_valide, "strategie": {"strategie": "Rehost", "justification": "Moins cher."}}
    faux_llm(monkeypatch, {"type": "modification", "message": "Je passe en Rehost.", "plan": nouveau})

    reponse = client.post("/chat", json=requete(description, plan_valide, "Option moins chère"))

    assert reponse.json()["type"] == "modification"
    assert reponse.json()["plan"]["strategie"]["strategie"] == "Rehost"


def test_plan_identique_n_est_pas_une_modification(client, monkeypatch, description, plan_valide):
    faux_llm(monkeypatch, {"type": "modification", "message": "Voici le plan.", "plan": plan_valide})

    reponse = client.post("/chat", json=requete(description, plan_valide, "Change rien"))

    assert reponse.json()["type"] == "reponse"
    assert reponse.json()["plan"] is None


def test_modification_sans_plan_est_invalide():
    with pytest.raises(ValidationError):
        ReponseAssistant(type="modification", message="Je modifie.")


def test_le_prompt_contient_la_conversation_et_le_message(description, plan_valide):
    historique = [
        MessageChat(role="utilisateur", contenu="Peut-on réduire le coût ?"),
        MessageChat(role="assistant", contenu="Oui : Rehost ou Replatform allégé ?"),
    ]
    prompt = build_chat_prompt(
        ApplicationDescription(**description), MigrationPlan(**plan_valide), historique, "Rehost"
    )

    assert "Peut-on réduire le coût ?" in prompt
    assert "<message>\nRehost\n</message>" in prompt
    assert "Replatform" in prompt  # le plan actuel est transmis


def test_message_vide_refuse(client, description, plan_valide):
    assert client.post("/chat", json=requete(description, plan_valide, "")).status_code == 422
