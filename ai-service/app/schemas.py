from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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

    nom: str = Field(min_length=1, max_length=100)
    domaine: Literal["Gestion de stock", "E-commerce", "RH", "Finance", "Autre"]
    objectifs: list[
        Literal["Réduire les coûts", "Performances", "Moderniser", "Sécuriser", "Scalabilité"]
    ] = Field(min_length=1)
    problemes_actuels: list[str] = []
    langage: str = Field(min_length=1)
    version_langage: str | None = None
    framework_backend: str | None = None
    interface_utilisateur: str = Field(min_length=1)
    type_base_donnees: str = Field(min_length=1)
    volume_donnees: Literal["< 10 Go", "10 à 100 Go", "100 Go à 1 To", "> 1 To"]
    type_architecture: Literal["Monolithe", "Plusieurs services", "Je ne sais pas"]
    hebergement_actuel: Literal["Serveur local", "Hébergeur", "Cloud"]
    hebergement_cible: Literal["AWS", "Azure", "GCP", "Local", "Pas de préférence"] = (
        "Pas de préférence"
    )
    integrations_externes: str | None = None
    nombre_utilisateurs: Literal["< 100", "100 à 1 000", "1 000 à 50 000", "> 50 000"]
    evolution_prevue: Literal["Stable", "Croissance modérée", "Croissance forte"]
    budget: Literal["Faible", "Moyen", "Élevé"]
    delai: Literal["< 3 mois", "3 à 6 mois", "6 à 12 mois", "> 12 mois"]
    interruption_acceptable: Literal["Aucune", "Quelques heures", "Quelques jours"]
    exigences_securite: list[str] = []
    taille_equipe: int = Field(ge=1, le=500)
    competences_equipe: str | None = None
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


TypeComposant = Literal[
    "utilisateur", "frontend", "backend", "base_de_donnees", "service_externe", "infrastructure"
]


class Composant(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$", max_length=30)
    libelle: str = Field(min_length=1, max_length=60)
    type: TypeComposant


class Lien(BaseModel):
    source: str
    cible: str
    libelle: str | None = Field(default=None, max_length=40)


class Diagramme(BaseModel):
    """Schéma d'architecture : des composants reliés par des liens."""

    composants: list[Composant] = Field(min_length=2, max_length=12)
    liens: list[Lien]

    @model_validator(mode="after")
    def verifier_liens(self) -> "Diagramme":
        ids = [c.id for c in self.composants]
        if len(ids) != len(set(ids)):
            raise ValueError("Deux composants ont le même identifiant.")
        for lien in self.liens:
            if lien.source not in ids or lien.cible not in ids:
                raise ValueError(f"Lien vers un composant inconnu : {lien.source} -> {lien.cible}")
        return self


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
    # Facultatifs : les plans enregistrés avant l'ajout des schémas restent valides
    schema_avant: Diagramme | None = None
    schema_apres: Diagramme | None = None


class RevisionResult(BaseModel):
    """Réponse du LLM à une demande de modification du plan."""

    demande_valide: bool = Field(
        description="false si la demande est incompréhensible ou sans rapport avec la migration"
    )
    message: str = Field(description="Explication courte destinée à l'utilisateur")
    changements: list[str] = Field(
        default=[], description="Liste courte des modifications apportées au plan"
    )
    plan: MigrationPlan | None = Field(
        default=None, description="Nouvelle version complète du plan si la demande est valide"
    )

    @model_validator(mode="after")
    def verifier_coherence(self) -> "RevisionResult":
        if self.demande_valide and self.plan is None:
            raise ValueError("Une demande valide doit être accompagnée du nouveau plan.")
        if self.demande_valide and not self.changements:
            raise ValueError("Une demande valide doit lister les changements apportés.")
        return self


# ---------- DIALOGUE avec l'assistant ----------


class MessageChat(BaseModel):
    """Un message de la conversation."""

    role: Literal["utilisateur", "assistant"]
    contenu: str


class ReponseAssistant(BaseModel):
    """Réponse de l'assistant à un message de l'utilisateur."""

    type: Literal["question", "reponse", "modification"]
    message: str = Field(min_length=1)
    plan: MigrationPlan | None = None

    @model_validator(mode="after")
    def verifier_plan(self) -> "ReponseAssistant":
        if self.type == "modification" and self.plan is None:
            raise ValueError("Une modification doit contenir le nouveau plan.")
        if self.type != "modification":
            self.plan = None  # seule une modification produit une nouvelle version
        return self
