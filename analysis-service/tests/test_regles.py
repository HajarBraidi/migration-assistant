from tests.conftest import PROJET_PHP, envoyer


def probleme(resultat: dict, regle: str) -> dict | None:
    return next((p for p in resultat["problemes"] if p["regle"] == regle), None)


def test_mysql_detecte_avec_fichier_et_ligne(client):
    mysql = probleme(envoyer(client, PROJET_PHP).json(), "php-mysql")

    assert mysql["gravite"] == "Bloquant"
    assert mysql["occurrences"] == [
        {"fichier": "app/Produits.php", "ligne": 3, "extrait": "$resultat = mysql_query($sql);"}
    ]


def test_les_commentaires_et_le_dossier_vendor_sont_ignores(client):
    mysql = probleme(envoyer(client, PROJET_PHP).json(), "php-mysql")

    assert mysql["total"] == 1  # ni la ligne commentée, ni vendor/


def test_each_de_laravel_n_est_pas_un_faux_positif(client):
    each = probleme(envoyer(client, PROJET_PHP).json(), "php-each")

    assert [o["ligne"] for o in each["occurrences"]] == [5]  # pas $collection->each(...)


def test_les_secrets_sont_masques(client):
    reponse = envoyer(client, PROJET_PHP)
    secret = probleme(reponse.json(), "secret-en-dur")

    assert secret is not None
    assert "Secret2015" not in reponse.text
    assert "****" in secret["occurrences"][0]["extrait"]


def test_version_et_framework_obsoletes(client):
    resultat = envoyer(client, PROJET_PHP).json()

    assert probleme(resultat, "version-obsolete")["titre"] == "PHP 5.6 n'est plus maintenu"
    assert probleme(resultat, "framework-obsolete")["titre"] == "Laravel 5.4 n'est plus maintenu"


def test_problemes_tries_par_gravite_et_score(client):
    resultat = envoyer(client, PROJET_PHP).json()
    gravites = [p["gravite"] for p in resultat["problemes"]]

    assert gravites == sorted(gravites, key=["Bloquant", "Important", "Conseil"].index)
    assert 0 <= resultat["score_preparation"] < 100


def test_projet_sans_probleme_a_un_score_de_100(client):
    projet = {
        "package.json": '{"engines": {"node": ">=22"}, "dependencies": {"express": "^5.0.0"}}',
        "server.js": "const app = require('express')();\napp.listen(process.env.PORT);\n",
    }

    resultat = envoyer(client, projet).json()

    assert resultat["problemes"] == []
    assert resultat["score_preparation"] == 100


def test_description_preremplie_pour_le_formulaire(client):
    description = envoyer(client, PROJET_PHP).json()["description_preremplie"]

    assert description["langage"] == "PHP"
    assert description["type_base_donnees"] == "MySQL"
    assert "Moderniser" in description["objectifs"]
    assert "Analyse automatique du code" in description["description_libre"]
