import httpx

import app.main as gateway
from tests.conftest import jeton


def faux_service(gestionnaire):
    """Remplace le réseau par une fonction qui simule les services."""
    gateway._transport = httpx.MockTransport(gestionnaire)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "service": "api-gateway"}


def test_projets_sans_jeton_renvoie_401(client):
    assert client.get("/api/projects").status_code == 401


def test_jeton_invalide_ou_expire_renvoie_401(client):
    assert client.get("/api/projects", headers=jeton(secret="mauvais-secret")).status_code == 401
    assert client.get("/api/projects", headers=jeton(minutes=-5)).status_code == 401


def test_transmet_la_creation_avec_l_identifiant_utilisateur(client):
    requetes = []

    def gestionnaire(request: httpx.Request) -> httpx.Response:
        requetes.append(request)
        return httpx.Response(201, json={"id": 1, "nom": "StockPro"})

    faux_service(gestionnaire)
    reponse = client.post("/api/projects", json={"nom": "StockPro"}, headers=jeton(user_id=7))

    assert reponse.status_code == 201
    assert requetes[0].url.path == "/projects"
    assert requetes[0].headers["X-User-Id"] == "7"


def test_un_client_ne_peut_pas_choisir_son_identifiant(client):
    requetes = []
    faux_service(lambda r: requetes.append(r) or httpx.Response(200, json=[]))

    client.get("/api/projects", headers={**jeton(user_id=7), "X-User-Id": "999"})

    assert requetes[0].headers["X-User-Id"] == "7"


def test_connexion_transmise_a_auth_service(client):
    requetes = []
    faux_service(lambda r: requetes.append(r) or httpx.Response(200, json={"access_token": "x"}))

    reponse = client.post("/api/auth/login", json={"email": "a@b.c", "mot_de_passe": "x"})

    assert reponse.status_code == 200
    assert requetes[0].url.path == "/login"


def test_transmet_les_erreurs_du_service(client):
    faux_service(lambda request: httpx.Response(404, json={"detail": "Projet introuvable."}))

    reponse = client.get("/api/projects/999", headers=jeton())

    assert reponse.status_code == 404
    assert reponse.json()["detail"] == "Projet introuvable."


def test_503_si_le_service_ne_repond_pas(client):
    def en_panne(request):
        raise httpx.ConnectError("connexion refusée")

    faux_service(en_panne)

    assert client.get("/api/projects", headers=jeton()).status_code == 503



def test_transmet_les_routes_de_dialogue_avec_l_identifiant(client):
    requetes = []
    faux_service(lambda r: requetes.append(r) or httpx.Response(200, json={"id": 3}))

    client.post("/api/projects/3/messages", json={"message": "Bonjour"}, headers=jeton(user_id=7))
    client.get("/api/projects/3/versions/1", headers=jeton(user_id=7))
    client.post("/api/projects/3/versions/1/restaurer", headers=jeton(user_id=7))

    chemins = [r.url.path for r in requetes]
    assert chemins == ["/projects/3/messages", "/projects/3/versions/1", "/projects/3/versions/1/restaurer"]
    assert all(r.headers["X-User-Id"] == "7" for r in requetes)


def test_dialogue_sans_jeton_renvoie_401(client):
    assert client.post("/api/projects/3/messages", json={"message": "x"}).status_code == 401


def test_transmet_l_archive_au_service_d_analyse(client):
    requetes = []
    faux_service(lambda r: requetes.append(r) or httpx.Response(200, json={"score_preparation": 40}))

    reponse = client.post(
        "/api/analyses", files={"archive": ("p.zip", b"PK...", "application/zip")}, headers=jeton()
    )

    assert reponse.status_code == 200
    assert requetes[0].url.path == "/analyses"
    assert requetes[0].headers["Content-Type"].startswith("multipart/form-data; boundary=")
    assert b"p.zip" in requetes[0].content


def test_analyse_sans_jeton_renvoie_401(client):
    assert client.post("/api/analyses", files={"archive": ("p.zip", b"x")}).status_code == 401


def test_transmet_l_estimation_des_couts(client):
    requetes = []
    faux_service(lambda r: requetes.append(r) or httpx.Response(200, json={"moins_chere": "OVHcloud"}))

    reponse = client.post("/api/estimations", json={"nombre_utilisateurs": "< 100"}, headers=jeton())

    assert reponse.status_code == 200
    assert requetes[0].url.path == "/estimations"
    assert client.post("/api/estimations", json={}).status_code == 401
