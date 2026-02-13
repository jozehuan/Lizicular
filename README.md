# Lizicular 🚀

**Lizicular** es una plataforma diseñada para la gestión y automatización de procesos en licitaciones, con un enfoque especializado en sistemas de **ticketing**. La aplicación busca optimizar el flujo de trabajo mediante automatismos que faciliten el seguimiento y la resolución de tareas relacionadas con concursos públicos.

## 🛠️ Stack Tecnológico

La aplicación se divide en diferentes módulos, utilizando las siguientes tecnologías:

### **Back-End (Núcleo)**
- **Lenguaje:** Python 3.11+
- **Framework:** FastAPI
- **Base de Datos:** PostgreSQL 15 (Identidad), MongoDB 6 (Licitaciones y Documentos)
- **Caché & Seguridad:** Redis 7 (Invalidación de tokens / Blacklist)
- **ORM:** SQLAlchemy (AsyncPG)
- **Infraestructura:** Docker & Docker Compose

### **Autenticación y Seguridad (Arquitectura "Gold Standard")**
- **Estrategia de Tokens Segura:**
  - **`accessToken` (15 min):** Un token de corta duración que se almacena exclusivamente en la memoria del frontend (React Context). Se utiliza para autorizar cada petición a la API. Al no persistir en `localStorage`, se mitiga el riesgo de robo por ataques XSS.
  - **`refreshToken` (7 días):** Un token de larga duración que se almacena en una **cookie `HttpOnly`, `Secure` y `SameSite=Lax`**. Es inaccesible para JavaScript y se utiliza únicamente para solicitar nuevos `accessToken`.
- **Flujo de Autenticación Robusto:** Tras un login exitoso, el frontend no recibe el `accessToken` directamente. En su lugar, el `AuthContext` utiliza el `refreshToken` de la cookie para obtener de forma segura el `accessToken` inicial, que se gestiona en memoria.
- **Rotación de Tokens y Lista Negra:** Cada vez que se usa un `refreshToken`, se emite uno nuevo (rotación) y el anterior se invalida inmediatamente en una "lista negra" en Redis, previniendo ataques de reutilización.
- **OAuth2 y RBAC:** Se mantiene la integración con proveedores externos y el sistema de roles a nivel de Workspace.
- **Auditoría Universal:** Registro detallado de todos los eventos de seguridad y acceso para una trazabilidad completa.

### **Módulos de Gestión**
- **Workspaces:** Organización lógica de licitaciones y equipos.
- **Audit System:** Helpers para monitoreo, estadísticas y detección de actividad sospechosa.

### **Front-End (En Desarrollo)**
- **Entorno:** Node.js
- **Framework:** React / Next.js (Planificado)

### **Chatbot (Backend)**
- **Arquitectura de Agentes:** Se ha implementado un "meta-agente" conversacional basado en `LlamaIndex` que orquesta un conjunto de herramientas (agentes especializados).
- **Agente de Revisión (`ReviewAgent`):** Un agente-herramienta que permite al chatbot consultar de forma segura los datos del usuario autenticado (workspaces, tenders, etc.) a través de los endpoints internos de la API.
- **Extensibilidad:** El sistema de `AgentFactory` y `EngineAIFactory` permite añadir nuevos agentes y motores de LLM (actualmente Azure OpenAI) de forma modular.
- **Observabilidad y Auditoría:** Todas las conversaciones se trazan con `Langfuse` para depuración y se registran en la tabla de `audit_logs` de PostgreSQL para un seguimiento completo.

### **Pruebas y Calidad**
- **Pytest:** Suite de pruebas unitarias y de integración asíncronas.
- **Postman:** Pruebas manuales y documentación de la API.
- **Httpx:** Cliente HTTP para pruebas de integración de FastAPI.

## 📂 Estructura del Proyecto

- `backend/main.py`: Punto de entrada de la aplicación (orquesta los routers).
- `backend/auth/`: Lógica de autenticación.
- `backend/workspaces/`: Lógica de gestión de workspaces.
- `backend/chatbot/`: Módulo del agente de IA conversacional.
  - `routes.py`: Endpoint `/chatbot/chat`.
  - `chat_bot_controller.py`: Lógica principal de la conversación.
  - `agents/`: Definiciones de agentes-herramienta (ej. `review_agent.py`).
  - `manager/`: Orquestación y ensamblaje del agente principal.
  - `engines/`: Fábrica para los motores de LLM.
- `backend/tenders/`: Gestión de licitaciones y documentos (NoSQL).
- `backend/database/`: Scripts de inicialización y configuración de DB.
- `backend/tests/`: Pruebas automatizadas.

## 🔌 API Endpoints

### **Autenticación Local (en `/auth/routes.py`)**
- `POST /auth/signup`: Registro de nuevos usuarios.
- `POST /auth/login/json`: Login mediante payload JSON + Set Refresh Cookie.
- `POST /auth/refresh`: Refresca el Access Token usando el Refresh Token de la cookie.
- `POST /auth/logout`: Invalida los tokens y elimina la cookie de sesión.

### **Autenticación Externa (OAuth2) (en `/auth/routes.py`)**
- `GET /auth/{provider}/login`: Inicia el flujo de autenticación con un proveedor.
- `GET /auth/{provider}/callback`: Endpoint de retorno para el intercambio de tokens.
- `GET /auth/providers`: Lista los proveedores externos configurados.

### **Usuarios (en `/auth/routes.py`)**
- `GET /users/me`: Obtiene la información del perfil del usuario autenticado (Protegido con JWT).

### **Chatbot (en `/chatbot/routes.py`)**
- `POST /chatbot/chat`: Envía un mensaje al chatbot y recibe una respuesta (Protegido con JWT).

### **Workspaces (Colaboración) (en `/workspaces/routes.py`)**
- `POST /workspaces/`: Crea un nuevo workspace (el creador es el OWNER).
- `GET /workspaces/`: Lista los workspaces a los que pertenece el usuario.
- `GET /workspaces/detailed/`: Lista los workspaces con un resumen de sus licitaciones y el rol del usuario.
- `GET /workspaces/{workspace_id}`: Obtiene detalles de un workspace específico.
- `PUT /workspaces/{workspace_id}`: Actualiza un workspace (solo OWNER/ADMIN).
- `DELETE /workspaces/{workspace_id}`: Elimina un workspace (solo OWNER).

#### **Miembros del Workspace (en `/workspaces/routes.py`)**
- `POST /workspaces/{workspace_id}/members`: Añade un usuario al workspace con un rol específico (solo OWNER/ADMIN).
- `GET /workspaces/{workspace_id}/members`: Lista todos los miembros del workspace.
- `PUT /workspaces/{workspace_id}/members/{user_id}`: Actualiza el rol de un miembro (solo OWNER/ADMIN).
- `DELETE /workspaces/{workspace_id}/members/{user_id}`: Elimina un miembro del workspace (solo OWNER/ADMIN).

### **Automatismos (en `/automations/routes.py`)**
- `POST /automations/`: Crea un nuevo automatismo.


### **Licitaciones (Tenders) (en `/tenders/routes.py`)**
- `POST /tenders`: Crea una nueva licitación (Requiere rol EDITOR).
- `GET /tenders/workspace/{workspace_id}`: Lista licitaciones de un workspace.
- `GET /tenders/{tender_id}`: Obtiene el detalle completo de una licitación.
- `PATCH /tenders/{tender_id}`: Actualiza datos de una licitación (Requiere rol EDITOR).
- `DELETE /tenders/{tender_id}`: Elimina una licitación (Requiere rol ADMIN).

### **Análisis de Licitaciones (en `/tenders/routes.py`)**
- `POST /tenders/{tender_id}/analysis`: Añade resultados de análisis a una licitación (Requiere rol EDITOR).
- `POST /tenders/{tender_id}/generate_analysis`: Inicia la generación de un nuevo análisis de forma asíncrona (Requiere rol EDITOR).
- `GET /analysis-results/{analysis_id}`: Obtiene el detalle de un resultado de análisis específico (usado por el chatbot).
- `DELETE /tenders/{tender_id}/analysis/{result_id}`: Elimina un análisis específico.

### **WebSockets**
- `ws /ws/analysis/{analysis_id}`: Conexión WebSocket para recibir actualizaciones en tiempo real sobre el estado y el resultado de un análisis.


### **Utilidad (en `/main.py`)**
- `GET /`: Health check del sistema.

## 📝 Resumen de Progreso

Actualmente, el proyecto se encuentra en su fase inicial de infraestructura y base de seguridad:

1.  **Base de Datos Contenedorizada:** Configuración de PostgreSQL mediante Docker Compose para un entorno de desarrollo reproducible.
2.  **Módulo de Autenticación Híbrida:** Implementación completa del sistema de registro y login, soportando tanto credenciales locales como OAuth2, con toda la lógica modularizada en `backend/auth/`.
3.  **Refactorización de Tipos:** Código optimizado para Python 3.11+ usando el estándar `Tipo | None` y Pydantic v2.
4.  **Infraestructura de Pruebas:** Creación de una suite de tests automáticos con `pytest` y `httpx`, además de colecciones en `Postman` para validación manual del flujo de usuarios.
5.  **Corrección de Dependencias:** Ajuste de versiones de seguridad (`bcrypt`) para asegurar compatibilidad en Windows y entornos asíncronos.
6.  **Gestión de Workspaces:** Implementación completa de la creación, gestión y control de acceso (RBAC) para organizar equipos y licitaciones, con toda la lógica modularizada en `backend/workspaces/`.
7.  **Sistema de Auditoría de Grado Empresarial:** Motor de logs universal con soporte para categorías (Auth, Workspace, Tender, etc.) y utilidades de consulta avanzada, detección de amenazas y exportación para cumplimiento.
8.  **Generación de Análisis Asíncrono:** Se ha implementado un flujo de generación de análisis asíncrono con notificaciones en tiempo real vía WebSockets. El frontend puede disparar un análisis y, en lugar de esperar, recibe una respuesta inmediata. El estado y el resultado final de la tarea son enviados al frontend a través de un WebSocket, eliminando la necesidad de polling.
9.  **Gestión de Automatismos:** Se ha añadido una tabla `autos` en PostgreSQL y endpoints en `/automations` para registrar y gestionar los automatismos externos (ej. webhooks de n8n) que pueden ser invocados.
10. **Modelos de Datos Extensibles:** Los esquemas de Pydantic para los resultados de análisis se han actualizado para soportar estructuras de datos más complejas y anidadas, incluyendo un nuevo JSON `estimacion`.
11. **Arquitectura de Chatbot:** Se ha implementado la base para un agente de IA conversacional, con un sistema de agentes-herramienta, autenticación de usuario y registro de auditoría.

---
**Desarrollado para la automatización eficiente de licitaciones.**

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
