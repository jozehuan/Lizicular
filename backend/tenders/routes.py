from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Any
import uuid
from starlette.responses import StreamingResponse
import io
from bson import ObjectId
import httpx

from backend.auth.database import get_db
from backend.auth.auth_utils import get_current_active_user
from backend.auth.audit_utils import log_tender_event, create_audit_log
from backend.auth.models import AuditAction, AuditCategory
from backend.workspaces.models import WorkspaceRole, WorkspaceMember
from backend.tenders.schemas import (
    Tender, TenderCreate, TenderUpdate, AnalysisResult, 
    GenerateAnalysisRequest, GenerateAnalysisResponse, AnalysisStatus
)
from backend.tenders.tenders_utils import (
    create_tender, get_tender_by_id, get_tenders_by_workspace,
    update_tender, delete_tender, add_analysis_result_to_tender,
    delete_analysis_result, MongoDB, delete_document, add_documents_to_existing_tender,
    create_placeholder_analysis, update_analysis_result, get_analysis_by_id
)
from backend.automations.models import Automation
from backend.automations.websocket.connection_manager import ConnectionManager, get_connection_manager
# from backend.automations.encryption import encrypt_data


router = APIRouter(prefix="/tenders", tags=["Tenders"])

async def check_workspace_permission(
    workspace_id: str,
    user_id: Any,
    db: AsyncSession,
    required_role: WorkspaceRole = WorkspaceRole.EDITOR
) -> bool:
    """
    Verifica si un usuario tiene el rol necesario en un workspace.
    Permite el acceso si el usuario tiene el rol requerido o uno superior (OWNER > ADMIN > EDITOR).
    """
    # Definir jerarquía de roles
    role_hierarchy = {
        WorkspaceRole.OWNER: 4,
        WorkspaceRole.ADMIN: 3,
        WorkspaceRole.EDITOR: 2,
        WorkspaceRole.VIEWER: 1
    }
    
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == uuid.UUID(workspace_id), # Ensure UUID type match
            WorkspaceMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        return False
        
    return role_hierarchy.get(member.role, 0) >= role_hierarchy.get(required_role, 0)


# ============================================================================
# TENDERS ENDPOINTS (MongoDB)
# ============================================================================

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tender"
)
async def api_create_tender(
    request: Request, # Moved to the beginning
    name: str = Form(...),
    workspace_id: str = Form(...),
    description: str | None = Form(None),
    files: List[UploadFile] = File(default_factory=list), # Accept list of files
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """Crea una licitación si el usuario es EDITOR o superior en el workspace y permite cargar documentos."""
    if not await check_workspace_permission(workspace_id, current_user.id, db):
        await create_audit_log(
            db=db,
            category=AuditCategory.TENDER,
            action=AuditAction.TENDER_CREATE,
            user_id=current_user.id,
            workspace_id=uuid.UUID(workspace_id),
            success=False,
            error_message="Permission denied",
            ip_address=request.client.host
        )
        raise HTTPException(status_code=403, detail="Permission denied in this workspace")
    
    # Create TenderCreate object from form data
    tender_create_data = TenderCreate(
        name=name,
        description=description,
        workspace_id=workspace_id,
        created_by=str(current_user.id) # Add created_by from current user
    )
    
    new_tender = await create_tender(MongoDB.database, tender_create_data, files, str(current_user.id)) # Pass files and created_by to create_tender
    
    # Log audit
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


@router.get(
    "/workspace/{workspace_id}",
    response_model=List[Tender],
    summary="List tenders in workspace"
)
async def api_get_tenders(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """Lista licitaciones si el usuario tiene acceso al workspace."""
    if not await check_workspace_permission(workspace_id, current_user.id, db, WorkspaceRole.VIEWER):
        raise HTTPException(status_code=403, detail="Access denied to this workspace")
    
    return await get_tenders_by_workspace(MongoDB.database, workspace_id)


@router.get(
    "/{tender_id}",
    response_model=Tender,
    summary="Get tender details"
)
async def api_get_tender(
    tender_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """Obtiene detalles de una licitación verificando permisos en su workspace."""
    tender = await get_tender_by_id(MongoDB.database, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    if not await check_workspace_permission(tender.workspace_id, current_user.id, db, WorkspaceRole.VIEWER):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return tender


@router.patch(
    "/{tender_id}",
    response_model=Tender,
    summary="Update tender"
)
async def api_update_tender(
    tender_id: str,
    update_data: TenderUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """Actualiza una licitación si el usuario es EDITOR o superior."""
    tender = await get_tender_by_id(MongoDB.database, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    if not await check_workspace_permission(tender.workspace_id, current_user.id, db):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    updated = await update_tender(MongoDB.database, tender_id, update_data)
    
    # Log audit
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


@router.delete(
    "/{tender_id}",
    summary="Delete tender"
)
async def api_delete_tender(
    tender_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """Elimina una licitación si el usuario es ADMIN o superior."""
    tender = await get_tender_by_id(MongoDB.database, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    if not await check_workspace_permission(tender.workspace_id, current_user.id, db, WorkspaceRole.ADMIN):
        raise HTTPException(status_code=403, detail="Permission denied (Admin required)")
    
    success = await delete_tender(MongoDB.database, tender_id)
    
    # Log audit
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


@router.get(
    "/{tender_id}/documents/{document_id}/download",
    summary="Download a tender document"
)
async def api_download_tender_document(
    tender_id: str,
    document_id: str,
    db_session: AsyncSession = Depends(get_db), # Renamed to avoid conflict with MongoDB.database
    current_user: Any = Depends(get_current_active_user)
):
    """
    Permite descargar un documento específico de una licitación,
    si el usuario tiene al menos el rol de VIEWER en el workspace.
    """
    # 1. Verify tender existence and user permissions
    tender = await get_tender_by_id(MongoDB.database, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    if not await check_workspace_permission(tender.workspace_id, current_user.id, db_session, WorkspaceRole.VIEWER):
        raise HTTPException(status_code=403, detail="Access denied to this tender's documents")

    # 2. Find the document metadata in the tender's documents list
    doc_metadata = next((doc for doc in tender.documents if doc.id == document_id), None)
    if not doc_metadata:
        raise HTTPException(status_code=404, detail="Document not found within this tender")

    # 3. Retrieve the actual file content from the 'tender_files' collection
    file_record = await MongoDB.database.tender_files.find_one({"_id": ObjectId(document_id)})
    if not file_record or not file_record.get("data"):
        raise HTTPException(status_code=404, detail="File content not found")

    file_content = file_record["data"]
    filename = doc_metadata.filename
    content_type = doc_metadata.content_type

    # 4. Return as a StreamingResponse for download
    import io

    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Content-Length": str(len(file_content))
        }
    )


@router.post(
    "/{tender_id}/documents",
    response_model=Tender, # Return the updated tender object
    summary="Add document(s) to a tender"
)
async def api_add_documents_to_tender(
    tender_id: str,
    request: Request,
    files: List[UploadFile] = File(...), # Expect a list of files
    db_session: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Añade uno o más documentos a una licitación existente.
    Requiere rol EDITOR o superior en el workspace.
    """
    tender = await get_tender_by_id(MongoDB.database, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    if not await check_workspace_permission(tender.workspace_id, current_user.id, db_session, WorkspaceRole.EDITOR):
        raise HTTPException(status_code=403, detail="Permission denied (Editor role required)")

    # Call a helper function to add documents and update the tender
    updated_tender = await add_documents_to_existing_tender(
        MongoDB.database,
        tender_id,
        files
    )

    # Log audit
    await log_tender_event(
        db=db_session,
        action=AuditAction.TENDER_UPDATE, # Consider a more specific action like DOCUMENT_ADD
        tender_id=tender_id,
        workspace_id=uuid.UUID(tender.workspace_id) if isinstance(tender.workspace_id, str) else tender.workspace_id,
        user_id=current_user.id,
        request=request,
        details=f"Added {len(files)} document(s) to tender",
        payload={"added_files": [file.filename for file in files]}
    )

    return updated_tender


@router.delete(
    "/{tender_id}/documents/{document_id}",
    response_model=Tender,
    summary="Delete a document from a tender"
)
async def api_delete_document_from_tender(
    tender_id: str,
    document_id: str,
    request: Request,
    db_session: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Elimina un documento de una licitación.
    Requiere rol EDITOR o superior en el workspace.
    """
    tender = await get_tender_by_id(MongoDB.database, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    if not await check_workspace_permission(tender.workspace_id, current_user.id, db_session, WorkspaceRole.EDITOR):
        raise HTTPException(status_code=403, detail="Permission denied (Editor role required)")

    # Find the document to get its filename for the audit log
    document_to_delete = next((doc for doc in tender.documents if doc.id == document_id), None)
    if not document_to_delete:
        raise HTTPException(status_code=404, detail="Document not found in this tender")
    
    deleted_filename = document_to_delete.filename

    updated_tender = await delete_document(
        MongoDB.database,
        tender_id,
        document_id
    )

    # Log audit
    await log_tender_event(
        db=db_session,
        action=AuditAction.TENDER_UPDATE, # Or a specific DOCUMENT_DELETE
        tender_id=tender_id,
        workspace_id=uuid.UUID(tender.workspace_id) if isinstance(tender.workspace_id, str) else tender.workspace_id,
        user_id=current_user.id,
        request=request,
        details=f"Deleted document from tender",
        payload={"deleted_file": deleted_filename}
    )

    return updated_tender


# ============================================================================
# ANALYSIS RESULTS ENDPOINTS (MongoDB)
# ============================================================================

@router.post(
    "/{tender_id}/analysis",
    response_model=Tender,
    summary="Add analysis result to tender",
    tags=["Analysis"]
)
async def api_add_analysis(
    tender_id: str,
    analysis_result: AnalysisResult,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """Añade un resultado de análisis si el usuario es EDITOR o superior."""
    tender = await get_tender_by_id(MongoDB.database, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    if not await check_workspace_permission(tender.workspace_id, current_user.id, db):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = await add_analysis_result_to_tender(MongoDB.database, tender_id, analysis_result)
    
    # Log audit
    await log_tender_event(
        db=db,
        action=AuditAction.TENDER_ANALYZE,
        tender_id=tender_id,
        workspace_id=uuid.UUID(tender.workspace_id) if isinstance(tender.workspace_id, str) else tender.workspace_id,
        user_id=current_user.id,
        request=request,
        analysis_name=analysis_result.name
    )
    
    return result


@router.delete(
    "/{tender_id}/analysis/{result_id}",
    response_model=Tender,
    summary="Remove analysis result from tender",
    tags=["Analysis"]
)
async def api_delete_analysis(
    tender_id: str,
    result_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """Elimina un resultado de análisis si el usuario es EDITOR o superior en el workspace."""
    tender = await get_tender_by_id(MongoDB.database, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    # Verificación explícita de rol EDITOR o superior
    if not await check_workspace_permission(tender.workspace_id, current_user.id, db, WorkspaceRole.EDITOR):
        raise HTTPException(status_code=403, detail="Permission denied (Editor role required)")
    
    result = await delete_analysis_result(MongoDB.database, tender_id, result_id)
    
    # Log audit
    await log_tender_event(
        db=db,
        action=AuditAction.TENDER_UPDATE, # Or a generic update
        tender_id=tender_id,
        workspace_id=uuid.UUID(tender.workspace_id) if isinstance(tender.workspace_id, str) else tender.workspace_id,
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
    db: AsyncSession,
    current_user: Any,
    request: Request,
    manager_instance: ConnectionManager,
):
    """
    This function is executed in the background to generate the analysis.
    """
    await update_analysis_result(MongoDB.database, tender_id, analysis_id, status=AnalysisStatus.PROCESSING)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                automation_url,
                json={"tender_id": tender_id, "analysis_id": analysis_id},
                timeout=3600.0,
            )
            response.raise_for_status()

            # Assuming n8n returns a success status
            if response.json().get("status") == "success":
                await update_analysis_result(
                    MongoDB.database,
                    tender_id,
                    analysis_id,
                    status=AnalysisStatus.COMPLETED,
                )
            else:
                error_message = response.json().get("message", "n8n workflow failed")
                await update_analysis_result(
                    MongoDB.database,
                    tender_id,
                    analysis_id,
                    status=AnalysisStatus.FAILED,
                    error_message=error_message,
                )
            
            # Log audit
            tender = await get_tender_by_id(MongoDB.database, tender_id)
            await log_tender_event(
                db=db,
                action=AuditAction.TENDER_ANALYZE,
                tender_id=tender_id,
                workspace_id=uuid.UUID(tender.workspace_id),
                user_id=current_user.id,
                request=request,
                details=f"Generated analysis with automation",
                payload={"automation_id": automation_id}
            )
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            error_message = f"Error from automation service: {e}"
            await update_analysis_result(
                MongoDB.database,
                tender_id,
                analysis_id,
                status=AnalysisStatus.FAILED,
                error_message=error_message,
            )
            await manager_instance.send_to_analysis_id(
                {"status": "FAILED", "error": error_message},
                analysis_id
            )
        else:
            analysis_result = await get_analysis_by_id(MongoDB.database, tender_id, analysis_id)
            await manager_instance.send_to_analysis_id(
                {"status": "COMPLETED", "result": analysis_result.model_dump()},
                analysis_id
            )

@router.post(
    "/{tender_id}/generate_analysis",
    summary="Generate analysis for a tender",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=GenerateAnalysisResponse,
    tags=["Analysis"]
)
async def api_generate_analysis(
    tender_id: str,
    analysis_request: GenerateAnalysisRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user),
    manager_instance: ConnectionManager = Depends(get_connection_manager)
):
    """Generates an analysis for a tender by calling an automation service."""
    tender = await get_tender_by_id(MongoDB.database, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    if not await check_workspace_permission(tender.workspace_id, current_user.id, db, WorkspaceRole.EDITOR):
        raise HTTPException(status_code=403, detail="Permission denied (Editor role required)")

    automation = await db.get(Automation, uuid.UUID(analysis_request.automation_id))
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")

    placeholder = await create_placeholder_analysis(
        MongoDB.database,
        tender_id,
        analysis_request.automation_id,
        str(current_user.id)
    )

    if not placeholder:
        raise HTTPException(status_code=500, detail="Could not create analysis placeholder")

    background_tasks.add_task(
        run_analysis_in_background,
        tender_id,
        placeholder.id,
        automation.url,
        str(automation.id),
        db,
        current_user,
        request,
        manager_instance,
    )
    
    return GenerateAnalysisResponse(
        message="Analysis generation started.",
        analysis_id=placeholder.id
    )



