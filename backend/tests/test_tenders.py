import pytest
import pytest_asyncio
from httpx import AsyncClient
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.tenders.tenders_utils import MongoDB
from bson import ObjectId

# --- Helper Functions ---

async def create_user_and_login(client: AsyncClient, role_name: str) -> tuple[str, dict]:
    """Creates a user, logs them in, and returns their token and user data."""
    email = f"{role_name}_{uuid.uuid4().hex[:8]}@example.com"
    password = "Password123!"
    
    signup_res = await client.post("/auth/signup", json={"email": email, "password": password, "full_name": f"{role_name.capitalize()} User"})
    assert signup_res.status_code == 201
    user_data = signup_res.json()
    
    login_res = await client.post("/auth/login/json", json={"email": email, "password": password})
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
    tender_data = {
        "workspace_id": workspace_id,
        "name": "New Public Tender",
        "description": "Construction of a new bridge",
    }
    files = {"files": ("document1.pdf", b"dummy content", "application/pdf")}
    response = await client.post("/tenders/", data=tender_data, files=files, headers=editor_headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Public Tender"
    assert data["workspace_id"] == workspace_id
    assert "id" in data

@pytest.mark.asyncio
async def test_create_tender_with_viewer_role_fails(client: AsyncClient):
    """A user with VIEWER role should NOT be able to create a tender."""
    owner_token, _ = await create_user_and_login(client, "owner")
    viewer_token, viewer_data = await create_user_and_login(client, "viewer")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    workspace_id = await create_workspace(client, owner_token)
    
    await client.post(f"/workspaces/{workspace_id}/members", json={"user_email": viewer_data["email"], "role": "VIEWER"}, headers=owner_headers)
    
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    tender_data = {
        "workspace_id": workspace_id,
        "name": "Illegal Tender",
    }
    files = {"files": ("document1.pdf", b"dummy content", "application/pdf")}
    response = await client.post("/tenders/", data=tender_data, files=files, headers=viewer_headers)
    
    assert response.status_code == 403
    assert "permission denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_and_get_tender(client: AsyncClient):
    """Test listing tenders in a workspace and getting one by ID."""
    owner_token, owner_data = await create_user_and_login(client, "owner")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    workspace_id = await create_workspace(client, owner_token)

    # Create a tender
    tender_data = {
        "workspace_id": workspace_id,
        "name": "Gettable Tender",
    }
    files = {"files": ("doc.pdf", b"dummy content", "application/pdf")}
    create_res = await client.post("/tenders/", data=tender_data, files=files, headers=owner_headers)
    assert create_res.status_code == 201
    tender_id = create_res.json()["id"]

    # List tenders in workspace
    list_res = await client.get(f"/tenders/workspace/{workspace_id}", headers=owner_headers)
    assert list_res.status_code == 200
    tenders = list_res.json()
    assert len(tenders) == 1
    assert tenders[0]["id"] == tender_id

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
    tender_data = {
        "workspace_id": workspace_id,
        "name": "Deletable Tender",
    }
    files = {"files": ("doc_to_del.pdf", b"dummy content", "application/pdf")}
    create_res = await client.post("/tenders/", data=tender_data, files=files, headers=owner_headers)
    assert create_res.status_code == 201
    tender_id = create_res.json()["id"]
    
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

@pytest_asyncio.fixture
async def setup_tender_with_analysis(client: AsyncClient):
    owner_token, owner_data = await create_user_and_login(client, "owner")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    workspace_id = await create_workspace(client, owner_token)

    tender_data = {
        "workspace_id": workspace_id,
        "name": "Analysis Tender",
    }
    files = {"files": ("analysis_doc.pdf", b"dummy content", "application/pdf")}
    create_res = await client.post("/tenders/", data=tender_data, files=files, headers=owner_headers)
    assert create_res.status_code == 201
    tender_id = create_res.json()["id"]
    
    analysis_id = str(uuid.uuid4())
    analysis_result = {
        "id": analysis_id,
        "name": "Initial Analysis",
        "procedure_id": "proc-123",
        "procedure_name": "Basic Extraction",
        "created_by": owner_data["id"],
        "status": "completed",
    }

    await MongoDB.database.tenders.update_one(
        {"_id": ObjectId(tender_id)},
        {"$push": {"analysis_results": analysis_result}}
    )
    return owner_headers, tender_id, analysis_id


@pytest.mark.asyncio
async def test_add_and_delete_analysis_result(client: AsyncClient, setup_tender_with_analysis):
    """Test adding and deleting an analysis result from a tender."""
    owner_headers, tender_id, analysis_id = setup_tender_with_analysis
    
    # Delete the analysis result
    delete_res = await client.delete(f"/tenders/{tender_id}/analysis/{analysis_id}", headers=owner_headers)
    assert delete_res.status_code == 200
    tender_after_delete = delete_res.json()
    assert len(tender_after_delete["analysis_results"]) == 0


@pytest.mark.asyncio
async def test_get_all_tenders_for_user_permissions(client: AsyncClient):
    """
    Tests that the /tenders/all_for_user endpoint correctly returns only the tenders
    a user has access to, across their own and shared workspaces.
    """
    # 1. Setup Users and Workspaces
    token_a, user_a = await create_user_and_login(client, "alpha")
    token_b, user_b = await create_user_and_login(client, "beta")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates their own workspace and tender
    ws_a_id = await create_workspace(client, token_a)
    tender_a_name = f"Tender-A-{uuid.uuid4().hex[:4]}"
    res_a = await client.post(
        "/tenders/",
        headers=headers_a,
        data={"workspace_id": ws_a_id, "name": tender_a_name},
        files={"files": ("file_a.txt", b"content", "text/plain")}
    )
    assert res_a.status_code == 201

    # User B creates their own workspace and tender
    ws_b_id = await create_workspace(client, token_b)
    tender_b_name = f"Tender-B-{uuid.uuid4().hex[:4]}"
    res_b = await client.post(
        "/tenders/",
        headers=headers_b,
        data={"workspace_id": ws_b_id, "name": tender_b_name},
        files={"files": ("file_b.txt", b"content", "text/plain")}
    )
    assert res_b.status_code == 201

    # 2. Test initial separation
    # User A should only see their own tender
    all_tenders_a_res = await client.get("/tenders/all_for_user", headers=headers_a)
    assert all_tenders_a_res.status_code == 200
    tenders_a = all_tenders_a_res.json()
    assert len(tenders_a) == 1
    assert tenders_a[0]["name"] == tender_a_name

    # User B should only see their own tender
    all_tenders_b_res = await client.get("/tenders/all_for_user", headers=headers_b)
    assert all_tenders_b_res.status_code == 200
    tenders_b = all_tenders_b_res.json()
    assert len(tenders_b) == 1
    assert tenders_b[0]["name"] == tender_b_name

    # 3. Test after sharing a workspace
    # User A adds User B to their workspace
    add_member_res = await client.post(
        f"/workspaces/{ws_a_id}/members",
        headers=headers_a,
        json={"user_email": user_b["email"], "role": "VIEWER"}
    )
    assert add_member_res.status_code == 201

    # Now, User B should see both their own tender and User A's tender
    all_tenders_b_shared_res = await client.get("/tenders/all_for_user", headers=headers_b)
    assert all_tenders_b_shared_res.status_code == 200
    tenders_b_shared = all_tenders_b_shared_res.json()
    assert len(tenders_b_shared) == 2
    
    seen_names = {t["name"] for t in tenders_b_shared}
    assert tender_a_name in seen_names
    assert tender_b_name in seen_names

    # User A's view should remain unchanged
    all_tenders_a_after_share_res = await client.get("/tenders/all_for_user", headers=headers_a)
    assert all_tenders_a_after_share_res.status_code == 200
    tenders_a_after_share = all_tenders_a_after_share_res.json()
    assert len(tenders_a_after_share) == 1
    assert tenders_a_after_share[0]["name"] == tender_a_name

@pytest.mark.asyncio
async def test_patch_tender(client: AsyncClient):
    """Test updating a tender's name."""
    owner_token, owner_data = await create_user_and_login(client, "owner_patch")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    workspace_id = await create_workspace(client, owner_token)

    tender_data = {
        "workspace_id": workspace_id,
        "name": "Old Tender Name",
    }
    create_res = await client.post("/tenders/", data=tender_data, headers=owner_headers)
    assert create_res.status_code == 201
    tender_id = create_res.json()["id"]

    patch_payload = {"name": "New Tender Name"}
    patch_res = await client.patch(f"/tenders/{tender_id}", json=patch_payload, headers=owner_headers)
    
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "New Tender Name"

@pytest.mark.asyncio
async def test_add_and_delete_document(client: AsyncClient):
    """Test adding and deleting a document from an existing tender."""
    owner_token, owner_data = await create_user_and_login(client, "owner_doc")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    workspace_id = await create_workspace(client, owner_token)

    # Need at least one doc to create the tender
    create_res = await client.post(
        "/tenders/",
        headers=owner_headers,
        data={"workspace_id": workspace_id, "name": "Document Tender"},
        files={"files": ("file1.txt", b"content", "text/plain")}
    )
    assert create_res.status_code == 201
    tender_id = create_res.json()["id"]
    
    # Add a new document
    add_res = await client.post(
        f"/tenders/{tender_id}/documents",
        headers=owner_headers,
        files={"files": ("file2.txt", b"new content", "text/plain")}
    )
    assert add_res.status_code == 200
    data = add_res.json()
    assert len(data["documents"]) == 2
    
    doc_to_delete_id = data["documents"][1]["id"]
    
    # Delete the document
    del_res = await client.delete(f"/tenders/{tender_id}/documents/{doc_to_delete_id}", headers=owner_headers)
    assert del_res.status_code == 200
    assert len(del_res.json()["documents"]) == 1

@pytest.mark.asyncio
async def test_rename_analysis_result(client: AsyncClient, setup_tender_with_analysis):
    """Test renaming an analysis result."""
    owner_headers, tender_id, analysis_id = setup_tender_with_analysis
    
    # Rename
    patch_res = await client.patch(
        f"/analysis-results/{analysis_id}",
        json={"name": "New Analysis Name"},
        headers=owner_headers
    )
    assert patch_res.status_code == 200
    
    # Verify
    get_res = await client.get(f"/tenders/{tender_id}", headers=owner_headers)
    updated_analysis = next(ar for ar in get_res.json()["analysis_results"] if ar["id"] == analysis_id)
    assert updated_analysis["name"] == "New Analysis Name"

@pytest.mark.asyncio
async def test_generate_analysis_has_pending_since(client: AsyncClient, monkeypatch):
    """Test that generating an analysis initializes the 'pending_since' field."""
    from backend.automations.models import Automation
    from backend.auth.database import get_db
    from sqlalchemy import insert

    owner_token, owner_data = await create_user_and_login(client, "owner_gen")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    workspace_id = await create_workspace(client, owner_token)

    # 1. Create a tender
    tender_res = await client.post(
        "/tenders/",
        headers=owner_headers,
        data={"workspace_id": workspace_id, "name": "Gen Tender"},
        files={"files": ("file.pdf", b"content", "application/pdf")}
    )
    tender_id = tender_res.json()["id"]

    # 2. Create a dummy automation in PostgreSQL
    automation_id = str(uuid.uuid4())
    async for db in get_db():
        await db.execute(
            insert(Automation).values(
                id=uuid.UUID(automation_id),
                name="Test Auto",
                url="http://localhost/webhook",
                owner_id=uuid.UUID(owner_data["id"])
            )
        )
        await db.commit()
        break

    # 3. Mock the background task httpx call
    import httpx
    async def mock_post(*args, **kwargs):
        class MockResponse:
            def raise_for_status(self): pass
        return MockResponse()
    
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    # 4. Generate analysis
    gen_res = await client.post(
        f"/tenders/{tender_id}/generate_analysis",
        json={"automation_id": automation_id, "name": "My Analysis"},
        headers=owner_headers
    )
    assert gen_res.status_code == 200
    
    # 5. Verify pending_since in the tender response
    get_res = await client.get(f"/tenders/{tender_id}", headers=owner_headers)
    assert get_res.status_code == 200
    tender_data = get_res.json()
    assert len(tender_data["analysis_results"]) == 1
    analysis = tender_data["analysis_results"][0]
    assert analysis["status"] in ["pending", "processing"]
    assert "pending_since" in analysis
    assert analysis["pending_since"] is not None
    
    # Verify it's a valid ISO format date
    from datetime import datetime
    datetime.fromisoformat(analysis["pending_since"].replace('Z', '+00:00'))