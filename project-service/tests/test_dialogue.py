from tests.conftest import UTILISATEUR_1, UTILISATEUR_2


def creer_projet(client, description):
    return client.post("/projects", json=description, headers=UTILISATEUR_1).json()


def envoyer(client, projet, message, entetes=UTILISATEUR_1):
    return client.post(f"/projects/{projet['id']}/messages", json={"message": message}, headers=entetes)


def test_un_nouveau_projet_a_la_version_1(client, description):
    projet = creer_projet(client, description)

    assert [v["numero"] for v in projet["versions"]] == [1]
    assert projet["versions"][0]["origine"] == "Plan initial"
    assert projet["messages"] == []


def test_une_question_ne_cree_pas_de_version(client, description):
    projet = creer_projet(client, description)

    resultat = envoyer(client, projet, "bhjhbjbj").json()

    assert len(resultat["versions"]) == 1
    assert [m["role"] for m in resultat["messages"]] == ["utilisateur", "assistant"]
    assert resultat["messages"][1]["type"] == "question"
    assert resultat["plan"]["strategie"]["strategie"] == "Replatform"  # plan inchangé


def test_une_modification_cree_une_nouvelle_version(client, description):
    projet = creer_projet(client, description)

    resultat = envoyer(client, projet, "Une option moins chère").json()

    assert [v["numero"] for v in resultat["versions"]] == [1, 2]
    assert resultat["plan"]["strategie"]["strategie"] == "Rehost"
    assert resultat["messages"][1]["version_creee"] == 2


def test_l_ancienne_version_reste_consultable(client, description):
    projet = creer_projet(client, description)
    envoyer(client, projet, "Une option moins chère")

    v1 = client.get(f"/projects/{projet['id']}/versions/1", headers=UTILISATEUR_1).json()

    assert v1["plan"]["strategie"]["strategie"] == "Replatform"


def test_restaurer_cree_une_nouvelle_version(client, description):
    projet = creer_projet(client, description)
    envoyer(client, projet, "Une option moins chère")

    resultat = client.post(
        f"/projects/{projet['id']}/versions/1/restaurer", headers=UTILISATEUR_1
    ).json()

    assert [v["numero"] for v in resultat["versions"]] == [1, 2, 3]
    assert resultat["versions"][2]["origine"] == "Restauration de la version 1"
    assert resultat["plan"]["strategie"]["strategie"] == "Replatform"


def test_version_inexistante_renvoie_404(client, description):
    projet = creer_projet(client, description)

    assert client.get(f"/projects/{projet['id']}/versions/9", headers=UTILISATEUR_1).status_code == 404


def test_impossible_de_discuter_sur_le_projet_d_un_autre(client, description):
    projet = creer_projet(client, description)

    assert envoyer(client, projet, "Une option moins chère", UTILISATEUR_2).status_code == 404


def test_message_vide_refuse(client, description):
    projet = creer_projet(client, description)

    assert envoyer(client, projet, "").status_code == 422
