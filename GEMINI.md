# Contexto del Proyecto: Lizicular

## Objetivo
Esta aplicación es un proyecto para el desarrollo de una aplicación web llamada "Lizicular", que se encarga de aplicar procesos de automatización sobre licitaciones.

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
  - `/automations`: Lógica de gestión de automatismos.
    - `models.py`: Modelo SQLAlchemy para automatismos.
    - `routes.py`: Endpoints para gestionar automatismos.
    - `/websocket`: Lógica para WebSockets de automatismos.
      - `routes.py`: Endpoints WebSocket.
      - `connection_manager.py`: Gestión de conexiones WebSocket.
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
3. **Control de Acceso:** Implementación completa de Workspaces para organizar la colaboración en licitaciones, incluyendo gestión de miembros y roles. Los roles definidos son "OWNER", "ADMIN", "EDITOR" y "VIEWER". Estos roles son encapsulados, lo que significa que los roles superiores heredan todos los permisos de los inferiores. La jerarquía es la siguiente: `VIEWER` (el más bajo) < `EDITOR` < `ADMIN` < `OWNER`.

4. **Trazabilidad:** Sistema de auditoría universal listo para cumplimiento (compliance) y monitoreo de seguridad, ahora extendido a acciones de Workspaces.
5. **Estrategia de Seguridad de Tokens:** Implementación de Access Tokens efímeros (15m) y Refresh Tokens persistentes en cookies HttpOnly para protección contra XSS.
6. **Invalidación de Tokens (Redis Blacklist):** Uso de Redis para invalidar inmediatamente tokens durante el logout o rotación, garantizando que un token robado no pueda ser reutilizado.
7. **Preparación para el Chatbot:** La estructura de auditoría y workspaces está diseñada para integrarse con los flujos de automatización y el chatbot futuro.
8. **Generación de Análisis Asíncrono:** Se ha implementado un flujo de generación de análisis asíncrono con notificaciones en tiempo real vía WebSockets. El frontend puede iniciar una tarea de análisis y, en lugar de esperar, recibe una respuesta inmediata. El estado y el resultado final de la tarea son enviados al frontend a través de un WebSocket, eliminando la necesidad de polling.
9. **Gestión de Automatismos:** Se ha creado una nueva tabla `autos` en PostgreSQL para almacenar información sobre los automatismos (como webhooks de n8n) y un endpoint para gestionarlos.
10. **Modelos de Datos Flexibles:** Los modelos de Pydantic se han actualizado para soportar estructuras de datos más complejas en los resultados de los análisis, incluyendo un nuevo JSON `estimacion`.



## Reglas de Oro (Instrucciones para Gemini)
1. Siempre responde en español.
2. Usa tipado estricto si usamos TypeScript.
3. No sugieras librerías obsoletas.
4. Usa siempre el estándar de tipado `Tipo | None` en Python (PEP 604).
5. Mantén la documentación de los endpoints actualizada.
6. Siempre que se modifique, añada o elimine un endpoint, tanto en back como en front, se deben modificar los archivos `GEMINI.md` y `README.md`.

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
**Conclusiones de la Refactorización:** El backend ha sido sometido a una importante revisión de seguridad y estabilidad. Como conclusión, la autenticación de usuarios es ahora significativamente más segura, cerrando vulnerabilidades críticas de toma de cuentas y fuga de información. La arquitectura es más robusta y escalable, gracias a la correcta gestión de sesiones y tareas en segundo plano, lo que garantiza el funcionamiento fiable de características clave como la generación de análisis y el login con OAuth en entornos de producción. Se han resuelto bugs de lógica que afectaban la integridad de los datos, asegurando que las operaciones como la carga y borrado de documentos se comporten de manera predecible y atómica. En resumen, el estado del backend ha pasado de ser una prueba de concepto funcional a tener una base preparada para producción.