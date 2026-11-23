import io
import zipfile

from tests.conftest import DEMANDE, chemins, fichier, generer


def test_contenu_de_base(client):
    kit = generer(client)

    assert kit["projet"] == "rh-portal"
    assert {"GUIDE-DEPLOIEMENT.md", "Dockerfile", ".env.example", "docker-compose.yml",
            ".github/workflows/deploy.yml", "infra/aws/main.tf"} <= chemins(kit)


def test_securite_de_la_base_aws(client):
    main = fichier(generer(client), "infra/aws/main.tf")

    assert "publicly_accessible    = false" in main
    assert "storage_encrypted      = true" in main
    assert "deletion_protection       = true" in main
    assert "backup_retention_period   = 7" in main


def test_aucun_mot_de_passe_dans_les_fichiers(client):
    kit = generer(client)
    variables = fichier(kit, "infra/aws/variables.tf")

    assert "sensitive   = true" in variables
    assert "mot_de_passe" not in fichier(kit, "infra/aws/terraform.tfvars.example").split("#")[0]
    assert "terraform.tfvars" in fichier(kit, "infra/.gitignore")
    assert ".env" in fichier(kit, ".dockerignore")


def test_repartiteur_seulement_avec_plusieurs_serveurs(client):
    assert "infra/aws/repartiteur.tf" not in chemins(generer(client))
    assert "infra/aws/repartiteur.tf" in chemins(generer(client, haute_disponibilite=True))
    assert "infra/aws/repartiteur.tf" in chemins(generer(client, nombre_utilisateurs="> 50 000"))


def test_dimensionnement_selon_les_utilisateurs(client):
    petit = fichier(generer(client, nombre_utilisateurs="< 100"), "infra/aws/variables.tf")
    grand = fichier(generer(client, nombre_utilisateurs="> 50 000"), "infra/aws/variables.tf")

    assert '"t3.small"' in petit and "default = 1" in petit
    assert '"t3.xlarge"' in grand and "default = 3" in grand


def test_azure_haute_disponibilite_exige_la_gamme_general_purpose(client):
    kit = generer(client, fournisseur="Azure", nombre_utilisateurs="< 100", haute_disponibilite=True)
    variables = fichier(kit, "infra/azure/variables.tf")

    assert "GP_Standard_D2ds_v4" in variables
    assert "infra/azure/base-postgresql.tf" in chemins(kit)


def test_gcp_sauvegardes_selon_le_moteur(client):
    postgres = fichier(generer(client, fournisseur="GCP"), "infra/gcp/main.tf")
    mysql = fichier(generer(client, fournisseur="GCP", base_cible="MySQL", type_base_donnees="MySQL"), "infra/gcp/main.tf")

    assert "POSTGRES_16" in postgres and "point_in_time_recovery_enabled = true" in postgres
    assert "MYSQL_8_4" in mysql and "binary_log_enabled             = true" in mysql


def test_ovhcloud_sans_terraform(client):
    kit = generer(client, fournisseur="OVHcloud")

    assert "infra/ovhcloud/installer-base.sh" in chemins(kit)
    assert not any(c.endswith(".tf") for c in chemins(kit))
    assert "DOCKER-USER" in fichier(kit, "infra/ovhcloud/installer-base.sh")  # Docker ignore ufw


def test_dockerfile_selon_le_langage(client):
    assert "eclipse-temurin:21-jre" in fichier(generer(client), "Dockerfile")
    assert "tomcat:9.0-jdk21" in fichier(generer(client, framework_backend="Servlets / JSP"), "Dockerfile")
    php = fichier(generer(client, langage="PHP", framework_backend="Laravel 5.4"), "Dockerfile")
    assert "php:8.3-apache" in php and "pdo_pgsql" in php and "/var/www/html/public" in php
    assert "node:22-alpine" in fichier(generer(client, langage="JavaScript"), "Dockerfile")


def test_scenarios_de_migration_de_la_base(client):
    meme_moteur = generer(client, type_base_donnees="MySQL", base_cible="MySQL")
    assert {"migration-base/exporter.sh", "migration-base/importer.sh", "migration-base/verifier.sh"} <= chemins(meme_moteur)

    mysql_vers_pg = generer(client, type_base_donnees="MySQL")
    assert "pgloader" in fichier(mysql_vers_pg, "migration-base/convertir.sh")
    assert "${table,,}" in fichier(mysql_vers_pg, "migration-base/verifier.sh")

    oracle = generer(client)
    assert "migration-base/oracle-vers-postgresql.sh" in chemins(oracle)
    assert any("PL/SQL" in a for a in oracle["avertissements"])

    non_couvert = generer(client, type_base_donnees="Oracle", base_cible="MySQL")
    assert not any(c.startswith("migration-base/") for c in chemins(non_couvert))
    assert any("choisissez PostgreSQL" in a for a in non_couvert["avertissements"])


def test_pipeline_image_en_minuscules_et_jeton_protege(client):
    pipeline = fichier(generer(client), ".github/workflows/deploy.yml")

    assert "${GITHUB_REPOSITORY,,}" in pipeline
    assert "--password-stdin" in pipeline
    assert "UTILISATEUR_SSH: ubuntu" in pipeline


def test_archive_zip_avec_scripts_executables(client):
    reponse = client.post("/kits/archive", json=DEMANDE)

    assert reponse.status_code == 200
    assert reponse.headers["content-type"] == "application/zip"
    archive = zipfile.ZipFile(io.BytesIO(reponse.content))
    noms = archive.namelist()
    assert "rh-portal-kit/GUIDE-DEPLOIEMENT.md" in noms
    script = archive.getinfo("rh-portal-kit/infra/commun/installer-serveur.sh")
    assert (script.external_attr >> 16) & 0o111  # droit d'exécution


def test_langage_non_pris_en_charge(client):
    assert client.post("/kits", json={**DEMANDE, "langage": "Python"}).status_code == 422
