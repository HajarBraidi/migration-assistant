from tests.conftest import PROJET_JAVA, PROJET_NODE, PROJET_PHP, envoyer


def test_projet_php(client):
    resultat = envoyer(client, PROJET_PHP).json()

    assert resultat["pile"] == {
        "langage": "PHP",
        "version_langage": "5.6",
        "framework": "Laravel 5.4",
        "interface": "HTML/jQuery",
        "base_de_donnees": "MySQL",
        "architecture": "Monolithe",
        "integrations": ["Paiement Stripe"],
    }


def test_projet_java(client):
    pile = envoyer(client, PROJET_JAVA).json()["pile"]

    assert pile["langage"] == "Java"
    assert pile["version_langage"] == "8"  # « 1.8 » devient « 8 »
    assert pile["framework"] == "Spring Boot 2.7"
    assert pile["base_de_donnees"] == "PostgreSQL"


def test_projet_node(client):
    resultat = envoyer(client, PROJET_NODE).json()

    assert resultat["pile"]["langage"] == "Node.js"
    assert resultat["pile"]["framework"] == "Express 4.17"
    assert resultat["pile"]["interface"] == "React"
    assert resultat["pile"]["base_de_donnees"] == "MongoDB"
    # Le formulaire attend « JavaScript » (valeur du contrat)
    assert resultat["description_preremplie"]["langage"] == "JavaScript"


def test_le_dossier_racine_est_retire_des_chemins(client):
    problemes = envoyer(client, PROJET_PHP).json()["problemes"]
    fichiers = {o["fichier"] for p in problemes for o in p["occurrences"]}

    assert "app/Produits.php" in fichiers
    assert not any(f.startswith("stockpro/") for f in fichiers)
