"""Chaque combinaison produit des fichiers syntaxiquement valides."""

import io
import itertools
import re
import shutil
import subprocess

import hcl2
import pytest
import yaml

from app.kit import generer
from app.schemas import DemandeKit

COMBINAISONS = list(itertools.product(
    [("PHP", "Laravel 5.4"), ("PHP", None), ("Java", "Spring Boot 2.3"), ("Java", "Servlets / JSP"),
     ("JavaScript", "Express 4.16")],
    ["AWS", "Azure", "GCP", "OVHcloud"],
    ["PostgreSQL", "MySQL"],
    ["MySQL", "PostgreSQL", "Oracle", "SQL Server"],
    [("< 100", False), ("> 50 000", True)],
))


def kit(combinaison):
    (langage, framework), fournisseur, cible, source, (utilisateurs, ha) = combinaison
    return generer(DemandeKit(
        nom="Projet Test", langage=langage, framework_backend=framework, type_base_donnees=source,
        base_cible=cible, fournisseur=fournisseur, nombre_utilisateurs=utilisateurs,
        volume_donnees="10 à 100 Go", haute_disponibilite=ha,
    ))


@pytest.mark.parametrize("combinaison", COMBINAISONS)
def test_fichiers_valides(combinaison):
    for f in kit(combinaison).fichiers:
        assert not re.search(r"«\w+»", f.contenu), f"{f.chemin} : valeur non remplie"
        if f.chemin.endswith(".tf"):
            hcl2.load(io.StringIO(f.contenu))
        elif f.chemin.endswith((".yml", ".yaml")):
            yaml.safe_load(f.contenu)


@pytest.mark.skipif(shutil.which("shellcheck") is None, reason="ShellCheck non installé")
def test_scripts_valides_avec_shellcheck(tmp_path):
    scripts = {}
    for combinaison in COMBINAISONS:
        for f in kit(combinaison).fichiers:
            if f.chemin.endswith(".sh"):
                scripts[f.contenu] = f.chemin
    for numero, (contenu, chemin) in enumerate(scripts.items()):
        script = tmp_path / f"script{numero}.sh"
        script.write_text(contenu)
        resultat = subprocess.run(["shellcheck", "-S", "warning", str(script)], capture_output=True, text=True)
        assert resultat.returncode == 0, f"{chemin}\n{resultat.stdout}"
