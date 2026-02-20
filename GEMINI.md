# Contexto del Proyecto: Lizicular

## Objetivo
Esta aplicación es un proyecto para el desarrollo de una aplicación web llamada "Lizicular", que se encarga de aplicar procesos de automatización sobre licitaciones.

## Stack Tecnológico
- **BackEnd:** Python 3.10+ - FastAPI
- **FrontEnd:** Next.js (App Router), React, TypeScript, Tailwind CSS, Shadcn/UI, Next-Intl
- **Base de Datos:** PostgreSQL 15 (Identidad y Auditoría), MongoDB 6 (Licitaciones y Documentos).
- **Caché y Seguridad:** Redis 7 (Lista negra de tokens, invalidación inmediata).
- **Seguridad:** JWT (JSON Web Tokens) y OAuth2
- **Infraestructura:** Docker Compose para orquestación de servicios locales.
- **Estándares:** Tipado moderno (`Tipo | None`) y compatibilidad con Pydantic v2.

## Arquitectura de Datos (MongoDB)
La persistencia de los datos de negocio se gestiona en MongoDB a través de tres colecciones principales, siguiendo una arquitectura que separa los metadatos, los archivos binarios y los resultados detallados.

1.  **`tenders`**:
    *   **Propósito:** Es la colección central. Cada documento representa una única licitación y actúa como el contenedor principal de metadatos.
    *   **Estructura:** Contiene campos como `name`, `description`, `workspace_id`, etc. Además, incluye dos arrays importantes:
        *   `documents`: Un array de objetos que contienen los metadatos de los archivos subidos (nombre, tipo, tamaño), pero no el contenido binario.
        *   `analysis_results`: Un array de **resúmenes ligeros** de los análisis ejecutados. Cada objeto en este array contiene metadatos como `id`, `name`, `status`, y `created_at`. El campo pesado `data` ha sido eliminado de esta vista para optimizar el rendimiento y el tamaño de los documentos.

2.  **`tender_files`**:
    *   **Propósito:** Almacena el contenido binario de todos los archivos que se suben al sistema.
    *   **Estructura:** Cada documento contiene el `_id` (referenciado por el `id` en el array `documents` de un `tender`) y un campo `data` que guarda el archivo en formato binario de BSON. Esto evita sobrecargar los documentos de la colección `tenders` con datos pesados.

3.  **`analysis_results`**:
    *   **Propósito:** Almacena los documentos JSON completos y detallados generados por los automatismos (n8n). Esta es la **única fuente de la verdad** para el contenido detallado de un análisis.
    *   **Estructura Dinámica:** La estructura de un documento en esta colección es **flexible y dinámica**. No sigue un esquema fijo. Cada documento contiene un `_id` (que corresponde al `id` en el array de resúmenes del `tender`), pero los demás campos dependen enteramente de lo que el automatismo específico haya extraído y devuelto. Esto permite una total flexibilidad para diferentes tipos de análisis sin restricciones de esquema.

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
  - `/chatbot`: Lógica para el agente de IA conversacional.
    - `routes.py`: Define el endpoint protegido `/chat`.
    - `chat_bot_controller.py`: Orquesta la lógica de la conversación.
    - `bot_manager.py`: Gestiona la inicialización del agente principal.
    - `models.py`: Modelos Pydantic para el chatbot.
    - `/agents`: Contiene las definiciones de los agentes (herramientas).
        - `base_agent.py`: Clase base abstracta para todos los agentes.
        - `agent_factory.py`: Fábrica para crear instancias de agentes.
        - `/agent_tools`: Implementaciones concretas de agentes.
            - `review_agent.py`: Agente para consultar datos del usuario (workspaces, tenders).
    - `/engines`: Lógica para la creación de motores de LLM.
        - `engine_ai_factory.py`: Fábrica que selecciona el motor (actualmente solo Azure).
    - `/manager`: Gestiona el ensamblaje de los agentes.
        - `base_manager.py`: Clase base para los gestores de agentes.
        - `main_manager.py`: Gestor principal que registra los agentes disponibles.
  - `/tenders`: Gestión de licitaciones y documentos.
    - `schemas.py`: Esquemas Pydantic para NoSQL.
    - `tenders_utils.py`: Operaciones CRUD y conexión.
  - `/database`: Configuración de persistencia e inicialización.
    - `/postgres-init`: Scripts SQL para Docker.
  - `/tests`: Pruebas automatizadas (test_auth.py, test_workspaces.py, test_tenders.py).
- `docker-compose.yml`: Orquestación de servicios locales (PostgreSQL, Redis, MongoDB).
- `/frontend`: Aplicación Next.js (App Router).
  - `/app`: Rutas de la aplicación y componentes principales.
    - `/[locale]`: Contiene todas las rutas internacionalizadas.
      - `/dashboard`: Página principal del usuario.
      - `/profile`: Perfil de usuario y ajustes.
      - `/space/[spaceId]`: Vista detallada de un workspace.
      - `/space/[spaceId]/tender/[tenderId]`: Vista de una licitación y sus análisis.
    - `/api`: Rutas de API que actúan como Backend-for-Frontend (BFF).
      - `/auth`: Endpoints de proxy para autenticación (login, refresh, logout).
  - `/components`: Componentes de React reutilizables (UI, layout, etc.).
  - `/lib`: Lógica principal del lado del cliente (contexto de autenticación, hook `useApi`, etc.).
  - `/hooks`: Hooks de React personalizados.
  - `next.config.mjs`: Configuración de Next.js, incluyendo el proxy de reescritura para la API.

## Estado del Proyecto
El módulo de autenticación y seguridad es completamente funcional y ha sido expandido con capacidades de nivel empresarial:
1. **Seguridad Avanzada:** Optimizado con estándares modernos de Python 3.10+ y Pydantic v2.
2. **Infraestructura de Datos:** PostgreSQL para identidad y auditoría; MongoDB planificado para licitaciones y documentos.
3. **Control de Acceso:** Implementación completa de Workspaces para organizar la colaboración en licitaciones, incluyendo gestión de miembros y roles. Los roles definidos son "OWNER", "ADMIN", "EDITOR" y "VIEWER". Estos roles son encapsulados, lo que significa que los roles superiores heredan todos los permisos de los inferiores. La jerarquía es la siguiente: `VIEWER` (el más bajo) < `EDITOR` < `ADMIN` < `OWNER`.
4. **Trazabilidad:** Sistema de auditoría universal listo para cumplimiento (compliance) y monitoreo de seguridad, ahora extendido a acciones de Workspaces.
5. **Estrategia de Seguridad de Tokens (Revisada):** Se ha implementado una arquitectura de autenticación "Gold Standard". El `accessToken` (efímero, 15m) se almacena únicamente en la memoria del frontend (React Context) para autorizar las peticiones a la API. El `refreshToken` (larga duración, 7 días) se almacena en una cookie `HttpOnly`, `Secure` y `SameSite=Lax`, haciéndolo inaccesible a ataques XSS. Tras el login/signup, el frontend solo recibe los datos del usuario; inmediatamente después, utiliza la cookie `HttpOnly` para obtener el `accessToken` inicial, evitando la exposición de tokens en el cuerpo de la respuesta. Las API Routes de Next.js actúan como un proxy seguro para gestionar y propagar estas cookies.
6. **Invalidación de Tokens (Redis Blacklist):** Uso de Redis para invalidar inmediatamente tokens durante el logout o rotación, garantizando que un token robado no pueda ser reutilizado.
7. **Arquitectura de Chatbot Avanzada:** Se ha implementado la base para un agente de IA conversacional con una arquitectura modular y extensible.
    - **Sistema de Agentes (Tools):** El chatbot opera como un "meta-agente" que utiliza un conjunto de herramientas (otros agentes especializados). Se ha creado el `ReviewAgent`, que permite al chatbot consultar información específica del usuario (workspaces, tenders) llamando a los endpoints internos del backend de forma segura.
    - **Gestión y Orquestación:** Un `BotManager` se encarga de construir el agente principal, registrando dinámicamente los agentes-herramienta disponibles a través de un sistema de fábricas (`AgentFactory`).
    - **Motores de IA Flexibles:** La arquitectura incluye un `EngineAIFactory` que permite intercambiar el motor de LLM subyacente. Actualmente está configurado para usar Azure OpenAI.
    - **Autenticación y Auditoría:** El endpoint `/chatbot/chat` está protegido y requiere autenticación de usuario. Todas las interacciones (preguntas, respuestas y errores) se registran en la tabla de `audit_logs` de PostgreSQL.
    - **Observabilidad:** Integración con `Langfuse` para trazar y depurar las interacciones y el razonamiento del agente en tiempo real.
    - **Integración en Frontend (React):** La interfaz del chatbot se implementa a través de una arquitectura cohesiva en React:
        - **`ChatbotProvider` y `useChatbot`:** Un contexto global de React (`ChatbotContext`) envuelve la aplicación, gestionando el estado de la conversación (historial de mensajes, estado de "escribiendo"). El hook `useChatbot` proporciona acceso a este estado y a la función `sendMessage`.
        - **`ChatbotWidget`:** Un componente UI que se renderiza en la página principal del dashboard. Se presenta como un botón flotante en la esquina inferior derecha que, al hacer clic, abre la ventana de chat.
        - **Comunicación Segura:** La función `sendMessage` utiliza el hook `useApi` existente, asegurando que todas las comunicaciones con el endpoint `/chatbot/chat` pasen a través del proxy BFF de Next.js, heredando la autenticación y seguridad de la aplicación.
        - **Renderizado Avanzado:** Las respuestas del bot se renderizan con `ReactMarkdown`, permitiendo la visualización de texto enriquecido (listas, negritas, etc.) para una mejor experiencia de usuario.
8. **Arquitectura de Red y API (BFF):** El frontend utiliza un patrón de **Backend-for-Frontend (BFF)**, donde la aplicación Next.js actúa como un proxy seguro entre el navegador del cliente y el backend de FastAPI. Esto mejora la seguridad (ocultando la URL del backend y las claves de API), simplifica la gestión de cookies de autenticación y evita problemas de CORS. La comunicación se gestiona de dos maneras:
    - **Proxy de Autenticación Manual:** Las rutas en `/app/api/auth/` (ej. `login`, `refresh`) son manejadas por código explícito en el servidor de Next.js. Estas rutas leen y escriben cookies `HttpOnly` y orquestan el flujo de autenticación con el backend, asegurando que los tokens sensibles nunca se expongan directamente al cliente.
    - **Proxy de API General (Reescritura):** Las llamadas a la API generales (ej. para obtener datos de workspaces o licitaciones) se dirigen al prefijo `/api/backend/*` en el frontend. Una regla de reescritura en `next.config.mjs` redirige de forma transparente estas peticiones al backend de FastAPI, utilizando una variable de entorno (`process.env.BACKEND_URL`) para definir la URL de destino. El hook `useApi` se encarga de realizar estas llamadas de forma centralizada.
9. **Generación de Análisis Asíncrono:** Se ha implementado un flujo de generación de análisis asíncrono con notificaciones en tiempo real vía WebSockets. El frontend puede iniciar una tarea de análisis y, en lugar de esperar, recibe una respuesta inmediata. El estado y el resultado final de la tarea son enviados al frontend a través de un WebSocket, eliminando la necesidad de polling.
10. **Gestión de Automatismos:** Se ha creado una nueva tabla `autos` en PostgreSQL para almacenar información sobre los automatismos (como webhooks de n8n) y un endpoint para gestionarlos.
11. **Modelos de Datos Flexibles:** Los modelos de Pydantic se han actualizado para soportar estructuras de datos más complejas en los resultados de los análisis, incluyendo un nuevo JSON `estimacion`.
12. **Internacionalización (i18n):** El frontend está preparado para soportar múltiples idiomas. Utiliza la librería `next-intl` para gestionar las traducciones, con los textos centralizados en archivos JSON (`/messages/{locale}.json`) y un enrutamiento que incluye el locale en la URL (ej. `/en/...` o `/es/...`).
13. **Eliminación Segura en Cascada:** Se ha refactorizado la lógica de eliminación de workspaces para mejorar la seguridad transaccional. El nuevo proceso primero ejecuta las operaciones en la base de datos relacional (PostgreSQL) y, solo si la transacción tiene éxito, procede con el borrado de los datos asociados en MongoDB. Esto previene estados inconsistentes si una de las operaciones falla.
14. **Tareas Asíncronas Robustas:** El proceso de generación de análisis en segundo plano se ha mejorado para ser resiliente a condiciones de carrera. Antes de actualizar un análisis finalizado, la tarea ahora verifica si la licitación principal todavía existe. Si fue eliminada durante el procesamiento, la tarea se aborta de forma segura, previniendo errores y notificando al cliente a través del WebSocket.
15. **Gestión de Nombres de Análisis:** Se ha añadido un nuevo endpoint `PATCH /analysis-results/{analysis_id}` que permite a los usuarios con permisos de `EDITOR` renombrar un resultado de análisis. La operación se registra en el sistema de auditoría.
16. **Consistencia y Optimización de Datos:** Se ha corregido una inconsistencia en la arquitectura de MongoDB. Los resúmenes de análisis dentro de `tenders` ya no contienen el campo pesado `data`. La fuente de la verdad para los resultados detallados es exclusivamente la colección `analysis_results`. Se han refactorizado los modelos Pydantic y la lógica de actualización para eliminar redundancias y optimizar el tamaño de los documentos.
17. **Carga Secuencial y Exhaustiva (Frontend):** Se ha implementado un sistema de parcheo secuencial para los resultados de análisis en la página de detalles. Esto evita límites de conexión del navegador y garantiza que, tras cada refresco, se obtenga la información detallada de *todos* los análisis completados directamente desde su colección dedicada.
18. **Refresco Silencioso y Eficiente:** El frontend ahora utiliza la API de visibilidad del navegador para realizar refrescos parciales y silenciosos de los análisis cuando el usuario vuelve a la pestaña. Esto mantiene la información actualizada sin interrumpir la experiencia del usuario con pantallas de carga globales.
19. **Gestión de Perfil de Usuario:** Se ha implementado una página de perfil completa (`/profile`) que permite a los usuarios:
    - **Personalización de Identidad:** Cambiar su avatar seleccionando entre una galería predefinida (por defecto se asigna `blue_lizard.png`).
    - **Actualización de Datos:** Modificar su nombre completo (limitado a 30 caracteres). El email permanece protegido como identificador único.
    - **Eliminación Segura de Cuenta:** Un flujo destructivo que elimina al usuario de PostgreSQL y realiza una limpieza exhaustiva de toda su información en propiedad (workspaces, licitaciones, archivos y análisis) en MongoDB antes de cerrar la sesión.
20. **Restricciones de Longitud y Validación:** Se han aplicado límites de caracteres estrictos en todos los niveles (DB, Backend y Frontend) para asegurar la integridad de los datos y la coherencia de la interfaz.

## Arquitectura de Autenticación ("Gold Standard")

La aplicación implementa un flujo de autenticación moderno y seguro, a menudo denominado "Gold Standard", que separa los tokens por su función y limita su exposición. El objetivo es proteger el `refreshToken` (de larga duración) de ataques XSS, mientras se utiliza un `accessToken` (de corta duración) para las operaciones diarias.

Este es el flujo detallado, desde el login hasta la gestión de la sesión:

**1. Proceso de Login**

1.  **Inicio (Frontend)**: El usuario introduce su email y contraseña en el formulario de login. La lógica del `AuthContext` de React llama al endpoint del proxy de Next.js en `/api/auth/login`.
2.  **Proxy de Next.js (BFF)**: La ruta `/api/auth/login` actúa como un intermediario seguro (Backend-for-Frontend). No realiza la autenticación directamente, sino que llama al backend de FastAPI al endpoint `POST /auth/login/json`.
3.  **Validación (Backend FastAPI)**:
    *   El backend recibe las credenciales, las valida contra la base de datos (usando `authenticate_user`) y, si son correctas, genera dos tokens JWT:
        *   Un **`accessToken`** de corta duración (15 minutos).
        *   Un **`refreshToken`** de larga duración (7 días).
4.  **Respuesta del Backend al Proxy**:
    *   El `accessToken` se devuelve en el **cuerpo** de la respuesta JSON.
    *   El `refreshToken` se establece en una **cookie `HttpOnly`, `Secure` y `SameSite=Lax`**. Esto es crucial, ya que el navegador almacenará esta cookie de forma segura y la enviará automáticamente en futuras peticiones, pero será inaccesible para el código JavaScript del cliente.
5.  **Respuesta del Proxy al Cliente**:
    *   El proxy de Next.js recibe la respuesta del backend. **No reenvía el `accessToken` al cliente**.
    *   En su lugar, utiliza el `accessToken` recién obtenido para hacer una segunda llamada al backend, al endpoint `GET /users/me`, para obtener los datos del usuario (ID, nombre, email).
    *   Finalmente, el proxy responde al cliente del navegador con los **datos del usuario** y, lo más importante, **propaga la cookie `Set-Cookie`** que contiene el `refreshToken`.

**2. Establecimiento de la Sesión en el Cliente**

1.  **Recepción de Datos (Frontend)**: El `AuthContext` recibe la respuesta del proxy con los datos del usuario, pero sin ningún token.
2.  **Obtención del Primer `accessToken`**: Inmediatamente después del login exitoso, el `AuthContext` llama a su propia función `refreshToken()`.
3.  **Llamada de Refresco**: La función `refreshToken()` llama al proxy `POST /api/auth/refresh`. Como el navegador ya tiene la cookie `HttpOnly` con el `refreshToken`, la envía automáticamente.
4.  **Generación de Nuevo Token (Backend)**: El backend, a través del proxy, recibe el `refreshToken`, lo valida, y genera un **nuevo `accessToken`**.
5.  **Almacenamiento en Memoria**: El proxy devuelve este nuevo `accessToken` al `AuthContext`, que finalmente lo almacena en el estado de React (en memoria).

A partir de este momento, la aplicación tiene el `accessToken` en memoria para realizar llamadas a la API y el `refreshToken` almacenado de forma segura en una cookie.

**3. Llamadas a la API Autenticadas**

*   Cada vez que el frontend necesita acceder a un recurso protegido, utiliza una utilidad (`useApi`) que toma el `accessToken` del estado del `AuthContext` y lo añade a la cabecera de la petición: `Authorization: Bearer <accessToken>`.
*   El backend valida este `accessToken` en cada llamada para autorizar la operación.

**4. Renovación Automática de la Sesión (Token Refresh)**

*   **Proactiva**: El `AuthContext` tiene un temporizador (`setInterval`) que se ejecuta cada 14 minutos (justo antes de que el `accessToken` de 15 minutos expire) y llama automáticamente a la función `refreshToken()` para obtener un nuevo `accessToken` y mantener la sesión activa sin que el usuario lo note.
*   **Reactiva (Manejo de Errores)**: La utilidad `useApi` también está preparada para interceptar errores `401 Unauthorized`. Si una llamada a la API falla porque el `accessToken` ha expirado justo en el intervalo entre renovaciones, puede intentar llamar a `refreshToken()` una vez y, si tiene éxito, reintentar la llamada original fallida de forma transparente para el usuario.
*   **Rotación de Refresh Tokens**: El endpoint de refresco del backend implementa la rotación de tokens: cada vez que se usa un `refreshToken`, se invalida (añadiéndolo a una lista negra en Redis) y se emite uno nuevo, mejorando aún más la seguridad.

**5. Cierre de Sesión (Logout)**

*   El `logout` llama al endpoint `POST /api/auth/logout`.
*   El backend invalida tanto el `accessToken` como el `refreshToken` (añadiéndolos a la lista negra de Redis) y elimina la cookie del navegador.
*   El frontend borra el usuario y el `accessToken` de su estado, completando el cierre de sesión.


11. **Flujo de Obtención de Resultados de Análisis**: El proceso para obtener y mostrar los resultados de los análisis en la página de una licitación (`/space/{spaceId}/tender/{tenderId}`) es un flujo de varios pasos que combina la obtención de datos iniciales con un enriquecimiento posterior ("parcheo") de la información.
    1.  **Carga Inicial de Datos (Frontend)**:
        *   Cuando la página de la licitación se carga, el componente principal (`TenderAnalysisPage`) lanza una serie de llamadas a la API del backend de forma paralela.
        *   La llamada más importante es a `GET /tenders/{tenderId}`. Esta petición obtiene el documento principal de la licitación desde la base de datos MongoDB.
        *   Este documento de la licitación contiene una lista (`analysis_results`) con los metadatos de todos los análisis que se han ejecutado para esa licitación. Para optimizar el rendimiento y reducir el tamaño de la respuesta inicial, los resultados de análisis que están en estado `"completed"` **no incluyen el campo `data`** (que contiene los JSONs con el detalle del análisis), devolviéndolo como `null`.
    2.  **Enriquecimiento de Datos o "Parcheo" (Frontend)**:
        *   Una vez que el frontend recibe los datos iniciales, recorre la lista `analysis_results`.
        *   Por cada resultado que tiene el estado `"completed"` pero su campo `data` es `null`, el frontend realiza una **segunda llamada** a la API, esta vez a un endpoint específico: `GET /analysis-results/{analysis.id}`.
        *   Esta segunda petición está diseñada para obtener exclusivamente los datos completos de un único resultado de análisis, incluyendo el campo `data` que faltaba.
        *   El frontend "parchea" la lista original, reemplazando los resultados incompletos con la versión completa que acaba de obtener.
    3.  **Renderizado del Componente de Visualización (Frontend)**:
        *   La lista de resultados de análisis, ya enriquecida, se pasa al componente `AnalysisDisplay`.
        *   Este componente itera sobre la lista y crea un acordeón desplegable para cada resultado.
        *   El contenido de cada acordeón depende del estado del análisis:
            *   Si el estado es `"pending"` o `"processing"`, muestra un mensaje indicando que el análisis está en curso.
            *   Si el estado es `"failed"`, muestra un mensaje de error.
            *   Si el estado es `"completed"` y el campo `data` (obtenido en el paso de "parcheo") existe, se renderiza el componente `DynamicSummary`, que muestra de forma estructurada toda la información contenida en los JSONs del análisis.
    4.  **Actualización en Tiempo Real (Backend y Frontend)**:
        *   Para los análisis que están en estado `"pending"` o `"processing"`, el frontend abre una conexión **WebSocket** con el backend.
        *   Cuando el backend termina de procesar un análisis (ya sea con éxito o con error), envía un mensaje a través del WebSocket.
        *   Al recibir este mensaje, el frontend es notificado e **inicia de nuevo todo el proceso de recarga de datos** (vuelve al paso 1) para obtener la información más reciente y reflejar el nuevo estado del análisis.

        En esencia, es un sistema de **carga en dos fases**: primero se obtiene una vista general y ligera de todos los análisis, y luego se cargan los detalles pesados (el `data`) bajo demanda solo para aquellos que ya han finalizado, optimizando así la velocidad de carga inicial de la página.
    
    ## Restricciones de Longitud (Validación Multi-Nivel)
    
    Para garantizar la integridad de los datos y una interfaz de usuario limpia, se aplican los siguientes límites de caracteres en la base de datos, los esquemas de Pydantic y los campos de entrada del frontend:
    
    ### **Usuarios (PostgreSQL)**
    - **Nombre completo:** Máximo **50 caracteres**.
    - **Email:** Máximo **255 caracteres** (estándar).
    
    ### **Workspaces (PostgreSQL)**
    - **Nombre:** Máximo **50 caracteres**.
    - **Descripción:** Máximo **500 caracteres**.
    
    ### **Licitaciones (MongoDB)**
    - **Nombre:** Máximo **255 caracteres**.
    - **Descripción:** Máximo **1000 caracteres**.
    
    ### **Análisis (MongoDB)**
    - **Nombre (General):** Máximo **255 caracteres**.
    - **Nombre (Vista de resultados):** Máximo **50 caracteres**.    
    ## Reglas de Oro (Instrucciones para Gemini)
1. Siempre responde en español.
2. Usa tipado estricto si usamos TypeScript.
3. No sugieras librerías obsoletas.
4. Usa siempre el estándar de tipado `Tipo | None` en Python (PEP 604).
5. Mantén la documentación de los endpoints actualizada.
6. Siempre que se modifique, añada o elimine un endpoint, tanto en back como en front, se deben modificar los archivos `GEMINI.md` y `README.md`.

---