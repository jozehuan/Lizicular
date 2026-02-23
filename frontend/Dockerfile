# ============================================
# Frontend Dockerfile - Producción Optimizado
# ============================================

# Dependencias
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat

# Instalar pnpm
RUN npm install -g pnpm

WORKDIR /app

# Copiar archivos de dependencias
COPY package.json pnpm-lock.yaml ./

# Instalar dependencias
RUN pnpm install --frozen-lockfile

# ============================================
# Builder
# ============================================
FROM node:20-alpine AS builder

# Instalar pnpm
RUN npm install -g pnpm

WORKDIR /app

# Copiar dependencias desde deps
COPY --from=deps /app/node_modules ./node_modules

# Copiar código fuente
COPY . .

# Variables de entorno necesarias para el build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Añadir estos ARG/ENV antes del build:
ARG NEXT_PUBLIC_BACKEND_URL
ENV NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL
ARG INTERNAL_BACKEND_URL=http://backend:8000
ENV INTERNAL_BACKEND_URL=$INTERNAL_BACKEND_URL

# Build de Next.js con standalone output
RUN pnpm build

# ============================================
# Runner - Imagen Final
# ============================================
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Crear usuario no-root
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copiar archivos públicos
COPY --from=builder /app/public ./public

# Copiar archivos de internacionalización
COPY --from=builder /app/messages ./messages

# Copiar archivos standalone (optimizado)
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Cambiar a usuario no-root
USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Healthcheck
HEALTHCHECK NONE 

# Comando de inicio
CMD ["node", "server.js"]
