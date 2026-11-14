import copy
import os

# Fausse clé : les tests n'appellent jamais Gemini
os.environ.setdefault("GEMINI_API_KEY", "cle-de-test")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.schemas import EXEMPLE_DESCRIPTION  # noqa: E402

PLAN_VALIDE = {
    "resume_existant": {
        "resume": "Monolithe PHP 5.6 hébergé localement.",
        "points_faibles": ["PHP obsolète"],
    },
    "strategie": {"strategie": "Replatform", "justification": "Budget faible et délai court."},
    "architecture_cible": [
        {"composant": "Runtime", "choix": "PHP 8.2", "justification": "Version maintenue."}
    ],
    "phases": [
        {
            "nom": "Préparation",
            "description": "Audit du code.",
            "taches": ["Audit"],
            "duree_semaines": 2,
        }
    ],
    "bascule": {
        "type": "Big bang",
        "justification": "Interruption de quelques heures acceptée.",
        "deroulement": ["Mode maintenance", "Migration", "Vérification"],
    },
    "risques": [
        {"risque": "Perte de données", "niveau": "Moyen", "solution": "Sauvegarde complète."}
    ],
    "rollback": {"declencheur": "Bug bloquant.", "etapes": ["Revenir à l'ancien serveur"]},
    "estimation": {"duree_totale_semaines": 2, "equipe": ["1 développeur"], "cout": "Faible"},
}


@pytest.fixture
def client() -> TestClient:
    """Client qui envoie des requêtes à l'API sans lancer de serveur."""
    return TestClient(app)


@pytest.fixture
def description() -> dict:
    """Une description d'application valide (copie, modifiable par chaque test)."""
    return copy.deepcopy(EXEMPLE_DESCRIPTION)


@pytest.fixture
def plan_valide() -> dict:
    """Un plan de migration valide, utilisé comme fausse réponse du LLM."""
    return copy.deepcopy(PLAN_VALIDE)