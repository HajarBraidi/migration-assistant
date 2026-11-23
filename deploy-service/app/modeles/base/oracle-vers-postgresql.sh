#!/usr/bin/env bash
# Convertit la base Oracle en PostgreSQL avec ora2pg (https://ora2pg.darold.net).
# Prérequis : ora2pg et le client Oracle Instant Client installés sur la machine qui lance le script.
# Variables : SOURCE_HOTE, SOURCE_PORT (1521 par défaut), SOURCE_SERVICE, SOURCE_UTILISATEUR,
#             SOURCE_MOT_DE_PASSE, SOURCE_SCHEMA, CIBLE_HOTE, CIBLE_UTILISATEUR, CIBLE_MOT_DE_PASSE, CIBLE_BASE
set -euo pipefail
: "${SOURCE_HOTE:?}" "${SOURCE_SERVICE:?}" "${SOURCE_UTILISATEUR:?}" "${SOURCE_MOT_DE_PASSE:?}" "${SOURCE_SCHEMA:?}"
: "${CIBLE_HOTE:?}" "${CIBLE_UTILISATEUR:?}" "${CIBLE_MOT_DE_PASSE:?}" "${CIBLE_BASE:?}"
cd "$(dirname "$0")"

# Configuration générée au moment du lancement : les mots de passe ne sont jamais écrits dans Git
umask 077
cat > ora2pg.conf <<CONF
ORACLE_DSN   dbi:Oracle:host=${SOURCE_HOTE};service_name=${SOURCE_SERVICE};port=${SOURCE_PORT:-1521}
ORACLE_USER  ${SOURCE_UTILISATEUR}
ORACLE_PWD   ${SOURCE_MOT_DE_PASSE}
SCHEMA       ${SOURCE_SCHEMA}
PG_DSN       dbi:Pg:dbname=${CIBLE_BASE};host=${CIBLE_HOTE};port=5432
PG_USER      ${CIBLE_UTILISATEUR}
PG_PWD       ${CIBLE_MOT_DE_PASSE}
PG_VERSION   16
CONF

echo "1/4 Rapport d'évaluation (difficulté et charge estimées)"
ora2pg -c ora2pg.conf -t SHOW_REPORT --estimate_cost > rapport-ora2pg.txt

echo "2/4 Conversion du schéma (tables, séquences, vues)"
mkdir -p schema
ora2pg -c ora2pg.conf -t TABLE -o schema/tables.sql
ora2pg -c ora2pg.conf -t SEQUENCE -o schema/sequences.sql
ora2pg -c ora2pg.conf -t VIEW -o schema/vues.sql
echo "   Relisez schema/*.sql (et convertissez les procédures PL/SQL avec -t PROCEDURE), puis :"
echo "   psql -h \$CIBLE_HOTE -U \$CIBLE_UTILISATEUR -d \$CIBLE_BASE -f schema/tables.sql"
read -r -p "   Schéma importé dans PostgreSQL ? Appuyez sur Entrée pour copier les données..." _

echo "3/4 Copie des données"
ora2pg -c ora2pg.conf -t COPY

echo "4/4 Comparaison du nombre de lignes Oracle / PostgreSQL"
ora2pg -c ora2pg.conf -t TEST_COUNT | tee verification-ora2pg.txt
rm -f ora2pg.conf
