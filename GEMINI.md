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
5. **Estrategia de Seguridad de Tokens (Revisada):** Se ha implementado una arquitectura de autenticación "Gold Standard". El `accessToken` (efímero, 15m) se almacena únicamente en la memoria del frontend (React Context) para autorizar las peticiones a la API. El `refreshToken` (larga duración, 7 días) se almacena en una cookie `HttpOnly`, `Secure` y `SameSite=Lax`, haciéndolo inaccesible a ataques XSS. Tras el login/signup, el frontend solo recibe los datos del usuario; inmediatamente después, utiliza la cookie `HttpOnly` para obtener el `accessToken` inicial, evitando la exposición de tokens en el cuerpo de la respuesta. Las API Routes de Next.js actúan como un proxy seguro para gestionar y propagar estas cookies.
6. **Invalidación de Tokens (Redis Blacklist):** Uso de Redis para invalidar inmediatamente tokens durante el logout o rotación, garantizando que un token robado no pueda ser reutilizado.
7. **Preparación para el Chatbot:** La estructura de auditoría y workspaces está diseñada para integrarse con los flujos de automatización y el chatbot futuro.
8. **Generación de Análisis Asíncrono:** Se ha implementado un flujo de generación de análisis asíncrono con notificaciones en tiempo real vía WebSockets. El frontend puede iniciar una tarea de análisis y, en lugar de esperar, recibe una respuesta inmediata. El estado y el resultado final de la tarea son enviados al frontend a través de un WebSocket, eliminando la necesidad de polling.
9. **Gestión de Automatismos:** Se ha creado una nueva tabla `autos` en PostgreSQL para almacenar información sobre los automatismos (como webhooks de n8n) y un endpoint para gestionarlos.
10. **Modelos de Datos Flexibles:** Los modelos de Pydantic se han actualizado para soportar estructuras de datos más complejas en los resultados de los análisis, incluyendo un nuevo JSON `estimacion`.

### Arquitectura de Autenticación ("Gold Standard")

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
- **Refactorización Crítica de Autenticación:**
    - Se ha refactorizado completamente el flujo de autenticación para seguir las mejores prácticas de seguridad ("Gold Standard"). El `accessToken` ya no se expone en el cuerpo de las respuestas de login/signup, mitigando riesgos de XSS.
    - Se ha solucionado una condición de carrera (`race condition`) que provocaba un error `401 Unauthorized` al intentar refrescar el token inmediatamente después del login. El `AuthContext` ahora gestiona el ciclo de vida del token de forma robusta.
    - Se ha corregido el reenvío de cookies en las API Routes de Next.js para garantizar que el `refreshToken` se propague correctamente entre el navegador, el servidor de Next.js y el backend de FastAPI.
- **Corrección de Autenticación (Previa):**
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