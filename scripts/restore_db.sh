#!/bin/sh

set -e

# =========================
# Cargar variables del .env
# =========================
export $(grep -v '^#' .env | xargs)

# =========================
# Validar argumento
# =========================
if [ -z "$1" ]; then
  echo "Uso: ./scripts/restore_db.sh backups/archivo.sql.gz"
  exit 1
fi

BACKUP_FILE="$1"

# =========================
# Validar que exista el archivo
# =========================
if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ Error: el archivo no existe"
  exit 1
fi

echo "♻️ Restaurando base de datos..."

# =========================
# Restore (soporta gzip)
# =========================
gunzip -c "$BACKUP_FILE" | docker exec -i psm_playon_db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

echo "✅ Restore completado desde: $BACKUP_FILE"xx|