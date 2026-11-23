#!/usr/bin/env bash
# Étape 2 : importe l'export dans la nouvelle base «moteur_cible_nom».
# Usage : ./importer.sh FICHIER_EXPORT
# Variables : CIBLE_HOTE, CIBLE_UTILISATEUR, CIBLE_MOT_DE_PASSE, CIBLE_BASE
set -euo pipefail
: "${CIBLE_HOTE:?}" "${CIBLE_UTILISATEUR:?}" "${CIBLE_MOT_DE_PASSE:?}" "${CIBLE_BASE:?}"
FICHIER="${1:?Indiquer le fichier exporté}"

«commande_import»
echo "Import terminé dans $CIBLE_BASE sur $CIBLE_HOTE"
