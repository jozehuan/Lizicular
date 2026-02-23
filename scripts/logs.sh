#!/bin/bash

# ============================================
# Script para ver logs de servicios
# ============================================

SERVICE=${1:-backend}
LINES=${2:-100}

echo "📋 Mostrando logs de lizicular_${SERVICE} (últimas ${LINES} líneas)..."
echo "Presiona Ctrl+C para salir"
echo ""

docker service logs \
    --follow \
    --tail ${LINES} \
    --timestamps \
    lizicular_${SERVICE}
