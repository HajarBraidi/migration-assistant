#!/usr/bin/env bash
# Installe la base «moteur_nom» de «nom_projet» sur un VPS OVHcloud dédié.
# À lancer en root, APRÈS ../commun/installer-serveur.sh, avec les adresses des serveurs d'application :
#   export MOT_DE_PASSE_BASE='...'
#   sudo -E ./installer-base.sh 51.38.12.34 51.38.12.35
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage : $0 IP_SERVEUR_APP [IP_SERVEUR_APP ...]" >&2
  exit 1
fi
: "${MOT_DE_PASSE_BASE:?Définir MOT_DE_PASSE_BASE avant de lancer le script}"

PORT=«port_base»
mkdir -p /opt/base/donnees /opt/base/sauvegardes
chmod 700 /opt/base

# Le mot de passe reste dans un fichier lisible par root uniquement
umask 077
cat > /opt/base/.env <<CONFIG
«variables_conteneur»
CONFIG

cat > /opt/base/docker-compose.yml <<'COMPOSE'
services:
  base:
    image: «image_base»
    env_file: .env
    ports:
      - "«port_base»:«port_base»"
    volumes:
      - ./donnees:«dossier_donnees»
    restart: unless-stopped
COMPOSE

cd /opt/base
docker compose up -d

# Docker ignore les règles d'ufw : on filtre directement dans la chaîne DOCKER-USER.
# Seuls les serveurs d'application peuvent joindre la base.
apt-get install -y iptables-persistent
iptables -I DOCKER-USER -p tcp -m conntrack --ctorigdstport "$PORT" --ctdir ORIGINAL -j DROP
for ip in "$@"; do
  iptables -I DOCKER-USER -p tcp -s "$ip" -m conntrack --ctorigdstport "$PORT" --ctdir ORIGINAL -j ACCEPT
done
netfilter-persistent save

# Sauvegarde quotidienne à 2 h, conservée 7 jours (en plus de la sauvegarde du VPS)
cat > /etc/cron.d/sauvegarde-base <<'CRON'
0 2 * * * root cd /opt/base && «commande_sauvegarde» | gzip > /opt/base/sauvegardes/base-$(date +\%Y\%m\%d).sql.gz && find /opt/base/sauvegardes -name '*.sql.gz' -mtime +7 -delete
CRON

echo "Base installée. Port $PORT ouvert uniquement pour : $*"
