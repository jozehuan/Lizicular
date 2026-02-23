
# Lizicular

## Introducción

**Lizicular** es una plataforma web integral de nivel empresarial, diseñada para transformar la manera en que las organizaciones gestionan los procesos de licitaciones públicas y privadas. La aplicación centraliza la información, automatiza tareas repetitivas y potencia la colaboración en equipo, abordando los desafíos comunes de la descentralización de documentos y la falta de trazabilidad.

El objetivo principal de Lizicular es proporcionar un entorno unificado y seguro donde los equipos puedan:
- **Centralizar y Colaborar**: A través de **espacios de trabajo (`Workspaces`)**, los equipos pueden organizar licitaciones, gestionar documentos y controlar el acceso mediante un sistema de roles (RBAC), asegurando que cada miembro tenga los permisos adecuados.
- **Automatizar el Análisis**: La plataforma se integra con flujos de trabajo externos (construidos en n8n) que automatizan el procesamiento y análisis de los documentos de las licitaciones, extrayendo información clave y generando resultados estructurados.
- **Interactuar con Inteligencia Artificial**: Un **agente conversacional (chatbot)**, impulsado por modelos de lenguaje avanzados, permite a los usuarios consultar el estado de sus licitaciones, buscar información y obtener resúmenes utilizando lenguaje natural.
- **Garantizar la Seguridad y Auditoría**: La arquitectura de autenticación "Gold Standard" y un sistema de **auditoría universal** registran cada acción importante, proporcionando un alto nivel de seguridad y cumplimiento normativo.

En esencia, Lizicular es la herramienta definitiva para equipos que buscan optimizar su flujo de trabajo en la gestión de licitaciones, aumentando la eficiencia y reduciendo errores manuales.

## Detalles del Proyecto

La presentación es un Power Point, el cual está dentro de este repositorio, en la rama develop. El archivo se llama "presentacion.pptx". 

El proyecto que se presenta es el contenido en la rama develop.

## Cómo iniciar la aplicación

Sigue estos pasos para configurar y ejecutar el entorno de desarrollo completo en tu máquina local.

**Pre-requisitos:**
*   Python 3.11 o superior.
*   Node.js (v18 o superior) con `pnpm` como gestor de paquetes.
*   Docker y Docker Compose.

### 1. Configuración del Backend

Primero, configura el entorno virtual y las dependencias del backend.

```bash
# Crea un entorno virtual (Python 3.11)
python3 -m venv .venv

# Activa el entorno virtual
# En macOS/Linux:
source .venv/bin/activate
# En Windows:
# .\.venv\Scripts\activate

# Instala las dependencias de Python
pip install -r requirements.txt
```

### 2. Configuración del Frontend

Ahora, instala las dependencias del frontend usando `pnpm`.

```bash
# Navega a la carpeta del frontend
cd frontend

# Instala las dependencias de Node.js
pnpm install
```

### 3. Configuración de Variables de Entorno

La aplicación necesita archivos `.env` para funcionar.

*   **Para el Backend:** En la **raíz del proyecto**, copia el archivo de ejemplo y rellena las credenciales.
    ```bash
    # Desde la raíz del proyecto
    cp .env.example .env
    ```
    Asegúrate de configurar todas las variables (`DATABASE_URL`, `REDIS_URL`, `MONGODB_URL`, ...) y las claves secretas (`SECRET_KEY`, etc.) dentro de este nuevo archivo `.env`.

*   **Para el Frontend:** Crea un archivo `.env.local` en la carpeta `frontend`.
    ```bash
    # Dentro de la carpeta frontend/
    touch .env.local
    ```
    Añade las siguientes variables, apuntando a la URL donde correrá tu backend:
    ```
    NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
    BACKEND_URL=http://localhost:8000
    ```

### 4. Iniciar Servicios de Infraestructura

Levanta las bases de datos y Redis usando Docker Compose.

```bash
# Desde la raíz del proyecto, asegúrate de que Docker Desktop está en ejecución
docker compose up -d
```
Este comando iniciará los contenedores de PostgreSQL, MongoDB y Redis en segundo plano.

### 5. Ejecutar la Aplicación

Finalmente, inicia los servidores de desarrollo del backend y el frontend en dos terminales separadas.

*   **Terminal 1: Iniciar Backend (FastAPI)**
    ```bash
    # Desde la raíz, inicia el servidor de desarrollo
    uvicorn backend.main:app --reload
    ```

*   **Terminal 2: Iniciar Frontend (Next.js)**
    ```bash
    # Desde la raíz, navega a la carpeta del frontend
    cd frontend

    # Inicia el servidor de desarrollo
    pnpm dev
    ```

¡Listo! Ahora puedes acceder a la aplicación frontend (normalmente en `http://localhost:3000`) y la API del backend estará disponible en `http://localhost:8000`.

## Aviso sobre Ramas y Despliegue

> **Importante:** La versión del código que se describe en este documento corresponde a la rama **`develop`** del repositorio, destinada al desarrollo local.
>
> Existen otras ramas con configuraciones específicas para el despliegue:
> *   **`LIZ-19`**: Contiene una versión de la aplicación preparada para el despliegue automático mediante **GitHub Actions**.
> *   **`main`**: Es una extensión de `develop` adaptada para el **despliegue manual** en un servidor.
>
> Ambas ramas se utilizan para desplegar una versión de *staging* de la aplicación en un servidor de **Oracle Cloud**.
>
> ### Entorno de Staging
>
> Se ha habilitado un entorno de *staging* público donde la aplicación está funcional. Es la forma más sencilla de probar todas las características sin necesidad de configuración local.
>
> *   **URL de Acceso:** [**http://130.110.240.99/**](http://130.110.240.99/)
>
> En este entorno de staging, tanto el **chatbot** como los **automatismos de n8n** están completamente operativos y pueden ser utilizados directamente, eliminando la necesidad de configurar las claves de API de Azure, Langfuse o los webhooks de n8n en el entorno local.
>
> Como pruebas, se ha habilitado un usuario (user: big_school@gmail.com / password: bigschool1234) que tiene acceso a un workspace pre-cargado con un licitación y documentos, lo que permite experimentar todas las funcionalidades de la aplicación, incluyendo el análisis de licitaciones y la interacción con el chatbot.

## Herramientas de IA Utilizadas

El desarrollo de Lizicular ha sido realizado mediante el uso de herramientas de Inteligencia Artificial, cada una cumpliendo un rol específico en el ciclo de vida del proyecto.

### Desarrollo Principal: Gemini CLI

Gemini CLI ha sido el motor principal para la arquitectura del software y la implementación de lógica avanzada, funcionando como un asistente de co-programación de alto nivel.

-   **Gestión de Contexto**: Se ha utilizado un archivo `GEMINI.md` para proporcionar un contexto persistente y detallado de la aplicación a través de diferentes sesiones de desarrollo. Esto ha permitido a Gemini mantener una comprensión profunda de la arquitectura, los modelos de datos y los objetivos del proyecto, asegurando la coherencia en sus contribuciones.
-   **Modelos Utilizados**: Principalmente `Gemini 2.5 Pro` y `Gemini 2.5 Flash`.
-   **Impacto en el Backend**: Ha sido fundamental para la definición y refactorización de los modelos de Pydantic y SQLAlchemy. Su capacidad para entender la relación entre los esquemas de la API y los modelos de la base de datos ha garantizado validaciones de datos robustas y una gestión de cambios coherente.
-   **Impacto General**: Más allá del código, se ha utilizado para analizar la viabilidad de nuevas ideas, cooperar en el diseño de arquitecturas complejas (como el flujo de autenticación "Gold Standard" o la arquitectura de datos, por ejemplo) y refactorizar lógica de negocio.

### Co-programación y Calidad de Código

Para agilizar el desarrollo diario y mantener altos estándares de calidad, se han integrado varias herramientas directamente en el entorno de desarrollo y el flujo de trabajo de Git.

-   **GitHub Copilot**: Ha funcionado como un asistente en el IDE (VSCode), agilizando la escritura de código manual, autocompletando patrones repetitivos y reduciendo el *boilerplate*, lo que ha permitido al desarrollador centrarse en la lógica de negocio.
-   **CodeRabbit (Reviewer IA)**: Integrado en el repositorio de GitHub para realizar un análisis automático y crítico de los *Pull Requests* (PRs). Revisa los cambios propuestos, sugiere mejoras, detecta posibles errores y asegura que el código nuevo se alinee con las convenciones del proyecto antes de ser fusionado.
-   **Copilot Actions**: Utilizado para automatizar la documentación de los *Pull Requests*, generando resúmenes del impacto de los cambios. Esto ha mejorado significativamente la trazabilidad y la comprensión del historial del proyecto.

### Prototipado Rápido y Diseño Visual

-   **Prototipado con V0**: En las fases iniciales del proyecto, se utilizó V0 para generar rápidamente componentes de interfaz de usuario basados en prompts. Esto permitió crear un prototipo (MVP) visualmente sólido sobre **React, Next.js y Tailwind CSS**, que sirvió como una base excelente para definir la estructura y el diseño del frontend final.
-   **Identidad Visual con Nano Banana**: Para superar los diseños genéricos de los prototipos, se utilizó Nano Banana para la creación de una identidad visual coherente. Esto incluye logotipos, e iconografía (como los avatares), que han dotado a la aplicación de un aspecto profesional y realista desde el desarrollo temprano.

### Automatización y Lógica de Negocio

-   **Workflows de n8n con IA**: La lógica de negocio más compleja, como la extracción de datos de documentos de licitaciones, se ha implementado en flujos de trabajo de **n8n**. Dentro de estos flujos, se utiliza **Gemini** para interpretar el contenido, filtrar información relevante basada en parámetros dinámicos y estructurar los resultados.

### Agente Conversacional y Trazabilidad

-   **Chatbot con LlamaIndex**: El agente conversacional de la aplicación se ha construido utilizando el framework LlamaIndex, que permite orquestar las interacciones entre el LLM, las herramientas personalizadas (como la capacidad de consultar la propia API de la aplicación) y la base de conocimientos.
-   **Trazabilidad con LangFuse**: Cada conversación y cada "pensamiento" del agente se registra y monitoriza con LangFuse. Esto proporciona una trazabilidad completa, esencial para depurar el comportamiento del agente, entender sus decisiones y mejorar su rendimiento.

> #### Estado Actual de la IA
>
> Actualmente, el prototipo es funcional en el entorno local para la captura y gestión de datos. Los modelos utilizados en las fases de testing, como `Gemini 1.5 Flash`, se encuentran en estado de "Preview".
>
> *   **Nota técnica**: Se monitoriza activamente la tasa de saturación y las cuotas de uso de estos modelos. Al estar en fase de preview, pueden ser sensibles a fallos o latencias, especialmente con cargas de trabajo pesadas.

## Stack Tecnológico

La aplicación sigue una arquitectura de microservicios orquestada con Docker, separando claramente el backend del frontend.

### Backend

*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) sobre [Uvicorn](https://www.uvicorn.org/) para un alto rendimiento en I/O.
*   **Lenguaje**: Python 3.10+
*   **Base de Datos Relacional (Identidad y Auditoría)**: [PostgreSQL](https://www.postgresql.org/) con [SQLAlchemy](https://www.sqlalchemy.org/) (para el ORM) y `asyncpg` (para acceso asíncrono).
*   **Base de Datos NoSQL (Datos de Negocio)**: [MongoDB](https://www.mongodb.com/) para almacenar licitaciones, documentos y resultados de análisis, accedido con `motor`.
*   **Caché y Mensajería**: [Redis](https://redis.io/) para la gestión de listas negras de tokens y otros almacenamientos temporales.
*   **Autenticación**: JWT (`python-jose`) y OAuth2, con hashing de contraseñas mediante `passlib` y `bcrypt`.
*   **Validación de Datos**: [Pydantic](https.pydantic.dev) v2 para un tipado estricto y validación de modelos.
*   **Inteligencia Artificial**:
    *   **Orquestación**: [LlamaIndex](https://www.llamaindex.ai/) para la coordinación del agente de IA.
    *   **Motor de IA**: Integrado con [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service).
    *   **Observabilidad**: [Langfuse](https://langfuse.com/) para el seguimiento y depuración de las interacciones del chatbot.

### Frontend

*   **Framework**: [Next.js](https://nextjs.org/) con el App Router.
*   **Lenguaje**: [TypeScript](https://www.typescriptlang.org/).
*   **Librería UI**: [React](https://react.dev/).
*   **Estilos**: [Tailwind CSS](https://tailwindcss.com/) para un diseño basado en utilidades.
*   **Componentes UI**: Construido sobre [Shadcn/UI](https://ui.shadcn.com/), utilizando primitivas de Radix UI.
*   **Internacionalización (i18n)**: `next-intl` para soportar múltiples idiomas.
*   **Pruebas E2E**: [Playwright](https://playwright.dev/).

### Infraestructura

*   **Orquestación Local**: [Docker Compose](https://docs.docker.com/compose/) para definir y ejecutar el entorno de desarrollo multi-contenedor.

## Estructura del Proyecto

A continuación se detalla la estructura de directorios y el propósito de los archivos más importantes del proyecto.

```
/
├── docker-compose.yml      # Orquesta los servicios de infraestructura (PostgreSQL, Redis, MongoDB).
├── requirements.txt        # Dependencias de Python para el backend.
│
├── backend/                  # Contenedor del código de la API de FastAPI.
│   ├── main.py               # Punto de entrada de FastAPI, monta los routers de los módulos.
│   │
│   ├── auth/                 # Módulo para autenticación, autorización y gestión de usuarios.
│   │   ├── routes.py         # Endpoints para login, registro, OAuth2 y perfil de usuario.
│   │   ├── auth_utils.py     # Utilidades para crear/validar tokens JWT y hashear contraseñas.
│   │   ├── models.py         # Modelos de BBDD (SQLAlchemy) para Usuarios y Logs de Auditoría.
│   │   └── schemas.py        # Esquemas Pydantic para validación de datos en los endpoints.
│   │
│   ├── workspaces/           # Módulo para la gestión de espacios de trabajo colaborativos.
│   │   ├── routes.py         # Endpoints CRUD para workspaces y la gestión de sus miembros.
│   │   └── models.py         # Modelos de BBDD para Workspaces y sus relaciones.
│   │
│   ├── tenders/              # Módulo para la gestión de licitaciones y sus documentos.
│   │   ├── routes.py         # Endpoints para el CRUD de licitaciones, documentos y análisis.
│   │   └── tenders_utils.py  # Lógica de negocio para interactuar con la colección de MongoDB.
│   │
│   ├── automations/          # Módulo para la gestión y ejecución de automatismos.
│   │   ├── routes.py         # Endpoints para disparar y gestionar automatismos (webhooks).
│   │   └── websocket/        # Lógica para notificaciones en tiempo real vía WebSockets.
│   │
│   ├── chatbot/              # Módulo para el agente conversacional de IA.
│   │   ├── routes.py         # Define el endpoint /chat para interactuar con el bot.
│   │   ├── chat_bot_controller.py # Orquesta la lógica y el flujo de la conversación.
│   │   └── agents/           # Contiene los "agentes" (herramientas) que el chatbot puede usar.
│   │
│   └── tests/                # Suite de pruebas de integración con Pytest.
│       └── test_*.py         # Archivos de prueba para cada módulo (auth, workspaces, etc.).
│
└── frontend/                 # Contenedor de la aplicación Next.js (interfaz de usuario).
    ├── package.json          # Dependencias de JavaScript y scripts (dev, build, test).
    ├── next.config.mjs       # Configuración de Next.js, incluyendo el proxy de API a backend.
    ├── tsconfig.json         # Configuración del compilador de TypeScript y alias de rutas (`@/*`).
    │
    ├── app/                  # Directorio principal del App Router de Next.js.
    │   ├── [locale]/           # Enrutamiento dinámico para internacionalización (i18n).
    │   │   ├── layout.tsx      # Layout principal que envuelve todas las páginas de la aplicación.
    │   │   ├── page.tsx        # Página de inicio (renderiza el formulario de login/registro).
    │   │   ├── dashboard/      # Páginas y componentes del panel de control del usuario.
    │   │   └── space/          # Páginas para la vista detallada de un workspace y sus licitaciones.
    │   │
    │   └── api/              # Route Handlers que actúan como un BFF (Backend-for-Frontend).
    │       └── auth/         # Orquestan el flujo de autenticación (login, refresh, logout).
    │
    ├── components/           # Componentes de React reutilizables.
    │   ├── ui/               # Componentes de bajo nivel de Shadcn/UI (Button, Card, Input...).
    │   ├── layout/           # Componentes de estructura de página (Header, Sidebar, Footer...).
    │   └── auth/             # Componentes específicos de autenticación (ej. AuthForm).
    │
    ├── hooks/                # Hooks personalizados de React (ej. useApi, useToast).
    │
    ├── e2e/                  # Pruebas End-to-End con Playwright.
    │   └── *.spec.ts         # Escenarios de prueba para flujos críticos (auth, tenders, etc.).
    │
    ├── messages/             # Archivos JSON con las traducciones para i18n (`en.json`, `es.json`).
    │
    └── public/               # Contiene todos los archivos estáticos (imágenes, fuentes, etc.).

```

## Automatismos (Workflows n8n)

> **Nota sobre la Lógica de Negocio**
>
> Una parte fundamental de la lógica de negocio de Lizicular, especialmente la relacionada con el procesamiento y análisis de documentos, se gestiona a través de workflows externos construidos en **n8n**.
>
> Estos flujos de trabajo son propiedad intelectual de la empresa **NAZARIES INTELLIGENIA** y, por motivos de confidencialidad, su definición y código no se incluyen en este repositorio público. LA autoría de este código es la misma que la de este proyecto, es decir, yo JOSE JUAN MORALES OLIVER, declaro que soy el autor tanto de este proyecto como de los workflows de n8n, pero solo el código de este repositorio es público y compartido, mientras que el de n8n permanece privado. Cualquier referencia a la funcionalidad de estos automatismos en la documentación se hace de manera descriptiva, sin revelar detalles técnicos o lógicos específicos.
>
> **Implicaciones para el Entorno Local:**
> *   La funcionalidad de ejecutar un análisis sobre una licitación **no operará en el entorno de desarrollo local**, ya que los webhooks configurados en la base de datos apuntan a endpoints privados.
> *   Sin embargo, si fuera necesario para una evaluación, el código de dichos flujos de trabajo puede ser mostrado y explicado sin problema.
>
> **Entorno de Staging para Demostración:**
> Para permitir la prueba y validación de esta funcionalidad, se ha habilitado un entorno de *staging* completamente funcional.
> *   **URL de Staging:** [**http://130.110.240.99/**](http://130.110.240.99/)
>
> **Aviso sobre los Modelos LLM en Staging:**
> Los modelos de lenguaje (LLM) que se utilizan actualmente en los automatismos de este entorno de pruebas son `gemini-2.5-flash`. Debido a que es una versión de prueba, estos modelos pueden saturarse o experimentar demoras, especialmente al procesar archivos de gran tamaño.

## Pruebas (Testing)

La aplicación cuenta con una robusta estrategia de testing que combina pruebas de backend y frontend para garantizar la calidad, seguridad y estabilidad del código.

### Backend (Pytest)
Suite exhaustiva de pruebas unitarias y de integración para validar la lógica de negocio, seguridad y endpoints.

-   **`test_auth.py`**: Autenticación, gestión de sesiones y perfil de usuario.
-   **`test_workspaces.py`**: CRUD de espacios y control de acceso (RBAC).
-   **`test_tenders.py`**: Gestión de licitaciones, documentos y permisos.
-   **`test_automations.py`**: Creación y listado de automatismos.
-   **`test_chatbot.py`**: Interacción segura con el agente conversacional.

### Frontend (Playwright)
Pruebas End-to-End (E2E) que simulan el comportamiento real del usuario en el navegador.

-   **`auth.spec.ts`**: Flujos de registro e inicio de sesión.
-   **`dashboard.spec.ts`**: Navegación y creación de espacios.
-   **`profile.spec.ts`**: Edición de perfil y avatar.
-   **`tenders.spec.ts`**: Creación de licitaciones.

### Herramientas Complementarias
-   **Postman**: Colecciones para validación manual y documentación interactiva de la API. Permite probar endpoints individualmente y compartir ejemplos de peticiones.

## Autenticación y Seguridad (Arquitectura "Gold Standard")

La aplicación implementa un flujo de autenticación moderno y seguro, a menudo denominado "Gold Standard", que separa los tokens por su función y limita su exposición para mitigar ataques como XSS y CSRF. El objetivo es proteger el `refreshToken` (de larga duración) de ser accesible por JavaScript, mientras se utiliza un `accessToken` (de corta duración) para las operaciones diarias.

El flujo se orquesta entre tres actores principales: el **Cliente** (navegador), el **BFF** (Backend-for-Frontend, las rutas API de Next.js) y el **Backend** (API de FastAPI).

### Flujo de Login

1.  **Cliente → BFF**: El usuario envía su email y contraseña al endpoint del proxy de Next.js (`/api/auth/login`).
2.  **BFF → Backend**: El proxy reenvía estas credenciales al backend de FastAPI (`/auth/login/json`).
3.  **Respuesta del Backend al BFF**: El backend valida las credenciales. Si son correctas, responde con dos cosas:
    *   Un `accessToken` (corta duración, ~15 min) en el **cuerpo de la respuesta JSON**.
    *   Un `refreshToken` (larga duración, ~7 días) en una **cookie `HttpOnly`, `Secure` y `SameSite=Lax`**.
4.  **Procesamiento en el BFF**: El proxy de Next.js recibe esta respuesta. **No reenvía el `accessToken` al cliente**. En su lugar, lo usa para hacer una llamada interna al endpoint `/users/me` del backend para obtener los datos del perfil del usuario.
5.  **Respuesta del BFF al Cliente**: El proxy responde al navegador con los datos del usuario en el cuerpo JSON y, crucialmente, **propaga la cookie `Set-Cookie`** que contiene el `refreshToken`. El navegador la almacena de forma segura, inaccesible para el código JavaScript.

### Establecimiento de la Sesión

1.  **El cliente NO tiene tokens**: Tras el login, el `AuthContext` de React solo tiene los datos del usuario, pero ningún token en memoria.
2.  **Primera llamada de refresco**: Inmediatamente, el cliente realiza una llamada a `/api/auth/refresh`. El navegador adjunta automáticamente la cookie `HttpOnly` con el `refreshToken`.
3.  **Generación del primer `accessToken`**: El BFF recibe la petición, la reenvía al backend, que valida el `refreshToken` y genera un nuevo `accessToken`.
4.  **Almacenamiento en Memoria**: El BFF devuelve este `accessToken` al cliente, que finalmente lo almacena en el estado de React (en memoria). A partir de este momento, la aplicación está lista para hacer llamadas a la API.

### Llamadas a la API Autenticadas

*   Para acceder a un recurso protegido, el frontend (a través de un hook como `useApi`) coge el `accessToken` de la memoria y lo añade a la cabecera `Authorization: Bearer <token>` de la petición.
*   El backend valida este `accessToken` en cada llamada.

### Renovación de la Sesión (Token Refresh)

*   **Proactiva**: Un temporizador en el `AuthContext` de React llama a la función de refresco (paso 2 de "Establecimiento de la Sesión") cada ~14 minutos para obtener un nuevo `accessToken` antes de que el antiguo expire.
*   **Rotación de Refresh Tokens**: Para mayor seguridad, cada vez que se usa un `refreshToken`, el backend lo invalida (añadiéndolo a una lista negra en Redis) y emite uno nuevo en la cookie de respuesta. Esto previene que un `refreshToken` robado pueda ser reutilizado indefinidamente.

### Cierre de Sesión (Logout)

*   El cliente llama a `/api/auth/logout`.
*   El backend recibe la llamada (con el `accessToken` en la cabecera y el `refreshToken` en la cookie), invalida ambos tokens en la lista negra de Redis y responde instruyendo al navegador para que elimine la cookie.
*   El frontend borra los datos de usuario y el token de su estado en memoria.

## Arquitectura de Datos

La aplicación utiliza un enfoque de persistencia políglota, combinando una base de datos relacional (PostgreSQL) y una base de datos documental (MongoDB) para aprovechar las fortalezas de cada una.

### PostgreSQL (Identidad, Permisos y Auditoría)

PostgreSQL es la fuente de la verdad para todos los datos relacionales y estructurados que requieren consistencia transaccional (ACID). Su esquema está gestionado por SQLAlchemy.

*   **Propósito**: Almacenar datos de identidad de usuario, control de acceso, configuración y un registro inmutable de auditoría.
*   **Tablas Principales**:
    *   `users`: Contiene la información de cada usuario, incluyendo su email, contraseña hasheada (para login local), y datos de perfil como el nombre y el avatar. También almacena información de proveedores OAuth si el usuario se registra con un tercero.
    *   `workspaces`: Define los espacios de trabajo colaborativos. Cada workspace tiene un propietario (`owner_id`) y un nombre.
    *   `workspace_members`: Tabla asociativa que conecta a los usuarios (`user_id`) con los workspaces (`workspace_id`) y les asigna un rol (`OWNER`, `ADMIN`, `EDITOR`, `VIEWER`), definiendo así sus permisos.
    *   `autos`: Un catálogo que almacena la información de los automatismos disponibles en el sistema, como su nombre, descripción y la URL del webhook a la que deben llamar.
    *   `audit_logs`: Una tabla universal que registra cada acción significativa que ocurre en la aplicación (login, creación de un workspace, eliminación de un documento, etc.). Almacena quién hizo qué, cuándo, sobre qué recurso y si la operación fue exitosa, proporcionando una trazabilidad completa.

### MongoDB (Datos de Negocio y Contenido)

MongoDB se utiliza para los datos de negocio principales, que son semi-estructurados, pueden crecer mucho en tamaño y se benefician de un esquema flexible. La arquitectura está diseñada para ser eficiente y escalable.

*   **Propósito**: Almacenar los datos operativos de las licitaciones, los archivos binarios y los resultados detallados y dinámicos de los análisis.
*   **Colecciones Principales**:
    1.  **`tenders`**: Es la colección central. Cada documento representa una única licitación y actúa como el contenedor principal de metadatos (nombre, descripción, ID del workspace, etc.). Contiene dos arrays importantes:
        *   `documents`: Un array de sub-documentos con los **metadatos** de los archivos subidos (nombre, tipo, tamaño), pero no su contenido binario.
        *   `analysis_results`: Un array de **resúmenes** de los análisis ejecutados, conteniendo metadatos como el estado, el nombre y la fecha de creación.
    2.  **`tender_files`**: Almacena el **contenido binario** (en formato BSON) de todos los archivos que se suben. Cada documento aquí es referenciado por el `id` de un sub-documento en el array `documents` de un `tender`. Esto evita sobrecargar los documentos de la colección `tenders` con datos pesados.
    3.  **`analysis_results`**: Almacena los documentos JSON **completos y detallados** generados por los automatismos. La estructura de un documento en esta colección es completamente **dinámica y flexible**, ya que depende de lo que cada automatismo específico extraiga y devuelva. Esta es la fuente de la verdad para el contenido detallado de un análisis.

## Chatbot (Agente Conversacional)

La aplicación incluye un agente de IA conversacional avanzado, construido sobre LlamaIndex, que permite a los usuarios interactuar con sus datos (workspaces, licitaciones, etc.) mediante lenguaje natural.

> **Aviso Importante**
> La funcionalidad del chatbot **no estará disponible** si no se configuran las siguientes variables de entorno en el archivo `.env` principal:
> *   `AZURE_OPENAI_API_KEY`
> *   `AZURE_OPENAI_ENDPOINT`
> *   `OPENAI_API_VERSION`
> *   `LANGFUSE_SECRET_KEY`
> *   `LANGFUSE_PUBLIC_KEY`

### Arquitectura Modular

El chatbot está diseñado con una arquitectura modular y extensible que facilita la adición de nuevas capacidades.

1.  **Meta-Agente y Herramientas (Tools)**: El sistema se basa en un "meta-agente" principal que no responde directamente, sino que utiliza un conjunto de "herramientas" (otros agentes especializados) para realizar tareas. Esto le permite decidir qué herramienta es la más adecuada para una pregunta específica.

2.  **Agente de Revisión (`ReviewAgent`)**: Es una herramienta clave que le da al chatbot la capacidad de "ver" los datos del usuario. Este agente está programado para hacer llamadas seguras a la propia API del backend, permitiéndole consultar información sobre los workspaces, licitaciones y análisis del usuario que está realizando la pregunta.

3.  **Orquestación y Fábricas (`BotManager` y `AgentFactory`)**: El `BotManager` es responsable de construir el agente principal en el arranque de la aplicación. Utiliza una `AgentFactory` para descubrir y registrar dinámicamente todas las herramientas (agentes) disponibles, lo que permite añadir nuevas capacidades sin modificar el núcleo del controlador del chat.

### Motor de IA y Observabilidad

*   **Motor de IA Flexible**: El sistema utiliza una `EngineAIFactory` para desacoplar la lógica del agente del motor de lenguaje (LLM) subyacente. Actualmente, está configurado para usar **Azure OpenAI**, pero la arquitectura permite cambiar a otros proveedores en el futuro.
*   **Observabilidad con Langfuse**: Todas las interacciones con el chatbot, incluyendo las decisiones del agente, las llamadas a herramientas y los errores, se trazan y registran en **Langfuse**. Esto proporciona una visibilidad completa del "proceso de pensamiento" del agente, lo cual es crucial para la depuración y la mejora continua.

### Flujo de Interacción

1.  El usuario envía un mensaje a través de la interfaz de chat.
2.  La petición llega al endpoint protegido `/chatbot/chat`, que autentica al usuario.
3.  El `ChatBotController` recibe el mensaje y lo pasa al `BotManager`.
4.  El agente principal analiza la pregunta y decide si puede responder directamente o si necesita usar una herramienta (por ejemplo, el `ReviewAgent` para buscar licitaciones).
5.  Si se usa una herramienta, esta ejecuta su lógica (ej. llamar a la API) y devuelve el resultado al agente principal.
6.  El agente utiliza esta nueva información para formular una respuesta final y la devuelve al usuario.
7.  Toda la secuencia queda registrada como una traza en Langfuse.

## API Endpoints

A continuación se detallan los principales endpoints expuestos por la API de FastAPI. La mayoría de los endpoints requieren autenticación mediante un `accessToken` de tipo Bearer.

---

### Autenticación y Usuarios (`/auth`, `/users`)

*   `POST /auth/signup`: Registro de un nuevo usuario con email y contraseña.
*   `POST /auth/login/json`: Autentifica a un usuario con un cuerpo JSON y devuelve un `accessToken` y una cookie `refreshToken`.
*   `POST /auth/refresh`: Renueva el `accessToken` utilizando el `refreshToken` almacenado en la cookie `HttpOnly`. Implementa rotación de tokens.
*   `POST /auth/logout`: Cierra la sesión, invalidando tanto el `accessToken` como el `refreshToken` en Redis y eliminando la cookie.
*   `GET /auth/providers`: Devuelve una lista de los proveedores OAuth2 habilitados en la configuración.
*   `GET /auth/oauth/{provider}/login`: Inicia el flujo de autenticación con un proveedor OAuth2 (ej. Google, GitHub).
*   `GET /auth/oauth/{provider}/callback`: Endpoint al que el proveedor OAuth2 redirige tras la autorización del usuario.
*   `GET /users/me`: Devuelve la información del perfil del usuario autenticado.
*   `PATCH /users/me`: Permite al usuario autenticado actualizar su perfil (nombre, avatar).
*   `DELETE /users/me`: Elimina la cuenta del usuario autenticado y todos los datos de su propiedad en cascada (workspaces, licitaciones, etc.).

---

### Workspaces (`/workspaces`)

*   `POST /`: Crea un nuevo espacio de trabajo.
*   `GET /`: Lista todos los workspaces a los que pertenece el usuario.
*   `GET /detailed`: Lista los workspaces del usuario, incluyendo un resumen de sus licitaciones y miembros.
*   `GET /{workspace_id}`: Obtiene los detalles de un workspace específico.
*   `PUT /{workspace_id}`: Actualiza el nombre o la descripción de un workspace (solo para el propietario).
*   `DELETE /{workspace_id}`: Elimina un workspace y todos sus contenidos (solo para el propietario).
*   `POST /{workspace_id}/members`: Añade un nuevo miembro a un workspace (requiere rol de Admin o superior).
*   `GET /{workspace_id}/members`: Lista todos los miembros de un workspace.
*   `PUT /{workspace_id}/members/{user_id}`: Modifica el rol de un miembro en un workspace (requiere rol de Admin o superior).
*   `DELETE /{workspace_id}/members/{user_id}`: Elimina a un miembro de un workspace (requiere rol de Admin o superior).

---

### Licitaciones y Análisis (`/tenders`, `/analysis-results`)

*   `POST /tenders/`: Crea una nueva licitación dentro de un workspace, permitiendo la subida inicial de archivos.
*   `GET /tenders/workspace/{workspace_id}`: Lista todas las licitaciones de un workspace específico.
*   `GET /tenders/all_for_user`: Devuelve un resumen de todas las licitaciones a las que el usuario tiene acceso en todos sus workspaces.
*   `GET /tenders/{tender_id}`: Obtiene la información detallada de una licitación, incluyendo los metadatos de sus documentos y análisis.
*   `PATCH /tenders/{tender_id}`: Actualiza el nombre o la descripción de una licitación.
*   `DELETE /tenders/{tender_id}`: Elimina una licitación, incluyendo sus documentos y análisis asociados.
*   `POST /tenders/{tender_id}/documents`: Añade nuevos documentos a una licitación existente.
*   `GET /tenders/{tender_id}/documents/{document_id}/download`: Permite la descarga del contenido binario de un documento.
*   `DELETE /tenders/{tender_id}/documents/{document_id}`: Elimina un documento de una licitación.
*   `POST /tenders/{tender_id}/generate_analysis`: Inicia un flujo de análisis asíncrono sobre una licitación utilizando un automatismo registrado.
*   `DELETE /tenders/{tender_id}/analysis/{result_id}`: Elimina un resultado de análisis de una licitación.
*   `GET /analysis-results/{analysis_id}`: Obtiene el documento JSON completo y detallado de un resultado de análisis finalizado.
*   `PATCH /analysis-results/{analysis_id}`: Permite renombrar un resultado de análisis.

---

### Automatismos (`/automations`)

*   `POST /`: Registra un nuevo automatismo (webhook) en el sistema.
*   `GET /`: Lista todos los automatismos disponibles.
*   `DELETE /{automation_id}`: Elimina un automatismo del sistema.

---

### Chatbot (`/chatbot`)

*   `POST /chatbot/chat`: Envía un mensaje al agente conversacional y recibe una respuesta.

---

### WebSockets

*   `WS /ws/analysis/{analysis_id}`: Establece una conexión WebSocket para recibir notificaciones en tiempo real sobre el progreso de un análisis específico (estados `PROCESSING`, `COMPLETED`, `FAILED`).
