#!/usr/bin/env bash
# Étape 3 : compare le nombre de lignes de chaque table entre l'ancienne et la nouvelle base.
# À lancer après chaque répétition, puis le jour de la bascule. Code de sortie 1 si une table diffère.
set -euo pipefail
: "${SOURCE_HOTE:?}" "${SOURCE_UTILISATEUR:?}" "${SOURCE_MOT_DE_PASSE:?}" "${SOURCE_BASE:?}"
: "${CIBLE_HOTE:?}" "${CIBLE_UTILISATEUR:?}" "${CIBLE_MOT_DE_PASSE:?}" "${CIBLE_BASE:?}"

tables_mysql() { # hote utilisateur mot_de_passe base
  MYSQL_PWD="$3" mysql --host="$1" --user="$2" -N -B -e \
    "SELECT table_name FROM information_schema.tables WHERE table_schema='$4' AND table_type='BASE TABLE'"
}
compter_mysql() { # hote utilisateur mot_de_passe base table
  MYSQL_PWD="$3" mysql --host="$1" --user="$2" -N -B -e "SELECT COUNT(*) FROM \`$5\`" "$4"
}
tables_postgresql() {
  PGPASSWORD="$3" psql --host="$1" --username="$2" --dbname="$4" -At -c \
    "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
}
compter_postgresql() {
  PGPASSWORD="$3" psql --host="$1" --username="$2" --dbname="$4" -At -c "SELECT COUNT(*) FROM \"$5\""
}

SOURCE=«moteur_source»
CIBLE=«moteur_cible»
ecarts=0
printf '%-40s %12s %12s\n' "TABLE" "ANCIENNE" "NOUVELLE"
while read -r table; do
  [ -z "$table" ] && continue
  avant=$("compter_$SOURCE" "$SOURCE_HOTE" "$SOURCE_UTILISATEUR" "$SOURCE_MOT_DE_PASSE" "$SOURCE_BASE" "$table")
  # Les outils de conversion mettent les noms de tables en minuscules
  apres=$("compter_$CIBLE" "$CIBLE_HOTE" "$CIBLE_UTILISATEUR" "$CIBLE_MOT_DE_PASSE" "$CIBLE_BASE" "«nom_table_cible»" 2>/dev/null || echo "absente")
  etat=""
  if [ "$avant" != "$apres" ]; then
    etat="  <-- ÉCART"
    ecarts=$((ecarts + 1))
  fi
  printf '%-40s %12s %12s%s\n' "$table" "$avant" "$apres" "$etat"
done < <("tables_$SOURCE" "$SOURCE_HOTE" "$SOURCE_UTILISATEUR" "$SOURCE_MOT_DE_PASSE" "$SOURCE_BASE")

if [ "$ecarts" -gt 0 ]; then
  echo "$ecarts table(s) différente(s) : NE PAS basculer." >&2
  exit 1
fi
echo "Toutes les tables ont le même nombre de lignes."
