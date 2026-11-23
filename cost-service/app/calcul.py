"""Calcul des coûts mensuels par fournisseur, à partir de tarifs.json."""

import json
from pathlib import Path

from app.schemas import DemandeEstimation, Dimensionnement, Estimation, Ligne, Offre

TARIFS = json.loads((Path(__file__).parent / "tarifs.json").read_text(encoding="utf-8"))

# Dimensionnement par nombre d'utilisateurs : (serveurs, taille, trafic sortant en Go/mois)
DIMENSIONS = {
    "< 100": (1, "small", 20),
    "100 à 1 000": (1, "medium", 100),
    "1 000 à 50 000": (2, "large", 1000),
    "> 50 000": (3, "xlarge", 10000),
}
TAILLES = {
    "small": "2 vCPU, 2 Go de mémoire",
    "medium": "2 vCPU, 4 Go de mémoire",
    "large": "2 vCPU, 8 Go de mémoire",
    "xlarge": "4 vCPU, 16 Go de mémoire",
}
STOCKAGE_GO = {"< 10 Go": 20, "10 à 100 Go": 150, "100 Go à 1 To": 1000, "> 1 To": 3000}
DISQUE_SERVEUR_GO = 30
# Les bases sous licence coûtent environ deux fois plus cher en service géré
MOTEURS_SOUS_LICENCE = {"Oracle", "SQL Server"}
FACTEUR_LICENCE = 2.0
# Services gérés proposés pour chaque moteur sous licence
SERVICES_LICENCE = {
    ("AWS", "Oracle"): "Amazon RDS for Oracle (licence incluse)",
    ("AWS", "SQL Server"): "Amazon RDS for SQL Server (licence incluse)",
    ("Azure", "SQL Server"): "Azure SQL Database (licence incluse)",
    ("GCP", "SQL Server"): "Cloud SQL for SQL Server (licence incluse)",
}


def dimensionner(demande: DemandeEstimation) -> Dimensionnement:
    serveurs, taille, trafic = DIMENSIONS[demande.nombre_utilisateurs]
    if demande.haute_disponibilite:
        serveurs = max(serveurs, 2)  # au moins deux serveurs, dans deux zones
    return Dimensionnement(
        serveurs=serveurs,
        taille=taille,
        description_taille=TAILLES[taille],
        base_de_donnees=demande.type_base_donnees,
        instances_base=2 if demande.haute_disponibilite else 1,
        stockage_go=STOCKAGE_GO[demande.volume_donnees],
        trafic_sortant_go=trafic,
        repartiteur_de_charge=serveurs > 1,
    )


def _en_euros(montant: float, devise: str) -> float:
    return montant * TARIFS["taux_de_change"]["usd_vers_eur"] if devise == "USD" else montant


def _offre(code: str, d: Dimensionnement) -> Offre:
    t = TARIFS["fournisseurs"][code]
    heures = TARIFS["heures_par_mois"]
    licence = FACTEUR_LICENCE if d.base_de_donnees in MOTEURS_SOUS_LICENCE else 1.0
    lignes: list[tuple[str, str, float]] = []

    if code == "OVHcloud":
        prix_vps = t["serveur_par_mois"][d.taille]
        lignes.append((
            "Serveurs d'application",
            f"{d.serveurs} × {t['serveur_reference'][d.taille]} ({t['serveur_caracteristiques'][d.taille]})",
            d.serveurs * prix_vps,
        ))
        lignes.append((
            "Base de données",
            f"{d.instances_base} × {t['serveur_reference'][d.taille]} — {t['base_reference']}",
            d.instances_base * prix_vps,
        ))
        if licence > 1:
            lignes.append((
                f"Licence {d.base_de_donnees}",
                "Non incluse : à acheter auprès de l'éditeur (souvent plusieurs milliers d'euros par an)",
                0.0,
            ))
        supplement = max(0, d.stockage_go - t["disque_inclus_go"][d.taille])
        lignes.append((
            "Stockage supplémentaire",
            f"{supplement} Go au-delà du disque inclus",
            supplement * t["stockage_par_go_mois"] * d.instances_base,
        ))
        lignes.append(("Sauvegardes", "Sauvegarde quotidienne incluse", 0.0))
        lignes.append(("Trafic sortant", "Trafic illimité inclus", 0.0))
    else:
        lignes.append((
            "Serveurs d'application",
            f"{d.serveurs} × {t['serveur_reference'][d.taille]} ({d.description_taille})",
            d.serveurs * t["serveur_par_heure"][d.taille] * heures,
        ))
        if licence > 1:
            service = SERVICES_LICENCE.get(
                (code, d.base_de_donnees),
                f"pas de service {d.base_de_donnees} géré : estimation pour un serveur équivalent, "
                "licence à acheter en plus",
            )
        else:
            service = t["base_reference"]
        lignes.append((
            "Base de données gérée",
            f"{d.instances_base} instance(s) — {service}",
            d.instances_base * t["base_par_heure"][d.taille] * heures * licence,
        ))
        disques = d.stockage_go * d.instances_base + DISQUE_SERVEUR_GO * d.serveurs
        lignes.append(("Stockage", f"{disques} Go de disques SSD", disques * t["stockage_par_go_mois"]))
        lignes.append((
            "Sauvegardes",
            f"{d.stockage_go} Go (une copie complète des données)",
            d.stockage_go * t["sauvegarde_par_go_mois"],
        ))
        payant = max(0, d.trafic_sortant_go - t["trafic_gratuit_go"])
        lignes.append((
            "Trafic sortant",
            f"{d.trafic_sortant_go} Go/mois estimés ({t['trafic_gratuit_go']} Go gratuits)",
            payant * t["trafic_sortant_par_go"],
        ))

    if d.repartiteur_de_charge:
        lignes.append(("Répartiteur de charge", "Répartit le trafic entre les serveurs", t["repartiteur_par_mois"]))

    lignes_eur = [
        Ligne(
            poste=p, detail=detail, cout_mensuel_eur=round(_en_euros(c, t["devise"]), 2),
            prix_texte=None if c else ("En plus" if p.startswith("Licence") else "Inclus"),
        )
        for p, detail, c in lignes
    ]
    total = round(sum(l.cout_mensuel_eur for l in lignes_eur), 2)
    return Offre(
        fournisseur=code, nom=t["nom"], region=t["region"], lignes=lignes_eur,
        gestion="Serveurs à administrer" if code == "OVHcloud" else "Services gérés",
        total_mensuel_eur=total, total_annuel_eur=round(total * 12, 2), calculateur=t["calculateur"],
    )


def _remarques(demande: DemandeEstimation, d: Dimensionnement, offres: list[Offre]) -> list[str]:
    remarques = []
    if d.base_de_donnees in MOTEURS_SOUS_LICENCE:
        # Économie mesurée sur l'offre gérée la moins chère (licence incluse dans le prix)
        gerees = [o for o in offres if o.gestion == "Services gérés"]
        sans_licence = {
            o.fournisseur: o.total_mensuel_eur
            for o in estimer(demande.model_copy(update={"type_base_donnees": "PostgreSQL"})).offres
        }
        economie = gerees[0].total_mensuel_eur - sans_licence[gerees[0].fournisseur]
        remarques.append(
            f"{d.base_de_donnees} est sous licence : en service géré, la base coûte environ deux fois "
            f"plus cher, et sur un serveur à administrer la licence s'achète en plus. Migrer vers "
            f"PostgreSQL (open source) économiserait environ {economie:.0f} € par mois "
            f"chez {gerees[0].nom}, soit {economie * 12:.0f} € par an."
        )
    if demande.haute_disponibilite:
        remarques.append(
            "Haute disponibilité : deux serveurs minimum et une base de données répliquée, "
            "pour éviter toute interruption de service."
        )
    remarques.append(
        "OVHcloud est nettement moins cher car il fournit des serveurs à administrer : l'équipe gère "
        "elle-même la base de données, les mises à jour de sécurité, la réplication et la surveillance. "
        "AWS, Azure et Google Cloud vendent des services gérés qui font ce travail à sa place."
    )
    remarques.append(
        "Un engagement d'un ou trois ans réduit généralement le coût de 30 à 60 % chez AWS, Azure et Google Cloud."
    )
    return remarques


def estimer(demande: DemandeEstimation) -> Estimation:
    d = dimensionner(demande)
    offres = sorted(
        (_offre(code, d) for code in TARIFS["fournisseurs"]), key=lambda o: o.total_mensuel_eur
    )
    estimation = Estimation(
        dimensionnement=d,
        offres=offres,
        moins_chere=offres[0].fournisseur,
        remarques=[],
        releve_le=TARIFS["releve_le"],
        eur_vers_mad=TARIFS["taux_de_change"]["eur_vers_mad"],
    )
    estimation.remarques = _remarques(demande, d, offres)
    return estimation
