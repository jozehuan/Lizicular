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
  - `main.py`: Punto de entrada de la API (orquesta los routers).
  - `/auth`: Lógica de autenticación.
    - `models.py`: Modelos SQLAlchemy para usuarios y auditoría.
    - `schemas.py`: Esquemas Pydantic para autenticación.
    - `auth_utils.py`: Utilidades de autenticación.
    - `routes.py`: Endpoints de autenticación y OAuth2.
    - `redis_client.py`: Configuración del cliente Redis.
  - `/workspaces`: Lógica de gestión de workspaces.
    - `models.py`: Modelos SQLAlchemy para workspaces y miembros.
    - `schemas.py`: Esquemas Pydantic para workspaces.
    - `routes.py`: Endpoints CRUD para workspaces y miembros.
  - `/tenders`: Gestión de licitaciones y documentos.
    - `schemas.py`: Esquemas Pydantic para NoSQL.
    - `tenders_utils.py`: Operaciones CRUD y conexión.
  - `/database`: Configuración de persistencia e inicialización.
    - `/postgres-init`: Scripts SQL para Docker.
  - `/tests`: Pruebas automatizadas (test_auth.py, test_workspaces.py, test_tenders.py).
- `docker-compose.yml`: Orquestación de servicios locales (PostgreSQL, Redis, MongoDB).

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

---
### Actualizaciones Recientes (Febrero 2026)

Se han realizado una serie de correcciones y mejoras en el frontend para estabilizar la aplicación, solucionar errores de ejecución y mejorar la experiencia de usuario.

#### Frontend (`Next.js`)
- **Solución de Errores de Referencia:** Corregido un error donde `DashboardHeader` no estaba definido en varias páginas.
- **Compatibilidad con React 19:** Actualizada la forma de acceder a los parámetros de ruta dinámica (`params`) en páginas de cliente para ser compatible con las últimas versiones de Next.js y React.
- **Modernización de Componentes:** Actualizado el uso del componente `<Link>` de Next.js para eliminar la etiqueta anidada `<a>`, siguiendo las nuevas convenciones.
- **Corrección de Autenticación:**
    - Solucionado un error crítico en el hook `useApi` que impedía que el token de autenticación se enviara correctamente en las llamadas a la API.
    - Corregida la interfaz de `User` en el contexto de autenticación para incluir la propiedad opcional `picture`, evitando errores al renderizar el avatar del usuario.
- **Configuración de Red y API:**
    - Las llamadas a la API ahora se realizan directamente al servidor backend (ej. `http://localhost:8000`) utilizando la variable de entorno `NEXT_PUBLIC_BACKEND_URL`. Para evitar problemas de CORS, es necesario configurar el soporte CORS directamente en el backend de FastAPI.
    - Eliminado un bucle infinito de llamadas a la API en la página de detalles de la licitación mediante la memoización de la función de fetching de datos con `useCallback`.
- **Mejoras en la Experiencia de Usuario (UX):**
    - Eliminado el header duplicado que aparecía en algunas páginas.
    - Corregido el flujo de logout para que siempre redirija a la página principal (`/`) de forma predecible, solucionando una condición de carrera que a veces redirigía a `/auth`.

#### Backend (`FastAPI`)
- No se han realizado cambios en el código del backend. El enfoque ha sido alinear el frontend con la API ya existente.