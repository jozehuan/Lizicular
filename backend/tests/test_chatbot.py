import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
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
async def test_chatbot_chat_success(client: AsyncClient, monkeypatch):
    """Test successful interaction with the chatbot."""
    token, user_data = await create_user_and_login(client, "chat_user")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Mock the chatbot controller
    mock_controller = AsyncMock(return_value="This is a mocked response from the chatbot.")
    monkeypatch.setattr("backend.chatbot.routes.chat_bot_controller", mock_controller)
    
    payload = {
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ]
    }
    
    res = await client.post("/chatbot/chat", json=payload, headers=headers)
    
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert data["answer"] == "This is a mocked response from the chatbot."
    
    mock_controller.assert_called_once()
    
@pytest.mark.asyncio
async def test_chatbot_chat_unauthorized(client: AsyncClient):
    """Test that unauthorized users cannot access the chatbot."""
    payload = {
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ]
    }
    
    res = await client.post("/chatbot/chat", json=payload)
    
    assert res.status_code == 401
