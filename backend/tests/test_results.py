import pytest
import pytest_asyncio
from httpx import AsyncClient, Response, RequestError
import uuid
import asyncio
from sqlalchemy import select
from unittest.mock import AsyncMock # Import AsyncMock

from backend.auth.auth_utils import create_access_token
from backend.auth.models import User
from backend.workspaces.models import Workspace, WorkspaceMember, WorkspaceRole
from backend.tenders.tenders_utils import MongoDB
from bson import ObjectId
from backend.auth.database import get_db
from backend.automations.websocket.connection_manager import ConnectionManager, get_connection_manager

USER_ID = "aebadb74-6ecc-46f6-bd1b-e9359cf2c135"
AUTOMATION_ID = "2cf9e384-b633-5c8c-9488-2f47b6796791"
TENDER_ID = "6989b78b433ebeb986d294a9"
WORKSPACE_ID = str(uuid.uuid4())

@pytest.fixture(scope="module")
def access_token():
    return create_access_token(data={"sub": USER_ID})

@pytest_asyncio.fixture
async def setup_data(test_app):
    db_gen = test_app.dependency_overrides.get(get_db, get_db)
    db = db_gen().__next__()
    
    result = await db.execute(select(User).where(User.id == USER_ID))
    user = result.scalar_one_or_none()
    if not user:
        user = User(id=USER_ID, email="test@test.com", full_name="Test User", hashed_password="password")
        db.add(user)
    
    workspace = Workspace(id=WORKSPACE_ID, name="Test Workspace", owner_id=USER_ID)
    db.add(workspace)
    
    member = WorkspaceMember(workspace_id=WORKSPACE_ID, user_id=USER_ID, role=WorkspaceRole.OWNER)
    db.add(member)
    
    await db.commit()

    await MongoDB.database.tenders.update_one(
        {"_id": ObjectId(TENDER_ID)},
        {"$set": {"workspace_id": WORKSPACE_ID}},
        upsert=True
    )

    yield

    await db.execute(WorkspaceMember.__table__.delete().where(WorkspaceMember.workspace_id == WORKSPACE_ID))
    await db.execute(Workspace.__table__.delete().where(Workspace.id == WORKSPACE_ID)) # Fixed typo here
    result = await db.execute(select(User).where(User.id == USER_ID))
    user = result.scalar_one_or_none()
    if user and user.email == "test@test.com":
        await db.delete(user)
        await db.commit()
        
    await MongoDB.database.tenders.update_one(
        {"_id": ObjectId(TENDER_ID)},
        {"$unset": {"workspace_id": ""}}
    )

@pytest_asyncio.fixture
async def mock_connection_manager(monkeypatch):
    mock_manager = ConnectionManager()
    mock_manager.send_to_analysis_id = AsyncMock() # Mock the async method
    monkeypatch.setattr("backend.automations.websocket.connection_manager.get_connection_manager", lambda: mock_manager)
    return mock_manager

@pytest.mark.asyncio
async def test_generate_analysis_success(client: AsyncClient, access_token: str, setup_data, monkeypatch, mock_connection_manager):
    async def mock_post(*args, **kwargs):
        return Response(200, json={"status": "success"})

    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

    response = await client.post(
        f"/tenders/{TENDER_ID}/generate_analysis",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"automation_id": AUTOMATION_ID},
    )
    
    assert response.status_code == 202
    response_data = response.json()
    assert response_data["message"] == "Analysis generation started."
    assert "analysis_id" in response_data

    # Give the background task a moment to run
    await asyncio.sleep(0.1)

    mock_connection_manager.send_to_analysis_id.assert_called_once()
    args, kwargs = mock_connection_manager.send_to_analysis_id.call_args
    assert args[0]["status"] == "COMPLETED"
    assert "result" in args[0]
    assert args[1] == response_data["analysis_id"]

@pytest.mark.asyncio
async def test_generate_analysis_tender_not_found(client: AsyncClient, access_token: str, setup_data):
    response = await client.post(
        f"/tenders/000000000000000000000000/generate_analysis",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"automation_id": AUTOMATION_ID},
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_generate_analysis_no_permission(client: AsyncClient, setup_data, test_app):
    other_user_id = str(uuid.uuid4())
    other_access_token = create_access_token(data={"sub": other_user_id})
    db_gen = test_app.dependency_overrides.get(get_db, get_db)
    db = db_gen().__next__()
    user = User(id=other_user_id, email="other@test.com", full_name="Other User", hashed_password="password")
    db.add(user)
    await db.commit()

    response = await client.post(
        f"/tenders/{TENDER_ID}/generate_analysis",
        headers={"Authorization": f"Bearer {other_access_token}"},
        json={"automation_id": AUTOMATION_ID},
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_generate_analysis_automation_not_found(client: AsyncClient, access_token: str, setup_data):
    response = await client.post(
        f"/tenders/{TENDER_ID}/generate_analysis",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"automation_id": str(uuid.uuid4())},
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_generate_analysis_n8n_fails(client: AsyncClient, access_token: str, setup_data, monkeypatch, mock_connection_manager):
    async def mock_post(*args, **kwargs):
        raise RequestError("N8N is down")

    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

    response = await client.post(
        f"/tenders/{TENDER_ID}/generate_analysis",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"automation_id": AUTOMATION_ID},
    )
    assert response.status_code == 202
    analysis_id = response.json()["analysis_id"]

    # Give the background task a moment to run
    await asyncio.sleep(0.1)

    mock_connection_manager.send_to_analysis_id.assert_called_once()
    args, kwargs = mock_connection_manager.send_to_analysis_id.call_args
    assert args[0]["status"] == "FAILED"
    assert "error" in args[0]
    assert args[1] == analysis_id

@pytest.mark.asyncio
async def test_websocket_connection(client: AsyncClient):
    async with client.websocket_connect(f"/ws/analysis/{TENDER_ID}") as websocket:
        await websocket.send_text("test message")
        # In a real scenario, you'd expect a response, but for now, just ensure connection is stable.
        # This test ensures the endpoint can be connected to.
        # The ConnectionManager mock needs to be active during this.
        assert websocket.accepted