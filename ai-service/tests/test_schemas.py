import pytest
from pydantic import ValidationError

from app.schemas import Diagramme

SCHEMA_VALIDE = {
    "composants": [
        {"id": "utilisateurs", "libelle": "Employés", "type": "utilisateur"},
        {"id": "app_php", "libelle": "Application PHP 5.6", "type": "backend"},
        {"id": "base_mysql", "libelle": "MySQL", "type": "base_de_donnees"},
    ],
    "liens": [
        {"source": "utilisateurs", "cible": "app_php", "libelle": "HTTP"},
        {"source": "app_php", "cible": "base_mysql"},
    ],
}


def test_schema_valide():
    diagramme = Diagramme(**SCHEMA_VALIDE)

    assert len(diagramme.composants) == 3


def test_lien_vers_un_composant_inconnu_est_refuse():
    donnees = {**SCHEMA_VALIDE, "liens": [{"source": "app_php", "cible": "inconnu"}]}

    with pytest.raises(ValidationError):
        Diagramme(**donnees)


def test_identifiant_avec_espace_est_refuse():
    composants = [*SCHEMA_VALIDE["composants"], {"id": "mon app", "libelle": "X", "type": "backend"}]

    with pytest.raises(ValidationError):
        Diagramme(composants=composants, liens=[])


def test_identifiants_en_double_sont_refuses():
    composants = [*SCHEMA_VALIDE["composants"], {"id": "app_php", "libelle": "Doublon", "type": "backend"}]

    with pytest.raises(ValidationError):
        Diagramme(composants=composants, liens=[])
