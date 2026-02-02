import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app
import uuid

# URL base para los tests
BASE_URL = "http://testserver"

@pytest_asyncio.fixture
async def client():
    """Fixture que proporciona un cliente HTTP asíncrono configurado para la app."""
    # El lifespan de la app creará las tablas automáticamente al iniciar el cliente
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        yield ac

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
async def test_signup_duplicate_email(client):
    """Prueba que no se puede registrar un usuario con un email ya existente."""
    email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "password": "Password123!",
        "full_name": "User One"
    }
    
    # Primer registro
    await client.post("/auth/signup", json=payload)
    # Segundo registro con el mismo email
    response = await client.post("/auth/signup", json=payload)
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_login_success(client):
    """Prueba el inicio de sesión exitoso y la obtención de un token JWT."""
    email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    password = "LoginPass123!"
    
    # Registrar primero
    await client.post("/auth/signup", json={
        "email": email,
        "password": password,
        "full_name": "Login User"
    })
    
    # Intentar login (form data)
    login_payload = {
        "username": email,
        "password": password
    }
    response = await client.post("/auth/login", data=login_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Prueba el fallo de login con credenciales incorrectas."""
    login_payload = {
        "username": f"no_{uuid.uuid4().hex[:8]}@example.com",
        "password": "WrongPassword"
    }
    response = await client.post("/auth/login", data=login_payload)
    
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_read_users_me(client):
    """Prueba la obtención de la información del usuario actual usando el token."""
    email = f"me_{uuid.uuid4().hex[:8]}@example.com"
    password = "MePassword123!"
    
    # 1. Registro
    await client.post("/auth/signup", json={
        "email": email,
        "password": password,
        "full_name": "Me User"
    })
    
    # 2. Login para obtener token
    login_res = await client.post("/auth/login", data={"username": email, "password": password})
    token = login_res.json()["access_token"]
    
    # 3. Acceder a /users/me
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/users/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email