# Sistema de Autenticación Centralizado con OAuth2

Sistema de autenticación robusto y seguro con FastAPI, PostgreSQL, JWT y soporte para OAuth2 (Google, Facebook, GitHub, Microsoft).

## 🚀 Características

- ✅ **Autenticación Local** con email/password
- ✅ **OAuth2 con Google, Facebook, GitHub y Microsoft**
- ✅ **JWT** con expiración configurable
- ✅ **Base de datos PostgreSQL** con SQLAlchemy asíncrono
- ✅ **Hashing de contraseñas** con bcrypt
- ✅ **Validación de datos** con Pydantic
- ✅ **Type hints** completos
- ✅ **Manejo de excepciones HTTP**
- ✅ **Endpoints protegidos** con dependencias
- ✅ **Linking de cuentas** (vincular OAuth con cuenta existente)
- ✅ **Profile pictures** desde proveedores OAuth

## 📋 Tabla de Contenidos

- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Configuración OAuth](#-configuración-oauth)
- [Endpoints](#-endpoints)
- [Ejemplos de Uso](#-ejemplos-de-uso)
- [Testing](#-testing)
- [Seguridad](#-seguridad)

## 🛠️ Instalación

### 1. Requisitos Previos

- Python 3.9+
- PostgreSQL 12+
- pip

### 2. Clonar o crear el proyecto

```bash
mkdir auth-system
cd auth-system
```

### 3. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar base de datos

#### Opción A: Usando Docker (Recomendada) 🐳

El proyecto incluye un archivo `docker-compose.yml` para levantar la base de datos rápidamente.

1. Asegúrate de tener [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo.
2. Ejecuta el siguiente comando en la raíz del proyecto:

```bash
docker-compose up -d
```

Esto levantará una instancia de PostgreSQL en el puerto 5432 con las credenciales por defecto (`postgres`/`postgres`).

> ⚠️ Advertencia: Estas credenciales son solo para desarrollo local. Nunca uses credenciales por defecto en producción. Se recomienda encarecidamente sobrescribir estas credenciales usando variables de entorno o un sistema de gestión de secretos seguro, y utilizar contraseñas robustas y rotadas en entornos de producción.

#### Opción B: Instalación Local

```sql
-- Conectarse a PostgreSQL
psql -U postgres

-- Crear base de datos
CREATE DATABASE authdb;

-- Crear usuario (opcional)
CREATE USER authuser WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE authdb TO authuser;
```

## ⚙️ Configuración

### Variables de Entorno

Copia el archivo de ejemplo y edítalo:

```bash
cp .env.example .env
nano .env
```

**Configuración mínima:**

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/authdb
SECRET_KEY=tu-clave-secreta-super-segura-cambiar-en-produccion
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Generar SECRET_KEY segura:**
```bash
openssl rand -hex 32
```

## 🔐 Configuración OAuth

Para habilitar la autenticación con proveedores externos, necesitas configurar cada proveedor que desees usar.

### Consulta la [Guía Completa de OAuth](OAUTH_SETUP.md) 📖

La guía incluye instrucciones paso a paso para:
- 🔵 Google OAuth2
- 🔵 Facebook OAuth2
- 🔵 GitHub OAuth2
- 🔵 Microsoft OAuth2

### Resumen Rápido

1. **Google**: [Console](https://console.cloud.google.com/)
2. **Facebook**: [Developers](https://developers.facebook.com/apps/)
3. **GitHub**: [Settings](https://github.com/settings/developers)
4. **Microsoft**: [Azure Portal](https://portal.azure.com/)

Agrega las credenciales al `.env`:

```env
# Google
GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu-client-secret

# Facebook
FACEBOOK_CLIENT_ID=tu-app-id
FACEBOOK_CLIENT_SECRET=tu-app-secret

# GitHub
GITHUB_CLIENT_ID=tu-client-id
GITHUB_CLIENT_SECRET=tu-client-secret

# Microsoft
MICROSOFT_CLIENT_ID=tu-client-id
MICROSOFT_CLIENT_SECRET=tu-client-secret
```

## 🏃 Ejecución

### Desarrollo

```bash
uvicorn main:app --reload
```

### Producción

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

La aplicación estará disponible en: `http://localhost:8000`

## 📚 Documentación API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 Endpoints

### Autenticación Local

#### Registro
```http
POST /auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "Juan Pérez"
}
```

#### Login (OAuth2 Form)
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePass123!
```

#### Login (JSON)
```http
POST /auth/login/json
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

### OAuth2 (Terceros)

#### Iniciar Login con OAuth
```http
GET /auth/{provider}/login
```

Proveedores soportados: `google`, `facebook`, `github`, `microsoft`

**Ejemplo:**
```
http://localhost:8000/auth/google/login
```

Esto redirigirá al usuario a Google para autenticación.

#### Callback OAuth (Automático)
```http
GET /auth/{provider}/callback?code={code}&state={state}
```

Este endpoint es llamado automáticamente por el proveedor OAuth después de la autenticación.

#### Verificar Proveedores Habilitados
```http
GET /auth/providers
```

**Respuesta:**
```json
{
  "enabled_providers": ["google", "github"],
  "available_providers": ["google", "facebook", "github", "microsoft"]
}
```

### Endpoints Protegidos

#### Obtener Usuario Actual
```http
GET /users/me
Authorization: Bearer {token}
```

**Respuesta:**
```json
{
  "id": "uuid",
  "email": "user@gmail.com",
  "full_name": "Juan Pérez",
  "is_active": true,
  "oauth_provider": "google",
  "profile_picture": "https://lh3.googleusercontent.com/...",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

## 💡 Ejemplos de Uso

### Registro y Login Local

```bash
# 1. Registrar usuario
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Password123!",
    "full_name": "Test User"
  }'

# 2. Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=Password123!"

# 3. Usar token
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

### Login con OAuth (Frontend)

```html
<!DOCTYPE html>
<html>
<body>
    <h1>Login</h1>
    
    <!-- Botones OAuth -->
    <a href="http://localhost:8000/auth/google/login">
        <button>Login with Google</button>
    </a>
    
    <a href="http://localhost:8000/auth/github/login">
        <button>Login with GitHub</button>
    </a>
    
    <a href="http://localhost:8000/auth/facebook/login">
        <button>Login with Facebook</button>
    </a>
    
    <a href="http://localhost:8000/auth/microsoft/login">
        <button>Login with Microsoft</button>
    </a>
</body>
</html>
```

### Cliente Python

```python
import httpx
import asyncio

async def login_with_email():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/auth/login",
            data={
                "username": "user@example.com",
                "password": "Password123!"
            }
        )
        token_data = response.json()
        return token_data["access_token"]

async def get_user_info(token):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()

# Uso
token = asyncio.run(login_with_email())
user = asyncio.run(get_user_info(token))
print(user)
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx

# Ejecutar tests
pytest test_main.py -v
```

### Script de Ejemplo

```bash
python example_usage.py
```

## 🔒 Seguridad

### Características de Seguridad

1. ✅ **Bcrypt** para hashing de contraseñas (costoso computacionalmente)
2. ✅ **JWT con expiración** configurable
3. ✅ **State tokens** para prevenir CSRF en OAuth
4. ✅ **Validación de emails** con Pydantic
5. ✅ **Contraseñas mínimo 8 caracteres**
6. ✅ **UUIDs** para IDs de usuarios
7. ✅ **Índices optimizados** en base de datos
8. ✅ **Linking de cuentas** seguro (OAuth + local)

### Recomendaciones para Producción

#### Obligatorias
- ✅ Usar **HTTPS** (SSL/TLS)
- ✅ Cambiar `SECRET_KEY` a una clave segura única
- ✅ Usar variables de entorno seguras (AWS Secrets Manager, Vault)
- ✅ Configurar CORS apropiadamente
- ✅ Actualizar URLs de callback OAuth a producción

#### Recomendadas
- ⭐ Implementar **rate limiting**
- ⭐ Agregar **logging** y monitoreo
- ⭐ Implementar **refresh tokens**
- ⭐ Agregar **2FA** (autenticación de dos factores)
- ⭐ Validar **fortaleza de contraseñas**
- ⭐ Implementar **política de bloqueo** de cuentas
- ⭐ Usar **Redis** para almacenar state tokens OAuth

### Configuración CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tu-frontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📁 Estructura del Proyecto

```
backend/
├── main.py              # FastAPI app y endpoints
├── auth/                # Módulo de identidad y seguridad
│   ├── models.py        # Modelos SQLAlchemy
│   ├── schemas.py       # Schemas Pydantic
│   ├── auth_utils.py    # Utilidades local
│   └── ...
├── database/            # Infraestructura DB
└── tests/               # Pruebas automatizadas
    └── test_auth.py     # Suite de tests de seguridad
```

## 🔄 Flujo de Autenticación

### Local (Email/Password)

```
1. Usuario → POST /auth/signup → Registro
2. Usuario → POST /auth/login → Login
3. Sistema → JWT Token → Usuario
4. Usuario → GET /users/me (con token) → Datos protegidos
```

### OAuth2

```
1. Usuario → GET /auth/google/login
2. Sistema → Redirect a Google
3. Usuario autentica en Google
4. Google → Redirect a /auth/google/callback?code=...
5. Sistema intercambia code por token
6. Sistema obtiene info de usuario de Google
7. Sistema crea/actualiza usuario en DB
8. Sistema → JWT Token → Usuario
9. Usuario → GET /users/me (con token) → Datos protegidos
```

## 🌐 Linking de Cuentas

El sistema soporta vincular cuentas OAuth con cuentas locales existentes:

1. Usuario se registra con email/password
2. Luego hace login con Google usando el mismo email
3. El sistema automáticamente vincula las cuentas
4. Usuario puede usar ambos métodos de autenticación

## 📊 Modelo de Base de Datos

### Tabla `users` (Identidad)
| Campo            | Tipo      | Descripción                        |
|------------------|-----------|------------------------------------|
| id               | UUID      | Primary key                        |
| email            | String    | Único, indexado                    |
| hashed_password  | String    | Hash bcrypt (nullable para OAuth)  |
| full_name        | String    | Nombre completo                    |
| is_active        | Boolean   | Estado activo                      |
| oauth_provider   | String    | Proveedor OAuth (nullable)         |
| oauth_id         | String    | ID del usuario en proveedor        |
| profile_picture  | Text      | URL de foto de perfil              |

### Tabla `workspaces` (Colaboración)
| Campo            | Tipo      | Descripción                        |
|------------------|-----------|------------------------------------|
| id               | UUID      | Primary key                        |
| name             | String    | Nombre del workspace               |
| owner_id         | UUID      | FK a users.id (Propietario)        |
| is_active        | Boolean   | Estado del workspace               |

### Tabla `audit_logs` (Trazabilidad Universal)
| Campo            | Tipo      | Descripción                        |
|------------------|-----------|------------------------------------|
| id               | UUID      | Primary key                        |
| user_id          | UUID      | Usuario que ejecutó la acción      |
| category         | Enum      | AUTH, WORKSPACE, TENDER, etc.      |
| action           | Enum      | Acción específica (LOGIN, CREATE..) |
| payload          | JSONB     | Datos detallados del evento        |
| success          | Boolean   | Resultado de la operación           |

## 🐛 Troubleshooting

Ver la sección de [Troubleshooting en OAUTH_SETUP.md](OAUTH_SETUP.md#-troubleshooting)

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 🤝 Contribución

¿Quieres mejorar este proyecto?

- Agregar más proveedores OAuth (Twitter, LinkedIn, etc.)
- Implementar refresh tokens
- Agregar recuperación de contraseña
- Implementar verificación de email
- Agregar roles y permisos (RBAC)

## 📞 Soporte

Para problemas o preguntas:
1. Revisa la [documentación de FastAPI](https://fastapi.tiangolo.com/)
2. Consulta la [guía OAuth](OAUTH_SETUP.md)
3. Revisa los logs de la aplicación

---

**Desarrollado con ❤️ usando FastAPI**
