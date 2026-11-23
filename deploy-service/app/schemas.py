from typing import Literal

from pydantic import BaseModel, Field

Fournisseur = Literal["AWS", "Azure", "GCP", "OVHcloud"]
Categorie = Literal["Guide", "Application", "Infrastructure", "Déploiement", "Base de données"]


class DemandeKit(BaseModel):
    """Ce qu'il faut savoir du projet (valeurs du formulaire du plan)."""

    nom: str = Field(min_length=1, max_length=100)
    langage: Literal["PHP", "Java", "JavaScript"]
    framework_backend: str | None = None
    type_base_donnees: str  # base actuelle
    base_cible: Literal["PostgreSQL", "MySQL"]
    fournisseur: Fournisseur
    nombre_utilisateurs: Literal["< 100", "100 à 1 000", "1 000 à 50 000", "> 50 000"]
    volume_donnees: Literal["< 10 Go", "10 à 100 Go", "100 Go à 1 To", "> 1 To"]
    haute_disponibilite: bool = False


class Fichier(BaseModel):
    chemin: str
    categorie: Categorie
    description: str
    contenu: str


class Kit(BaseModel):
    projet: str  # nom court utilisé pour les ressources cloud
    fichiers: list[Fichier]
    avertissements: list[str]
