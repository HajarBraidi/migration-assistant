#!/usr/bin/env bash
# Prépare un serveur Ubuntu 24.04 pour «nom_projet» : Docker, utilisateur de déploiement, pare-feu.
# Exécuté automatiquement au premier démarrage (cloud-init), ou à la main sur un VPS.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y
apt-get install -y docker.io docker-compose-v2 ufw fail2ban unattended-upgrades

# Mises à jour de sécurité automatiques
dpkg-reconfigure -f noninteractive unattended-upgrades

# Docker au démarrage
systemctl enable --now docker

# Dossier de l'application (le fichier .env y sera déposé, jamais dans Git)
mkdir -p /opt/app
chmod 750 /opt/app

# L'utilisateur de connexion peut lancer Docker
UTILISATEUR="«utilisateur_ssh»"
if id "$UTILISATEUR" >/dev/null 2>&1; then
  usermod -aG docker "$UTILISATEUR"
  chown "$UTILISATEUR":"$UTILISATEUR" /opt/app
fi

# Pare-feu : SSH, HTTP et HTTPS uniquement
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
