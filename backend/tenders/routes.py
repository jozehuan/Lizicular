from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Any, Dict
import uuid
import asyncio
from urllib.parse import quote
from starlette.responses import StreamingResponse
import io
from bson import ObjectId
import httpx
from fastapi.responses import JSONResponse
from fastapi import Query
from sqlalchemy.orm import selectinload
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.auth.database import get_db
from backend.auth.auth_utils import get_current_active_user
from backend.auth.audit_utils import log_tender_event, create_audit_log
from backend.auth.models import AuditAction, AuditCategory, User
from backend.workspaces.models import Workspace, WorkspaceRole, WorkspaceMember
from backend.tenders.schemas import (
    Tender, TenderCreate, TenderUpdate, AnalysisResult, 
    GenerateAnalysisRequest, GenerateAnalysisResponse, AnalysisStatus,
    AnalysisResultSummary
)
from backend.tenders.tenders_utils import (
    create_tender, get_tender_by_id, get_tenders_by_workspace,
    update_tender, delete_tender, add_analysis_result_to_tender,
    delete_analysis_result, delete_document, add_documents_to_existing_tender,
    create_placeholder_analysis, update_analysis_result, get_analysis_by_id, get_tender_by_analysis_id,
    get_all_tenders_for_user, get_mongo_db, MongoDB, check_for_existing_analysis
)
from backend.automations.models import Automation
from backend.automations.websocket.connection_manager import ConnectionManager, get_connection_manager
from backend.workspaces.schemas import TenderSummaryResponse


router = APIRouter(prefix="/tenders", tags=["Tenders"])

async def check_workspace_permission(
    workspace_id: str,
    user_id: Any,
    db: AsyncSession,
    required_role: WorkspaceRole = WorkspaceRole.EDITOR
) -> bool:
    role_hierarchy = {
        WorkspaceRole.OWNER: 4,
        WorkspaceRole.ADMIN: 3,
        WorkspaceRole.EDITOR: 2,
        WorkspaceRole.VIEWER: 1
    }
    try:
        member_result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == uuid.UUID(workspace_id),
                WorkspaceMember.user_id == user_id
            )
        )
        member = member_result.scalar_one_or_none()
        if not member:
            return False
        return role_hierarchy.get(member.role, 0) >= role_hierarchy.get(required_role, 0)
    except (ValueError, TypeError):
        return False

# ============================================================================
# TENDERS ENDPOINTS (MongoDB)
# ============================================================================

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create a new tender")
async def api_create_tender(
    request: Request,
    name: str = Form(...),
    workspace_id: str = Form(...),
    description: str | None = Form(None),
    files: List[UploadFile] = File(default_factory=list),
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user: Any = Depends(get_current_active_user)
):
    if not await check_workspace_permission(workspace_id, current_user.id, db):
        raise HTTPException(status_code=403, detail="Permission denied in this workspace")
    
    tender_create_data = TenderCreate(
        name=name,
        description=description,
        workspace_id=workspace_id,
        created_by=str(current_user.id)
    )
    
    new_tender = await create_tender(mongo_db, tender_create_data, files, str(current_user.id))
    
    await log_tender_event(
        db=db,
        action=AuditAction.TENDER_CREATE,
        tender_id=str(new_tender.id),
        workspace_id=uuid.UUID(workspace_id),
        user_id=current_user.id,
        request=request,
        name=new_tender.name,
        payload={"files_count": len(files)}
    )
    
    return new_tender


@router.get("/workspace/{workspace_id}", response_model=List[Tender], summary="List tenders in workspace")
async def api_get_tenders(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user: Any = Depends(get_current_active_user)
):
    if not await check_workspace_permission(workspace_id, current_user.id, db, WorkspaceRole.VIEWER):
        raise HTTPException(status_code=403, detail="Access denied to this workspace")
    
    return await get_tenders_by_workspace(mongo_db, workspace_id)


@router.get("/find_by_name", response_model=List[TenderSummaryResponse], summary="Find tenders by name across user's workspaces")
async def api_find_tender_by_name(
    name: str = Query(..., description="Name of the tender to search for."),
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user: User = Depends(get_current_active_user)
):
    tenders = await get_all_tenders_for_user(db, current_user.id, mongo_db, name=name)
    if not tenders:
        return []

    workspace_ids = {uuid.UUID(t.workspace_id) for t in tenders if t.workspace_id}
    if not workspace_ids:
        return []
        
    workspace_results = await db.execute(
        select(Workspace.id, Workspace.name).where(Workspace.id.in_(workspace_ids))
    )
    workspace_map = {str(ws_id): ws_name for ws_id, ws_name in workspace_results}

    return [
        TenderSummaryResponse(
            id=str(t.id),
            name=t.name,
            created_at=t.created_at,
            workspace_id=uuid.UUID(t.workspace_id),
            workspace_name=workspace_map.get(t.workspace_id, "Unknown Workspace")
        )
        for t in tenders if t.workspace_id in workspace_map
    ]


@router.get("/all_for_user", response_model=List[TenderSummaryResponse], summary="Get all tenders visible to the current user")
async def api_get_all_tenders_for_user(
    name: str = Query(None, description="Optional filter by tender name."),
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user: User = Depends(get_current_active_user)
):
    tenders = await get_all_tenders_for_user(db, current_user.id, mongo_db, name=name)
    if not tenders:
        return []

    valid_workspace_ids = set()
    for t in tenders:
        try:
            valid_workspace_ids.add(uuid.UUID(t.workspace_id))
        except (ValueError, TypeError):
            print(f"WARNING: Tender with ID {t.id} has an invalid or null workspace_id '{t.workspace_id}'. Skipping.")
            continue

    if not valid_workspace_ids:
        return []

    workspace_results = await db.execute(
        select(Workspace.id, Workspace.name).where(Workspace.id.in_(valid_workspace_ids))
    )
    workspace_map = {str(ws_id): ws_name for ws_id, ws_name in workspace_results}

    response_list = []
    for t in tenders:
        if t.workspace_id in workspace_map:
            response_list.append(
                TenderSummaryResponse(
                    id=str(t.id),
                    name=t.name,
                    created_at=t.created_at,
                    workspace_id=uuid.UUID(t.workspace_id),
                    workspace_name=workspace_map.get(t.workspace_id, "Unknown Workspace")
                )
            )
    return response_list


@router.get("/{tender_id}", response_model=Tender, summary="Get tender details")
async def api_get_tender(
    tender_id: str,
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user: Any = Depends(get_current_active_user)
):
    tender = await get_tender_by_id(mongo_db, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    if not await check_workspace_permission(tender.workspace_id, current_user.id, db, WorkspaceRole.VIEWER):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return tender

@router.patch("/{tender_id}", response_model=Tender, summary="Update tender")
async def api_update_tender(
    tender_id: str,
    update_data: TenderUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user: Any = Depends(get_current_active_user)
):
    tender = await get_tender_by_id(mongo_db, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    if not await check_workspace_permission(tender.workspace_id, current_user.id, db):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    updated = await update_tender(mongo_db, tender_id, update_data)
    
    await log_tender_event(
        db=db,
        action=AuditAction.TENDER_UPDATE,
        tender_id=tender_id,
        workspace_id=uuid.UUID(tender.workspace_id) if isinstance(tender.workspace_id, str) else tender.workspace_id,
        user_id=current_user.id,
        request=request,
        changes=update_data.model_dump(exclude_unset=True)
    )
    
    return updated


@router.delete("/{tender_id}", summary="Delete tender")
async def api_delete_tender(
    tender_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user: Any = Depends(get_current_active_user)
):
    tender = await get_tender_by_id(mongo_db, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    if not await check_workspace_permission(tender.workspace_id, current_user.id, db, WorkspaceRole.ADMIN):
        raise HTTPException(status_code=403, detail="Permission denied (Admin required)")
    
    success = await delete_tender(mongo_db, tender_id)
    
    if success:
        await log_tender_event(
            db=db,
            action=AuditAction.TENDER_DELETE,
            tender_id=tender_id,
            workspace_id=uuid.UUID(tender.workspace_id) if isinstance(tender.workspace_id, str) else tender.workspace_id,
            user_id=current_user.id,
            request=request,
            name=tender.name
        )
        
    return {"status": "deleted" if success else "failed"}


@router.get("/{tender_id}/documents/{document_id}/download", summary="Download a tender document")
async def api_download_tender_document(
    tender_id: str,
    document_id: str,
    db_session: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user: Any = Depends(get_current_active_user)
):
    tender = await get_tender_by_id(mongo_db, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    if not await check_workspace_permission(tender.workspace_id, current_user.id, db_session, WorkspaceRole.VIEWER):
        raise HTTPException(status_code=403, detail="Access denied to this tender's documents")

    doc_metadata = next((doc for doc in tender.documents if doc.id == document_id), None)
    if not doc_metadata:
        raise HTTPException(status_code=404, detail="Document not found within this tender")

    file_record = await mongo_db.tender_files.find_one({"_id": ObjectId(document_id)})
    if not file_record or not file_record.get("data"):
        raise HTTPException(status_code=404, detail="File content not found")

    file_content = file_record["data"]
    
    encoded_filename = quote(doc_metadata.filename)
    
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=doc_metadata.content_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )


@router.post("/{tender_id}/documents", response_model=Tender, summary="Add document(s) to a tender")
async def api_add_documents_to_tender(
    tender_id: str,
    request: Request,
    files: List[UploadFile] = File(...),
    db_session: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user: Any = Depends(get_current_active_user)
):
    tender = await get_tender_by_id(mongo_db, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    if not await check_workspace_permission(tender.workspace_id, current_user.id, db_session, WorkspaceRole.EDITOR):
        raise HTTPException(status_code=403, detail="Permission denied (Editor role required)")

    updated_tender = await add_documents_to_existing_tender(mongo_db, tender_id, files)

    await log_tender_event(
        db=db_session,
        action=AuditAction.TENDER_UPDATE,
        tender_id=tender_id,
        workspace_id=uuid.UUID(tender.workspace_id),
        user_id=current_user.id,
        request=request,
        details=f"Added {len(files)} document(s) to tender",
        payload={"added_files": [file.filename for file in files]}
    )
    return updated_tender


@router.delete("/{tender_id}/documents/{document_id}", response_model=Tender, summary="Delete a document from a tender")
async def api_delete_document_from_tender(
    tender_id: str,
    document_id: str,
    request: Request,
    db_session: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user: Any = Depends(get_current_active_user)
):
    tender = await get_tender_by_id(mongo_db, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    if not await check_workspace_permission(tender.workspace_id, current_user.id, db_session, WorkspaceRole.EDITOR):
        raise HTTPException(status_code=403, detail="Permission denied (Editor role required)")
    
    document_to_delete = next((doc for doc in tender.documents if doc.id == document_id), None)
    if not document_to_delete:
        raise HTTPException(status_code=404, detail="Document not found in this tender")
    
    deleted_filename = document_to_delete.filename

    updated_tender = await delete_document(mongo_db, tender_id, document_id)

    await log_tender_event(
        db=db_session,
        action=AuditAction.TENDER_UPDATE,
        tender_id=tender_id,
        workspace_id=uuid.UUID(tender.workspace_id),
        user_id=current_user.id,
        request=request,
        details=f"Deleted document from tender",
        payload={"deleted_file": deleted_filename}
    )
    return updated_tender

@router.post("/{tender_id}/analysis", response_model=Tender, tags=["Analysis"])
async def api_add_analysis(
    tender_id: str,
    analysis_result: AnalysisResult,
    request: Request,
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user: Any = Depends(get_current_active_user)
):
    tender = await get_tender_by_id(mongo_db, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    if not await check_workspace_permission(tender.workspace_id, current_user.id, db):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = await add_analysis_result_to_tender(mongo_db, tender_id, analysis_result)
    
    await log_tender_event(
        db=db,
        action=AuditAction.TENDER_ANALYZE,
        tender_id=tender_id,
        workspace_id=uuid.UUID(tender.workspace_id),
        user_id=current_user.id,
        request=request,
        analysis_name=analysis_result.name
    )
    return result


@router.delete("/{tender_id}/analysis/{result_id}", response_model=Tender, tags=["Analysis"])
async def api_delete_analysis(
    tender_id: str,
    result_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user: Any = Depends(get_current_active_user)
):
    tender = await get_tender_by_id(mongo_db, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    if not await check_workspace_permission(tender.workspace_id, current_user.id, db, WorkspaceRole.EDITOR):
        raise HTTPException(status_code=403, detail="Permission denied (Editor role required)")
    
    result = await delete_analysis_result(mongo_db, tender_id, result_id)
    
    await log_tender_event(
        db=db,
        action=AuditAction.TENDER_UPDATE,
        tender_id=tender_id,
        workspace_id=uuid.UUID(tender.workspace_id),
        user_id=current_user.id,
        request=request,
        details=f"Deleted analysis result {result_id}"
    )
    return result

async def run_analysis_in_background(
    tender_id: str,
    analysis_id: str,
    automation_url: str,
    automation_id: str,
    user_id: str,
    workspace_id: str,
    client_ip: str | None,
    manager_instance: ConnectionManager,
):
    await update_analysis_result(MongoDB.database, tender_id, analysis_id, status=AnalysisStatus.PROCESSING)
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Call the external automation service
            response = await client.post(
                automation_url,
                json={"tender_id": tender_id, "analysis_id": analysis_id},
                timeout=900.0,
            )
            response.raise_for_status()
            
            # This is the correct analysis data from the automation
            analysis_data = response.json()

            # 2. After getting the result, check if the parent tender still exists
            tender = await get_tender_by_analysis_id(MongoDB.database, analysis_id)
            if not tender:
                print(f"Tender for analysis_id {analysis_id} was deleted during processing. Aborting update.")
                await manager_instance.send_to_analysis_id({"status": "ABORTED", "error": "Tender was deleted."}, analysis_id)
                # No need to do anything with analysis_data, as the parent is gone
                return

            # 3. If tender exists, proceed with the update
            await update_analysis_result(
                MongoDB.database, 
                tender.id,  # Use the confirmed tender ID
                analysis_id, 
                status=AnalysisStatus.COMPLETED, 
                data=analysis_data
            )
            
            # 4. Log the successful event
            async for db in get_db():
                await log_tender_event(
                    db=db,
                    action=AuditAction.TENDER_ANALYZE,
                    tender_id=tender.id,
                    workspace_id=uuid.UUID(tender.workspace_id),
                    user_id=uuid.UUID(user_id),
                    ip_address=client_ip,
                    details="Generated analysis with automation",
                    payload={"automation_id": automation_id}
                )

        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            error_message = f"Error from automation service: {e}"
            # Also check for tender existence before updating with an error
            tender = await get_tender_by_analysis_id(MongoDB.database, analysis_id)
            if tender:
                await update_analysis_result(MongoDB.database, tender.id, analysis_id, status=AnalysisStatus.FAILED, error_message=error_message)
                await manager_instance.send_to_analysis_id({"status": "FAILED", "error": error_message}, analysis_id)
            else:
                print(f"Tender for analysis_id {analysis_id} was deleted. Skipping error update.")

        except Exception as e:
            error_message = f"An unexpected error occurred in background task: {e}"
            # Also check for tender existence before updating with an error
            tender = await get_tender_by_analysis_id(MongoDB.database, analysis_id)
            if tender:
                await update_analysis_result(MongoDB.database, tender.id, analysis_id, status=AnalysisStatus.FAILED, error_message=error_message)
                await manager_instance.send_to_analysis_id({"status": "FAILED", "error": error_message}, analysis_id)
            else:
                print(f"Tender for analysis_id {analysis_id} was deleted. Skipping error update.")
        else:
            # 5. If everything was successful, notify the client via WebSocket
            analysis_result = await get_analysis_by_id(MongoDB.database, tender.id, analysis_id)
            if analysis_result:
                 await manager_instance.send_to_analysis_id({"status": "COMPLETED", "result": analysis_result.model_dump()}, analysis_id)
            else:
                 # This case is unlikely if the update succeeded, but good to handle
                 await manager_instance.send_to_analysis_id({"status": "FAILED", "error": "Could not retrieve final analysis."}, analysis_id)

@router.post("/{tender_id}/generate_analysis", status_code=status.HTTP_202_ACCEPTED, response_model=GenerateAnalysisResponse, tags=["Analysis"])
async def api_generate_analysis(
    tender_id: str,
    analysis_request: GenerateAnalysisRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user: Any = Depends(get_current_active_user),
    manager_instance: ConnectionManager = Depends(get_connection_manager)
):
    tender = await get_tender_by_id(mongo_db, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    if not await check_workspace_permission(tender.workspace_id, current_user.id, db, WorkspaceRole.EDITOR):
        raise HTTPException(status_code=403, detail="Permission denied (Editor role required)")

    if await check_for_existing_analysis(mongo_db, tender_id, analysis_request.automation_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An analysis for this tender with the same automation is already pending or processing."
        )

    automation = await db.get(Automation, uuid.UUID(analysis_request.automation_id))
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")

    placeholder = await create_placeholder_analysis(mongo_db, tender_id, analysis_request.automation_id, str(current_user.id), name=analysis_request.name)

    if not placeholder:
        raise HTTPException(status_code=500, detail="Could not create analysis placeholder")

    background_tasks.add_task(
        run_analysis_in_background,
        tender_id=tender_id,
        analysis_id=placeholder.id,
        automation_url=automation.url,
        automation_id=str(automation.id),
        user_id=str(current_user.id),
        workspace_id=tender.workspace_id,
        client_ip=request.client.host if request.client else None,
        manager_instance=manager_instance,
    )
    
    return GenerateAnalysisResponse(
        message="Analysis generation started.",
        analysis_id=placeholder.id
    )

analysis_router = APIRouter(prefix="/analysis-results", tags=["Analysis"])

@analysis_router.get("/all_for_user", response_model=List[AnalysisResultSummary], summary="Get all analysis results visible to the current user")
async def api_get_all_analysis_results_for_user(
    name: str = Query(None, description="Optional filter by analysis result name."),
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(WorkspaceMember.workspace_id)
        .where(WorkspaceMember.user_id == current_user.id)
    )
    user_workspace_ids = [str(uuid_obj) for uuid_obj in result.scalars().all()]

    if not user_workspace_ids:
        return []

    pipeline = [
        {"$match": {"workspace_id": {"$in": user_workspace_ids}}},
        {"$unwind": "$analysis_results"},
    ]
    
    if name:
        pipeline.append({
            "$match": {"analysis_results.name": {"$regex": name, "$options": "i"}}
        })

    pipeline.append({
        "$project": {
            "id": "$analysis_results.id",
            "name": "$analysis_results.name",
            "status": "$analysis_results.status",
            "created_at": "$analysis_results.created_at",
            "_id": 0
        }
    })

    cursor = mongo_db.tenders.aggregate(pipeline)
    
    found_analysis_results: Dict[str, AnalysisResultSummary] = {}
    async for ar_doc in cursor:
        found_analysis_results[ar_doc["id"]] = AnalysisResultSummary(**ar_doc)
    
    return list(found_analysis_results.values())

@analysis_router.get("/{analysis_id}")
async def get_single_analysis_result(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    current_user: Any = Depends(get_current_active_user)
):
    tender = await mongo_db.tenders.find_one({"analysis_results.id": analysis_id})
    if not tender:
        raise HTTPException(status_code=404, detail="No tender associated with this analysis result found")

    if not await check_workspace_permission(tender["workspace_id"], current_user.id, db, WorkspaceRole.VIEWER):
        raise HTTPException(status_code=403, detail="Access denied to this analysis result")

    analysis_doc = await mongo_db.analysis_results.find_one({"_id": analysis_id})
    if not analysis_doc:
        raise HTTPException(status_code=404, detail="Analysis result not found in its collection")

    if "_id" in analysis_doc:
        analysis_doc["_id"] = str(analysis_doc["_id"])
    
    return JSONResponse(content=analysis_doc)
