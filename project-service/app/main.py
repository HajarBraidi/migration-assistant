from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_client import AIServiceError, demander_plan, demander_revision
from app.database import Base, engine, get_db
from app.models import Project, Revision
from app.rules import verifier_coherence
from app.schemas import ApplicationDescription, MigrationPlan


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Au démarrage : créer les tables si elles n'existent pas
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="project-service",
    description="Gère les projets de migration : validation, règles de cohérence, historique.",
    version="0.3.0",
    lifespan=lifespan,
)


class RevisionSummary(BaseModel):
    """Une modification demandée par l'utilisateur."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    demande: str
    cree_le: datetime


class ProjectResponse(BaseModel):
    """Un projet complet avec la dernière version de son plan."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    cree_le: datetime
    plan: MigrationPlan
    avertissements: list[str]
    revisions: list[RevisionSummary] = []


class DemandeRevision(BaseModel):
    demande: str = Field(min_length=3, max_length=500)


class ProjectSummary(BaseModel):
    """Résumé d'un projet pour l'historique."""

    id: int
    nom: str
    strategie: str
    cree_le: datetime


def utilisateur_courant(x_user_id: int = Header()) -> int:
    """Identifiant de l'utilisateur connecté, transmis par l'api-gateway (en-tête X-User-Id)."""
    return x_user_id


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "project-service"}


@app.post("/projects", response_model=ProjectResponse, status_code=201)
def creer_projet(
    description: ApplicationDescription,
    user_id: int = Depends(utilisateur_courant),
    db: Session = Depends(get_db),
) -> Project:
    """Génère le plan, vérifie sa cohérence et enregistre le projet."""
    try:
        plan = demander_plan(description)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    projet = Project(
        user_id=user_id,
        nom=description.nom,
        description=description.model_dump(mode="json"),
        plan=plan.model_dump(mode="json"),
        avertissements=verifier_coherence(description, plan),
    )
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
            id=p.id,
            nom=p.nom,
            strategie=p.plan["strategie"]["strategie"],
            cree_le=p.cree_le,
        )
        for p in projets
    ]


def projet_de_l_utilisateur(project_id: int, user_id: int, db: Session) -> Project:
    """Renvoie le projet s'il appartient à l'utilisateur, sinon une erreur 404."""
    projet = db.get(Project, project_id)
    if projet is None or projet.user_id != user_id:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    return projet


@app.get("/projects/{project_id}", response_model=ProjectResponse)
def obtenir_projet(
    project_id: int,
    user_id: int = Depends(utilisateur_courant),
    db: Session = Depends(get_db),
) -> Project:
    """Un projet précis, uniquement s'il appartient à l'utilisateur."""
    return projet_de_l_utilisateur(project_id, user_id, db)


@app.post("/projects/{project_id}/revisions", response_model=ProjectResponse)
def reviser_projet(
    project_id: int,
    corps: DemandeRevision,
    user_id: int = Depends(utilisateur_courant),
    db: Session = Depends(get_db),
) -> Project:
    """Modifie le plan selon la demande de l'utilisateur et garde la version précédente."""
    projet = projet_de_l_utilisateur(project_id, user_id, db)
    description = ApplicationDescription(**projet.description)

    try:
        nouveau_plan = demander_revision(
            description, MigrationPlan(**projet.plan), corps.demande
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    projet.revisions.append(Revision(demande=corps.demande, plan_precedent=projet.plan))
    projet.plan = nouveau_plan.model_dump(mode="json")
    projet.avertissements = verifier_coherence(description, nouveau_plan)
    db.commit()
    db.refresh(projet)
    return projet
