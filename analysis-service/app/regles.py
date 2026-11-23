"""Règles de détection des problèmes de migration.

Chaque règle : un motif recherché ligne par ligne dans les fichiers d'un langage,
avec sa gravité, son explication et la correction à appliquer.
"""

import re
from dataclasses import dataclass

# Date de référence des versions « encore maintenues » (à mettre à jour régulièrement)
DATE_REFERENCE = "novembre 2026"

CODE = {
    "PHP": (".php",),
    "Java": (".java",),
    "Node.js": (".js", ".mjs", ".cjs", ".ts"),
}
CONFIG = (".env", ".properties", ".yml", ".yaml", ".ini", ".conf", ".json", ".xml")


@dataclass(frozen=True)
class Regle:
    id: str
    langages: tuple[str, ...]  # langages concernés ; ("*",) = tous
    motif: str
    gravite: str
    categorie: str
    titre: str
    explication: str
    correction: str
    dans_config: bool = False  # chercher aussi dans les fichiers de configuration
    masquer: bool = False  # masquer la valeur trouvée (secrets)

    @property
    def regex(self) -> re.Pattern:
        return re.compile(self.motif)


REGLES = [
    # ---------- PHP (cible : PHP 8.2 ou plus) ----------
    Regle(
        "php-mysql", ("PHP",),
        r"\bmysql_(connect|pconnect|query|fetch_\w+|select_db|real_escape_string|num_rows|"
        r"affected_rows|insert_id|close|error|errno|result|free_result)\s*\(",
        "Bloquant", "Compatibilité", "Extension mysql_* supprimée",
        "Les fonctions mysql_* ont été supprimées en PHP 7.0 : le code ne fonctionnera plus.",
        "Remplacer par PDO ou mysqli, avec des requêtes préparées (ce qui protège aussi "
        "des injections SQL).",
    ),
    Regle(
        "php-ereg", ("PHP",), r"\b(ereg|eregi|ereg_replace|eregi_replace|split|spliti)\s*\(",
        "Bloquant", "Compatibilité", "Fonctions ereg / split supprimées",
        "Les fonctions POSIX ereg*, split et spliti ont été supprimées en PHP 7.0.",
        "Utiliser preg_match, preg_replace ou preg_split (expressions régulières PCRE), "
        "ou explode pour un séparateur simple.",
    ),
    Regle(
        "php-each", ("PHP",), r"(?<![>:\w$])each\s*\(",
        "Bloquant", "Compatibilité", "Fonction each() supprimée",
        "La fonction each() a été supprimée en PHP 8.0.",
        "Remplacer les boucles while (list(...) = each(...)) par foreach.",
    ),
    Regle(
        "php-create-function", ("PHP",), r"\bcreate_function\s*\(",
        "Bloquant", "Compatibilité", "create_function() supprimée",
        "create_function() a été supprimée en PHP 8.0 (et posait des risques de sécurité).",
        "Utiliser une fonction anonyme : function ($x) { ... } ou fn($x) => ...",
    ),
    Regle(
        "php-mcrypt", ("PHP",), r"\bmcrypt_\w+\s*\(",
        "Bloquant", "Compatibilité", "Extension mcrypt supprimée",
        "L'extension mcrypt a été retirée de PHP en version 7.2.",
        "Utiliser openssl_encrypt / openssl_decrypt ou l'extension sodium.",
    ),
    Regle(
        "php-autoload", ("PHP",), r"function\s+__autoload\s*\(",
        "Bloquant", "Compatibilité", "__autoload() supprimée",
        "La fonction magique __autoload() a été supprimée en PHP 8.0.",
        "Utiliser spl_autoload_register(), ou l'autoload de Composer.",
    ),
    Regle(
        "php-magic-quotes", ("PHP",),
        r"\b(get_magic_quotes_gpc|get_magic_quotes_runtime|set_magic_quotes_runtime)\s*\(",
        "Bloquant", "Compatibilité", "Fonctions magic quotes supprimées",
        "Les fonctions liées aux « magic quotes » ont été supprimées en PHP 8.0.",
        "Supprimer ces appels et échapper les données avec des requêtes préparées.",
    ),
    Regle(
        "php-money-format", ("PHP",), r"\bmoney_format\s*\(",
        "Bloquant", "Compatibilité", "money_format() supprimée",
        "money_format() a été supprimée en PHP 8.0.",
        "Utiliser NumberFormatter (extension intl).",
    ),
    Regle(
        "php-raw-post", ("PHP",), r"\$HTTP_RAW_POST_DATA\b",
        "Bloquant", "Compatibilité", "$HTTP_RAW_POST_DATA supprimée",
        "La variable $HTTP_RAW_POST_DATA a été supprimée en PHP 7.0.",
        "Lire le corps de la requête avec file_get_contents('php://input').",
    ),
    Regle(
        "php-accolades", ("PHP",), r"\$\w+\{\s*(\$\w+|\d+)\s*\}",
        "Important", "Compatibilité", "Accès à un caractère avec des accolades",
        "La syntaxe $chaine{0} a été supprimée en PHP 8.0.",
        "Utiliser des crochets : $chaine[0].",
    ),
    Regle(
        "php-short-tag", ("PHP",), r"<\?(?!php|=|xml)\s",
        "Important", "Compatibilité", "Balises courtes <?",
        "Les balises courtes <? sont désactivées par défaut sur les serveurs récents : "
        "le code s'afficherait au lieu d'être exécuté.",
        "Remplacer <? par <?php.",
    ),
    # ---------- Java (cible : Java 17 ou 21 LTS) ----------
    Regle(
        "java-jaxb", ("Java",), r"import\s+javax\.xml\.bind\.",
        "Bloquant", "Compatibilité", "JAXB retiré du JDK",
        "Le module JAXB (javax.xml.bind) a été retiré du JDK en Java 11.",
        "Ajouter la dépendance jakarta.xml.bind-api et son implémentation, "
        "puis utiliser le paquet jakarta.xml.bind.",
    ),
    Regle(
        "java-jaxws", ("Java",), r"import\s+javax\.(xml\.ws|jws|activation)\.",
        "Bloquant", "Compatibilité", "JAX-WS / Activation retirés du JDK",
        "Les modules JAX-WS et JavaBeans Activation ont été retirés du JDK en Java 11.",
        "Ajouter les dépendances Jakarta correspondantes (jakarta.xml.ws-api, jakarta.activation).",
    ),
    Regle(
        "java-corba", ("Java",), r"import\s+(org\.omg\.|javax\.rmi\.CORBA)",
        "Bloquant", "Compatibilité", "CORBA retiré du JDK",
        "CORBA a été retiré du JDK en Java 11.",
        "Remplacer les échanges CORBA par une API REST ou gRPC.",
    ),
    Regle(
        "java-base64", ("Java",), r"sun\.misc\.BASE64(En|De)coder",
        "Bloquant", "Compatibilité", "sun.misc.BASE64Encoder supprimé",
        "Ces classes internes n'existent plus depuis Java 9.",
        "Utiliser java.util.Base64.getEncoder() / getDecoder().",
    ),
    Regle(
        "java-nashorn", ("Java",), r"getEngineByName\(\s*\"(nashorn|javascript|js)\"",
        "Bloquant", "Compatibilité", "Moteur JavaScript Nashorn retiré",
        "Nashorn a été retiré du JDK en Java 15.",
        "Utiliser GraalJS, ou supprimer l'exécution de JavaScript côté serveur.",
    ),
    Regle(
        "java-sun-interne", ("Java",), r"import\s+sun\.(?!misc\.BASE64)\w+",
        "Important", "Compatibilité", "Utilisation d'API internes sun.*",
        "Les API internes du JDK sont inaccessibles par défaut depuis Java 17.",
        "Remplacer par l'API publique équivalente.",
    ),
    Regle(
        "java-security-manager", ("Java",), r"System\.(get|set)SecurityManager\s*\(",
        "Important", "Compatibilité", "Security Manager désactivé",
        "Le Security Manager est déprécié, puis définitivement désactivé dans les versions récentes.",
        "Supprimer cette dépendance et appliquer la sécurité au niveau de l'application "
        "ou du conteneur.",
    ),
    Regle(
        "java-javax", ("Java",), r"import\s+javax\.(servlet|persistence|validation|annotation)\.",
        "Conseil", "Compatibilité", "Paquets javax.* (Java EE)",
        "Spring Boot 3 et Jakarta EE 9+ utilisent les paquets jakarta.* au lieu de javax.*.",
        "En montant de version, renommer ces imports en jakarta.* (des outils comme "
        "OpenRewrite le font automatiquement).",
    ),
    Regle(
        "java-boxing", ("Java",),
        r"new\s+(Integer|Long|Double|Float|Short|Byte|Character|Boolean)\s*\(",
        "Conseil", "Compatibilité", "Constructeurs Integer(...) dépréciés",
        "Ces constructeurs sont dépréciés et marqués pour suppression.",
        "Utiliser Integer.valueOf(...) ou l'autoboxing.",
    ),
    Regle(
        "java-finalize", ("Java",), r"void\s+finalize\s*\(\s*\)",
        "Conseil", "Compatibilité", "Méthode finalize() dépréciée",
        "La finalisation est dépréciée pour suppression depuis Java 18.",
        "Utiliser try-with-resources ou java.lang.ref.Cleaner.",
    ),
    # ---------- Node.js (cible : Node.js 22 ou 24 LTS) ----------
    Regle(
        "node-create-cipher", ("Node.js",), r"\bcreate(De)?cipher\s*\(",
        "Bloquant", "Compatibilité", "crypto.createCipher() supprimée",
        "createCipher et createDecipher ont été supprimées en Node.js 22.",
        "Utiliser createCipheriv / createDecipheriv avec un vecteur d'initialisation.",
    ),
    Regle(
        "node-util-is", ("Node.js",),
        r"\butil\.is(Array|Boolean|Buffer|Date|Error|Function|Null|NullOrUndefined|Number|"
        r"Object|Primitive|RegExp|String|Symbol|Undefined)\s*\(",
        "Important", "Compatibilité", "Fonctions util.isXxx() retirées",
        "Ces fonctions sont dépréciées depuis longtemps et retirées des versions récentes de Node.js.",
        "Utiliser Array.isArray(), typeof, instanceof ou x === null.",
    ),
    Regle(
        "node-buffer", ("Node.js",), r"new\s+Buffer\s*\(",
        "Important", "Sécurité", "Constructeur new Buffer() déprécié",
        "new Buffer() est déprécié (DEP0005) et peut exposer de la mémoire non initialisée.",
        "Utiliser Buffer.from(), Buffer.alloc() ou Buffer.allocUnsafe().",
    ),
    Regle(
        "node-request", ("Node.js",), r"require\(\s*['\"]request['\"]\s*\)",
        "Important", "Compatibilité", "Paquet « request » abandonné",
        "Le paquet request n'est plus maintenu depuis 2020 : plus aucun correctif de sécurité.",
        "Utiliser fetch (intégré à Node.js 18+) ou axios.",
    ),
    Regle(
        "node-process-binding", ("Node.js",), r"process\.binding\s*\(",
        "Important", "Compatibilité", "process.binding() déprécié",
        "process.binding() est une API interne dépréciée.",
        "Utiliser les modules publics de Node.js.",
    ),
    Regle(
        "node-url-parse", ("Node.js",), r"\burl\.parse\s*\(",
        "Conseil", "Compatibilité", "url.parse() dépréciée",
        "url.parse() est une API ancienne et dépréciée.",
        "Utiliser new URL(adresse).",
    ),
    Regle(
        "node-fs-exists", ("Node.js",), r"\bfs\.exists\s*\(",
        "Conseil", "Compatibilité", "fs.exists() dépréciée",
        "fs.exists() est dépréciée.",
        "Utiliser fs.existsSync() ou fs.promises.access().",
    ),
    # ---------- Tous langages : sécurité et préparation au cloud ----------
    Regle(
        "secret-en-dur", ("*",),
        # 1) dans le code : motdepasse = "valeur"   2) dans un fichier .properties / .env : cle=valeur
        r"(?i)(?:password|passwd|pwd|mot_de_passe|secret|api_?key|access_?key|token)\w*['\"]?\s*"
        r"(?:=>|=|:)\s*['\"]([^'\"\s]{4,})['\"]"
        r"|^\s*[\w.\-]*(?:password|passwd|pwd|secret|api[_.\-]?key|access[_.\-]?key|token)[\w.\-]*"
        r"\s*=\s*([^\s'\"${;()]{4,})\s*$",
        "Important", "Sécurité", "Mot de passe ou clé écrit en dur",
        "Un secret écrit dans le code se retrouve dans Git et sur chaque serveur : "
        "c'est la première cause de fuite lors d'une migration.",
        "Lire le secret depuis une variable d'environnement, puis le stocker dans le "
        "gestionnaire de secrets du fournisseur cloud.",
        dans_config=True, masquer=True,
    ),
    Regle(
        "adresse-locale", ("*",), r"\b(localhost|127\.0\.0\.1)\b",
        "Important", "Cloud", "Adresse locale écrite en dur",
        "Dans le cloud, la base de données et les autres services ne sont plus sur la même "
        "machine : « localhost » ne fonctionnera plus.",
        "Mettre les adresses dans des variables d'environnement (ex. DB_HOST).",
        dans_config=True,
    ),
    Regle(
        "chemin-absolu", ("*",), r"([A-Za-z]:\\\\?[\w ]|/var/www/|/home/\w+/|/opt/\w+/)",
        "Important", "Cloud", "Chemin absolu du serveur",
        "Les chemins propres au serveur actuel n'existeront pas sur le serveur cloud.",
        "Utiliser des chemins relatifs au projet ou une variable de configuration.",
        dans_config=True,
    ),
    Regle(
        "fichiers-locaux", ("*",),
        r"\bmove_uploaded_file\s*\(|\.transferTo\s*\(|diskStorage\s*\(|multer\(\s*\{\s*dest",
        "Conseil", "Cloud", "Fichiers envoyés stockés sur le disque du serveur",
        "Dans le cloud, les serveurs peuvent être remplacés ou multipliés : "
        "les fichiers stockés sur leur disque peuvent être perdus.",
        "Stocker les fichiers dans un stockage objet (Amazon S3, Azure Blob, Google Cloud Storage).",
    ),
]

# Frameworks dont la version n'est plus maintenue à la DATE_REFERENCE :
# (motif sur le framework ou l'interface détectés, explication, correction)
FRAMEWORKS_OBSOLETES = [
    (r"^Spring Boot [12]\.", "Le support open source de Spring Boot 2 est terminé depuis 2023.",
     "Migrer vers Spring Boot 3 (nécessite Java 17 et le passage aux paquets jakarta.*)."),
    (r"^Laravel ([4-9]|1[01])(\.|$)", "Cette version de Laravel ne reçoit plus de correctifs de sécurité.",
     "Monter vers une version de Laravel encore maintenue, étape par étape."),
    (r"^AngularJS$", "AngularJS n'est plus maintenu depuis janvier 2022.",
     "Réécrire progressivement l'interface en Angular, React ou Vue."),
    (r"^CodeIgniter [23]", "CodeIgniter 2 et 3 ne sont plus maintenus.",
     "Migrer vers CodeIgniter 4."),
]

# Versions minimales encore maintenues à la DATE_REFERENCE
VERSIONS_MINIMALES = {"PHP": 8.2, "Java": 17, "Node.js": 22}
CONSEIL_VERSION = {
    "PHP": "Cibler PHP 8.3 ou 8.4.",
    "Java": "Cibler Java 21 (version LTS).",
    "Node.js": "Cibler Node.js 22 ou 24 (versions LTS).",
}
