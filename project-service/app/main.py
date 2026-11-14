from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_client import AIServiceError, demander_plan
from app.database import Base, engine, get_db
from app.models import Project
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


class ProjectResponse(BaseModel):
    """Un projet complet avec son plan."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    cree_le: datetime
    plan: MigrationPlan
    avertissements: list[str]


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


@app.get("/projects/{project_id}", response_model=ProjectResponse)
def obtenir_projet(
    project_id: int,
    user_id: int = Depends(utilisateur_courant),
    db: Session = Depends(get_db),
) -> Project:
    """Un projet précis, uniquement s'il appartient à l'utilisateur."""
    projet = db.get(Project, project_id)
    if projet is None or projet.user_id != user_id:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    return projet
