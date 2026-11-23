from typing import Literal

from pydantic import BaseModel

Tranche = Literal["< 100", "100 à 1 000", "1 000 à 50 000", "> 50 000"]
Volume = Literal["< 10 Go", "10 à 100 Go", "100 Go à 1 To", "> 1 To"]


class DemandeEstimation(BaseModel):
    """Les besoins de l'application (mêmes valeurs que le formulaire du plan)."""

    nombre_utilisateurs: Tranche
    volume_donnees: Volume
    type_base_donnees: str = "PostgreSQL"
    haute_disponibilite: bool = False


class Ligne(BaseModel):
    poste: str
    detail: str
    cout_mensuel_eur: float
    # Texte à afficher à la place du prix quand il est nul : « Inclus » ou « En plus »
    prix_texte: str | None = None


class Offre(BaseModel):
    fournisseur: str
    nom: str
    region: str
    gestion: str  # « Services gérés » ou « Serveurs à administrer »
    lignes: list[Ligne]
    total_mensuel_eur: float
    total_annuel_eur: float
    calculateur: str


class Dimensionnement(BaseModel):
    """Les hypothèses de l'estimation : ce qu'on suppose nécessaire."""

    serveurs: int
    taille: str
    description_taille: str
    base_de_donnees: str
    instances_base: int
    stockage_go: int
    trafic_sortant_go: int
    repartiteur_de_charge: bool


class Estimation(BaseModel):
    dimensionnement: Dimensionnement
    offres: list[Offre]  # de la moins chère à la plus chère
    moins_chere: str
    remarques: list[str]
    releve_le: str
    eur_vers_mad: float
