"""Détection des technologies à partir des fichiers de configuration du projet."""

import json
import re

from defusedxml import ElementTree

from app.archive import Projet
from app.schemas import Dependance, Pile

# ---------- Correspondances : nom de dépendance -> information détectée ----------

BASES_DE_DONNEES = [
    # (motif dans le nom de la dépendance ou le code, base de données)
    (r"mysql|mariadb", "MySQL"),
    (r"postgres|\bpg\b|pgsql", "PostgreSQL"),
    (r"ojdbc|oracledb|\boci_", "Oracle"),
    (r"mssql|sqlsrv|tedious|sqlserver", "SQL Server"),
    (r"mongo", "MongoDB"),
]

INTEGRATIONS = {
    "stripe": "Paiement Stripe",
    "paypal": "Paiement PayPal",
    "aws-sdk": "Services AWS",
    "awssdk": "Services AWS",
    "twilio": "SMS Twilio",
    "sendgrid": "Email SendGrid",
    "phpmailer": "Envoi d'emails",
    "nodemailer": "Envoi d'emails",
    "javax.mail": "Envoi d'emails",
    "jakarta.mail": "Envoi d'emails",
    "firebase": "Firebase",
    "elasticsearch": "Elasticsearch",
    "redis": "Cache Redis",
    "predis": "Cache Redis",
}


def _version_courte(contrainte: str | None) -> str | None:
    """« >=5.6 », « ^7.2 », « 5.4.* » -> « 5.6 », « 7.2 », « 5.4 »."""
    if not contrainte:
        return None
    trouve = re.search(r"(\d+)(?:\.(\d+))?", contrainte)
    if not trouve:
        return None
    return trouve.group(1) + (f".{trouve.group(2)}" if trouve.group(2) else "")


def _lire_json(projet: Projet, nom: str) -> dict:
    for chemin in projet.chercher(nom):
        try:
            donnees = json.loads(projet.fichiers[chemin])
        except ValueError:
            continue
        if isinstance(donnees, dict):
            return donnees
    return {}


def _base_depuis_texte(texte: str) -> str | None:
    for motif, base in BASES_DE_DONNEES:
        if re.search(motif, texte, re.IGNORECASE):
            return base
    return None


def _integrations(noms: list[str]) -> list[str]:
    trouvees = []
    for nom in noms:
        for cle, libelle in INTEGRATIONS.items():
            if cle in nom.lower() and libelle not in trouvees:
                trouvees.append(libelle)
    return trouvees


# ---------- PHP ----------


def _detecter_php(projet: Projet, pile: Pile, deps: list[Dependance]) -> None:
    composer = _lire_json(projet, "composer.json")
    requis = {**composer.get("require", {}), **composer.get("require-dev", {})}
    for nom, version in requis.items():
        if nom != "php" and not nom.startswith("ext-"):
            deps.append(Dependance(nom=nom, version=version, ecosysteme="composer"))

    pile.version_langage = _version_courte(requis.get("php"))
    frameworks = [
        ("laravel/framework", "Laravel"), ("symfony/framework-bundle", "Symfony"),
        ("symfony/symfony", "Symfony"), ("codeigniter4/framework", "CodeIgniter"),
        ("cakephp/cakephp", "CakePHP"), ("yiisoft/yii2", "Yii"), ("slim/slim", "Slim"),
    ]
    for paquet, nom in frameworks:
        if paquet in requis:
            version = _version_courte(requis[paquet])
            pile.framework = f"{nom} {version}" if version else nom
            break
    if pile.framework is None:
        for chemin, texte in projet.fichiers.items():
            if chemin.endswith("CodeIgniter.php"):
                version = re.search(r"CI_VERSION'\s*,\s*'([\d.]+)'", texte)
                pile.framework = f"CodeIgniter {version.group(1)}" if version else "CodeIgniter"
                break

    # Base de données : fichier .env, puis fonctions utilisées dans le code
    env = next((projet.fichiers[c] for c in projet.chercher(".env")), "")
    connexion = re.search(r"^DB_CONNECTION\s*=\s*(\w+)", env, re.MULTILINE)
    if connexion:
        pile.base_de_donnees = _base_depuis_texte(connexion.group(1))
    if pile.base_de_donnees is None:
        code = "\n".join(projet.par_extension(".php").values())
        for motif, base in [
            (r"\bmysqli?_\w+\s*\(|new\s+mysqli\b|['\"]mysql:", "MySQL"),
            (r"\bpg_connect\s*\(|['\"]pgsql:", "PostgreSQL"),
            (r"\boci_connect\s*\(|['\"]oci:", "Oracle"),
            (r"\bsqlsrv_connect\s*\(|['\"]sqlsrv:", "SQL Server"),
            (r"MongoDB\\Client", "MongoDB"),
        ]:
            if re.search(motif, code):
                pile.base_de_donnees = base
                break


# ---------- Java ----------

NS_MAVEN = re.compile(r"\{.*?\}")


def _texte_xml(element, chemin: str) -> str | None:
    """Cherche un élément du pom.xml sans tenir compte de l'espace de noms Maven."""
    for enfant in element.iter():
        if NS_MAVEN.sub("", enfant.tag) == chemin and enfant.text:
            return enfant.text.strip()
    return None


def _version_java(valeur: str | None) -> str | None:
    """« 1.8 » -> « 8 », « 17 » -> « 17 »."""
    if not valeur:
        return None
    valeur = valeur.replace("JavaVersion.VERSION_", "").replace("_", ".")
    return valeur[2:] if valeur.startswith("1.") else _version_courte(valeur)


def _detecter_java(projet: Projet, pile: Pile, deps: list[Dependance]) -> None:
    for chemin in projet.chercher("pom.xml")[:1]:
        try:
            racine = ElementTree.fromstring(projet.fichiers[chemin])
        except ElementTree.ParseError:
            break
        proprietes = {}
        for element in racine.iter():
            tag = NS_MAVEN.sub("", element.tag)
            if tag in {"java.version", "maven.compiler.source", "maven.compiler.release"}:
                proprietes[tag] = (element.text or "").strip()
            if tag == "dependency":
                groupe = _texte_xml(element, "groupId") or ""
                artefact = _texte_xml(element, "artifactId") or ""
                deps.append(
                    Dependance(
                        nom=f"{groupe}:{artefact}",
                        version=_texte_xml(element, "version"),
                        ecosysteme="maven",
                    )
                )
        pile.version_langage = _version_java(
            proprietes.get("java.version")
            or proprietes.get("maven.compiler.release")
            or proprietes.get("maven.compiler.source")
        )
        for parent in racine.iter():
            if NS_MAVEN.sub("", parent.tag) == "parent" and "spring-boot" in (
                _texte_xml(parent, "artifactId") or ""
            ):
                pile.framework = f"Spring Boot {_version_courte(_texte_xml(parent, 'version'))}"

    for chemin in (projet.chercher("build.gradle") + projet.chercher("build.gradle.kts"))[:1]:
        texte = projet.fichiers[chemin]
        version = re.search(
            r"sourceCompatibility\s*=?\s*['\"]?(JavaVersion\.VERSION_[\d_]+|[\d.]+)", texte
        ) or re.search(r"JavaLanguageVersion\.of\((\d+)\)", texte)
        if version:
            pile.version_langage = _version_java(version.group(1))
        boot = re.search(r"org\.springframework\.boot['\"]\)?\s*version\s*['\"]([\d.]+)", texte)
        if boot:
            pile.framework = f"Spring Boot {_version_courte(boot.group(1))}"
        for groupe, artefact, version in re.findall(
            r"['\"]([\w.\-]+):([\w.\-]+):?([\w.\-]*)['\"]", texte
        ):
            deps.append(
                Dependance(nom=f"{groupe}:{artefact}", version=version or None, ecosysteme="gradle")
            )

    noms = " ".join(d.nom for d in deps)
    if pile.framework is None:
        if "spring-webmvc" in noms or "spring-web" in noms:
            pile.framework = "Spring MVC"
        elif "struts" in noms:
            pile.framework = "Struts"
        elif projet.par_extension(".jsp") or "servlet" in noms:
            pile.framework = "Servlets / JSP"

    # Base de données : dépendances, puis configuration Spring
    pile.base_de_donnees = _base_depuis_texte(noms.replace("spring-boot-starter-data-jpa", ""))
    if pile.base_de_donnees is None:
        config = "\n".join(
            t for c, t in projet.fichiers.items() if c.endswith((".properties", ".yml", ".yaml"))
        )
        url = re.search(r"jdbc:(\w+)", config)
        if url:
            pile.base_de_donnees = _base_depuis_texte(url.group(1))


# ---------- Node.js ----------


def _detecter_node(projet: Projet, pile: Pile, deps: list[Dependance]) -> None:
    paquet = _lire_json(projet, "package.json")
    pile.version_langage = _version_courte(paquet.get("engines", {}).get("node"))
    for chemin in projet.chercher(".nvmrc")[:1]:
        pile.version_langage = _version_courte(projet.fichiers[chemin]) or pile.version_langage

    toutes = {**paquet.get("dependencies", {}), **paquet.get("devDependencies", {})}
    for nom, version in toutes.items():
        deps.append(Dependance(nom=nom, version=version, ecosysteme="npm"))

    for nom_paquet, nom in [
        ("@nestjs/core", "NestJS"), ("express", "Express"), ("koa", "Koa"),
        ("fastify", "Fastify"), ("@hapi/hapi", "Hapi"), ("hapi", "Hapi"),
    ]:
        if nom_paquet in toutes:
            version = _version_courte(toutes[nom_paquet])
            pile.framework = f"{nom} {version}" if version else nom
            break

    for motif, base in [
        (r"^(mysql2?|mariadb)$", "MySQL"), (r"^pg$", "PostgreSQL"),
        (r"^(mongoose|mongodb)$", "MongoDB"), (r"^oracledb$", "Oracle"),
        (r"^(mssql|tedious)$", "SQL Server"),
    ]:
        if any(re.match(motif, nom) for nom in toutes):
            pile.base_de_donnees = base
            break


# ---------- Interface, architecture, intégrations ----------


def _detecter_interface(projet: Projet) -> str | None:
    paquet = _lire_json(projet, "package.json")
    toutes = {**paquet.get("dependencies", {}), **paquet.get("devDependencies", {})}
    if "@angular/core" in toutes:
        return "Angular"
    if "react" in toutes:
        return "React"
    if "vue" in toutes:
        return "Vue"
    if "angular" in toutes or any("angular.js" in c or "angular.min.js" in c for c in projet.fichiers):
        return "AngularJS"
    pages = "\n".join(
        t for c, t in projet.fichiers.items()
        if c.endswith((".html", ".htm", ".php", ".jsp", ".twig", ".js"))
    )
    if re.search(r"\bng-app\b", pages):
        return "AngularJS"
    if "jquery" in toutes or re.search(r"jquery|\$\(\s*document\s*\)\.ready", pages, re.IGNORECASE):
        return "HTML/jQuery"
    # Pages générées par le serveur (sans framework JavaScript)
    if re.search(r"\bth:\w+=", pages) or any("/templates/" in c for c in projet.fichiers if c.endswith(".html")):
        return "Thymeleaf"
    if projet.par_extension(".jsp"):
        return "JSP"
    if projet.par_extension(".twig"):
        return "Twig"
    if projet.par_extension(".blade.php"):
        return "Blade"
    return None


def _detecter_architecture(projet: Projet, pile: Pile) -> None:
    for chemin in projet.chercher("docker-compose.yml") + projet.chercher("docker-compose.yaml"):
        texte = projet.fichiers[chemin]
        bloc = re.search(r"^services:\s*\n((?:[ \t]+.*\n?|\s*\n)*)", texte, re.MULTILINE)
        if bloc:
            services = re.findall(r"^  ([\w.-]+):\s*$", bloc.group(1), re.MULTILINE)
            images = re.findall(r"image:\s*['\"]?([\w./-]+)", texte)
            bases = [i for i in images if _base_depuis_texte(i)]
            applicatifs = [s for s in services if not _base_depuis_texte(s)]
            if len(applicatifs) - len(bases) > 1:
                pile.architecture = "Plusieurs services"
            if pile.base_de_donnees is None and bases:
                pile.base_de_donnees = _base_depuis_texte(bases[0])
        break


# ---------- Point d'entrée ----------


def _choisir_langage(projet: Projet) -> str | None:
    """Le langage principal du back-end, d'après les fichiers de configuration puis le code."""
    paquet = _lire_json(projet, "package.json")
    dependances_node = {**paquet.get("dependencies", {})}
    serveur_node = any(
        p in dependances_node for p in ["express", "@nestjs/core", "koa", "fastify", "@hapi/hapi", "hapi"]
    )
    scores = {
        "PHP": len(projet.par_extension(".php")) + (50 if projet.chercher("composer.json") else 0),
        "Java": len(projet.par_extension(".java"))
        + (50 if projet.chercher("pom.xml") or projet.chercher("build.gradle") else 0),
        "Node.js": (len(projet.par_extension(".js", ".ts")) if serveur_node else 0)
        + (50 if serveur_node else 0),
    }
    langage, score = max(scores.items(), key=lambda s: s[1])
    if score == 0 and paquet:
        return "Node.js"
    return langage if score > 0 else None


def detecter(projet: Projet) -> tuple[Pile, list[Dependance]]:
    pile = Pile(langage=_choisir_langage(projet))
    deps: list[Dependance] = []
    if pile.langage == "PHP":
        _detecter_php(projet, pile, deps)
    elif pile.langage == "Java":
        _detecter_java(projet, pile, deps)
    elif pile.langage == "Node.js":
        _detecter_node(projet, pile, deps)

    pile.interface = _detecter_interface(projet)
    _detecter_architecture(projet, pile)
    pile.integrations = _integrations([d.nom for d in deps])
    return pile, deps
