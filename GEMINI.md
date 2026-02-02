# Contexto del Proyecto: Lizicular

## Objetivo
Esta aplicación es un proyecto para el desarrollo de una aplicación web llamada "Lizicular", donde se encarge de aplicar procesos de automatización sobre licitaciones.

## Stack Tecnológico
- **BackEnd:** Python 3.10+ - FastAPI
- **FrontEnd:** Node.js (Pendiente de inicialización)
- **Base de Datos:** PostgreSQL 15 (Contenedorizado con Docker), MongoDB (Planificado)
- **Seguridad:** JWT (JSON Web Tokens) y OAuth2
- **Infraestructura:** Docker Compose para orquestación de servicios locales.

## Estructura Actual
- `/backend`
  - `/authentication`: Sistema centralizado de autenticación.
    - Soporte para Login/Registro local (Email/Password).
    - Integración con OAuth2 (Google, Facebook, GitHub, Microsoft).
    - Gestión de sesiones con JWT.
    - Persistencia con SQLAlchemy (AsyncPG).
- `docker-compose.yml`: Configuración de servicios de infraestructura (PostgreSQL).

## Estado del Proyecto
El módulo de autenticación es completamente funcional y ha sido optimizado con estándares modernos de Python 3.10+. Se ha integrado Docker para facilitar el despliegue de la base de datos PostgreSQL. El sistema está listo para comenzar la integración con la lógica de negocio de licitaciones y el desarrollo del frontend.

## Reglas de Oro (Instrucciones para Gemini)
1. Siempre responde en español.
2. Usa tipado estricto si usamos TypeScript.
3. No sugieras librerías obsoletas.
4. Usa siempre el estándar de tipado `Tipo | None` en Python (PEP 604).
5. Mantén la documentación de los endpoints actualizada.