# Guía de Configuración OAuth2

Esta guía te ayudará a configurar la autenticación con proveedores externos (Google, Facebook, GitHub, Microsoft).

## 📋 Tabla de Contenidos

1. [Configuración de Google](#google-oauth2)
2. [Configuración de Facebook](#facebook-oauth2)
3. [Configuración de GitHub](#github-oauth2)
4. [Configuración de Microsoft](#microsoft-oauth2)
5. [Testing OAuth Flow](#testing-oauth)

---

## 🔵 Google OAuth2

### Paso 1: Crear Proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Google+ (Google+ API)

### Paso 2: Configurar OAuth Consent Screen

1. En el menú lateral, ve a **APIs & Services** → **OAuth consent screen**
2. Selecciona el tipo de usuario (**External** para usuarios públicos)
3. Completa la información requerida:
   - Nombre de la aplicación
   - Email de soporte
   - Logo (opcional)
4. Agrega los scopes necesarios:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
   - `openid`

### Paso 3: Crear Credenciales OAuth2

1. Ve a **APIs & Services** → **Credentials**
2. Click en **Create Credentials** → **OAuth client ID**
3. Selecciona **Web application**
4. Configura:
   - **Name**: "Mi App Auth"
   - **Authorized JavaScript origins**: `http://localhost:8000`
   - **Authorized redirect URIs**: `http://localhost:8000/auth/google/callback`
5. Guarda el **Client ID** y **Client Secret**

### Paso 4: Configurar en .env

```env
GOOGLE_CLIENT_ID=123456789-abcdefghijk.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

---

## 🔵 Facebook OAuth2

### Paso 1: Crear App en Facebook Developers

1. Ve a [Facebook Developers](https://developers.facebook.com/apps/)
2. Click en **Create App**
3. Selecciona **Consumer** como tipo de app
4. Completa los detalles de la app

### Paso 2: Configurar Facebook Login

1. En el dashboard de tu app, agrega **Facebook Login**
2. Ve a **Facebook Login** → **Settings**
3. Agrega las **Valid OAuth Redirect URIs**:
   ```
   http://localhost:8000/auth/facebook/callback
   ```

### Paso 3: Configurar Permisos

1. Ve a **App Review** → **Permissions and Features**
2. Solicita los permisos:
   - `email` (requerido)
   - `public_profile` (básico)

### Paso 4: Obtener Credenciales

1. Ve a **Settings** → **Basic**
2. Copia el **App ID** y **App Secret**

### Paso 5: Configurar en .env

```env
FACEBOOK_CLIENT_ID=your-facebook-app-id
FACEBOOK_CLIENT_SECRET=your-facebook-app-secret
FACEBOOK_REDIRECT_URI=http://localhost:8000/auth/facebook/callback
```

---

## 🔵 GitHub OAuth2

### Paso 1: Registrar OAuth App

1. Ve a [GitHub Developer Settings](https://github.com/settings/developers)
2. Click en **New OAuth App**
3. Completa el formulario:
   - **Application name**: Mi App
   - **Homepage URL**: `http://localhost:8000`
   - **Authorization callback URL**: `http://localhost:8000/auth/github/callback`

### Paso 2: Obtener Credenciales

1. Después de crear la app, verás el **Client ID**
2. Genera un **Client Secret**
3. ⚠️ Guarda el secret inmediatamente (solo se muestra una vez)

### Paso 3: Configurar en .env

```env
GITHUB_CLIENT_ID=Iv1.your-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback
```

---

## 🔵 Microsoft OAuth2

### Paso 1: Registrar App en Azure Portal

1. Ve a [Azure Portal](https://portal.azure.com/)
2. Busca **Azure Active Directory** → **App registrations**
3. Click en **New registration**
4. Completa:
   - **Name**: Mi App
   - **Supported account types**: "Accounts in any organizational directory and personal Microsoft accounts"
   - **Redirect URI**: 
     - Platform: **Web**
     - URI: `http://localhost:8000/auth/microsoft/callback`

### Paso 2: Configurar API Permissions

1. En tu app, ve a **API permissions**
2. Click en **Add a permission** → **Microsoft Graph**
3. Selecciona **Delegated permissions**:
   - `openid`
   - `email`
   - `profile`
4. Click en **Grant admin consent** (si aplica)

### Paso 3: Crear Client Secret

1. Ve a **Certificates & secrets**
2. Click en **New client secret**
3. Agrega una descripción y selecciona expiración
4. **Guarda el valor del secret inmediatamente**

### Paso 4: Obtener IDs

1. Ve a **Overview** para ver:
   - **Application (client) ID**
   - **Directory (tenant) ID** (opcional, usa "common" para cuentas personales y organizacionales)

### Paso 5: Configurar en .env

```env
MICROSOFT_CLIENT_ID=your-application-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret-value
MICROSOFT_REDIRECT_URI=http://localhost:8000/auth/microsoft/callback
MICROSOFT_TENANT=common
```

**Opciones de TENANT:**
- `common`: Cuentas Microsoft personales y organizacionales
- `organizations`: Solo cuentas organizacionales
- `consumers`: Solo cuentas personales
- `{tenant-id}`: Tenant específico

---

## 🧪 Testing OAuth Flow

### Verificar Proveedores Habilitados

```bash
curl http://localhost:8000/auth/providers
```

Respuesta esperada:
```json
{
  "enabled_providers": ["google", "github"],
  "available_providers": ["google", "facebook", "github", "microsoft"]
}
```

### Flujo de Autenticación Completo

#### 1. Iniciar Login con OAuth

**En el navegador**, visita:
```
http://localhost:8000/auth/google/login
```

Esto redirigirá al usuario a Google para autenticación.

#### 2. Después de Autorizar

El usuario será redirigido a:
```
http://localhost:8000/auth/google/callback?code=xxx&state=xxx
```

El endpoint de callback devolverá un token JWT:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 3. Usar el Token

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

Respuesta:
```json
{
  "id": "uuid",
  "email": "user@gmail.com",
  "full_name": "John Doe",
  "is_active": true,
  "oauth_provider": "google",
  "profile_picture": "https://...",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

---

## 🔐 Seguridad en Producción

### URLs de Redirección

Para producción, actualiza las URLs en:

1. **Proveedores OAuth** (Google, Facebook, etc.):
   ```
   https://tu-dominio.com/auth/{provider}/callback
   ```

2. **Variables de entorno**:
   ```env
   GOOGLE_REDIRECT_URI=https://tu-dominio.com/auth/google/callback
   FACEBOOK_REDIRECT_URI=https://tu-dominio.com/auth/facebook/callback
   # etc...
   ```

### HTTPS Obligatorio

⚠️ **En producción, SIEMPRE usa HTTPS**. Los proveedores OAuth pueden rechazar conexiones no seguras.

### Manejo de Estado (State Token)

El sistema usa tokens de estado para prevenir ataques CSRF. En producción:
- Considera usar Redis para almacenar estados
- Implementa expiración de tokens de estado
- Valida el origen de las peticiones

---

## 🎨 Ejemplo de Frontend

### Botones de Login

```html
<!DOCTYPE html>
<html>
<head>
    <title>Login con OAuth</title>
    <style>
        .oauth-buttons {
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 300px;
            margin: 50px auto;
        }
        .oauth-button {
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            text-decoration: none;
            text-align: center;
            color: white;
        }
        .google { background-color: #4285f4; }
        .facebook { background-color: #1877f2; }
        .github { background-color: #333; }
        .microsoft { background-color: #00a4ef; }
    </style>
</head>
<body>
    <div class="oauth-buttons">
        <a href="http://localhost:8000/auth/google/login" class="oauth-button google">
            Continue with Google
        </a>
        <a href="http://localhost:8000/auth/facebook/login" class="oauth-button facebook">
            Continue with Facebook
        </a>
        <a href="http://localhost:8000/auth/github/login" class="oauth-button github">
            Continue with GitHub
        </a>
        <a href="http://localhost:8000/auth/microsoft/login" class="oauth-button microsoft">
            Continue with Microsoft
        </a>
    </div>
</body>
</html>
```

---

## 🐛 Troubleshooting

### Error: "redirect_uri_mismatch"

**Causa**: La URL de redirección no coincide.

**Solución**: Verifica que la URL en:
1. Tu configuración del proveedor OAuth
2. Tu archivo `.env`
3. Sean **exactamente iguales** (incluyendo protocolo, puerto, path)

### Error: "invalid_client"

**Causa**: Client ID o Secret incorrectos.

**Solución**: 
1. Verifica las credenciales en el dashboard del proveedor
2. Revisa que no haya espacios extra en el `.env`

### Error: "Email permission not granted"

**Causa**: El usuario no concedió permiso de email (especialmente en Facebook).

**Solución**:
1. Solicita explícitamente el scope de email
2. En Facebook, asegúrate de tener el permiso aprobado en App Review

### No puedo obtener el email del usuario (GitHub)

**Causa**: GitHub no siempre expone el email público.

**Solución**: El sistema automáticamente solicita la lista de emails del usuario y selecciona el email primario verificado.

---

## 📚 Referencias

- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Facebook Login Documentation](https://developers.facebook.com/docs/facebook-login)
- [GitHub OAuth Apps Documentation](https://docs.github.com/en/developers/apps/building-oauth-apps)
- [Microsoft Identity Platform](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
