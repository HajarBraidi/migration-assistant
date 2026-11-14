from app.rules import verifier_coherence
from app.schemas import ApplicationDescription


def test_plan_coherent_sans_avertissement(description, plan_valide):
    avertissements = verifier_coherence(ApplicationDescription(**description), plan_valide)

    assert avertissements == []


def test_refactor_avec_budget_faible_donne_un_avertissement(description, plan_valide):
    plan_valide.strategie.strategie = "Refactor"

    avertissements = verifier_coherence(ApplicationDescription(**description), plan_valide)

    assert any("Refactor" in a for a in avertissements)


def test_big_bang_sans_interruption_donne_un_avertissement(description, plan_valide):
    description["interruption_acceptable"] = "Aucune"

    avertissements = verifier_coherence(ApplicationDescription(**description), plan_valide)

    assert any("progressive" in a for a in avertissements)


def test_somme_des_phases_differente_de_la_duree(description, plan_valide):
    plan_valide.estimation.duree_totale_semaines = 10

    avertissements = verifier_coherence(ApplicationDescription(**description), plan_valide)

    assert any("somme des phases" in a for a in avertissements)