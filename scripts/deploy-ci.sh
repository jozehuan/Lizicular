#!/usr/bin/env bash
set -euo pipefail

# ============================================
# Deploy CI a Docker Swarm (sin build local)
# - Asume que las imágenes ya existen en un registry
# - Usa docker-stack.yml y variables en .env
# ============================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err() { echo -e "${RED}[ERROR]${NC} $*"; }

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [ ! -f "docker-stack.yml" ]; then
  err "docker-stack.yml no encontrado en $PROJECT_ROOT"
  exit 1
fi

if [ ! -f ".env" ]; then
  err ".env no encontrado. Crea / actualiza $PROJECT_ROOT/.env (secrets/vars)."
  exit 1
fi

# Cargar variables de entorno
set -a
# shellcheck disable=SC1091
source .env
set +a

# VERSION puede venir como argumento o desde .env
VERSION="${1:-${VERSION:-latest}}"
export VERSION

# REGISTRY_URL debe existir si tu docker-stack.yml usa ${REGISTRY_URL}
: "${REGISTRY_URL:?REGISTRY_URL no definido (ej: ghcr.io/jozehuan/)}"

# Variables mínimas que tu stack usa
REQUIRED_VARS=(
  POSTGRES_USER POSTGRES_PASSWORD
  REDIS_PASSWORD
  MONGO_INITDB_ROOT_USERNAME MONGO_INITDB_ROOT_PASSWORD
  SECRET_KEY
)

for v in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!v:-}" ]; then
    err "Variable requerida '$v' no está definida en .env"
    exit 1
  fi
done

log "Deploy CI Lizicular VERSION=${VERSION} REGISTRY_URL=${REGISTRY_URL}"

# 1) Swarm activo
if ! docker info 2>/dev/null | grep -q "Swarm: active"; then
  warn "Docker Swarm no está activo. Inicializando (docker swarm init)..."
  docker swarm init
fi

# 2) Etiquetar nodo (best effort)
NODE_ID="$(docker node ls --format '{{.ID}}' | head -n 1 || true)"
if [ -n "$NODE_ID" ]; then
  docker node update --label-add database=true "$NODE_ID" >/dev/null 2>&1 || true
  docker node update --label-add cache=true "$NODE_ID" >/dev/null 2>&1 || true
fi

# 3) Crear red overlay si no existe
if ! docker network ls --format '{{.Name}}' | grep -qx "lizicular_network"; then
  docker network create --driver overlay --attachable lizicular_network
fi

# 4) Deploy del stack
# Nota: Swarm NO usa depends_on como en compose; healthchecks ayudan.
log "Desplegando stack (docker stack deploy)..."
docker stack deploy -c docker-stack.yml --with-registry-auth lizicular

log "Stack desplegado. Estado:"
docker stack ps lizicular --no-trunc || true
docker service ls --filter "label=com.docker.stack.namespace=lizicular" || true

log "OK"