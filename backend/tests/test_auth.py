import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_signup_success(client):
    """Prueba el registro exitoso de un nuevo usuario."""
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": unique_email,
        "password": "Password123!",
        "full_name": "Test User"
    }
    response = await client.post("/auth/signup", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == unique_email
    assert "id" in data

@pytest.mark.asyncio
async def test_login_generates_cookies(client):
    """Verifica que el login genere tanto el access_token como la cookie de refresh_token."""
    email = f"login_cookie_{uuid.uuid4().hex[:8]}@example.com"
    password = "LoginPass123!"
    
    # Registro
    await client.post("/auth/signup", json={
        "email": email, "password": password, "full_name": "Cookie User"
    })
    
    # Login
    response = await client.post("/auth/login", data={"username": email, "password": password})
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in client.cookies

@pytest.mark.asyncio
async def test_refresh_token_flow(client):
    """Prueba el flujo completo de refresco de token."""
    email = f"refresh_{uuid.uuid4().hex[:8]}@example.com"
    password = "RefreshPass123!"
    
    await client.post("/auth/signup", json={
        "email": email, "password": password, "full_name": "Refresh User"
    })
    
    # 1. Login inicial
    login_res = await client.post("/auth/login", data={"username": email, "password": password})
    assert login_res.status_code == 200
    
    # 2. Llamar a /refresh (usa la cookie automáticamente)
    refresh_res = await client.post("/auth/refresh")
    
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()
    assert "refresh_token" in client.cookies

@pytest.mark.asyncio
async def test_logout_clears_cookie(client):
    """Verifica que el logout elimine la cookie de refresh token."""
    email = f"logout_{uuid.uuid4().hex[:8]}@example.com"
    password = "LogoutPass123!"
    
    await client.post("/auth/signup", json={
        "email": email, "password": password, "full_name": "Logout User"
    })
    
    # Login para tener cookie
    login_res = await client.post("/auth/login", data={"username": email, "password": password})
    token = login_res.json()["access_token"]
    assert "refresh_token" in client.cookies
    
    # Logout
    logout_res = await client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200
    
    # Intentar refresh después de logout debería fallar
    refresh_res = await client.post("/auth/refresh")
    assert refresh_res.status_code == 401

@pytest.mark.asyncio
async def test_access_token_type_security(client):
    """
    SEGURIDAD: Verifica que un Refresh Token no pueda ser usado como 
    Access Token en un endpoint protegido.
    """
    email = f"sec_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurityPass123!"
    
    await client.post("/auth/signup", json={
        "email": email, "password": password, "full_name": "Sec User"
    })
    
    await client.post("/auth/login", data={"username": email, "password": password})
    refresh_token = client.cookies.get("refresh_token")
    
    # Intentar usar el refresh_token como si fuera un access_token en /users/me
    headers = {"Authorization": f"Bearer {refresh_token}"}
    response = await client.get("/users/me", headers=headers)
    
    # Debería fallar porque el tipo de token es 'refresh', no 'access'
    assert response.status_code == 401
    assert "credentials" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_read_users_me_success(client):
    """Prueba acceso exitoso con access token."""
    email = f"me_{uuid.uuid4().hex[:8]}@example.com"
    password = "MePassword123!"
    
    await client.post("/auth/signup", json={
        "email": email, "password": password, "full_name": "Me User"
    })
    
    login_res = await client.post("/auth/login", data={"username": email, "password": password})
    token = login_res.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/users/me", headers=headers)
    
    assert response.status_code == 200
    assert response.json()["email"] == email

@pytest.mark.asyncio
async def test_token_blacklisting_on_logout(client):
    """SEGURIDAD: Verifica que el token de acceso quede invalidado tras el logout."""
    email = f"logout_sec_{uuid.uuid4().hex[:8]}@example.com"
    password = "LogoutSec123!"
    
    await client.post("/auth/signup", json={
        "email": email, "password": password, "full_name": "Logout Sec User"
    })
    
    # 1. Login
    login_res = await client.post("/auth/login", data={"username": email, "password": password})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Verificar que el token funciona
    me_res = await client.get("/users/me", headers=headers)
    assert me_res.status_code == 200
    
    # 3. Logout (esto debería añadir el JTI a la lista negra de Redis)
    logout_res = await client.post("/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    
    # 4. Intentar usar el MISMO token de nuevo
    me_res_retry = await client.get("/users/me", headers=headers)
    
    # Debería ser rechazado aunque el token no haya expirado técnicamente
    assert me_res_retry.status_code == 401
    assert "revoked" in me_res_retry.json()["detail"].lower()

@pytest.mark.asyncio
async def test_refresh_token_rotation_security(client):
    """
    SEGURIDAD: Verifica que al refrescar un token, el Refresh Token antiguo 
    quede invalidado en Redis y no pueda usarse dos veces.
    """
    email = f"rot_{uuid.uuid4().hex[:8]}@example.com"
    password = "RotationPass123!"
    
    await client.post("/auth/signup", json={
        "email": email, "password": password, "full_name": "Rotation User"
    })
    
    # 1. Login inicial
    await client.post("/auth/login", data={"username": email, "password": password})
    old_refresh_token = client.cookies.get("refresh_token")
    
    # 2. Primer refresco (exitoso)
    res1 = await client.post("/auth/refresh")
    assert res1.status_code == 200
    
    # 3. Segundo refresco usando el MISMO refresh token antiguo
    # (Simulamos esto enviando la cookie antigua manualmente si el cliente la actualizó)
    client.cookies.set("refresh_token", old_refresh_token)
    res2 = await client.post("/auth/refresh")
    
    # Debería fallar porque el token antiguo está en la blacklist de Redis
    assert res2.status_code == 401
    assert "revoked" in res2.json()["detail"].lower()

@pytest.mark.asyncio
async def test_update_user_me(client):
    """Test updating user profile."""
    email = f"update_{uuid.uuid4().hex[:8]}@example.com"
    password = "UpdatePass123!"
    
    await client.post("/auth/signup", json={"email": email, "password": password, "full_name": "Update User"})
    login_res = await client.post("/auth/login", data={"username": email, "password": password})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {"full_name": "Updated Name", "profile_picture": "/avatar/green_lizard.png"}
    response = await client.patch("/users/me", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["profile_picture"] == "/avatar/green_lizard.png"

@pytest.mark.asyncio
async def test_delete_user_me(client):
    """Test deleting the current user account."""
    email = f"delete_{uuid.uuid4().hex[:8]}@example.com"
    password = "DeletePass123!"
    
    await client.post("/auth/signup", json={"email": email, "password": password, "full_name": "Delete User"})
    login_res = await client.post("/auth/login", data={"username": email, "password": password})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to access me before deletion
    me_res_before = await client.get("/users/me", headers=headers)
    assert me_res_before.status_code == 200
    
    # Delete user
    delete_res = await client.delete("/users/me", headers=headers)
    assert delete_res.status_code == 204
    
    # Try to access me after deletion
    me_res_after = await client.get("/users/me", headers=headers)
    assert me_res_after.status_code == 401