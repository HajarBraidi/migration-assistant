import io
import zipfile

from app.config import settings
from tests.conftest import PROJET_NODE, creer_zip, envoyer


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "service": "analysis-service"}


def test_fichier_qui_n_est_pas_un_zip(client):
    reponse = client.post("/analyses", files={"archive": ("projet.txt", b"bonjour", "text/plain")})

    assert reponse.status_code == 400


def test_zip_corrompu(client):
    reponse = client.post("/analyses", files={"archive": ("projet.zip", b"pas un zip", "application/zip")})

    assert reponse.status_code == 400
    assert "archive .zip valide" in reponse.json()["detail"]


def test_archive_trop_volumineuse(client, monkeypatch):
    monkeypatch.setattr(settings, "taille_max_archive_mo", 0)

    assert envoyer(client, PROJET_NODE).status_code == 413


def test_chemins_dangereux_ignores(client):
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w") as archive:
        archive.writestr("../../etc/passwd.php", "<?php mysql_query('x');")
        archive.writestr("index.php", "<?php echo 'ok';")
    reponse = client.post("/analyses", files={"archive": ("p.zip", tampon.getvalue(), "application/zip")})

    assert reponse.status_code == 200
    assert reponse.json()["problemes"] == []  # le fichier « ../../ » n'a pas été lu


def test_archive_sans_code(client):
    reponse = client.post(
        "/analyses", files={"archive": ("p.zip", creer_zip({"photo.png": "x"}), "application/zip")}
    )

    assert reponse.status_code == 400
