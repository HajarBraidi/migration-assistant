#!/usr/bin/env bash
# Étape 1 : exporte la base actuelle «moteur_source_nom», sans arrêter l'application.
# Variables : SOURCE_HOTE, SOURCE_UTILISATEUR, SOURCE_MOT_DE_PASSE, SOURCE_BASE
set -euo pipefail
: "${SOURCE_HOTE:?}" "${SOURCE_UTILISATEUR:?}" "${SOURCE_MOT_DE_PASSE:?}" "${SOURCE_BASE:?}"

FICHIER="export-$(date +%Y%m%d-%H%M).«extension_export»"
«commande_export»
echo "Export terminé : $FICHIER ($(du -h "$FICHIER" | cut -f1))"
