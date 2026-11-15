import copy

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.schemas import EXEMPLE_DESCRIPTION, MigrationPlan, ReponseAssistant, RevisionResult

PLAN_VALIDE = {
    "resume_existant": {"resume": "Monolithe PHP.", "points_faibles": ["PHP obsolète"]},
    "strategie": {"strategie": "Replatform", "justification": "Budget faible."},
    "architecture_cible": [
        {"composant": "Runtime", "choix": "PHP 8.2", "justification": "Maintenu."}
    ],
    "phases": [
        {"nom": "Préparation", "description": "Audit.", "taches": ["Audit"], "duree_semaines": 2}
    ],
    "bascule": {"type": "Big bang", "justification": "Coupure acceptée.", "deroulement": ["Bascule"]},
    "risques": [{"risque": "Perte de données", "niveau": "Moyen", "solution": "Sauvegarde."}],
    "rollback": {"declencheur": "Bug bloquant.", "etapes": ["Retour arrière"]},
    "estimation": {"duree_totale_semaines": 2, "equipe": ["1 développeur"], "cout": "Faible"},
}

# En-têtes envoyés par l'api-gateway pour deux utilisateurs différents
UTILISATEUR_1 = {"X-User-Id": "1"}
UTILISATEUR_2 = {"X-User-Id": "2"}


@pytest.fixture
def client(monkeypatch):
    # Base SQLite en mémoire à la place de PostgreSQL
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    def get_test_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = get_test_db
    # Faux ai-service : renvoie toujours le plan valide
    monkeypatch.setattr(
        "app.main.demander_plan", lambda description: MigrationPlan(**PLAN_VALIDE)
    )
    # Faux assistant : modifie le plan si le message parle de coût (« moins cher »),
    # sinon pose une question (comme pour un message incompréhensible)
    def faux_assistant(description, plan, historique, message):
        if "moins ch" in message:
            nouveau = {**PLAN_VALIDE, "strategie": {"strategie": "Rehost", "justification": message}}
            return ReponseAssistant(type="modification", message="Je passe en Rehost.", plan=nouveau)
        return ReponseAssistant(type="question", message="Pouvez-vous préciser votre demande ?")

    monkeypatch.setattr("app.main.discuter", faux_assistant)
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def description() -> dict:
    return copy.deepcopy(EXEMPLE_DESCRIPTION)


@pytest.fixture
def plan_valide() -> MigrationPlan:
    return MigrationPlan(**PLAN_VALIDE)
