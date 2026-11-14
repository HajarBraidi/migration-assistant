import json

import pytest

from app.llm import LLMError
from app.planner import generate_plan
from app.prompt import build_plan_prompt
from app.schemas import ApplicationDescription


def test_nouvelle_tentative_si_la_reponse_est_invalide(monkeypatch, description, plan_valide):
    reponses = iter(["{}", json.dumps(plan_valide)])  # 1re réponse invalide, 2e valide
    appels = []

    def faux_llm(prompt):
        appels.append(prompt)
        return next(reponses)

    monkeypatch.setattr("app.planner.generate_json", faux_llm)

    plan = generate_plan(ApplicationDescription(**description))

    assert len(appels) == 2
    assert plan.strategie.strategie == "Replatform"


def test_erreur_apres_deux_reponses_invalides(monkeypatch, description):
    monkeypatch.setattr("app.planner.generate_json", lambda prompt: "{}")

    with pytest.raises(LLMError):
        generate_plan(ApplicationDescription(**description))


def test_le_prompt_contient_les_donnees_et_le_format(description):
    prompt = build_plan_prompt(ApplicationDescription(**description))

    assert "StockPro" in prompt  # les données de l'utilisateur
    assert "7R" in prompt  # les règles
    assert "resume_existant" in prompt  # le schéma JSON attendu