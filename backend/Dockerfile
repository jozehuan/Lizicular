# ============================================
# Backend Dockerfile - Producción Optimizado
# ============================================
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias en directorio de usuario
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# Imagen Final
# ============================================
FROM python:3.11-slim

RUN useradd -m -u 1000 appuser
WORKDIR /app

# Instalar runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl && rm -rf /var/lib/apt/lists/*

# Copiar dependencias instaladas desde builder
COPY --from=builder /root/.local /home/appuser/.local

# Asegurar que scripts estén en PATH
#ENV PATH=/root/.local/bin:$PATH

# Copiar código de la aplicación
COPY . ./backend/

# Crear usuario no-root
RUN chown -R appuser:appuser /app /home/appuser/.local

#COPY --from=builder /root/.local /home/appuser/.local

# Cambiar el dueño de la carpeta al nuevo usuario
#RUN chown -R appuser:appuser /home/appuser/.local

# Configurar el PATH para el nuevo usuario
ENV PYTHONPATH=/app:/home/appuser/.local/lib/python3.11/site-packages
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Cambiar al usuario no-privilegiado
USER appuser

# Exponer puerto
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicio con múltiples workers para producción
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop", "--http", "httptools"]
