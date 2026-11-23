#!/usr/bin/env bash
# Étapes 1 et 2 : convertit et copie la base «moteur_source_nom» vers «moteur_cible_nom» avec «outil».
# Variables : SOURCE_HOTE, SOURCE_UTILISATEUR, SOURCE_MOT_DE_PASSE, SOURCE_BASE,
#             CIBLE_HOTE, CIBLE_UTILISATEUR, CIBLE_MOT_DE_PASSE, CIBLE_BASE
set -euo pipefail
: "${SOURCE_HOTE:?}" "${SOURCE_UTILISATEUR:?}" "${SOURCE_MOT_DE_PASSE:?}" "${SOURCE_BASE:?}"
: "${CIBLE_HOTE:?}" "${CIBLE_UTILISATEUR:?}" "${CIBLE_MOT_DE_PASSE:?}" "${CIBLE_BASE:?}"
cd "$(dirname "$0")"

«commande_conversion»
