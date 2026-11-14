from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import User
from app.security import creer_jeton, hacher_mot_de_passe, lire_jeton, verifier_mot_de_passe


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="auth-service",
    description="Inscription, connexion et jetons JWT.",
    version="0.1.0",
    lifespan=lifespan,
)


class Inscription(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    email: EmailStr
    mot_de_passe: str = Field(min_length=8, max_length=72)


class Connexion(BaseModel):
    email: EmailStr
    mot_de_passe: str


class Utilisateur(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    email: EmailStr


class Jeton(BaseModel):
    access_token: str
    token_type: str = "bearer"
    utilisateur: Utilisateur


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "auth-service"}


@app.post("/register", response_model=Jeton, status_code=201)
def inscrire(donnees: Inscription, db: Session = Depends(get_db)) -> Jeton:
    """Crée un compte puis connecte directement l'utilisateur."""
    email = donnees.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Un compte existe déjà avec cet email.")

    utilisateur = User(
        nom=donnees.nom, email=email, mot_de_passe_hash=hacher_mot_de_passe(donnees.mot_de_passe)
    )
    db.add(utilisateur)
    db.commit()
    db.refresh(utilisateur)
    return Jeton(
        access_token=creer_jeton(utilisateur.id, utilisateur.nom),
        utilisateur=Utilisateur.model_validate(utilisateur),
    )


@app.post("/login", response_model=Jeton)
def connecter(donnees: Connexion, db: Session = Depends(get_db)) -> Jeton:
    """Vérifie l'email et le mot de passe, puis renvoie un jeton."""
    utilisateur = db.scalar(select(User).where(User.email == donnees.email.lower()))
    # Même message dans les deux cas : on ne révèle pas si l'email existe
    if utilisateur is None or not verifier_mot_de_passe(
        donnees.mot_de_passe, utilisateur.mot_de_passe_hash
    ):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    return Jeton(
        access_token=creer_jeton(utilisateur.id, utilisateur.nom),
        utilisateur=Utilisateur.model_validate(utilisateur),
    )


@app.get("/me", response_model=Utilisateur)
def moi(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> User:
    """Renvoie l'utilisateur correspondant au jeton."""
    jeton = authorization.removeprefix("Bearer ").strip()
    user_id = lire_jeton(jeton) if jeton else None
    utilisateur = db.get(User, user_id) if user_id else None
    if utilisateur is None:
        raise HTTPException(status_code=401, detail="Session invalide ou expirée.")
    return utilisateur
