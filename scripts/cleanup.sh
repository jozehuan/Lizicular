#!/bin/bash

# ============================================
# Script de Limpieza del Sistema
# ============================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo ""
warning "Este script eliminará:"
echo "  - Stack completo de Lizicular"
echo "  - Volúmenes de datos"
echo "  - Redes"
echo "  - Imágenes no usadas"
echo ""
read -p "¿Estás seguro? (escribe 'SI' para confirmar): " confirm

if [ "$confirm" != "SI" ]; then
    error "Cancelado"
    exit 1
fi

log "🧹 Iniciando limpieza..."

# ============================================
# ELIMINAR STACK
# ============================================
log "Eliminando stack lizicular..."
docker stack rm lizicular || warning "Stack no encontrado"

log "Esperando a que los contenedores terminen..."
sleep 15

# ============================================
# ELIMINAR VOLÚMENES (CUIDADO: DATOS PERMANENTES)
# ============================================
read -p "¿Eliminar también los volúmenes de datos? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "Eliminando volúmenes..."
    docker volume ls --filter "label=com.docker.stack.namespace=lizicular" -q | xargs -r docker volume rm || true
    log "✅ Volúmenes eliminados"
else
    log "⏭️  Volúmenes conservados"
fi

# ============================================
# ELIMINAR REDES
# ============================================
log "Eliminando redes..."
docker network rm lizicular_network 2>/dev/null || true

# ============================================
# LIMPIAR IMÁGENES NO USADAS
# ============================================
log "Limpiando imágenes no usadas..."
docker image prune -af --filter "label=com.docker.stack.namespace=lizicular"

# ============================================
# LIMPIEZA GENERAL DE DOCKER
# ============================================
log "Limpieza general de Docker..."
docker system prune -f

log "🎉 Limpieza completada!"

echo ""
log "Sistema limpiado. Para volver a desplegar:"
echo "  ./scripts/deploy.sh"
