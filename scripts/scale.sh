#!/bin/bash

# ============================================
# Script para escalar servicios
# ============================================

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

SERVICE=${1:-backend}
REPLICAS=${2:-2}

log "⚖️  Escalando lizicular_${SERVICE} a ${REPLICAS} réplicas..."

docker service scale lizicular_${SERVICE}=${REPLICAS}

log "✅ Servicio escalado"

echo ""
info "Estado actual:"
docker service ls --filter "name=lizicular_${SERVICE}"

echo ""
info "Réplicas en ejecución:"
docker service ps lizicular_${SERVICE} --filter "desired-state=running"
