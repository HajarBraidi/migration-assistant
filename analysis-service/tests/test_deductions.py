from tests.conftest import PROJET_JAVA, PROJET_PHP, envoyer

PROJET_RH = {
    **PROJET_JAVA,
    "README.md": "Portail RH utilisé par 850 employés, hébergé sur un serveur dans nos locaux.",
    "database/schema.sql": (
        "CREATE TABLE employes (id INT, email VARCHAR(100), telephone VARCHAR(20), rib VARCHAR(30));\n"
        "CREATE TABLE conges (id INT, employe_id INT);\n"
    ),
    "src/main/resources/templates/conges.html": '<tr th:each="c : ${conges}"></tr>',
}


def test_deductions_a_partir_du_readme_et_du_schema(client):
    resultat = envoyer(client, PROJET_RH).json()
    description = resultat["description_preremplie"]

    assert description["domaine"] == "RH"
    assert description["nombre_utilisateurs"] == "100 à 1 000"
    assert description["hebergement_actuel"] == "Serveur local"
    assert description["exigences_securite"] == [
        "Données personnelles (RGPD / loi 09-08)",
        "Données bancaires",
    ]
    assert description["competences_equipe"].startswith("Java")


def test_les_deductions_sont_a_verifier_et_les_detections_sont_sures(client):
    resultat = envoyer(client, PROJET_RH).json()

    assert {"domaine", "nombre_utilisateurs", "hebergement_actuel"} <= set(resultat["champs_a_verifier"])
    assert {"langage", "version_langage", "type_base_donnees"} <= set(resultat["champs_detectes"])
    assert not set(resultat["champs_a_verifier"]) & set(resultat["champs_detectes"])


def test_interface_thymeleaf_devient_autre_dans_le_formulaire(client):
    resultat = envoyer(client, PROJET_RH).json()

    assert resultat["pile"]["interface"] == "Thymeleaf"
    assert resultat["description_preremplie"]["interface_utilisateur"] == "Autre"


def test_hebergeur_et_grand_nombre_d_utilisateurs(client):
    projet = {**PROJET_PHP, "stockpro/README.md": "Environ 12 000 clients. Hébergée chez OVH."}

    description = envoyer(client, projet).json()["description_preremplie"]

    assert description["nombre_utilisateurs"] == "1 000 à 50 000"
    assert description["hebergement_actuel"] == "Hébergeur"


def test_sans_indice_rien_n_est_suppose(client):
    projet = {
        "package.json": '{"engines": {"node": ">=22"}, "dependencies": {"express": "^5.0.0"}}',
        "server.js": "const app = require('express')();\napp.listen(process.env.PORT);\n",
    }

    description = envoyer(client, projet).json()["description_preremplie"]

    for champ in ("domaine", "nombre_utilisateurs", "hebergement_actuel", "exigences_securite"):
        assert champ not in description
