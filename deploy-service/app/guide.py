"""Le guide de déploiement (GUIDE-DEPLOIEMENT.md), adapté au fournisseur et à la base."""

from app.schemas import DemandeKit, Fichier

NOMS = {"AWS": "Amazon Web Services", "Azure": "Microsoft Azure", "GCP": "Google Cloud", "OVHcloud": "OVHcloud"}
CONNEXION_CLI = {
    "AWS": "aws configure",
    "Azure": "az login",
    "GCP": "gcloud auth application-default login",
}


def _tableau(fichiers: list[Fichier]) -> str:
    lignes = ["| Fichier | Rôle |", "|---|---|"]
    lignes += [f"| `{f.chemin}` | {f.description} |" for f in fichiers]
    return "\n".join(lignes)


def _etape_infrastructure(d: DemandeKit) -> str:
    if d.fournisseur == "OVHcloud":
        return """## 2. Créer les serveurs (OVHcloud)

1. Commandez les VPS indiqués dans le plan (serveurs d'application + un VPS pour la base), sous Ubuntu 24.04.
2. Ajoutez votre clé SSH publique lors de la commande.
3. Sur **chaque** VPS, copiez `infra/commun/installer-serveur.sh` puis lancez :
   ```bash
   sudo bash installer-serveur.sh
   ```
4. Sur le VPS de la base uniquement, en donnant les adresses IP des serveurs d'application :
   ```bash
   export MOT_DE_PASSE_BASE='un-mot-de-passe-long-et-aleatoire'
   sudo -E bash installer-base.sh IP_SERVEUR_1 IP_SERVEUR_2
   ```
   La base n'est alors joignable que depuis vos serveurs, avec une sauvegarde chaque nuit.
"""
    dossier = d.fournisseur.lower()
    return f"""## 2. Créer l'infrastructure ({NOMS[d.fournisseur]}) avec Terraform

Terraform crée tout automatiquement : serveurs, pare-feu, base de données gérée et sauvegardes.

1. Installez [Terraform](https://developer.hashicorp.com/terraform/install) et l'outil en ligne de commande du fournisseur, puis connectez-vous : `{CONNEXION_CLI[d.fournisseur]}`.
2. Créez une clé SSH de déploiement : `ssh-keygen -t ed25519 -f ~/.ssh/deploiement`.
3. Préparez les variables :
   ```bash
   cd infra/{dossier}
   cp terraform.tfvars.example terraform.tfvars   # puis complétez-le
   export TF_VAR_mot_de_passe_base='un-mot-de-passe-long-et-aleatoire'
   ```
4. Vérifiez ce qui sera créé, **relisez le plan**, puis lancez la création :
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```
5. Notez les sorties affichées : `adresses_serveurs` et `adresse_base`.

La base de données n'est **pas** accessible depuis Internet : seuls les serveurs d'application peuvent s'y connecter. Elle est protégée contre la suppression accidentelle.
"""


def _etape_base(d: DemandeKit, fichiers: list[Fichier]) -> str:
    chemins = {f.chemin for f in fichiers}
    variables = """```bash
export SOURCE_HOTE=... SOURCE_UTILISATEUR=... SOURCE_MOT_DE_PASSE=... SOURCE_BASE=...
export CIBLE_HOTE=... CIBLE_UTILISATEUR=... CIBLE_MOT_DE_PASSE=... CIBLE_BASE=...
```"""
    if "migration-base/exporter.sh" in chemins:
        commandes = """```bash
./migration-base/exporter.sh
./migration-base/importer.sh export-AAAAMMJJ-HHMM.*
./migration-base/verifier.sh
```"""
    elif "migration-base/convertir.sh" in chemins:
        commandes = """```bash
./migration-base/convertir.sh      # nécessite pgloader
./migration-base/verifier.sh       # si le script est présent
```"""
    elif "migration-base/oracle-vers-postgresql.sh" in chemins:
        commandes = """```bash
./migration-base/oracle-vers-postgresql.sh   # nécessite ora2pg et Oracle Instant Client
```"""
    else:
        return """## 5. Migrer les données

Aucun script automatique n'est fourni pour cette combinaison de bases : voir les points d'attention en tête de ce guide.
"""
    return f"""## 5. Répéter la migration des données (au moins une fois)

Faites une **répétition complète** sur une copie, avant le jour J. Elle mesure la durée réelle de la coupure et révèle les erreurs sans risque.

{variables}

{commandes}

Le script de vérification compare le nombre de lignes de chaque table. **Ne basculez jamais si une table est en écart.**
"""


def guide(d: DemandeKit, projet: str, fichiers: list[Fichier], avertissements: list[str]) -> str:
    attention = ""
    if avertissements:
        attention = "## Points d'attention\n\n" + "\n".join(f"- {a}" for a in avertissements) + "\n\n"
    ha = "avec haute disponibilité" if d.haute_disponibilite else "sans haute disponibilité"
    return f"""# Guide de déploiement — {d.nom}

Kit généré par **MigraPlan** pour **{NOMS[d.fournisseur]}**, base cible **{d.base_cible}**, {ha}.
Nom court des ressources cloud : `{projet}`.

> Ce kit automatise la partie technique. Les décisions critiques (date de bascule, validation des
> données, retour arrière) restent celles de votre équipe.

{attention}## Contenu du kit

{_tableau(fichiers)}

## 1. Préparer le code et tester sur votre poste

1. Corrigez les problèmes **« Bloquant »** signalés par le scanner de code de MigraPlan.
2. Ajoutez au fichier `.gitignore` de votre projet : `.env`
3. Testez l'application conteneurisée avec la nouvelle base :
   ```bash
   cp .env.example .env
   docker compose up --build
   ```
   L'application répond sur http://localhost:8000.

{_etape_infrastructure(d)}
## 3. Configurer les serveurs

Sur chaque serveur, créez `/opt/app/.env` à partir de `.env.example`, avec `DB_HOST` = l'adresse de la base et le vrai mot de passe. Ce fichier reste sur le serveur : il n'est jamais envoyé dans Git.

## 4. Configurer le déploiement automatique (GitHub Actions)

Dans le dépôt GitHub : **Settings → Secrets and variables → Actions**, créez :

| Secret | Valeur |
|---|---|
| `SSH_PRIVATE_KEY` | le contenu de `~/.ssh/deploiement` (clé **privée**) |
| `SERVEURS` | les adresses des serveurs, séparées par des espaces |

À chaque push sur `main`, le pipeline construit l'image et met à jour les serveurs un par un.
Créez aussi l'environnement **production** (Settings → Environments) pour pouvoir exiger une validation avant chaque déploiement.

{_etape_base(d, fichiers)}
## 6. Jour J : la bascule

1. Prévenez les utilisateurs de la fenêtre de coupure.
2. Mettez l'ancienne application en **mode maintenance** (plus aucune écriture).
3. Lancez la migration finale des données, puis le script de vérification.
4. Testez la nouvelle application : connexion, consultation, création d'un enregistrement.
5. Modifiez le DNS pour pointer vers la nouvelle adresse (répartiteur ou serveur).
6. Surveillez les journaux pendant les premières heures : `docker compose -f docker-compose.prod.yml logs -f`

### Liste de contrôle avant de basculer

- [ ] Répétition de la migration réussie, durée mesurée
- [ ] Vérification des données sans aucun écart
- [ ] Sauvegarde complète de l'ancienne base conservée
- [ ] Tests fonctionnels validés sur la nouvelle plateforme
- [ ] Personne et procédure de retour arrière désignées

## 7. Retour arrière (rollback)

L'ancien système n'est **ni modifié ni supprimé** pendant la bascule. En cas de problème bloquant :

1. Remettez l'ancien DNS.
2. Retirez le mode maintenance de l'ancienne application.
3. Analysez les journaux de la nouvelle plateforme avant une nouvelle tentative.

Ne supprimez l'ancien serveur qu'après plusieurs semaines de fonctionnement stable.

## Sécurité

- Les mots de passe ne sont jamais écrits dans un fichier versionné (`.env`, `terraform.tfvars` et l'état Terraform sont exclus de Git).
- SSH n'est ouvert qu'à l'adresse des administrateurs ; la base n'accepte que les serveurs d'application.
- Les disques et les sauvegardes sont chiffrés ; les mises à jour de sécurité du système sont automatiques.
"""
