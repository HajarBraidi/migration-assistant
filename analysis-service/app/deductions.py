"""Déductions « à vérifier » : des indices dans le projet suggèrent des réponses
à des questions métier (domaine, utilisateurs, hébergement, données sensibles).

Contrairement à la détection (fichiers de configuration = certitude), ce sont des
suppositions : le formulaire les signale à l'utilisateur pour qu'il les confirme.
"""

import re
import unicodedata

from app.archive import Projet
from app.schemas import Pile

TRANCHES_UTILISATEURS = [(100, "< 100"), (1000, "100 à 1 000"), (50000, "1 000 à 50 000")]

MOTS_DOMAINES = {
    "RH": r"employe|salarie|conge|paie|recrutement|personnel|\brh\b|contrat_travail",
    "Gestion de stock": r"stock|inventaire|entrepot|fournisseur|reapprovision|article",
    "E-commerce": r"panier|commande|boutique|checkout|\bcart\b|\border|livraison|catalogue",
    "Finance": r"facture|comptab|banque|credit|ecriture|tresorerie|budget",
}

DONNEES_SENSIBLES = {
    "Données personnelles (RGPD / loi 09-08)":
        r"email|e_mail|telephone|phone|adresse|address|date_?naissance|birth_?date|\bcin\b|cnie|passeport",
    "Données bancaires": r"\biban\b|\brib\b|carte_?bancaire|card_?number|\bcvv\b|numero_?compte",
    "Données de santé": r"patient|diagnostic|medical|ordonnance|dossier_?medical|mutuelle",
}


def _sans_accents(texte: str) -> str:
    return unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode().lower()


def _readme(projet: Projet) -> str:
    for nom in ("README.md", "README.txt", "readme.md", "LISEZMOI.md", "README"):
        chemins = projet.chercher(nom)
        if chemins:
            return projet.fichiers[chemins[0]]
    return ""


def _identifiants(projet: Projet) -> str:
    """Chemins des fichiers, tables SQL et noms de classes : de quoi parle le projet."""
    morceaux = list(projet.fichiers)
    for chemin, texte in projet.fichiers.items():
        if chemin.endswith(".sql"):
            morceaux += re.findall(r"(?i)create\s+table\s+(?:if\s+not\s+exists\s+)?[`\"]?(\w+)", texte)
        if chemin.endswith((".java", ".php", ".js", ".ts")):
            morceaux += re.findall(r"\b(?:class|interface)\s+(\w+)", texte)
    return _sans_accents(" ".join(morceaux).replace("/", " ").replace(".", " "))


def _champs_de_donnees(projet: Projet) -> str:
    """Colonnes SQL et attributs du code : quelles données l'application manipule."""
    textes = [
        t for c, t in projet.fichiers.items() if c.endswith((".sql", ".java", ".php", ".js", ".ts"))
    ]
    return _sans_accents("\n".join(textes))


def nombre_utilisateurs(readme: str) -> str | None:
    trouve = re.search(
        r"(\d[\d\s. ]*)\s*(utilisateurs|employes|employés|clients|agents|collaborateurs|users)",
        readme, re.IGNORECASE,
    )
    if not trouve:
        return None
    nombre = int(re.sub(r"\D", "", trouve.group(1)) or 0)
    for limite, tranche in TRANCHES_UTILISATEURS:
        if nombre < limite:
            return tranche
    return "> 50 000"


def hebergement(projet: Projet, readme: str) -> str | None:
    texte = _sans_accents(readme)
    if re.search(r"\b(aws|azure|gcp|google cloud|amazon web services)\b", texte):
        return "Cloud"
    if re.search(r"\b(ovh|o2switch|hostinger|ionos|heberge(ur|ment) mutualise|hebergeur)\b", texte):
        return "Hébergeur"
    if re.search(r"serveur (local|interne|physique)|dans nos locaux|on[- ]premise|salle serveur", texte):
        return "Serveur local"
    if any(projet.chercher(n) for n in ("app.yaml", "Procfile", "serverless.yml")):
        return "Cloud"
    code = "\n".join(projet.fichiers.values())
    if re.search(r"\blocalhost\b|127\.0\.0\.1|[A-Za-z]:\\\\|/var/www/", code):
        return "Serveur local"
    return None


def domaine(projet: Projet, readme: str) -> str | None:
    texte = _identifiants(projet) + " " + _sans_accents(readme)
    scores = {d: len(re.findall(motif, texte)) for d, motif in MOTS_DOMAINES.items()}
    meilleur, score = max(scores.items(), key=lambda s: s[1])
    return meilleur if score >= 2 else None


def exigences(projet: Projet) -> list[str]:
    donnees = _champs_de_donnees(projet)
    trouvees = []
    for exigence, motif in DONNEES_SENSIBLES.items():
        # Au moins deux champs différents, pour éviter qu'un seul mot isolé suffise
        if len(set(re.findall(motif, donnees))) >= 2 or (
            exigence != "Données personnelles (RGPD / loi 09-08)" and re.search(motif, donnees)
        ):
            trouvees.append(exigence)
    return trouvees


def deduire(projet: Projet, pile: Pile) -> dict:
    """Renvoie les valeurs déduites, à faire confirmer par l'utilisateur."""
    readme = _readme(projet)
    valeurs: dict = {}
    if d := domaine(projet, readme):
        valeurs["domaine"] = d
    if n := nombre_utilisateurs(readme):
        valeurs["nombre_utilisateurs"] = n
    if h := hebergement(projet, readme):
        valeurs["hebergement_actuel"] = h
    if e := exigences(projet):
        valeurs["exigences_securite"] = e
    competences = [pile.langage, pile.framework, pile.base_de_donnees]
    if any(competences):
        valeurs["competences_equipe"] = ", ".join(filter(None, competences))
    return valeurs
