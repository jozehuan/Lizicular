#!/bin/bash

# ============================================
# Script de Rollback
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

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

SERVICE=${1:-all}

log "🔄 Iniciando rollback..."

if [ "$SERVICE" == "all" ]; then
    warning "Haciendo rollback de TODOS los servicios"
    
    SERVICES=$(docker service ls --filter "label=com.docker.stack.namespace=lizicular" --format "{{.Name}}" | grep -E "(backend|frontend)")
    
    for svc in $SERVICES; do
        log "Rolling back $svc..."
        docker service rollback $svc
    done
else
    log "Rolling back lizicular_${SERVICE}..."
    docker service rollback lizicular_${SERVICE}
fi

log "✅ Rollback completado"

echo ""
log "📊 Estado actual de los servicios:"
docker service ls --filter "label=com.docker.stack.namespace=lizicular"
