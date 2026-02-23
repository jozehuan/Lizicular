#!/bin/bash

# ============================================
# Script de Deployment a Docker Swarm
# ============================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función de log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-stack.yml" ]; then
    error "docker-stack.yml no encontrado. Ejecuta este script desde el directorio raíz del proyecto."
    exit 1
fi

# Cargar variables de entorno
if [ ! -f ".env" ]; then
    error "Archivo .env no encontrado. Ejecuta primero ./scripts/generate-secrets.sh"
    exit 1
fi

source .env

# Verificar variables críticas
REQUIRED_VARS=("DOMAIN" "POSTGRES_PASSWORD" "REDIS_PASSWORD" "MONGO_INITDB_ROOT_PASSWORD" "SECRET_KEY")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        error "Variable $var no está configurada en .env"
        exit 1
    fi
done

# Versión a desplegar
VERSION=${1:-${VERSION:-latest}}

log "🚀 Iniciando deployment de Lizicular v${VERSION}"
echo ""

# ============================================
# PASO 1: Verificar Swarm
# ============================================
log "📋 Verificando Docker Swarm..."

if ! docker info | grep -q "Swarm: active"; then
    warning "Docker Swarm no está activo. Inicializando..."
    docker swarm init
    log "✅ Swarm inicializado"
else
    log "✅ Swarm ya está activo"
fi

# ============================================
# PASO 2: Etiquetar nodos
# ============================================
log "🏷️  Configurando etiquetas de nodos..."

NODE_ID=$(docker node ls --format "{{.ID}}" | head -n 1)

docker node update --label-add database=true $NODE_ID
docker node update --label-add cache=true $NODE_ID

log "✅ Nodos etiquetados"

# ============================================
# PASO 3: Crear red si no existe
# ============================================
log "🌐 Verificando red overlay..."

if ! docker network ls | grep -q lizicular_network; then
    docker network create --driver overlay --attachable lizicular_network
    log "✅ Red creada"
else
    log "✅ Red ya existe"
fi

# ============================================
# PASO 4: Build de imágenes
# ============================================
log "🔨 Construyendo imágenes..."

# Backend
if [ -d "backend" ]; then
    log "Building backend..."
    docker build -t ${REGISTRY_URL}lizicular-backend:${VERSION} ./backend
    docker tag ${REGISTRY_URL}lizicular-backend:${VERSION} ${REGISTRY_URL}lizicular-backend:latest
    log "✅ Backend construido"
else
    warning "Directorio backend/ no encontrado. Asegúrate de copiar tu código aquí."
fi

# Frontend
if [ -d "frontend" ]; then
    log "Building frontend..."
    docker build -t ${REGISTRY_URL}lizicular-frontend:${VERSION} ./frontend
    docker tag ${REGISTRY_URL}lizicular-frontend:${VERSION} ${REGISTRY_URL}lizicular-frontend:latest
    log "✅ Frontend construido"
else
    warning "Directorio frontend/ no encontrado. Asegúrate de copiar tu código aquí."
fi

# ============================================
# PASO 5: Deploy del stack
# ============================================
log "📦 Desplegando stack a Swarm..."

# 1. Cargar y exportar TODAS las variables del archivo .env
if [ -f .env ]; then
    log "📝 Cargando variables desde .env..."
    set -a             # Exportar automáticamente todas las variables definidas
    source .env        # Leer el archivo .env
    set +a             # Desactivar exportación automática
else
    log "⚠️  Archivo .env no encontrado. El deploy podría fallar."
fi

# 2. Asegurarnos que VERSION esté disponible (por si se pasó por argumento)
export VERSION

docker stack deploy -c docker-stack.yml --with-registry-auth lizicular

log "✅ Stack desplegado"

# ============================================
# PASO 6: Esperar a que los servicios estén listos
# ============================================
log "⏳ Esperando a que los servicios estén listos..."

sleep 10

# Mostrar estado
docker stack ps lizicular --no-trunc

echo ""
log "📊 Estado de los servicios:"
docker service ls --filter "label=com.docker.stack.namespace=lizicular"

echo ""
log "🎉 Deployment completado!"
echo ""
info "Accede a tu aplicación en:"
info "  - Frontend: https://app.${DOMAIN}"
info "  - Backend:  https://api.${DOMAIN}"
info "  - Traefik:  https://traefik.${DOMAIN} (user: admin, pass: admin)"
echo ""
warning "IMPORTANTE: Cambia la contraseña de Traefik en docker-stack.yml"
echo ""
log "Para ver logs:"
info "  docker service logs -f lizicular_backend"
info "  docker service logs -f lizicular_frontend"
echo ""
log "Para escalar servicios:"
info "  docker service scale lizicular_backend=4"
echo ""
