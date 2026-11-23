"""Lecture sûre d'une archive .zip, entièrement en mémoire (rien n'est écrit sur le disque)."""

import io
import zipfile
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from app.config import settings

# Dossiers sans intérêt pour l'analyse (dépendances téléchargées, fichiers générés…)
DOSSIERS_IGNORES = {
    "node_modules", "vendor", ".git", "target", "build", "dist", ".idea", ".vscode",
    "bower_components", "__pycache__", ".gradle", "out", "coverage",
}

EXTENSIONS_TEXTE = {
    ".php", ".java", ".js", ".mjs", ".cjs", ".ts", ".jsx", ".tsx", ".json", ".xml",
    ".gradle", ".kts", ".properties", ".yml", ".yaml", ".env", ".ini", ".conf", ".sql",
    ".html", ".htm", ".twig", ".jsp", ".txt", ".md", ".lock",
}
NOMS_TEXTE = {"Dockerfile", ".env", ".htaccess", "Procfile"}


class ArchiveInvalide(Exception):
    """L'archive est illisible ou dépasse les limites autorisées."""


@dataclass
class Projet:
    """Les fichiers texte du projet : chemin relatif -> contenu."""

    fichiers: dict[str, str] = field(default_factory=dict)
    nombre_total_fichiers: int = 0

    def chercher(self, nom: str) -> list[str]:
        """Chemins des fichiers portant ce nom, du moins profond au plus profond."""
        return sorted(
            (c for c in self.fichiers if PurePosixPath(c).name == nom),
            key=lambda c: c.count("/"),
        )

    def par_extension(self, *extensions: str) -> dict[str, str]:
        return {c: t for c, t in self.fichiers.items() if c.endswith(extensions)}


def _est_ignore(chemin: str) -> bool:
    morceaux = PurePosixPath(chemin).parts
    return any(m in DOSSIERS_IGNORES for m in morceaux)


def _est_texte(chemin: str) -> bool:
    nom = PurePosixPath(chemin)
    return nom.suffix.lower() in EXTENSIONS_TEXTE or nom.name in NOMS_TEXTE


def _chemin_sur(nom: str) -> str | None:
    """Refuse les chemins absolus ou qui remontent l'arborescence (« ../ »)."""
    chemin = PurePosixPath(nom.replace("\\", "/"))
    if chemin.is_absolute() or ".." in chemin.parts:
        return None
    return str(chemin)


def _retirer_dossier_racine(fichiers: dict[str, str]) -> dict[str, str]:
    """Si tout est dans un seul dossier (ex. « stockpro/… »), on le retire des chemins."""
    racines = {c.split("/", 1)[0] for c in fichiers}
    if len(racines) == 1 and all("/" in c for c in fichiers):
        return {c.split("/", 1)[1]: t for c, t in fichiers.items()}
    return fichiers


def lire_archive(contenu: bytes) -> Projet:
    """Lit une archive .zip et renvoie ses fichiers texte utiles."""
    if len(contenu) > settings.taille_max_archive_mo * 1024 * 1024:
        raise ArchiveInvalide(f"L'archive dépasse {settings.taille_max_archive_mo} Mo.")
    try:
        archive = zipfile.ZipFile(io.BytesIO(contenu))
    except zipfile.BadZipFile as exc:
        raise ArchiveInvalide("Le fichier n'est pas une archive .zip valide.") from exc

    elements = [e for e in archive.infolist() if not e.is_dir()]
    if len(elements) > settings.nombre_max_fichiers:
        raise ArchiveInvalide(f"L'archive contient plus de {settings.nombre_max_fichiers} fichiers.")

    projet = Projet()
    total_lu = 0
    limite_totale = settings.taille_max_decompressee_mo * 1024 * 1024
    limite_fichier = settings.taille_max_fichier_ko * 1024

    for element in elements:
        chemin = _chemin_sur(element.filename)
        if chemin is None or _est_ignore(chemin):
            continue
        projet.nombre_total_fichiers += 1
        if not _est_texte(chemin):
            continue
        # On lit au plus « limite + 1 » octets : la taille annoncée dans l'archive peut mentir
        with archive.open(element) as flux:
            donnees = flux.read(limite_fichier + 1)
        if len(donnees) > limite_fichier:
            continue
        total_lu += len(donnees)
        if total_lu > limite_totale:
            raise ArchiveInvalide("Le contenu décompressé est trop volumineux.")
        projet.fichiers[chemin] = donnees.decode("utf-8", errors="replace")

    if not projet.fichiers:
        raise ArchiveInvalide("Aucun fichier de code n'a été trouvé dans l'archive.")
    projet.fichiers = _retirer_dossier_racine(projet.fichiers)
    return projet
