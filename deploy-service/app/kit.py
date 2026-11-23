"""Génère le kit de déploiement à partir des modèles du dossier app/modeles."""

import re
import unicodedata
from pathlib import Path

from app.schemas import DemandeKit, Fichier, Kit

MODELES = Path(__file__).parent / "modeles"

# ---------- Dimensionnement (mêmes règles que le comparateur de coûts) ----------

DIMENSIONS = {
    "< 100": (1, "small"),
    "100 à 1 000": (1, "medium"),
    "1 000 à 50 000": (2, "large"),
    "> 50 000": (3, "xlarge"),
}
STOCKAGE_GO = {"< 10 Go": 20, "10 à 100 Go": 150, "100 Go à 1 To": 1000, "> 1 To": 3000}

TYPES = {
    "AWS": {
        "serveur": {"small": "t3.small", "medium": "t3.medium", "large": "t3.large", "xlarge": "t3.xlarge"},
        "base": {"small": "db.t3.small", "medium": "db.t3.medium", "large": "db.t3.large", "xlarge": "db.t3.xlarge"},
    },
    "Azure": {
        "serveur": {"small": "Standard_B1ms", "medium": "Standard_B2s", "large": "Standard_B2ms", "xlarge": "Standard_B4ms"},
        "base": {
            "small": "B_Standard_B1ms", "medium": "B_Standard_B2s",
            "large": "GP_Standard_D2ds_v4", "xlarge": "GP_Standard_D4ds_v4",
        },
    },
    "GCP": {
        "serveur": {"small": "e2-small", "medium": "e2-medium", "large": "e2-standard-2", "xlarge": "e2-standard-4"},
        "base": {
            "small": "db-custom-1-3840", "medium": "db-custom-2-4096",
            "large": "db-custom-2-8192", "xlarge": "db-custom-4-16384",
        },
    },
    "OVHcloud": {
        "serveur": {"small": "VPS-1", "medium": "VPS-1", "large": "VPS-2", "xlarge": "VPS-4"},
        "base": {"small": "VPS-1", "medium": "VPS-1", "large": "VPS-2", "xlarge": "VPS-4"},
    },
}
UTILISATEUR_SSH = {"AWS": "ubuntu", "Azure": "deploiement", "GCP": "deploiement", "OVHcloud": "ubuntu"}
UTILISATEUR_BASE = "app_admin"

MOTEURS = {
    "PostgreSQL": {
        "port": 5432, "aws": ("postgres", "16"), "gcp": "POSTGRES_16", "image": "postgres:16",
        "client": "postgresql", "dossier": "/var/lib/postgresql/data",
    },
    "MySQL": {
        "port": 3306, "aws": ("mysql", "8.4"), "gcp": "MYSQL_8_4", "image": "mysql:8.4",
        "client": "mysql", "dossier": "/var/lib/mysql",
    },
}
# Tailles autorisées pour PostgreSQL Flexible Server (en Mo)
STOCKAGES_AZURE_PG = [32768, 65536, 131072, 262144, 524288, 1048576, 2097152, 4194304]

PORTS = {"PHP": 80, "Java": 8080, "JavaScript": 3000}


class ModeleIncomplet(Exception):
    """Un modèle contient encore une valeur non remplie : c'est un bogue du générateur."""


def remplir(texte: str, **valeurs) -> str:
    for cle, valeur in valeurs.items():
        texte = texte.replace(f"«{cle}»", str(valeur))
    restant = re.findall(r"«(\w+)»", texte)
    if restant:
        raise ModeleIncomplet(f"Valeurs manquantes : {sorted(set(restant))}")
    return texte


def lire(chemin: str) -> str:
    return (MODELES / chemin).read_text(encoding="utf-8")


def nom_court(nom: str) -> str:
    """« RH Portal (v2) » -> « rh-portal-v2 » : utilisable pour les ressources cloud."""
    texte = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode().lower()
    texte = re.sub(r"[^a-z0-9]+", "-", texte).strip("-")[:20].strip("-")
    if not texte or not texte[0].isalpha():
        texte = f"app-{texte}".strip("-")
    return texte


# ---------- Application : Dockerfile, .env, docker-compose ----------


def _dockerfile(d: DemandeKit) -> tuple[str, str]:
    framework = (d.framework_backend or "").lower()
    if d.langage == "PHP":
        extensions = (
            "RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev \\\n"
            "    && docker-php-ext-install pdo_pgsql pgsql \\\n"
            "    && rm -rf /var/lib/apt/lists/*"
            if d.base_cible == "PostgreSQL"
            else "RUN docker-php-ext-install pdo_mysql mysqli"
        )
        racine = "/var/www/html/public" if ("laravel" in framework or "symfony" in framework) else "/var/www/html"
        return (
            f"""# Image de l'application PHP, en version maintenue (8.3).
# Corrigez d'abord les problèmes « Bloquant » du scanner : le code PHP 5 ne fonctionne pas en PHP 8.

# Étape 1 : dépendances Composer (supprimez-la si le projet n'utilise pas Composer)
FROM composer:2 AS dependances
WORKDIR /app
COPY composer.json composer.lock* ./
RUN composer install --no-dev --no-scripts --prefer-dist --no-interaction --no-progress

# Étape 2 : serveur web Apache + PHP 8.3
FROM php:8.3-apache
{extensions}
RUN a2enmod rewrite headers

ENV APACHE_DOCUMENT_ROOT={racine}
RUN sed -ri -e 's!/var/www/html!${{APACHE_DOCUMENT_ROOT}}!g' /etc/apache2/sites-available/*.conf \\
    && sed -ri -e 's!/var/www/!${{APACHE_DOCUMENT_ROOT}}!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf

# Configuration de production : erreurs dans les journaux, jamais à l'écran
RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"

WORKDIR /var/www/html
COPY --from=dependances /app/vendor ./vendor
COPY . .
RUN chown -R www-data:www-data /var/www/html

EXPOSE 80
""",
            "Image PHP 8.3 + Apache, avec l'extension de la base cible",
        )
    if d.langage == "Java":
        if "spring" in framework:
            return (
                """# Image de l'application Spring Boot, compilée et exécutée en Java 21 (LTS).
# Corrigez d'abord les problèmes « Bloquant » du scanner (JAXB, Nashorn...).

# Étape 1 : compilation avec Maven (pour Gradle : image gradle:8-jdk21 et ./gradlew bootJar)
FROM maven:3.9-eclipse-temurin-21 AS construction
WORKDIR /app
COPY pom.xml .
RUN mvn -B -q dependency:go-offline
COPY src ./src
RUN mvn -B -q package -DskipTests

# Étape 2 : exécution avec un JRE seul (image plus légère, sans outils de compilation)
FROM eclipse-temurin:21-jre
WORKDIR /app
RUN useradd --system --create-home application
COPY --from=construction /app/target/*.jar app.jar
USER application

EXPOSE 8080
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "app.jar"]
""",
                "Image Java 21 (compilation Maven puis JRE seul)",
            )
        return (
            """# Image de l'application web Java (WAR), exécutée par Tomcat 9 sur Java 21.
# Tomcat 9 conserve les paquets javax.* : aucune réécriture en jakarta.* n'est nécessaire.

FROM maven:3.9-eclipse-temurin-21 AS construction
WORKDIR /app
COPY pom.xml .
RUN mvn -B -q dependency:go-offline
COPY src ./src
RUN mvn -B -q package -DskipTests

FROM tomcat:9.0-jdk21-temurin
RUN rm -rf /usr/local/tomcat/webapps/*
COPY --from=construction /app/target/*.war /usr/local/tomcat/webapps/ROOT.war

EXPOSE 8080
""",
            "Image Tomcat 9 + Java 21 pour une application WAR",
        )
    return (
        """# Image de l'application Node.js, en version LTS (22).
FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production

# Dépendances d'abord : elles restent en cache tant que package.json ne change pas
COPY package*.json ./
RUN npm ci --omit=dev

COPY . .
USER node

EXPOSE 3000
# Vérifiez que package.json contient un script « start » (ex. "node server.js")
CMD ["npm", "start"]
""",
        "Image Node.js 22 (LTS), sans dépendances de développement",
    )


DOCKERIGNORE = """.git
.env
.env.*
!.env.example
node_modules
vendor
target
infra
migration-base
*.log
"""


def _env_exemple(d: DemandeKit, nom_base: str) -> str:
    port = MOTEURS[d.base_cible]["port"]
    protocole = "postgresql" if d.base_cible == "PostgreSQL" else "mysql"
    lignes = [
        "# Copier en .env (jamais dans Git) et remplacer les valeurs.",
        "# En local, DB_HOST=base (service docker-compose).",
        "# En production, DB_HOST = sortie « adresse_base » de Terraform.",
        "DB_HOST=base",
        f"DB_PORT={port}",
        f"DB_NAME={nom_base}",
        f"DB_USER={UTILISATEUR_BASE}",
        "DB_PASSWORD=a_remplacer",
    ]
    if d.langage == "PHP" and "laravel" in (d.framework_backend or "").lower():
        lignes += [
            f"DB_CONNECTION={'pgsql' if d.base_cible == 'PostgreSQL' else 'mysql'}",
            f"DB_DATABASE={nom_base}",
            f"DB_USERNAME={UTILISATEUR_BASE}",
            "APP_ENV=production",
            "APP_DEBUG=false",
        ]
    if d.langage == "Java":
        lignes += [
            f"SPRING_DATASOURCE_URL=jdbc:{protocole}://base:{port}/{nom_base}",
            f"SPRING_DATASOURCE_USERNAME={UTILISATEUR_BASE}",
            "SPRING_DATASOURCE_PASSWORD=a_remplacer",
        ]
    if d.langage == "JavaScript":
        lignes += [f"DATABASE_URL={protocole}://{UTILISATEUR_BASE}:a_remplacer@base:{port}/{nom_base}"]
    return "\n".join(lignes) + "\n"


def _compose_local(d: DemandeKit) -> str:
    moteur = MOTEURS[d.base_cible]
    if d.base_cible == "PostgreSQL":
        variables = """      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}"""
    else:
        variables = """      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
      MYSQL_RANDOM_ROOT_PASSWORD: "yes\""""
    return f"""# Tester l'application conteneurisée sur son poste, avant toute mise en ligne :
#   cp .env.example .env   puis   docker compose up --build
services:
  app:
    build: .
    env_file: .env
    ports:
      - "8000:{PORTS[d.langage]}"
    depends_on:
      - base

  base:
    image: {moteur['image']}
    environment:
{variables}
    volumes:
      - donnees:{moteur['dossier']}

volumes:
  donnees:
"""


# ---------- Infrastructure ----------


def _infrastructure(d: DemandeKit, projet: str, nom_base: str) -> list[Fichier]:
    serveurs, taille = DIMENSIONS[d.nombre_utilisateurs]
    if d.haute_disponibilite:
        serveurs = max(serveurs, 2)
    stockage = STOCKAGE_GO[d.volume_donnees]
    moteur = MOTEURS[d.base_cible]
    types = TYPES[d.fournisseur]
    type_base = types["base"][taille]
    # La haute disponibilité Azure exige une gamme « General Purpose »
    if d.fournisseur == "Azure" and d.haute_disponibilite and type_base.startswith("B_"):
        type_base = "GP_Standard_D2ds_v4"

    valeurs = dict(
        nom_projet=projet, nombre_serveurs=serveurs, type_serveur=types["serveur"][taille],
        type_base=type_base, stockage_go=stockage, haute_disponibilite=str(d.haute_disponibilite).lower(),
        nom_base=nom_base, utilisateur_base=UTILISATEUR_BASE, port_base=moteur["port"],
        moteur_aws=moteur["aws"][0], version_aws=moteur["aws"][1], version_gcp=moteur["gcp"],
        pitr_postgresql=str(d.base_cible == "PostgreSQL").lower(),
        binlog_mysql=str(d.base_cible == "MySQL").lower(),
        stockage_mb=next(t for t in STOCKAGES_AZURE_PG if t >= stockage * 1024),
    )
    fichiers = [
        Fichier(
            chemin="infra/commun/installer-serveur.sh", categorie="Infrastructure",
            description="Prépare chaque serveur au premier démarrage : Docker, pare-feu, mises à jour de sécurité",
            contenu=remplir(lire("commun/installer-serveur.sh"), nom_projet=projet,
                            utilisateur_ssh=UTILISATEUR_SSH[d.fournisseur]),
        ),
        Fichier(
            chemin="infra/.gitignore", categorie="Infrastructure",
            description="Empêche d'envoyer dans Git l'état Terraform et les fichiers de variables",
            contenu=".terraform/\n*.tfstate\n*.tfstate.*\nterraform.tfvars\n",
        ),
    ]

    if d.fournisseur == "OVHcloud":
        fichiers.append(_ovh_base(d, projet, nom_base))
        return fichiers

    dossier = d.fournisseur.lower()
    modeles = ["main.tf", "variables.tf", "outputs.tf", "terraform.tfvars.example"]
    if d.fournisseur == "Azure":
        modeles.append("base-postgresql.tf" if d.base_cible == "PostgreSQL" else "base-mysql.tf")
    if serveurs > 1:
        modeles.append("repartiteur.tf")
    descriptions = {
        "main.tf": "Serveurs, pare-feu et base de données gérée",
        "variables.tf": "Paramètres : tailles, nombre de serveurs, région (déjà remplis)",
        "outputs.tf": "Adresses à récupérer après la création",
        "terraform.tfvars.example": "Valeurs propres à votre compte, à compléter",
        "base-postgresql.tf": "Base PostgreSQL gérée et règles d'accès",
        "base-mysql.tf": "Base MySQL gérée et règles d'accès",
        "repartiteur.tf": "Répartiteur de charge entre les serveurs",
    }
    for nom in modeles:
        fichiers.append(Fichier(
            chemin=f"infra/{dossier}/{nom}", categorie="Infrastructure",
            description=descriptions[nom], contenu=remplir(lire(f"{dossier}/{nom}"), **valeurs),
        ))
    return fichiers


def _ovh_base(d: DemandeKit, projet: str, nom_base: str) -> Fichier:
    moteur = MOTEURS[d.base_cible]
    if d.base_cible == "PostgreSQL":
        variables = (f"POSTGRES_DB={nom_base}\nPOSTGRES_USER={UTILISATEUR_BASE}\n"
                     "POSTGRES_PASSWORD=${MOT_DE_PASSE_BASE}")
        sauvegarde = f"docker compose exec -T base pg_dump -U {UTILISATEUR_BASE} {nom_base}"
    else:
        variables = (f"MYSQL_DATABASE={nom_base}\nMYSQL_USER={UTILISATEUR_BASE}\n"
                     "MYSQL_PASSWORD=${MOT_DE_PASSE_BASE}\nMYSQL_ROOT_PASSWORD=$(openssl rand -hex 24)")
        sauvegarde = ("docker compose exec -T base sh -c "
                      "'mysqldump -u\"$MYSQL_USER\" -p\"$MYSQL_PASSWORD\" --single-transaction \"$MYSQL_DATABASE\"'")
    return Fichier(
        chemin="infra/ovhcloud/installer-base.sh", categorie="Infrastructure",
        description="Installe la base sur un VPS dédié, ouverte seulement aux serveurs d'application, "
                    "avec une sauvegarde quotidienne",
        contenu=remplir(
            lire("ovhcloud/installer-base.sh"), nom_projet=projet, moteur_nom=d.base_cible,
            port_base=moteur["port"], image_base=moteur["image"], dossier_donnees=moteur["dossier"],
            variables_conteneur=variables, commande_sauvegarde=sauvegarde,
        ),
    )


# ---------- Migration de la base ----------

EXPORTS = {
    "MySQL": ("sql.gz", 'MYSQL_PWD="$SOURCE_MOT_DE_PASSE" mysqldump --host="$SOURCE_HOTE" '
                        '--user="$SOURCE_UTILISATEUR" \\\n  --single-transaction --routines --triggers '
                        '--events "$SOURCE_BASE" | gzip > "$FICHIER"'),
    "PostgreSQL": ("dump", 'PGPASSWORD="$SOURCE_MOT_DE_PASSE" pg_dump --host="$SOURCE_HOTE" '
                           '--username="$SOURCE_UTILISATEUR" \\\n  --format=custom --no-owner '
                           '--file="$FICHIER" "$SOURCE_BASE"'),
}
IMPORTS = {
    "MySQL": 'gunzip -c "$FICHIER" | MYSQL_PWD="$CIBLE_MOT_DE_PASSE" mysql --host="$CIBLE_HOTE" '
             '--user="$CIBLE_UTILISATEUR" "$CIBLE_BASE"',
    "PostgreSQL": 'PGPASSWORD="$CIBLE_MOT_DE_PASSE" pg_restore --host="$CIBLE_HOTE" '
                  '--username="$CIBLE_UTILISATEUR" \\\n  --dbname="$CIBLE_BASE" --no-owner '
                  '--no-privileges --jobs=4 "$FICHIER"',
}
PGLOADER_SOURCES = {"MySQL": "mysql", "SQL Server": "mssql"}


def _conversion_pgloader(source: str) -> str:
    schema = "mysql" if source == "MySQL" else "mssql"
    return f"""# Fichier de commandes pgloader créé au lancement (les mots de passe ne vont jamais dans Git).
# Si un mot de passe contient @ : / ou %, encodez ces caractères (par exemple @ devient %40).
umask 077
cat > conversion.load <<FIN_COMMANDES
LOAD DATABASE
     FROM {schema}://${{SOURCE_UTILISATEUR}}:${{SOURCE_MOT_DE_PASSE}}@${{SOURCE_HOTE}}/${{SOURCE_BASE}}
     INTO postgresql://${{CIBLE_UTILISATEUR}}:${{CIBLE_MOT_DE_PASSE}}@${{CIBLE_HOTE}}/${{CIBLE_BASE}}

 WITH include drop, create tables, create indexes, reset sequences, foreign keys

  SET maintenance_work_mem to '256MB', work_mem to '64MB';
FIN_COMMANDES

pgloader --summary rapport-pgloader.txt conversion.load
rm -f conversion.load
echo "Conversion terminée : relisez rapport-pgloader.txt (lignes copiées et erreurs par table)."
"""


def _migration_base(d: DemandeKit) -> tuple[list[Fichier], list[str]]:
    source, cible = d.type_base_donnees, d.base_cible
    noms = {"MySQL": "mysql", "PostgreSQL": "postgresql"}

    def verifier(table_cible: str) -> Fichier:
        return Fichier(
            chemin="migration-base/verifier.sh", categorie="Base de données",
            description="Compare le nombre de lignes de chaque table entre l'ancienne et la nouvelle base",
            contenu=remplir(lire("base/verifier.sh"), moteur_source=noms[source],
                            moteur_cible=noms[cible], nom_table_cible=table_cible),
        )

    if source == cible:
        extension, export = EXPORTS[source]
        return [
            Fichier(chemin="migration-base/exporter.sh", categorie="Base de données",
                    description="Étape 1 : exporte la base actuelle sans arrêter l'application",
                    contenu=remplir(lire("base/exporter.sh"), moteur_source_nom=source,
                                    extension_export=extension, commande_export=export)),
            Fichier(chemin="migration-base/importer.sh", categorie="Base de données",
                    description="Étape 2 : importe l'export dans la nouvelle base",
                    contenu=remplir(lire("base/importer.sh"), moteur_cible_nom=cible,
                                    commande_import=IMPORTS[cible])),
            verifier("$table"),
        ], []

    if cible == "PostgreSQL" and source in PGLOADER_SOURCES:
        fichiers = [Fichier(
            chemin="migration-base/convertir.sh", categorie="Base de données",
            description=f"Convertit la base {source} en PostgreSQL et copie les données (pgloader)",
            contenu=remplir(lire("base/convertir.sh"), moteur_source_nom=source, moteur_cible_nom=cible,
                            outil="pgloader", commande_conversion=_conversion_pgloader(source)),
        )]
        avertissements = []
        if source == "MySQL":
            # pgloader écrit les noms de tables en minuscules
            fichiers.append(verifier("${table,,}"))
        else:
            avertissements.append(
                "SQL Server : comparez les lignes copiées avec le rapport rapport-pgloader.txt "
                "(pas de script de vérification automatique pour SQL Server)."
            )
        return fichiers, avertissements

    if source == "Oracle" and cible == "PostgreSQL":
        return [Fichier(
            chemin="migration-base/oracle-vers-postgresql.sh", categorie="Base de données",
            description="Évalue, convertit et copie la base Oracle vers PostgreSQL (ora2pg), puis compare les lignes",
            contenu=lire("base/oracle-vers-postgresql.sh"),
        )], ["Oracle vers PostgreSQL : le schéma est converti automatiquement, mais les procédures PL/SQL "
             "doivent être relues à la main. Prévoyez du temps pour cette étape (voir rapport-ora2pg.txt)."]

    return [], [
        f"Aucun outil automatique fiable pour passer de {source} à {cible} : choisissez PostgreSQL "
        "comme base cible, ou utilisez un service de migration du fournisseur (par exemple AWS Database "
        "Migration Service)."
    ]


# ---------- Point d'entrée ----------


def generer(d: DemandeKit) -> Kit:
    from app.guide import guide  # import local : le guide dépend des fichiers générés

    projet = nom_court(d.nom)
    nom_base = projet.replace("-", "")[:16] or "application"
    contenu_dockerfile, description_dockerfile = _dockerfile(d)

    fichiers = [
        Fichier(chemin="Dockerfile", categorie="Application", description=description_dockerfile,
                contenu=contenu_dockerfile),
        Fichier(chemin=".dockerignore", categorie="Application",
                description="Exclut de l'image les secrets, dépendances et fichiers d'infrastructure",
                contenu=DOCKERIGNORE),
        Fichier(chemin=".env.example", categorie="Application",
                description="Variables de configuration à copier en .env (jamais dans Git)",
                contenu=_env_exemple(d, nom_base)),
        Fichier(chemin="docker-compose.yml", categorie="Application",
                description="Test de l'application et de la nouvelle base sur votre poste",
                contenu=_compose_local(d)),
        Fichier(chemin="deploiement/docker-compose.prod.yml", categorie="Déploiement",
                description="Lancement de l'application sur chaque serveur",
                contenu=remplir(lire("commun/docker-compose.prod.yml"), port_app=PORTS[d.langage])),
        Fichier(chemin=".github/workflows/deploy.yml", categorie="Déploiement",
                description="Pipeline GitHub Actions : construit l'image puis la déploie à chaque push sur main",
                contenu=remplir(lire("commun/deploy.yml"), utilisateur_ssh=UTILISATEUR_SSH[d.fournisseur])),
    ]
    fichiers += _infrastructure(d, projet, nom_base)
    fichiers_base, avertissements = _migration_base(d)
    fichiers += fichiers_base

    if d.type_base_donnees not in {"MySQL", "PostgreSQL", "Oracle", "SQL Server"}:
        avertissements.append(
            f"Base actuelle « {d.type_base_donnees} » : la migration des données n'est pas couverte par ce kit."
        )
    if d.fournisseur == "OVHcloud" and d.haute_disponibilite:
        avertissements.append(
            "OVHcloud (VPS) : la haute disponibilité de la base (réplication) n'est pas automatisée par ce kit. "
            "Ajoutez un Load Balancer OVHcloud et une réplique de la base, ou choisissez un fournisseur avec base gérée."
        )

    fichiers.insert(0, Fichier(
        chemin="GUIDE-DEPLOIEMENT.md", categorie="Guide",
        description="Le mode d'emploi pas à pas : de l'infrastructure à la bascule, avec le retour arrière",
        contenu=guide(d, projet, fichiers, avertissements),
    ))
    return Kit(projet=projet, fichiers=fichiers, avertissements=avertissements)
