import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.main import app


def creer_zip(fichiers: dict[str, str]) -> bytes:
    """Construit une archive .zip en mémoire : {chemin: contenu}."""
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w") as archive:
        for chemin, contenu in fichiers.items():
            archive.writestr(chemin, contenu)
    return tampon.getvalue()


PROJET_PHP = {
    "stockpro/composer.json": '{"require": {"php": ">=5.6", "laravel/framework": "5.4.*", "stripe/stripe-php": "^4.0"}}',
    "stockpro/.env": "DB_CONNECTION=mysql\nDB_HOST=localhost\nDB_PASSWORD=Secret2015\n",
    "stockpro/app/Produits.php": (
        "<?php\n"
        "// mysql_query('ancien code commenté');\n"
        "$resultat = mysql_query($sql);\n"
        "$produits = $collection->each(function ($p) { return $p; });\n"
        "while (list($k, $v) = each($tableau)) {}\n"
    ),
    "stockpro/vendor/lib/Ancien.php": "<?php mysql_connect('x');",
    "stockpro/public/index.html": "<script>$(document).ready(function () {});</script>",
}

PROJET_JAVA = {
    "pom.xml": (
        '<project xmlns="http://maven.apache.org/POM/4.0.0">'
        "<parent><artifactId>spring-boot-starter-parent</artifactId><version>2.7.18</version></parent>"
        "<properties><java.version>1.8</java.version></properties>"
        "<dependencies><dependency><groupId>org.postgresql</groupId><artifactId>postgresql</artifactId>"
        "<version>42.2.5</version></dependency></dependencies></project>"
    ),
    "src/main/java/App.java": "import javax.xml.bind.JAXBContext;\npublic class App {}\n",
}

PROJET_NODE = {
    "package.json": '{"engines": {"node": ">=12"}, "dependencies": {"express": "^4.17.1", "mongoose": "^5.0.0", "react": "^17.0.0"}}',
    "server.js": "const app = require('express')();\nconst b = new Buffer('x');\n",
}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def envoyer(client: TestClient, fichiers: dict[str, str], nom: str = "projet.zip"):
    return client.post(
        "/analyses", files={"archive": (nom, creer_zip(fichiers), "application/zip")}
    )
