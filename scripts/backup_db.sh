#!/bin/sh

set -e

# =========================
# Cargar variables del .env
# =========================
export $(grep -v '^#' .env | xargs)

# =========================
# Validar que la DB esté corriendo
# =========================
if ! docker ps | grep -q psm_playon_db; then
  echo "❌ Error: el contenedor de la DB no está corriendo"
  exit 1
fi

# =========================
# Crear carpeta backups
# =========================
mkdir -p backups

# =========================
# Generar nombre con timestamp
# =========================
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="backups/psm_playon_backup_$TIMESTAMP.sql.gz"

echo "📦 Creando backup..."

# =========================
# Backup + compresión
# =========================
docker exec -t psm_playon_db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BACKUP_FILE"

echo "✅ Backup creado en: $BACKUP_FILE"

# =========================
# Limpiar backups viejos (7 días)
# =========================
find backups/ -type f -name "*.sql.gz" -mtime +7 -delete

echo "🧹 Backups antiguos eliminados"