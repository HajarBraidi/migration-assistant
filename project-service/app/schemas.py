from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------- ENTRÉE : description de l'application ----------

EXEMPLE_DESCRIPTION = {
    "nom": "StockPro",
    "domaine": "Gestion de stock",
    "objectifs": ["Réduire les coûts", "Moderniser"],
    "problemes_actuels": ["Lenteur", "Pannes"],
    "langage": "PHP",
    "version_langage": "5.6",
    "framework_backend": "Aucun",
    "interface_utilisateur": "HTML/jQuery",
    "type_base_donnees": "MySQL",
    "volume_donnees": "< 10 Go",
    "type_architecture": "Monolithe",
    "hebergement_actuel": "Serveur local",
    "hebergement_cible": "Pas de préférence",
    "integrations_externes": None,
    "nombre_utilisateurs": "100 à 1 000",
    "evolution_prevue": "Stable",
    "budget": "Faible",
    "delai": "< 3 mois",
    "interruption_acceptable": "Quelques heures",
    "exigences_securite": ["Données personnelles (RGPD / loi 09-08)"],
    "taille_equipe": 2,
    "competences_equipe": "PHP, MySQL, notions de Linux",
    "description_libre": "Application interne utilisée par 200 employés.",
}


class ApplicationDescription(BaseModel):
    """Description de l'application existante (données du formulaire)."""

    model_config = ConfigDict(json_schema_extra={"examples": [EXEMPLE_DESCRIPTION]})

    # Général
    nom: str = Field(min_length=1, max_length=100)
    domaine: Literal["Gestion de stock", "E-commerce", "RH", "Finance", "Autre"]
    objectifs: list[
        Literal["Réduire les coûts", "Performances", "Moderniser", "Sécuriser", "Scalabilité"]
    ] = Field(min_length=1)
    problemes_actuels: list[str] = []

    # Technologies
    langage: str = Field(min_length=1)
    version_langage: str | None = None
    framework_backend: str | None = None
    interface_utilisateur: str = Field(min_length=1)

    # Base de données
    type_base_donnees: str = Field(min_length=1)
    volume_donnees: Literal["< 10 Go", "10 à 100 Go", "100 Go à 1 To", "> 1 To"]

    # Architecture et hébergement
    type_architecture: Literal["Monolithe", "Plusieurs services", "Je ne sais pas"]
    hebergement_actuel: Literal["Serveur local", "Hébergeur", "Cloud"]
    hebergement_cible: Literal["AWS", "Azure", "GCP", "Local", "Pas de préférence"] = (
        "Pas de préférence"
    )
    integrations_externes: str | None = None

    # Utilisation
    nombre_utilisateurs: Literal["< 100", "100 à 1 000", "1 000 à 50 000", "> 50 000"]
    evolution_prevue: Literal["Stable", "Croissance modérée", "Croissance forte"]

    # Contraintes
    budget: Literal["Faible", "Moyen", "Élevé"]
    delai: Literal["< 3 mois", "3 à 6 mois", "6 à 12 mois", "> 12 mois"]
    interruption_acceptable: Literal["Aucune", "Quelques heures", "Quelques jours"]
    exigences_securite: list[str] = []
    taille_equipe: int = Field(ge=1, le=500)
    competences_equipe: str | None = None

    # Détails
    description_libre: str | None = Field(default=None, max_length=3000)


# ---------- SORTIE : le plan de migration (8 sections) ----------

Niveau = Literal["Faible", "Moyen", "Élevé"]


class ResumeExistant(BaseModel):
    resume: str
    points_faibles: list[str]


class StrategieRecommandee(BaseModel):
    strategie: Literal[
        "Retire", "Retain", "Rehost", "Relocate", "Replatform", "Repurchase", "Refactor"
    ]
    justification: str


class ChoixTechnique(BaseModel):
    composant: str
    choix: str
    justification: str


class Phase(BaseModel):
    nom: str
    description: str
    taches: list[str]
    duree_semaines: int = Field(ge=1)


class StrategieBascule(BaseModel):
    type: Literal["Big bang", "Progressive"]
    justification: str
    deroulement: list[str]


class Risque(BaseModel):
    risque: str
    niveau: Niveau
    solution: str


class PlanRollback(BaseModel):
    declencheur: str
    etapes: list[str]


class Estimation(BaseModel):
    duree_totale_semaines: int = Field(ge=1)
    equipe: list[str]
    cout: str


class MigrationPlan(BaseModel):
    """Plan de migration généré par le LLM."""

    resume_existant: ResumeExistant
    strategie: StrategieRecommandee
    architecture_cible: list[ChoixTechnique]
    phases: list[Phase]
    bascule: StrategieBascule
    risques: list[Risque]
    rollback: PlanRollback
    estimation: Estimation