from typing import Literal

from pydantic import BaseModel

Gravite = Literal["Bloquant", "Important", "Conseil"]
Categorie = Literal["Compatibilité", "Sécurité", "Cloud"]


class Dependance(BaseModel):
    nom: str
    version: str | None = None
    ecosysteme: Literal["composer", "maven", "gradle", "npm"]


class Occurrence(BaseModel):
    fichier: str
    ligne: int
    extrait: str


class Probleme(BaseModel):
    """Un problème détecté, avec tous les endroits où il apparaît."""

    regle: str
    titre: str
    gravite: Gravite
    categorie: Categorie
    explication: str
    correction: str
    total: int
    occurrences: list[Occurrence]  # limitées aux premières, voir « total »


class Pile(BaseModel):
    """Les technologies détectées."""

    langage: str | None = None  # PHP, Java ou Node.js
    version_langage: str | None = None
    framework: str | None = None
    interface: str | None = None
    base_de_donnees: str | None = None
    architecture: Literal["Monolithe", "Plusieurs services"] = "Monolithe"
    integrations: list[str] = []


class Statistiques(BaseModel):
    fichiers: int
    fichiers_analyses: int
    lignes_de_code: int
    lignes_par_langage: dict[str, int]


class Resume(BaseModel):
    bloquants: int
    importants: int
    conseils: int


class AnalyseResultat(BaseModel):
    pile: Pile
    statistiques: Statistiques
    dependances: list[Dependance]
    problemes: list[Probleme]
    resume: Resume
    score_preparation: int  # de 0 à 100
    # Valeurs prêtes pour le formulaire « Nouvelle analyse » (mêmes valeurs que le contrat)
    description_preremplie: dict
    # Champs remplis avec certitude (fichiers de configuration) / déduits d'indices (à vérifier)
    champs_detectes: list[str]
    champs_a_verifier: list[str]
