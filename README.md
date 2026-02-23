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
- **Flujo de Autenticación Robusto:** Tras el login, el `AuthContext` del frontend no llama directamente al backend, sino a las **API Routes de Next.js** que actúan como un proxy seguro (BFF). Estas rutas gestionan la comunicación con el backend de FastAPI y propagan la cookie `HttpOnly` del `refreshToken`, mientras que el `accessToken` se obtiene de forma segura y se mantiene solo en la memoria del cliente.
- **Rotación de Tokens y Lista Negra:** Cada vez que se usa un `refreshToken`, se emite uno nuevo (rotación) y el anterior se invalida inmediatamente en una "lista negra" en Redis, previniendo ataques de reutilización.
- **OAuth2 y RBAC:** Se mantiene la integración con proveedores externos y el sistema de roles a nivel de Workspace.
- **Auditoría Universal:** Registro detallado de todos los eventos de seguridad y acceso para una trazabilidad completa.

### **Módulos de Gestión**
- **Workspaces:** Organización lógica de licitaciones y equipos.
- **Audit System:** Helpers para monitoreo, estadísticas y detección de actividad sospechosa.

### **Front-End (Implementado)**
- **Framework:** Next.js (App Router)
- **Lenguaje:** TypeScript
- **UI:** React, Tailwind CSS, Shadcn/UI
- **Páginas Principales:** Dashboard, Perfil de Usuario, Gestión de Espacios y Análisis de Licitaciones.
- **Internacionalización:** Soporte para múltiples idiomas con `next-intl`.

### **Chatbot**
- **Arquitectura de Agentes (Backend):** Se ha implementado un "meta-agente" conversacional basado en `LlamaIndex` que orquesta un conjunto de herramientas (agentes especializados).
- **Agente de Revisión (`ReviewAgent`):** Un agente-herramienta que permite al chatbot consultar de forma segura los datos del usuario autenticado (workspaces, tenders, etc.) a través de los endpoints internos de la API.
- **Interfaz de Usuario (Frontend):** Un widget de chat flotante, disponible en el dashboard del usuario, proporciona una interfaz de conversación directa. Este componente, impulsado por un Contexto de React, se comunica de forma segura con el backend a través del proxy BFF de Next.js.
- **Extensibilidad:** El sistema de `AgentFactory` y `EngineAIFactory` permite añadir nuevos agentes y motores de LLM (actualmente Azure OpenAI) de forma modular.
- **Observabilidad y Auditoría:** Todas las conversaciones se trazan con `Langfuse` para depuración y se registran en la tabla de `audit_logs` de PostgreSQL para un seguimiento completo.

### **Infraestructura de Pruebas (Frontend & Backend)**
- **Backend (Pytest):** Suite exhaustiva de pruebas unitarias y de integración para validar la lógica de negocio, seguridad y endpoints.
  - `test_auth.py`: Autenticación, gestión de sesiones y perfil de usuario.
  - `test_workspaces.py`: CRUD de espacios y control de acceso (RBAC).
  - `test_tenders.py`: Gestión de licitaciones, documentos y permisos.
  - `test_automations.py`: Creación y listado de automatismos.
  - `test_chatbot.py`: Interacción segura con el agente conversacional.
- **Frontend (Playwright):** Pruebas End-to-End (E2E) que simulan el comportamiento real del usuario en el navegador.
  - `auth.spec.ts`: Flujos de registro e inicio de sesión.
  - `dashboard.spec.ts`: Navegación y creación de espacios.
  - `profile.spec.ts`: Edición de perfil y avatar.
  - `tenders.spec.ts`: Creación de licitaciones.
- **Herramientas Complementarias:**
  - **Postman:** Colecciones para validación manual y documentación interactiva de la API. Permite probar endpoints individualmente y compartir ejemplos de peticiones.
  - **Httpx:** Cliente HTTP asíncrono de alto rendimiento utilizado internamente por la suite de Pytest para realizar peticiones de integración contra la API de FastAPI.

### **Base de Datos NoSQL (MongoDB)**
- **`tenders`**: Colección central con metadatos de licitaciones y **resúmenes ligeros** de sus documentos y análisis (sin datos pesados).
- **`tender_files`**: Almacena el contenido binario de los archivos subidos para mantener ágil la colección `tenders`.
- **`analysis_results`**: **Fuente única de la verdad** para los resultados JSON detallados. Su estructura es **dinámica** y flexible, adaptándose a cualquier salida de los automatismos.

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
- `backend/requirements.txt`: Dependencias del backend.
- `docker-compose.yml`: Orquestación de servicios locales.
- `docker-stack.yml`: Configuración para despliegue en Swarm.
- `scripts/`: Herramientas de automatización y despliegue.

## 🔌 API Endpoints

> **Nota sobre la Arquitectura (BFF):** La siguiente lista documenta los endpoints del backend (FastAPI). El frontend **nunca** los llama directamente. En su lugar, utiliza un patrón de **Backend-for-Frontend (BFF)**:
> - **Rutas de Autenticación:** Se accede a través de proxies manuales en Next.js (ej. el frontend llama a `/api/auth/login`, que a su vez llama al backend en `/auth/login/json`).
> - **Otras Rutas de API:** Se accede a través de un proxy genérico (ej. el frontend llama a `/api/backend/workspaces/`, que Next.js redirige al backend en `/workspaces/`).

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
- `PATCH /users/me`: Actualiza información del perfil (nombre, avatar).
- `DELETE /users/me`: Elimina permanentemente la cuenta y todos los datos asociados.

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
- `POST /tenders/{tender_id}/generate_analysis`: Inicia la generación de un nuevo análisis de forma asíncrona (Requiere rol EDITOR). Soporta un **timeout de 15 minutos** y cálculo automático de duración.
- `GET /analysis-results/{analysis_id}`: Obtiene el detalle de un resultado de análisis específico (usado por el chatbot).
- `PATCH /analysis-results/{analysis_id}`: Renombra un resultado de análisis específico (Requiere rol EDITOR).
- `DELETE /tenders/{tender_id}/analysis/{result_id}`: Elimina un análisis específico.

### **WebSockets**
- `ws /ws/analysis/{analysis_id}`: Conexión WebSocket para recibir actualizaciones en tiempo real sobre el estado y el resultado de un análisis, incluyendo notificaciones de finalización y errores.


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
7.  **Sistema de Auditoría de Grado Empresarial:** Motor de logs universal con soporte para categorías (Auth, Workspace, Tender, etc.) y utilidades de consulta avanzada, detección de amenazas y exportación para cumplimiento. Se ha extendido para cubrir todo el ciclo de vida de los automatismos (`WORKFLOW_START`, `COMPLETE`, `ERROR`).
8.  **Generación de Análisis Asíncrono:** Se ha implementado un flujo de generación de análisis asíncrono con notificaciones en tiempo real vía WebSockets. El frontend puede disparar un análisis y, en lugar de esperar, recibe una respuesta inmediata. El estado y el resultado final de la tarea son enviados al frontend a través de un WebSocket, eliminando la necesidad de polling.
9.  **Gestión de Automatismos:** Se ha añadido una tabla `autos` en PostgreSQL y endpoints en `/automations` para registrar y gestionar los automatismos externos (ej. webhooks de n8n) que pueden ser invocados.
10. **Modelos de Datos Extensibles:** Los esquemas de Pydantic para los resultados de análisis se han actualizado para soportar estructuras de datos más complejas y anidadas, incluyendo un nuevo JSON `estimacion`.
11. **Arquitectura de Chatbot:** Se ha implementado la base para un agente de IA conversacional, con un sistema de agentes-herramienta, autenticación de usuario y registro de auditoría.
12. **Robustez y Estabilidad del Backend:** Se han implementado mejoras significativas en la seguridad de las operaciones. La eliminación de workspaces ahora sigue un patrón transaccional para evitar datos huérfanos entre bases de datos. Además, las tareas asíncronas de análisis son ahora resilientes a condiciones de carrera, cancelándose de forma segura si la licitación asociada se elimina durante el procesamiento.
13. **Optimización de Interfaz y Carga (Frontend):** Se ha refinado la experiencia de usuario en la página de licitaciones. El sistema ahora realiza refrescos silenciosos en segundo plano al volver a la pestaña, sin interrumpir con pantallas de carga globales. Además, la obtención de resultados de análisis se ha hecho secuencial y exhaustiva, garantizando la carga completa de datos detallados desde la colección de MongoDB para todos los análisis finalizados.
14. **Gestión de Perfil y Validación Multi-Nivel:** Implementación de una página de perfil para personalización de avatares y nombres. Se han establecido restricciones de longitud estrictas en todos los elementos (Usuarios, Workspaces, Licitaciones) validadas tanto en base de datos como en backend y frontend para garantizar la integridad total de la información.
15. **Borrado Seguro de Usuario:** Sistema de eliminación de cuenta que orquesta la limpieza de datos en PostgreSQL y MongoDB, asegurando que no queden rastros de información personal o de negocio del usuario al retirarse de la plataforma.
16. **Cronómetro Digital y Control de Tiempo:** Se ha integrado un cronómetro digital en tiempo real para el seguimiento de análisis pendientes o en curso. El backend calcula ahora el tiempo exacto de procesamiento y mantiene la integridad de los datos en MongoDB limpiando marcas temporales obsoletas tras la finalización.
17. **Ciclo de Automatización de Larga Duración:** Soporte para procesos pesados mediante un sistema de espera de 15 minutos con gestión específica de timeouts y auditoría detallada en PostgreSQL.

---
**Desarrollado para la automatización eficiente de licitaciones.**

## Pruebas del Backend

El backend cuenta con una suite de pruebas automatizadas utilizando `pytest`. Estas pruebas cubren la funcionalidad principal de la API, asegurando la correcta operación de los endpoints y la lógica de negocio.

### `test_auth.py`

Este módulo se encarga de probar todos los aspectos de la autenticación y gestión de usuarios.

-   **test_signup_success**: Verifica que un usuario puede registrarse exitosamente.
-   **test_login_generates_cookies**: Asegura que el login genera tanto el `access_token` como la cookie `refresh_token`.
-   **test_refresh_token_flow**: Prueba el flujo completo de refresco de tokens.
-   **test_logout_clears_cookie**: Verifica que el logout elimina la cookie de `refresh_token`.
-   **test_access_token_type_security**: Asegura que un `refresh_token` no puede ser usado como `access_token`.
-   **test_read_users_me_success**: Prueba que se puede acceder al perfil del usuario con un `access_token` válido.
-   **test_token_blacklisting_on_logout**: Verifica que un `access_token` es invalidado después del logout.
-   **test_refresh_token_rotation_security**: Asegura que un `refresh_token` no puede ser usado dos veces.
-   **test_update_user_me**: Prueba la actualización del perfil del usuario.
-   **test_delete_user_me**: Prueba la eliminación de la cuenta del usuario.

### `test_automations.py`

Este módulo prueba la creación y listado de automatismos.

-   **test_create_automation**: Verifica que se puede crear un nuevo automatismo.
-   **test_list_automations**: Asegura que se pueden listar los automatismos existentes.

### `test_chatbot.py`

Este módulo prueba la interacción con el chatbot.

-   **test_chatbot_chat_success**: Verifica una interacción exitosa con el chatbot.
-   **test_chatbot_chat_unauthorized**: Asegura que usuarios no autorizados no pueden acceder al chatbot.

### `test_tenders.py`

Este módulo prueba la gestión de licitaciones y sus análisis.

-   **test_create_tender_with_editor_role**: Verifica que un usuario con rol `EDITOR` puede crear una licitación.
-   **test_create_tender_with_viewer_role_fails**: Asegura que un usuario con rol `VIEWER` no puede crear una licitación.
-   **test_list_and_get_tender**: Prueba el listado de licitaciones en un workspace y la obtención de una por su ID.
-   **test_delete_tender_with_admin_role**: Verifica que un usuario con rol `ADMIN` puede eliminar una licitación.
-   **test_add_and_delete_analysis_result**: Prueba que se puede añadir y eliminar un resultado de análisis de una licitación.
-   **test_get_all_tenders_for_user_permissions**: Asegura que un usuario solo puede ver las licitaciones a las que tiene acceso.
-   **test_patch_tender**: Prueba la actualización del nombre de una licitación.
-   **test_add_and_delete_document**: Prueba que se puede añadir y eliminar un documento de una licitación.
-   **test_rename_analysis_result**: Prueba que se puede renombrar un resultado de análisis.

### `test_workspaces.py`

Este módulo prueba la gestión de workspaces y sus miembros.

-   **test_create_workspace**: Verifica que se puede crear un nuevo workspace.
-   **test_get_user_workspaces**: Prueba el listado de todos los workspaces a los que un usuario pertenece.
-   **test_add_member_to_workspace**: Verifica que el propietario de un workspace puede añadir un nuevo miembro.
-   **test_non_admin_cannot_add_member**: Asegura que un usuario que no es administrador no puede añadir miembros.
-   **test_owner_can_remove_member**: Verifica que el propietario de un workspace puede eliminar un miembro.
-   **test_cannot_remove_workspace_owner**: Asegura que el propietario de un workspace no puede ser eliminado.
-   **test_update_workspace**: Prueba la actualización del nombre y la descripción de un workspace.