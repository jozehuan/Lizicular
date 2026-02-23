import pytest
from httpx import AsyncClient
import uuid

# --- Helper Functions ---

async def create_user(client: AsyncClient, email: str, password: str = "Password123!") -> dict:
    """Helper to create a user and return its data."""
    response = await client.post("/auth/signup", json={"email": email, "password": password, "full_name": "Test User"})
    assert response.status_code == 201
    return response.json()

async def login_and_get_token(client: AsyncClient, email: str, password: str = "Password123!") -> str:
    """Helper to log in a user and return the access token."""
    response = await client.post("/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]

# --- Workspace Tests ---

@pytest.mark.asyncio
async def test_create_workspace(client: AsyncClient):
    """Test creating a new workspace successfully."""
    user_email = f"owner_{uuid.uuid4().hex[:8]}@example.com"
    await create_user(client, user_email)
    token = await login_and_get_token(client, user_email)
    
    headers = {"Authorization": f"Bearer {token}"}
    workspace_data = {"name": "My First Workspace", "description": "A test workspace"}
    
    response = await client.post("/workspaces/", json=workspace_data, headers=headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == workspace_data["name"]
    assert "id" in data
    
    # Verify the creator is also a member with role OWNER
    members_response = await client.get(f"/workspaces/{data['id']}/members", headers=headers)
    assert members_response.status_code == 200
    members = members_response.json()
    assert len(members) == 1
    assert members[0]["email"] == user_email
    assert members[0]["role"] == "OWNER"

@pytest.mark.asyncio
async def test_get_user_workspaces(client: AsyncClient):
    """Test listing all workspaces a user is a member of."""
    user_email = f"member_{uuid.uuid4().hex[:8]}@example.com"
    await create_user(client, user_email)
    token = await login_and_get_token(client, user_email)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create two workspaces
    await client.post("/workspaces/", json={"name": "Workspace A"}, headers=headers)
    await client.post("/workspaces/", json={"name": "Workspace B"}, headers=headers)
    
    response = await client.get("/workspaces/", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert "Workspace A" in [w["name"] for w in data]
    assert "Workspace B" in [w["name"] for w in data]

# --- Member Management Tests ---

@pytest.mark.asyncio
async def test_add_member_to_workspace(client: AsyncClient):
    """Test that an owner can add a new member to a workspace."""
    owner_email = f"owner_add_{uuid.uuid4().hex[:8]}@example.com"
    editor_email = f"editor_{uuid.uuid4().hex[:8]}@example.com"
    
    # Create owner and new user
    await create_user(client, owner_email)
    await create_user(client, editor_email)
    
    # Owner logs in and creates a workspace
    owner_token = await login_and_get_token(client, owner_email)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    ws_res = await client.post("/workspaces/", json={"name": "Collaboration Space"}, headers=owner_headers)
    workspace_id = ws_res.json()["id"]
    
    # Owner adds the new user as an EDITOR
    add_payload = {"user_email": editor_email, "role": "EDITOR"}
    response = await client.post(f"/workspaces/{workspace_id}/members", json=add_payload, headers=owner_headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == editor_email
    assert data["role"] == "EDITOR"
    
    # Verify the new member is in the list
    members_res = await client.get(f"/workspaces/{workspace_id}/members", headers=owner_headers)
    assert len(members_res.json()) == 2

@pytest.mark.asyncio
async def test_non_admin_cannot_add_member(client: AsyncClient):
    """Test that a non-admin/non-owner cannot add members."""
    owner_email = f"owner_deny_{uuid.uuid4().hex[:8]}@example.com"
    editor_email = f"editor_deny_{uuid.uuid4().hex[:8]}@example.com"
    new_user_email = f"new_user_deny_{uuid.uuid4().hex[:8]}@example.com"

    # Create users
    await create_user(client, owner_email)
    await create_user(client, editor_email)
    await create_user(client, new_user_email)

    # Owner creates workspace and adds editor
    owner_token = await login_and_get_token(client, owner_email)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    ws_res = await client.post("/workspaces/", json={"name": "Limited Access"}, headers=owner_headers)
    workspace_id = ws_res.json()["id"]
    await client.post(f"/workspaces/{workspace_id}/members", json={"user_email": editor_email, "role": "EDITOR"}, headers=owner_headers)

    # Editor (non-admin) tries to add another user
    editor_token = await login_and_get_token(client, editor_email)
    editor_headers = {"Authorization": f"Bearer {editor_token}"}
    add_payload = {"user_email": new_user_email, "role": "VIEWER"}
    response = await client.post(f"/workspaces/{workspace_id}/members", json=add_payload, headers=editor_headers)
    
    assert response.status_code == 403
    assert "only workspace owners or admins can add members" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_owner_can_remove_member(client: AsyncClient):
    """Test that an owner can remove a member from a workspace."""
    owner_email = f"owner_remove_{uuid.uuid4().hex[:8]}@example.com"
    editor_email = f"editor_remove_{uuid.uuid4().hex[:8]}@example.com"
    
    owner_data = await create_user(client, owner_email)
    editor_data = await create_user(client, editor_email)
    
    owner_token = await login_and_get_token(client, owner_email)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    
    ws_res = await client.post("/workspaces/", json={"name": "Removal Test"}, headers=owner_headers)
    workspace_id = ws_res.json()["id"]
    
    # Add editor
    await client.post(f"/workspaces/{workspace_id}/members", json={"user_email": editor_email, "role": "EDITOR"}, headers=owner_headers)
    
    # Verify member count is 2
    members_res = await client.get(f"/workspaces/{workspace_id}/members", headers=owner_headers)
    assert len(members_res.json()) == 2
    
    # Owner removes editor
    editor_id = editor_data["id"]
    response = await client.delete(f"/workspaces/{workspace_id}/members/{editor_id}", headers=owner_headers)
    assert response.status_code == 204
    
    # Verify member count is now 1
    members_res_after = await client.get(f"/workspaces/{workspace_id}/members", headers=owner_headers)
    assert len(members_res_after.json()) == 1
    assert members_res_after.json()[0]["email"] == owner_email

@pytest.mark.asyncio
async def test_cannot_remove_workspace_owner(client: AsyncClient):
    """Test that the owner of a workspace cannot be removed."""
    owner_email = f"owner_noremo_{uuid.uuid4().hex[:8]}@example.com"
    owner_data = await create_user(client, owner_email)
    owner_token = await login_and_get_token(client, owner_email)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    
    ws_res = await client.post("/workspaces/", json={"name": "No Remove Owner"}, headers=owner_headers)
    workspace_id = ws_res.json()["id"]
    owner_id = owner_data["id"]
    
    response = await client.delete(f"/workspaces/{workspace_id}/members/{owner_id}", headers=owner_headers)
    
    assert response.status_code == 400
    assert "workspace owner cannot be removed" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_update_workspace(client: AsyncClient):
    """Test updating a workspace's name and description."""
    owner_email = f"owner_update_{uuid.uuid4().hex[:8]}@example.com"
    await create_user(client, owner_email)
    token = await login_and_get_token(client, owner_email)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create workspace
    ws_res = await client.post("/workspaces/", json={"name": "Old Name", "description": "Old Desc"}, headers=headers)
    workspace_id = ws_res.json()["id"]
    
    # Update workspace
    update_payload = {"name": "New Name", "description": "New Desc"}
    update_res = await client.put(f"/workspaces/{workspace_id}", json=update_payload, headers=headers)
    
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["name"] == "New Name"
    assert data["description"] == "New Desc"