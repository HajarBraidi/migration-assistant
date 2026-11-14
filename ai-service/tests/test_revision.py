import json

from app.prompt import build_revision_prompt
from app.schemas import ApplicationDescription, MigrationPlan


def test_revise_plan_renvoie_la_nouvelle_version(client, monkeypatch, description, plan_valide):
    nouveau = {**plan_valide, "strategie": {"strategie": "Rehost", "justification": "Moins cher."}}
    prompts = []

    def faux_llm(prompt):
        prompts.append(prompt)
        return json.dumps(nouveau)

    monkeypatch.setattr("app.planner.generate_json", faux_llm)

    reponse = client.post(
        "/revise-plan",
        json={"description": description, "plan": plan_valide, "demande": "Option moins chère"},
    )

    assert reponse.status_code == 200
    assert reponse.json()["strategie"]["strategie"] == "Rehost"
    assert "Option moins chère" in prompts[0]


def test_demande_trop_courte_refusee(client, description, plan_valide):
    reponse = client.post(
        "/revise-plan", json={"description": description, "plan": plan_valide, "demande": "a"}
    )

    assert reponse.status_code == 422


def test_le_prompt_contient_le_plan_actuel_et_la_demande(description, plan_valide):
    prompt = build_revision_prompt(
        ApplicationDescription(**description), MigrationPlan(**plan_valide), "Je préfère AWS"
    )

    assert "Je préfère AWS" in prompt
    assert "Plan de migration actuel" in prompt
    assert "Replatform" in prompt  # le plan actuel est bien transmis
