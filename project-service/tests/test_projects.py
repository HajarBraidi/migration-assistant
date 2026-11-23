from tests.conftest import UTILISATEUR_1, UTILISATEUR_2


def test_creer_puis_lire_un_projet(client, description):
    reponse = client.post("/projects", json=description, headers=UTILISATEUR_1)

    assert reponse.status_code == 201
    projet = reponse.json()
    assert projet["nom"] == "StockPro"
    assert projet["plan"]["strategie"]["strategie"] == "Replatform"
    assert projet["description"]["budget"] == "Faible"  # utile au calcul des coûts

    lecture = client.get(f"/projects/{projet['id']}", headers=UTILISATEUR_1)
    assert lecture.status_code == 200
    assert lecture.json()["id"] == projet["id"]


def test_historique_liste_les_projets(client, description):
    client.post("/projects", json=description, headers=UTILISATEUR_1)
    client.post("/projects", json=description, headers=UTILISATEUR_1)

    reponse = client.get("/projects", headers=UTILISATEUR_1)

    assert reponse.status_code == 200
    assert len(reponse.json()) == 2
    assert reponse.json()[0]["strategie"] == "Replatform"


def test_chaque_utilisateur_ne_voit_que_ses_projets(client, description):
    projet = client.post("/projects", json=description, headers=UTILISATEUR_1).json()

    assert client.get("/projects", headers=UTILISATEUR_2).json() == []
    assert client.get(f"/projects/{projet['id']}", headers=UTILISATEUR_2).status_code == 404


def test_identifiant_utilisateur_obligatoire(client, description):
    reponse = client.post("/projects", json=description)

    assert reponse.status_code == 422


def test_projet_inexistant_renvoie_404(client):
    reponse = client.get("/projects/999", headers=UTILISATEUR_1)

    assert reponse.status_code == 404


def test_description_invalide_renvoie_422(client, description):
    description["budget"] = "Pas cher"

    reponse = client.post("/projects", json=description, headers=UTILISATEUR_1)

    assert reponse.status_code == 422
