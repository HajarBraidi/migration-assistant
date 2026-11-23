from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_client import AIServiceError, demander_plan, discuter
from app.database import Base, engine, get_db
from app.models import Message, Project, Version
from app.rules import verifier_coherence
from app.schemas import ApplicationDescription, MessageChat, MigrationPlan


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Au démarrage : créer les tables si elles n'existent pas
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="project-service",
    description="Projets de migration : règles de cohérence, historique, versions et dialogue.",
    version="0.4.0",
    lifespan=lifespan,
)


# ---------- Formats de réponse ----------


class VersionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    numero: int
    origine: str
    cree_le: datetime


class VersionDetail(VersionSummary):
    plan: MigrationPlan
    avertissements: list[str]


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    contenu: str
    type: str | None
    version_creee: int | None
    cree_le: datetime


class ProjectResponse(BaseModel):
    """Un projet avec la version la plus récente de son plan, ses versions et la conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    cree_le: datetime
    description: ApplicationDescription
    plan: MigrationPlan
    avertissements: list[str]
    versions: list[VersionSummary]
    messages: list[MessageOut]


class ProjectSummary(BaseModel):
    id: int
    nom: str
    strategie: str
    cree_le: datetime


class NouveauMessage(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


# ---------- Outils ----------


def utilisateur_courant(x_user_id: int = Header()) -> int:
    """Identifiant de l'utilisateur connecté, transmis par l'api-gateway (en-tête X-User-Id)."""
    return x_user_id


def projet_de_l_utilisateur(project_id: int, user_id: int, db: Session) -> Project:
    """Renvoie le projet s'il appartient à l'utilisateur, sinon une erreur 404."""
    projet = db.get(Project, project_id)
    if projet is None or projet.user_id != user_id:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    return projet


def ajouter_version(projet: Project, plan: MigrationPlan, origine: str) -> Version:
    """Crée une nouvelle version du plan (les anciennes sont conservées) et la rend courante."""
    description = ApplicationDescription(**projet.description)
    version = Version(
        numero=len(projet.versions) + 1,
        origine=origine[:300],
        plan=plan.model_dump(mode="json"),
        avertissements=verifier_coherence(description, plan),
    )
    projet.versions.append(version)
    projet.plan = version.plan
    projet.avertissements = version.avertissements
    return version


# ---------- Routes ----------


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "project-service"}


@app.post("/projects", response_model=ProjectResponse, status_code=201)
def creer_projet(
    description: ApplicationDescription,
    user_id: int = Depends(utilisateur_courant),
    db: Session = Depends(get_db),
) -> Project:
    """Génère le plan, vérifie sa cohérence et enregistre le projet (version 1)."""
    try:
        plan = demander_plan(description)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    projet = Project(
        user_id=user_id,
        nom=description.nom,
        description=description.model_dump(mode="json"),
        plan={},
        avertissements=[],
    )
    ajouter_version(projet, plan, "Plan initial")
    db.add(projet)
    db.commit()
    db.refresh(projet)
    return projet


@app.get("/projects", response_model=list[ProjectSummary])
def lister_projets(
    user_id: int = Depends(utilisateur_courant), db: Session = Depends(get_db)
) -> list[ProjectSummary]:
    """Historique des projets de l'utilisateur, du plus récent au plus ancien."""
    projets = db.scalars(
        select(Project).where(Project.user_id == user_id).order_by(Project.cree_le.desc())
    ).all()
    return [
        ProjectSummary(
            id=p.id, nom=p.nom, strategie=p.plan["strategie"]["strategie"], cree_le=p.cree_le
        )
        for p in projets
    ]


@app.get("/projects/{project_id}", response_model=ProjectResponse)
def obtenir_projet(
    project_id: int,
    user_id: int = Depends(utilisateur_courant),
    db: Session = Depends(get_db),
) -> Project:
    """Un projet précis, uniquement s'il appartient à l'utilisateur."""
    return projet_de_l_utilisateur(project_id, user_id, db)


@app.post("/projects/{project_id}/messages", response_model=ProjectResponse)
def envoyer_message(
    project_id: int,
    corps: NouveauMessage,
    user_id: int = Depends(utilisateur_courant),
    db: Session = Depends(get_db),
) -> Project:
    """Envoie un message à l'assistant. Une nouvelle version n'est créée que s'il modifie le plan."""
    projet = projet_de_l_utilisateur(project_id, user_id, db)
    historique = [MessageChat(role=m.role, contenu=m.contenu) for m in projet.messages]

    try:
        reponse = discuter(
            ApplicationDescription(**projet.description),
            MigrationPlan(**projet.plan),
            historique,
            corps.message,
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    projet.messages.append(Message(role="utilisateur", contenu=corps.message))
    version_creee = None
    if reponse.type == "modification":
        version_creee = ajouter_version(projet, reponse.plan, f"Demande : {corps.message}").numero
    projet.messages.append(
        Message(
            role="assistant",
            contenu=reponse.message,
            type=reponse.type,
            version_creee=version_creee,
        )
    )
    db.commit()
    db.refresh(projet)
    return projet


@app.get("/projects/{project_id}/versions/{numero}", response_model=VersionDetail)
def obtenir_version(
    project_id: int,
    numero: int,
    user_id: int = Depends(utilisateur_courant),
    db: Session = Depends(get_db),
) -> Version:
    """Consulter une version précise du plan."""
    projet = projet_de_l_utilisateur(project_id, user_id, db)
    for version in projet.versions:
        if version.numero == numero:
            return version
    raise HTTPException(status_code=404, detail="Version introuvable.")


@app.post("/projects/{project_id}/versions/{numero}/restaurer", response_model=ProjectResponse)
def restaurer_version(
    project_id: int,
    numero: int,
    user_id: int = Depends(utilisateur_courant),
    db: Session = Depends(get_db),
) -> Project:
    """Revient à une ancienne version en créant une NOUVELLE version (rien n'est effacé)."""
    projet = projet_de_l_utilisateur(project_id, user_id, db)
    ancienne = next((v for v in projet.versions if v.numero == numero), None)
    if ancienne is None:
        raise HTTPException(status_code=404, detail="Version introuvable.")

    nouvelle = ajouter_version(
        projet, MigrationPlan(**ancienne.plan), f"Restauration de la version {numero}"
    )
    projet.messages.append(
        Message(
            role="assistant",
            contenu=f"La version {numero} a été restaurée : elle devient la version {nouvelle.numero}.",
            type="modification",
            version_creee=nouvelle.numero,
        )
    )
    db.commit()
    db.refresh(projet)
    return projet
