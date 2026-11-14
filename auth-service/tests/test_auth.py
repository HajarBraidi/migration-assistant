from app.security import hacher_mot_de_passe, lire_jeton, verifier_mot_de_passe
from tests.conftest import COMPTE


def test_inscription_renvoie_un_jeton(client):
    reponse = client.post("/register", json=COMPTE)

    assert reponse.status_code == 201
    assert reponse.json()["access_token"]
    assert reponse.json()["utilisateur"]["email"] == COMPTE["email"]


def test_email_deja_utilise_renvoie_409(client):
    client.post("/register", json=COMPTE)

    reponse = client.post("/register", json=COMPTE)

    assert reponse.status_code == 409


def test_mot_de_passe_trop_court_renvoie_422(client):
    reponse = client.post("/register", json={**COMPTE, "mot_de_passe": "court"})

    assert reponse.status_code == 422


def test_connexion_avec_le_bon_mot_de_passe(client):
    client.post("/register", json=COMPTE)

    reponse = client.post(
        "/login", json={"email": COMPTE["email"], "mot_de_passe": COMPTE["mot_de_passe"]}
    )

    assert reponse.status_code == 200
    assert lire_jeton(reponse.json()["access_token"]) == reponse.json()["utilisateur"]["id"]


def test_connexion_avec_un_mauvais_mot_de_passe_renvoie_401(client):
    client.post("/register", json=COMPTE)

    reponse = client.post("/login", json={"email": COMPTE["email"], "mot_de_passe": "faux"})

    assert reponse.status_code == 401


def test_me_avec_et_sans_jeton(client):
    jeton = client.post("/register", json=COMPTE).json()["access_token"]

    assert client.get("/me", headers={"Authorization": f"Bearer {jeton}"}).status_code == 200
    assert client.get("/me").status_code == 401
    assert client.get("/me", headers={"Authorization": "Bearer faux"}).status_code == 401


def test_le_mot_de_passe_n_est_jamais_stocke_en_clair():
    empreinte = hacher_mot_de_passe("motdepasse123")

    assert empreinte != "motdepasse123"
    assert verifier_mot_de_passe("motdepasse123", empreinte)
    assert not verifier_mot_de_passe("autre", empreinte)
