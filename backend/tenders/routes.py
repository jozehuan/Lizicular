from __future__ import annotations
from typing import List, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.auth.database import get_db
from backend.auth.auth_utils import get_current_active_user
from backend.auth.audit_utils import log_tender_event, create_audit_log
from backend.auth.models import AuditAction, AuditCategory
from backend.workspaces.models import WorkspaceRole, WorkspaceMember
from backend.tenders.schemas import Tender, TenderCreate, TenderUpdate, AnalysisResult
from backend.tenders.tenders_utils import (
    create_tender, get_tender_by_id, get_tenders_by_workspace,
    update_tender, delete_tender, add_analysis_result_to_tender,
    delete_analysis_result, MongoDB
)

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
            WorkspaceMember.workspace_id == workspace_id,
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
    response_model=Tender,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tender"
)
async def api_create_tender(
    tender_data: TenderCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """Crea una licitación si el usuario es EDITOR o superior en el workspace."""
    if not await check_workspace_permission(tender_data.workspace_id, current_user.id, db):
        await create_audit_log(
            db=db,
            category=AuditCategory.TENDER,
            action=AuditAction.TENDER_CREATE,
            user_id=current_user.id,
            workspace_id=uuid.UUID(tender_data.workspace_id) if isinstance(tender_data.workspace_id, str) else tender_data.workspace_id,
            success=False,
            error_message="Permission denied",
            ip_address=request.client.host
        )
        raise HTTPException(status_code=403, detail="Permission denied in this workspace")
    
    new_tender = await create_tender(MongoDB.database, tender_data)
    
    # Log audit
    await log_tender_event(
        db=db,
        action=AuditAction.TENDER_CREATE,
        tender_id=str(new_tender.id),
        workspace_id=uuid.UUID(tender_data.workspace_id) if isinstance(tender_data.workspace_id, str) else tender_data.workspace_id,
        user_id=current_user.id,
        request=request,
        name=new_tender.name
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
