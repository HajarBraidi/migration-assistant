def test_creer_puis_lire_un_projet(client, description):
    reponse = client.post("/projects", json=description)

    assert reponse.status_code == 201
    projet = reponse.json()
    assert projet["nom"] == "StockPro"
    assert projet["plan"]["strategie"]["strategie"] == "Replatform"

    lecture = client.get(f"/projects/{projet['id']}")
    assert lecture.status_code == 200
    assert lecture.json()["id"] == projet["id"]


def test_historique_liste_les_projets(client, description):
    client.post("/projects", json=description)
    client.post("/projects", json=description)

    reponse = client.get("/projects")

    assert reponse.status_code == 200
    assert len(reponse.json()) == 2
    assert reponse.json()[0]["strategie"] == "Replatform"


def test_projet_inexistant_renvoie_404(client):
    reponse = client.get("/projects/999")

    assert reponse.status_code == 404


def test_description_invalide_renvoie_422(client, description):
    description["budget"] = "Pas cher"

    reponse = client.post("/projects", json=description)

    assert reponse.status_code == 422