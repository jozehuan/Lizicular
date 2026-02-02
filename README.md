# Lizicular 🚀

**Lizicular** es una plataforma diseñada para la gestión y automatización de procesos en licitaciones, con un enfoque especializado en sistemas de **ticketing**. La aplicación busca optimizar el flujo de trabajo mediante automatismos que faciliten el seguimiento y la resolución de tareas relacionadas con concursos públicos.

## 🛠️ Stack Tecnológico

La aplicación se divide en diferentes módulos, utilizando las siguientes tecnologías:

### **Back-End (Núcleo)**
- **Lenguaje:** Python 3.11+
- **Framework:** FastAPI
- **Base de Datos:** PostgreSQL 15 (Principal), MongoDB (Planificado para chatbot/logs)
- **ORM:** SQLAlchemy (AsyncPG)
- **Infraestructura:** Docker & Docker Compose

### **Autenticación y Seguridad**
- **JWT (JSON Web Tokens):** Gestión de sesiones segura.
- **OAuth2:** Integración con proveedores externos (Google, Facebook, GitHub, Microsoft).
- **Hashing:** Bcrypt (via Passlib) para protección de contraseñas.

### **Front-End (En Desarrollo)**
- **Entorno:** Node.js
- **Framework:** React / Next.js (Planificado)

### **Chatbot & Automatización (Planificado)**
- Procesamiento de lenguaje natural para asistencia en licitaciones.

### **Pruebas y Calidad**
- **Pytest:** Suite de pruebas unitarias y de integración asíncronas.
- **Postman:** Pruebas manuales y documentación de la API.
- **Httpx:** Cliente HTTP para pruebas de integración de FastAPI.

## 🔌 API Endpoints (Módulo de Autenticación)

### **Autenticación Local**
- `POST /auth/signup`: Registro de nuevos usuarios.
- `POST /auth/login`: Login mediante Form Data (estándar OAuth2).
- `POST /auth/login/json`: Login mediante payload JSON.

### **Autenticación Externa (OAuth2)**
- `GET /auth/{provider}/login`: Inicia el flujo de autenticación con un proveedor.
- `GET /auth/{provider}/callback`: Endpoint de retorno para el intercambio de tokens.
- `GET /auth/providers`: Lista los proveedores externos configurados.

### **Usuarios**
- `GET /users/me`: Obtiene la información del perfil del usuario autenticado (Protegido con JWT).

### **Utilidad**
- `GET /`: Health check del sistema.

## 📝 Resumen de Progreso

Actualmente, el proyecto se encuentra en su fase inicial de infraestructura y base de seguridad:

1.  **Base de Datos Contenedorizada:** Configuración de PostgreSQL mediante Docker Compose para un entorno de desarrollo reproducible.
2.  **Módulo de Autenticación Híbrida:** Implementación completa del sistema de registro y login, soportando tanto credenciales locales como OAuth2.
3.  **Refactorización de Tipos:** Código optimizado para Python 3.10+ usando el estándar `Tipo | None` y Pydantic v2.
4.  **Infraestructura de Pruebas:** Creación de una suite de tests automáticos con `pytest` y `httpx`, además de colecciones en `Postman` para validación manual del flujo de usuarios.
5.  **Corrección de Dependencias:** Ajuste de versiones de seguridad (`bcrypt`) para asegurar compatibilidad en Windows y entornos asíncronos.

---
**Desarrollado para la automatización eficiente de licitaciones.**
