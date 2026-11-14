from tests.conftest import UTILISATEUR_1, UTILISATEUR_2


def creer_projet(client, description):
    return client.post("/projects", json=description, headers=UTILISATEUR_1).json()


def test_reviser_met_a_jour_le_plan_et_garde_l_historique(client, description):
    projet = creer_projet(client, description)

    reponse = client.post(
        f"/projects/{projet['id']}/revisions",
        json={"demande": "Propose une option moins chère"},
        headers=UTILISATEUR_1,
    )

    assert reponse.status_code == 200
    resultat = reponse.json()
    assert resultat["plan"]["strategie"]["strategie"] == "Rehost"
    assert [r["demande"] for r in resultat["revisions"]] == ["Propose une option moins chère"]


def test_les_revisions_s_accumulent(client, description):
    projet = creer_projet(client, description)
    url = f"/projects/{projet['id']}/revisions"

    client.post(url, json={"demande": "Option moins chère"}, headers=UTILISATEUR_1)
    client.post(url, json={"demande": "Je préfère AWS"}, headers=UTILISATEUR_1)

    lecture = client.get(f"/projects/{projet['id']}", headers=UTILISATEUR_1).json()
    assert [r["demande"] for r in lecture["revisions"]] == ["Option moins chère", "Je préfère AWS"]


def test_impossible_de_reviser_le_projet_d_un_autre(client, description):
    projet = creer_projet(client, description)

    reponse = client.post(
        f"/projects/{projet['id']}/revisions", json={"demande": "Option moins chère"}, headers=UTILISATEUR_2
    )

    assert reponse.status_code == 404


def test_demande_vide_refusee(client, description):
    projet = creer_projet(client, description)

    reponse = client.post(
        f"/projects/{projet['id']}/revisions", json={"demande": ""}, headers=UTILISATEUR_1
    )

    assert reponse.status_code == 422
