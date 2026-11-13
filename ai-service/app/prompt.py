import json

from app.schemas import ApplicationDescription, MigrationPlan

ROLE = """Tu es un architecte logiciel expert en migration d'applications \
(cloud, bases de données, modernisation, microservices)."""

REGLES = """Règles à respecter :
1. Réponds en français, uniquement avec un objet JSON conforme au schéma fourni.
2. Choisis UNE stratégie parmi les 7R et justifie-la avec les contraintes de l'utilisateur
   (budget, délai, interruption acceptable, taille et compétences de l'équipe).
3. Le plan doit être cohérent avec les contraintes :
   - budget faible ou délai court : évite Refactor ;
   - aucune interruption acceptable : bascule progressive obligatoire.
4. Les phases doivent être ordonnées et concrètes, avec une durée réaliste.
   La durée totale de l'estimation doit correspondre à la somme des phases.
5. Propose au moins 4 risques avec un niveau et une solution.
6. N'invente pas d'informations : si une donnée manque, indique ton hypothèse
   dans le résumé de l'existant."""


def build_plan_prompt(description: ApplicationDescription) -> str:
    """Construit le prompt envoyé au LLM pour générer le plan de migration."""
    schema = json.dumps(MigrationPlan.model_json_schema(), ensure_ascii=False)
    donnees = description.model_dump_json(indent=2)

    return f"""{ROLE}

{REGLES}

Description de l'application existante :
{donnees}

Schéma JSON attendu pour la réponse :
{schema}
"""