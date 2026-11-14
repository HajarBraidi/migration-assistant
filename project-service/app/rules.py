from app.schemas import ApplicationDescription, MigrationPlan

# Délai souhaité converti en nombre maximum de semaines
DELAI_MAX_SEMAINES = {
    "< 3 mois": 13,
    "3 à 6 mois": 26,
    "6 à 12 mois": 52,
    "> 12 mois": None,  # pas de limite
}


def verifier_coherence(description: ApplicationDescription, plan: MigrationPlan) -> list[str]:
    """Vérifie que le plan respecte les contraintes. Renvoie la liste des avertissements."""
    avertissements: list[str] = []

    if plan.strategie.strategie == "Refactor" and (
        description.budget == "Faible" or description.delai == "< 3 mois"
    ):
        avertissements.append(
            "La stratégie Refactor est peu adaptée à un budget faible "
            "ou à un délai de moins de 3 mois."
        )

    if description.interruption_acceptable == "Aucune" and plan.bascule.type == "Big bang":
        avertissements.append(
            "Aucune interruption n'est acceptable : une bascule progressive est recommandée."
        )

    delai_max = DELAI_MAX_SEMAINES[description.delai]
    duree = plan.estimation.duree_totale_semaines
    if delai_max is not None and duree > delai_max:
        avertissements.append(
            f"La durée estimée ({duree} semaines) dépasse le délai souhaité ({description.delai})."
        )

    somme_phases = sum(phase.duree_semaines for phase in plan.phases)
    if somme_phases != duree:
        avertissements.append(
            f"La somme des phases ({somme_phases} semaines) ne correspond pas "
            f"à la durée totale ({duree} semaines)."
        )

    return avertissements