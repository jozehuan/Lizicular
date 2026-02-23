#!/bin/bash

# ============================================
# Script de Backup de Bases de Datos
# ============================================

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Cargar variables de entorno
if [ ! -f ".env" ]; then
    echo "Error: .env no encontrado"
    exit 1
fi

source .env

# Crear directorio de backups
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p ${BACKUP_DIR}

log "💾 Iniciando backup de bases de datos..."
log "Destino: ${BACKUP_DIR}"

# ============================================
# BACKUP POSTGRESQL
# ============================================
log "📦 Backup de PostgreSQL..."

POSTGRES_CONTAINER=$(docker ps --filter "name=lizicular_db" --format "{{.Names}}" | head -n 1)

if [ -n "$POSTGRES_CONTAINER" ]; then
    docker exec ${POSTGRES_CONTAINER} pg_dump \
        -U ${POSTGRES_USER} \
        -d ${POSTGRES_DB} \
        > ${BACKUP_DIR}/postgres_backup.sql
    
    gzip ${BACKUP_DIR}/postgres_backup.sql
    log "✅ PostgreSQL backup completado: postgres_backup.sql.gz"
else
    warning "Contenedor de PostgreSQL no encontrado"
fi

# ============================================
# BACKUP MONGODB
# ============================================
log "📦 Backup de MongoDB..."

MONGO_CONTAINER=$(docker ps --filter "name=lizicular_mongodb" --format "{{.Names}}" | head -n 1)

if [ -n "$MONGO_CONTAINER" ]; then
    docker exec ${MONGO_CONTAINER} mongodump \
        --username=${MONGO_INITDB_ROOT_USERNAME} \
        --password=${MONGO_INITDB_ROOT_PASSWORD} \
        --authenticationDatabase=admin \
        --archive > ${BACKUP_DIR}/mongodb_backup.archive
    
    gzip ${BACKUP_DIR}/mongodb_backup.archive
    log "✅ MongoDB backup completado: mongodb_backup.archive.gz"
else
    warning "Contenedor de MongoDB no encontrado"
fi

# ============================================
# BACKUP REDIS (opcional - principalmente cache)
# ============================================
log "📦 Backup de Redis..."

REDIS_CONTAINER=$(docker ps --filter "name=lizicular_redis" --format "{{.Names}}" | head -n 1)

if [ -n "$REDIS_CONTAINER" ]; then
    docker exec ${REDIS_CONTAINER} redis-cli \
        -a ${REDIS_PASSWORD} \
        --rdb ${BACKUP_DIR}/redis_backup.rdb \
        SAVE
    
    docker cp ${REDIS_CONTAINER}:${BACKUP_DIR}/redis_backup.rdb ${BACKUP_DIR}/
    gzip ${BACKUP_DIR}/redis_backup.rdb
    log "✅ Redis backup completado: redis_backup.rdb.gz"
else
    warning "Contenedor de Redis no encontrado"
fi

# ============================================
# RESUMEN
# ============================================
log "🎉 Backup completado exitosamente!"
echo ""
log "📁 Archivos de backup:"
ls -lh ${BACKUP_DIR}

echo ""
log "💡 Para restaurar:"
echo "   PostgreSQL: gunzip -c postgres_backup.sql.gz | docker exec -i <container> psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}"
echo "   MongoDB:    gunzip -c mongodb_backup.archive.gz | docker exec -i <container> mongorestore --archive"

# ============================================
# LIMPIAR BACKUPS ANTIGUOS (mantener últimos 7 días)
# ============================================
log "🧹 Limpiando backups antiguos (>7 días)..."
find ./backups -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
log "✅ Limpieza completada"
