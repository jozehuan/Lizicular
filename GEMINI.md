# Contexto del Proyecto: Lizicular

## Objetivo
Esta aplicación es un proyecto para el desarrollo de una aplicación web llamada "Lizicular", donde se encarge de aplicar procesos de automatización sobre licitaciones.

## Stack Tecnológico
- **BackEnd:** Python 3.10+ - FastAPI
- **FrontEnd:** Node.js (Pendiente de inicialización)
- **Base de Datos:** PostgreSQL 15 (Identidad y Auditoría), MongoDB 6 (Licitaciones y Documentos).
- **Caché y Seguridad:** Redis 7 (Lista negra de tokens, invalidación inmediata).
- **Seguridad:** JWT (JSON Web Tokens) y OAuth2
- **Infraestructura:** Docker Compose para orquestación de servicios locales.
- **Estándares:** Tipado moderno (`Tipo | None`) y compatibilidad con Pydantic v2.

## Estructura Actual
- `/backend`
  - `main.py`: Punto de entrada de la API (incluye router para Workspaces).
  - `/auth`: Lógica de autenticación, modelos (RBAC), auditoría y esquemas (incluye esquemas de Workspaces).
    - `redis_client.py`: Configuración del cliente Redis.
  - `/mongodb`: Gestión de licitaciones y documentos.
    - `schemas.py`: Esquemas Pydantic para NoSQL.
    - `tenders_utils.py`: Operaciones CRUD y conexión.
  - `/database`: Configuración de persistencia e inicialización.
    - `/postgres-init`: Scripts SQL para Docker.
  - `/tests`: Pruebas automatizadas (test_auth.py, test_workspaces.py).
- `docker-compose.yml`: Orquestación de servicios locales (PostgreSQL, Redis).

## Estado del Proyecto
El módulo de autenticación y seguridad es completamente funcional y ha sido expandido con capacidades de nivel empresarial:
1. **Seguridad Avanzada:** Optimizado con estándares modernos de Python 3.10+ y Pydantic v2.
2. **Infraestructura de Datos:** PostgreSQL para identidad y auditoría; MongoDB planificado para licitaciones y documentos.
3. **Control de Acceso:** Implementación completa de Workspaces para organizar la colaboración en licitaciones, incluyendo gestión de miembros y roles (OWNER, ADMIN, EDITOR, VIEWER).
4. **Trazabilidad:** Sistema de auditoría universal listo para cumplimiento (compliance) y monitoreo de seguridad, ahora extendido a acciones de Workspaces.
5. **Estrategia de Seguridad de Tokens:** Implementación de Access Tokens efímeros (15m) y Refresh Tokens persistentes en cookies HttpOnly para protección contra XSS.
6. **Invalidación de Tokens (Redis Blacklist):** Uso de Redis para invalidar inmediatamente tokens durante el logout o rotación, garantizando que un token robado no pueda ser reutilizado.
7. **Preparación para el Chatbot:** La estructura de auditoría y workspaces está diseñada para integrarse con los flujos de automatización y el chatbot futuro.


## Reglas de Oro (Instrucciones para Gemini)
1. Siempre responde en español.
2. Usa tipado estricto si usamos TypeScript.
3. No sugieras librerías obsoletas.
4. Usa siempre el estándar de tipado `Tipo | None` en Python (PEP 604).
5. Mantén la documentación de los endpoints actualizada.