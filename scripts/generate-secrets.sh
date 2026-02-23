#!/bin/bash

# ============================================
# Script para generar secretos seguros
# ============================================

set -e

echo "🔐 Generando secretos seguros para Lizicular..."
echo ""

# Función para generar password aleatorio
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Función para generar secret key
generate_secret_key() {
    openssl rand -hex 32
}

# Crear archivo .env si no existe
if [ -f .env ]; then
    echo "⚠️  El archivo .env ya existe."
    read -p "¿Quieres sobrescribirlo? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cancelado."
        exit 1
    fi
    mv .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backup creado de .env anterior"
fi

# Copiar ejemplo
cp .env.example .env

# Generar passwords
POSTGRES_PASSWORD=$(generate_password)
REDIS_PASSWORD=$(generate_password)
MONGO_PASSWORD=$(generate_password)
SECRET_KEY=$(generate_secret_key)

# Reemplazar en .env
sed -i.bak "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${POSTGRES_PASSWORD}/" .env
sed -i.bak "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=${REDIS_PASSWORD}/" .env
sed -i.bak "s/MONGO_INITDB_ROOT_PASSWORD=.*/MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASSWORD}/" .env
sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=${SECRET_KEY}/" .env

# Limpiar archivo backup de sed
rm -f .env.bak

echo "✅ Secretos generados exitosamente!"
echo ""
echo "📝 Configuración generada en .env"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   1. Edita .env y configura tu DOMAIN"
echo "   2. Configura ACME_EMAIL con tu email real"
echo "   3. (Opcional) Añade credenciales de OAuth"
echo "   4. NUNCA subas .env a Git"
echo ""
echo "🔒 Passwords generados:"
echo "   PostgreSQL: ${POSTGRES_PASSWORD:0:10}..."
echo "   Redis:      ${REDIS_PASSWORD:0:10}..."
echo "   MongoDB:    ${MONGO_PASSWORD:0:10}..."
echo "   Secret Key: ${SECRET_KEY:0:20}..."
echo ""
echo "💾 Guarda estos valores en un lugar seguro (password manager)"
