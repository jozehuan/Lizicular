#!/bin/bash

# ============================================
# Script de Monitoreo del Stack
# ============================================

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

clear

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          LIZICULAR - SWARM MONITORING                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================
# ESTADO DEL SWARM
# ============================================
echo -e "${GREEN}📊 ESTADO DEL SWARM:${NC}"
docker node ls
echo ""

# ============================================
# SERVICIOS
# ============================================
echo -e "${GREEN}🔧 SERVICIOS LIZICULAR:${NC}"
docker service ls --filter "label=com.docker.stack.namespace=lizicular" --format "table {{.Name}}\t{{.Mode}}\t{{.Replicas}}\t{{.Image}}"
echo ""

# ============================================
# TAREAS EN EJECUCIÓN
# ============================================
echo -e "${GREEN}🏃 TAREAS EN EJECUCIÓN:${NC}"
docker stack ps lizicular --filter "desired-state=running" --format "table {{.Name}}\t{{.Node}}\t{{.CurrentState}}\t{{.Error}}"
echo ""

# ============================================
# TAREAS FALLIDAS
# ============================================
FAILED=$(docker stack ps lizicular --filter "desired-state=shutdown" | grep -v "Shutdown" | wc -l)
if [ $FAILED -gt 1 ]; then
    echo -e "${RED}❌ TAREAS FALLIDAS:${NC}"
    docker stack ps lizicular --filter "desired-state=shutdown" --format "table {{.Name}}\t{{.Node}}\t{{.CurrentState}}\t{{.Error}}" | head -n 10
    echo ""
fi

# ============================================
# HEALTH CHECKS
# ============================================
echo -e "${GREEN}💚 HEALTH STATUS:${NC}"
docker ps --filter "label=com.docker.stack.namespace=lizicular" --format "table {{.Names}}\t{{.Status}}"
echo ""

# ============================================
# USO DE RECURSOS
# ============================================
echo -e "${GREEN}📈 USO DE RECURSOS:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
    $(docker ps --filter "label=com.docker.stack.namespace=lizicular" --format "{{.Names}}")
echo ""

# ============================================
# VOLÚMENES
# ============================================
echo -e "${GREEN}💾 VOLÚMENES:${NC}"
docker volume ls --filter "label=com.docker.stack.namespace=lizicular" --format "table {{.Name}}\t{{.Driver}}"
echo ""

# ============================================
# REDES
# ============================================
echo -e "${GREEN}🌐 REDES:${NC}"
docker network ls --filter "label=com.docker.stack.namespace=lizicular" --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}"
echo ""

# ============================================
# ÚLTIMOS LOGS CON ERRORES
# ============================================
echo -e "${YELLOW}⚠️  ÚLTIMOS ERRORES (si hay):${NC}"

for service in backend frontend; do
    ERRORS=$(docker service logs lizicular_${service} --tail 50 2>&1 | grep -i "error\|exception\|fatal" | tail -n 3)
    if [ -n "$ERRORS" ]; then
        echo -e "${RED}Servicio: ${service}${NC}"
        echo "$ERRORS"
        echo ""
    fi
done

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Actualizado: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""
echo "💡 Ejecuta './scripts/logs.sh [servicio]' para ver logs detallados"
echo "💡 Ejecuta './scripts/scale.sh [servicio] [replicas]' para escalar"
