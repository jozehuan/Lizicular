
import pytest
from httpx import AsyncClient
import uuid

# --- Helper Functions ---

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

async def create_workspace(client: AsyncClient, owner_token: str) -> str:
    """Creates a workspace and returns its ID."""
    headers = {"Authorization": f"Bearer {owner_token}"}
    response = await client.post("/workspaces/", json={"name": "Test Workspace for Tenders"}, headers=headers)
    assert response.status_code == 201
    return response.json()["id"]

# --- Tender Endpoint Tests ---

@pytest.mark.asyncio
async def test_create_tender_with_editor_role(client: AsyncClient):
    """A user with EDITOR role should be able to create a tender."""
    # 1. Create Owner and Editor users
    owner_token, _ = await create_user_and_login(client, "owner")
    editor_token, editor_data = await create_user_and_login(client, "editor")

    # 2. Owner creates a workspace
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    workspace_id = await create_workspace(client, owner_token)
    
    # 3. Owner adds the second user as an EDITOR
    await client.post(f"/workspaces/{workspace_id}/members", json={"user_email": editor_data["email"], "role": "EDITOR"}, headers=owner_headers)
    
    # 4. Editor creates a tender in that workspace
    editor_headers = {"Authorization": f"Bearer {editor_token}"}
    tender_payload = {
        "workspace_id": workspace_id,
        "name": "New Public Tender",
        "description": "Construction of a new bridge",
        "created_by": editor_data["id"],
        "documents": [{
            "id": str(uuid.uuid4()),
            "name": "document1.pdf",
            "file_type": "pdf",
            "file_size": 1024,
            "file_url": "s3://bucket/document1.pdf",
            "uploaded_by": editor_data["id"]
        }]
    }
    response = await client.post("/tenders/", json=tender_payload, headers=editor_headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Public Tender"
    assert data["workspace_id"] == workspace_id
    assert "_id" in data

@pytest.mark.asyncio
async def test_create_tender_with_viewer_role_fails(client: AsyncClient):
    """A user with VIEWER role should NOT be able to create a tender."""
    owner_token, _ = await create_user_and_login(client, "owner")
    viewer_token, viewer_data = await create_user_and_login(client, "viewer")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    workspace_id = await create_workspace(client, owner_token)
    
    await client.post(f"/workspaces/{workspace_id}/members", json={"user_email": viewer_data["email"], "role": "VIEWER"}, headers=owner_headers)
    
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    tender_payload = {
        "workspace_id": workspace_id,
        "name": "Illegal Tender",
        "created_by": viewer_data["id"],
        "documents": [{
            "id": str(uuid.uuid4()),
            "name": "document1.pdf",
            "file_type": "pdf",
            "file_size": 1024,
            "file_url": "s3://bucket/document1.pdf",
            "uploaded_by": viewer_data["id"]
        }]
    }
    response = await client.post("/tenders/", json=tender_payload, headers=viewer_headers)
    
    assert response.status_code == 403
    assert "permission denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_and_get_tender(client: AsyncClient):
    """Test listing tenders in a workspace and getting one by ID."""
    owner_token, owner_data = await create_user_and_login(client, "owner")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    workspace_id = await create_workspace(client, owner_token)

    # Create a tender
    tender_payload = {
        "workspace_id": workspace_id,
        "name": "Gettable Tender",
        "created_by": owner_data["id"],
        "documents": [{
            "id": str(uuid.uuid4()),
            "name": "doc.pdf",
            "file_type": "pdf",
            "file_size": 2048,
            "file_url": "s3://bucket/doc.pdf",
            "uploaded_by": owner_data["id"]
        }]
    }
    create_res = await client.post("/tenders/", json=tender_payload, headers=owner_headers)
    assert create_res.status_code == 201
    tender_id = create_res.json()["_id"]

    # List tenders in workspace
    list_res = await client.get(f"/tenders/workspace/{workspace_id}", headers=owner_headers)
    assert list_res.status_code == 200
    tenders = list_res.json()
    assert len(tenders) == 1
    assert tenders[0]["_id"] == tender_id

    # Get tender by ID
    get_res = await client.get(f"/tenders/{tender_id}", headers=owner_headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Gettable Tender"

@pytest.mark.asyncio
async def test_delete_tender_with_admin_role(client: AsyncClient):
    """A user with ADMIN role should be able to delete a tender."""
    owner_token, owner_data = await create_user_and_login(client, "owner")
    admin_token, admin_data = await create_user_and_login(client, "admin")
    
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    workspace_id = await create_workspace(client, owner_token)
    
    # Owner creates a tender
    tender_payload = {
        "workspace_id": workspace_id,
        "name": "Deletable Tender",
        "created_by": owner_data["id"],
        "documents": [{
            "id": str(uuid.uuid4()),
            "name": "doc_to_del.pdf",
            "file_type": "pdf",
            "file_size": 100,
            "file_url": "s3://bucket/doc.pdf",
            "uploaded_by": owner_data["id"]
        }]
    }
    create_res = await client.post("/tenders/", json=tender_payload, headers=owner_headers)
    assert create_res.status_code == 201
    tender_id = create_res.json()["_id"]
    
    # Owner makes the other user an ADMIN
    await client.post(f"/workspaces/{workspace_id}/members", json={"user_email": admin_data["email"], "role": "ADMIN"}, headers=owner_headers)
    
    # Admin deletes the tender
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    delete_res = await client.delete(f"/tenders/{tender_id}", headers=admin_headers)
    
    assert delete_res.status_code == 200
    assert delete_res.json()["status"] == "deleted"
    
    # Verify it's gone
    get_res = await client.get(f"/tenders/{tender_id}", headers=owner_headers)
    assert get_res.status_code == 404

# --- Analysis Results Tests ---

@pytest.mark.asyncio
async def test_add_and_delete_analysis_result(client: AsyncClient):
    """Test adding and deleting an analysis result from a tender."""
    owner_token, owner_data = await create_user_and_login(client, "owner")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    workspace_id = await create_workspace(client, owner_token)

    # Create a tender
    tender_payload = {
        "workspace_id": workspace_id,
        "name": "Analysis Tender",
        "created_by": owner_data["id"],
        "documents": [{
            "id": str(uuid.uuid4()),
            "name": "analysis_doc.pdf",
            "file_type": "pdf",
            "file_size": 512,
            "file_url": "s3://bucket/doc.pdf",
            "uploaded_by": owner_data["id"]
        }]
    }
    create_res = await client.post("/tenders/", json=tender_payload, headers=owner_headers)
    assert create_res.status_code == 201
    tender_id = create_res.json()["_id"]

    # Add an analysis result
    analysis_payload = {
        "id": str(uuid.uuid4()),
        "name": "Initial Analysis",
        "procedure_id": "proc-123",
        "procedure_name": "Basic Extraction",
        "created_by": owner_data["id"],
        "data": {}
    }
    add_res = await client.post(f"/tenders/{tender_id}/analysis", json=analysis_payload, headers=owner_headers)
    assert add_res.status_code == 200
    tender_with_analysis = add_res.json()
    assert len(tender_with_analysis["analysis_results"]) == 1
    
    result_id = tender_with_analysis["analysis_results"][0]["id"]
    
    # Delete the analysis result
    delete_res = await client.delete(f"/tenders/{tender_id}/analysis/{result_id}", headers=owner_headers)
    assert delete_res.status_code == 200
    tender_after_delete = delete_res.json()
    assert len(tender_after_delete["analysis_results"]) == 0
