# migration-assistant

Assistant de migration d'applications basé sur l'IA générative (PFA – 3e année).

L'utilisateur décrit son application existante (technologies, base de données,
nombre d'utilisateurs, contraintes) et l'assistant génère un plan de migration complet.

## Architecture

| Service | Rôle |
|---|---|
| api-gateway | Point d'entrée unique de l'API |
| project-service | Validation, règles de cohérence, sauvegarde des plans |
| ai-service | Construction du prompt et appel au LLM (Gemini) |
| export-service | Export du plan en PDF |
| auth-service | Inscription, connexion (JWT) |
| frontend | Interface web (React) |

## Lancer le projet

1. Copier `.env.example` en `.env` et ajouter la clé API Gemini.
2. Lancer : `docker compose up --build`

## Équipe

- Hajar Braidi
- Khadija Ait Oufkir # migration-assistant
Assistant de migration d'applications basé sur l'IA générative (PFA)
