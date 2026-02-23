import pytest
from httpx import AsyncClient
import uuid

async def create_user_and_login(client: AsyncClient, role_name: str) -> tuple[str, dict]:
    """Creates a user, logs them in, and returns their token and user data."""
    email = f"{role_name}_{uuid.uuid4().hex[:8]}@example.com"
    password = "Password123!"
    
    signup_res = await client.post("/auth/signup", json={"email": email, "password": password, "full_name": f"{role_name.capitalize()} User"})
    assert signup_res.status_code == 201
    user_data = signup_res.json()
    
    login_res = await client.post("/auth/login", data={"username": email, "password": password})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    
    return token, user_data

@pytest.mark.asyncio
async def test_create_automation(client: AsyncClient):
    token, user_data = await create_user_and_login(client, "auto_creator")
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "name": "Test Automation",
        "url": "http://example.com/webhook",
        "description": "A test automation"
    }
    
    res = await client.post("/automations/", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Test Automation"
    assert data["url"] == "http://example.com/webhook"
    assert "id" in data

@pytest.mark.asyncio
async def test_list_automations(client: AsyncClient):
    token, user_data = await create_user_and_login(client, "auto_viewer")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create an automation first
    payload = {
        "name": "Listable Automation",
        "url": "http://example.com/webhook2"
    }
    await client.post("/automations/", json=payload, headers=headers)
    
    res = await client.get("/automations/", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    assert any(a["name"] == "Listable Automation" for a in data)
