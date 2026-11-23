import pytest
from fastapi.testclient import TestClient

from app.calcul import TARIFS
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def estimer(client, **besoins):
    demande = {"nombre_utilisateurs": "100 à 1 000", "volume_donnees": "< 10 Go", **besoins}
    reponse = client.post("/estimations", json=demande)
    assert reponse.status_code == 200
    return reponse.json()


def test_quatre_fournisseurs_du_moins_cher_au_plus_cher(client):
    resultat = estimer(client)
    totaux = [o["total_mensuel_eur"] for o in resultat["offres"]]

    assert {o["fournisseur"] for o in resultat["offres"]} == {"AWS", "Azure", "GCP", "OVHcloud"}
    assert totaux == sorted(totaux)
    assert resultat["moins_chere"] == resultat["offres"][0]["fournisseur"]


def test_le_total_est_la_somme_des_lignes(client):
    for offre in estimer(client)["offres"]:
        assert offre["total_mensuel_eur"] == pytest.approx(sum(l["cout_mensuel_eur"] for l in offre["lignes"]), abs=0.05)
        assert offre["total_annuel_eur"] == pytest.approx(offre["total_mensuel_eur"] * 12, abs=0.5)


def test_calcul_aws_verifiable_a_la_main(client):
    aws = next(o for o in estimer(client)["offres"] if o["fournisseur"] == "AWS")
    serveur = next(l for l in aws["lignes"] if l["poste"] == "Serveurs d'application")
    t = TARIFS["fournisseurs"]["AWS"]

    attendu = t["serveur_par_heure"]["medium"] * 730 * TARIFS["taux_de_change"]["usd_vers_eur"]
    assert serveur["cout_mensuel_eur"] == pytest.approx(attendu, abs=0.01)
    assert "t3.medium" in serveur["detail"]


def test_plus_d_utilisateurs_coute_plus_cher(client):
    petit = estimer(client, nombre_utilisateurs="< 100")
    grand = estimer(client, nombre_utilisateurs="> 50 000")

    for fournisseur in ("AWS", "Azure", "GCP", "OVHcloud"):
        cout = lambda r: next(o for o in r["offres"] if o["fournisseur"] == fournisseur)["total_mensuel_eur"]
        assert cout(grand) > cout(petit)


def test_haute_disponibilite_double_la_base_et_ajoute_un_repartiteur(client):
    resultat = estimer(client, haute_disponibilite=True)

    assert resultat["dimensionnement"]["serveurs"] >= 2
    assert resultat["dimensionnement"]["instances_base"] == 2
    assert resultat["dimensionnement"]["repartiteur_de_charge"] is True


def test_base_sous_licence_et_economie_avec_postgresql(client):
    oracle = estimer(client, type_base_donnees="Oracle")
    postgres = estimer(client, type_base_donnees="PostgreSQL")

    aws = lambda r: next(o for o in r["offres"] if o["fournisseur"] == "AWS")["total_mensuel_eur"]
    assert aws(oracle) > aws(postgres)
    assert any("PostgreSQL" in r and "économiserait" in r for r in oracle["remarques"])
    ovh = next(o for o in oracle["offres"] if o["fournisseur"] == "OVHcloud")
    licence = next(l for l in ovh["lignes"] if l["poste"] == "Licence Oracle")
    assert licence["prix_texte"] == "En plus"  # jamais « Inclus »


def test_gestion_indiquee_pour_chaque_offre(client):
    gestions = {o["fournisseur"]: o["gestion"] for o in estimer(client)["offres"]}

    assert gestions["OVHcloud"] == "Serveurs à administrer"
    assert gestions["AWS"] == "Services gérés"


def test_valeur_hors_liste_refusee(client):
    reponse = client.post("/estimations", json={"nombre_utilisateurs": "beaucoup", "volume_donnees": "< 10 Go"})

    assert reponse.status_code == 422


def test_tarifs_dates_et_consultables(client):
    tarifs = client.get("/tarifs").json()

    assert tarifs["releve_le"]
    assert set(tarifs["fournisseurs"]) == {"AWS", "Azure", "GCP", "OVHcloud"}
