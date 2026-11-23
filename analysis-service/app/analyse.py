"""Analyse complète : détection de la pile, recherche des problèmes, score et pré-remplissage."""

import re

from app.archive import Projet
from app.deductions import deduire
from app.detection import detecter
from app.regles import (
    CODE, CONFIG, CONSEIL_VERSION, DATE_REFERENCE, FRAMEWORKS_OBSOLETES, REGLES,
    VERSIONS_MINIMALES, Regle,
)
from app.schemas import AnalyseResultat, Occurrence, Pile, Probleme, Resume, Statistiques

MAX_OCCURRENCES = 20  # nombre d'endroits détaillés par problème
POIDS = {"Bloquant": 12, "Important": 5, "Conseil": 1}
COMMENTAIRE = re.compile(r"^\s*(//|#|\*|/\*|<!--)")
LANGAGES_FORMULAIRE = {"PHP": "PHP", "Java": "Java", "Node.js": "JavaScript"}
INTERFACES_FORMULAIRE = {"HTML/jQuery", "AngularJS", "Angular", "React", "Vue"}


def _fichiers_cibles(projet: Projet, regle: Regle, langage: str | None) -> dict[str, str]:
    if "*" in regle.langages:
        extensions = tuple(e for exts in CODE.values() for e in exts)
    elif langage in regle.langages:
        extensions = CODE[langage]
    else:
        return {}
    if regle.dans_config:
        extensions += CONFIG
    return {
        c: t for c, t in projet.fichiers.items()
        if c.endswith(extensions) or c.rsplit("/", 1)[-1] == ".env"
        if not c.endswith(("package-lock.json", "composer.lock"))
    }


def _extrait(ligne: str, regle: Regle, trouve: re.Match) -> str:
    texte = ligne.strip()
    if regle.masquer:
        secret = next((g for g in reversed(trouve.groups()) if g), "")
        texte = texte.replace(secret, "****") if secret else texte
    return texte[:160]


def _chercher(projet: Projet, regle: Regle, langage: str | None) -> Probleme | None:
    occurrences = []
    for chemin, texte in sorted(_fichiers_cibles(projet, regle, langage).items()):
        for numero, ligne in enumerate(texte.splitlines(), start=1):
            if COMMENTAIRE.match(ligne):
                continue
            trouve = regle.regex.search(ligne)
            if trouve:
                occurrences.append(Occurrence(fichier=chemin, ligne=numero, extrait=_extrait(ligne, regle, trouve)))
    if not occurrences:
        return None
    return Probleme(
        regle=regle.id, titre=regle.titre, gravite=regle.gravite, categorie=regle.categorie,
        explication=regle.explication, correction=regle.correction,
        total=len(occurrences), occurrences=occurrences[:MAX_OCCURRENCES],
    )


def _probleme_version(pile: Pile) -> Probleme | None:
    """Signale une version du langage qui n'est plus maintenue."""
    minimum = VERSIONS_MINIMALES.get(pile.langage or "")
    if not minimum or not pile.version_langage:
        return None
    try:
        version = float(pile.version_langage)
    except ValueError:
        return None
    if version >= minimum:
        return None
    return Probleme(
        regle="version-obsolete",
        titre=f"{pile.langage} {pile.version_langage} n'est plus maintenu",
        gravite="Important", categorie="Sécurité",
        explication=f"En {DATE_REFERENCE}, {pile.langage} {pile.version_langage} ne reçoit plus "
        "de correctifs de sécurité, et les hébergeurs cloud ne le proposent plus.",
        correction=CONSEIL_VERSION[pile.langage],
        total=1, occurrences=[],
    )


def _problemes_frameworks(pile: Pile) -> list[Probleme]:
    """Signale un framework ou une interface dont la version n'est plus maintenue."""
    problemes = []
    for nom in filter(None, [pile.framework, pile.interface]):
        for motif, explication, correction in FRAMEWORKS_OBSOLETES:
            if re.search(motif, nom):
                problemes.append(Probleme(
                    regle="framework-obsolete", titre=f"{nom} n'est plus maintenu",
                    gravite="Important", categorie="Sécurité",
                    explication=f"{explication} (situation en {DATE_REFERENCE})",
                    correction=correction, total=1, occurrences=[],
                ))
    return problemes


def _statistiques(projet: Projet) -> Statistiques:
    lignes = {}
    for langage, extensions in CODE.items():
        total = sum(t.count("\n") + 1 for c, t in projet.fichiers.items() if c.endswith(extensions))
        if total:
            lignes[langage] = total
    return Statistiques(
        fichiers=projet.nombre_total_fichiers,
        fichiers_analyses=len(projet.fichiers),
        lignes_de_code=sum(lignes.values()),
        lignes_par_langage=lignes,
    )


def _resume_texte(pile: Pile, problemes: list[Probleme], resume: Resume) -> str:
    """Résumé transmis à l'IA dans la description libre, pour qu'elle en tienne compte."""
    morceaux = [
        f"Analyse automatique du code : {resume.bloquants} problème(s) bloquant(s), "
        f"{resume.importants} important(s), {resume.conseils} conseil(s)."
    ]
    for p in problemes[:8]:
        morceaux.append(f"- [{p.gravite}] {p.titre} ({p.total} occurrence(s)) : {p.correction}")
    return "\n".join(morceaux)[:2900]


def _description(pile: Pile, problemes: list[Probleme], resume: Resume) -> dict:
    """Valeurs du formulaire, avec exactement les options du contrat."""
    description: dict = {}
    if pile.langage:
        description["langage"] = LANGAGES_FORMULAIRE[pile.langage]
    if pile.version_langage:
        description["version_langage"] = pile.version_langage
    if pile.framework:
        description["framework_backend"] = pile.framework
    if pile.interface:
        # Thymeleaf, JSP, Twig… ne sont pas dans la liste du formulaire : « Autre »
        description["interface_utilisateur"] = (
            pile.interface if pile.interface in INTERFACES_FORMULAIRE else "Autre"
        )
    if pile.base_de_donnees:
        description["type_base_donnees"] = pile.base_de_donnees
    description["type_architecture"] = pile.architecture
    if pile.integrations:
        description["integrations_externes"] = ", ".join(pile.integrations)

    categories = {p.categorie for p in problemes}
    problemes_actuels = []
    if "Sécurité" in categories:
        problemes_actuels.append("Failles de sécurité")
    if resume.bloquants:
        problemes_actuels.append("Code difficile à maintenir")
    description["problemes_actuels"] = problemes_actuels
    if any(p.regle in {"version-obsolete", "framework-obsolete"} for p in problemes) or resume.bloquants:
        description["objectifs"] = ["Moderniser"]
    description["description_libre"] = _resume_texte(pile, problemes, resume)
    return description


def analyser(projet: Projet) -> AnalyseResultat:
    pile, dependances = detecter(projet)

    problemes = [p for r in REGLES if (p := _chercher(projet, r, pile.langage))]
    if version := _probleme_version(pile):
        problemes.append(version)
    problemes += _problemes_frameworks(pile)
    ordre = {"Bloquant": 0, "Important": 1, "Conseil": 2}
    problemes.sort(key=lambda p: (ordre[p.gravite], -p.total))

    resume = Resume(
        bloquants=sum(p.gravite == "Bloquant" for p in problemes),
        importants=sum(p.gravite == "Important" for p in problemes),
        conseils=sum(p.gravite == "Conseil" for p in problemes),
    )
    score = max(0, 100 - sum(POIDS[p.gravite] for p in problemes))

    description = _description(pile, problemes, resume)
    a_verifier = deduire(projet, pile)
    if "objectifs" in description:
        a_verifier["objectifs"] = description.pop("objectifs")

    return AnalyseResultat(
        pile=pile,
        statistiques=_statistiques(projet),
        dependances=dependances,
        problemes=problemes,
        resume=resume,
        score_preparation=score,
        description_preremplie={**description, **a_verifier},
        champs_detectes=sorted(description),
        champs_a_verifier=sorted(a_verifier),
    )
