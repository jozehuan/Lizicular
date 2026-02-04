"""
Audit logging utilities.
Helpers para crear y consultar logs de auditoría.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from .models import AuditLog, AuditCategory, AuditAction, User
import json


# ============================================================================
# AUDIT LOG CREATION
# ============================================================================

async def create_audit_log(
    db: AsyncSession,
    category: AuditCategory,
    action: AuditAction,
    user_id: Optional[UUID] = None,
    workspace_id: Optional[UUID] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> AuditLog:
    """
    Crea un registro de auditoría.
    
    Args:
        db: Sesión de base de datos
        category: Categoría del evento
        action: Acción específica
        user_id: ID del usuario (opcional para eventos del sistema)
        workspace_id: ID del workspace relacionado
        resource_type: Tipo de recurso (workspace, tender, document)
        resource_id: ID del recurso afectado
        payload: Datos adicionales en formato dict
        ip_address: IP del cliente
        user_agent: User agent del cliente
        success: Si la operación fue exitosa
        error_message: Mensaje de error si falló
        
    Returns:
        AuditLog creado
    """
    audit_log = AuditLog(
        user_id=user_id,
        category=category,
        action=action,
        workspace_id=workspace_id,
        resource_type=resource_type,
        resource_id=resource_id,
        payload=payload,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        error_message=error_message
    )
    
    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)
    
    return audit_log


async def log_auth_event(
    db: AsyncSession,
    action: AuditAction,
    user_id: Optional[UUID] = None,
    email: Optional[str] = None,
    success: bool = True,
    request: Optional[Request] = None,
    **kwargs
) -> AuditLog:
    """
    Registra un evento de autenticación.
    
    Ejemplos:
        - LOGIN_SUCCESS
        - LOGIN_FAILED
        - LOGOUT
        - PASSWORD_CHANGE
        - OAUTH_LOGIN
    """
    payload = {"email": email} if email else {}
    payload.update(kwargs)
    
    return await create_audit_log(
        db=db,
        category=AuditCategory.AUTH,
        action=action,
        user_id=user_id,
        payload=payload,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        success=success
    )


async def log_workspace_event(
    db: AsyncSession,
    action: AuditAction,
    workspace_id: UUID,
    user_id: UUID,
    request: Optional[Request] = None,
    **kwargs
) -> AuditLog:
    """
    Registra un evento relacionado con workspaces.
    
    Ejemplos:
        - WORKSPACE_CREATE
        - WORKSPACE_UPDATE
        - WORKSPACE_DELETE
        - MEMBER_ADD
        - MEMBER_REMOVE
        - ROLE_CHANGE
    """
    return await create_audit_log(
        db=db,
        category=AuditCategory.WORKSPACE,
        action=action,
        user_id=user_id,
        workspace_id=workspace_id,
        resource_type="workspace",
        resource_id=str(workspace_id),
        payload=kwargs,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )


async def log_tender_event(
    db: AsyncSession,
    action: AuditAction,
    tender_id: str,  # MongoDB ObjectId as string
    workspace_id: UUID,
    user_id: Optional[UUID] = None,
    request: Optional[Request] = None,
    **kwargs
) -> AuditLog:
    """
    Registra un evento relacionado con licitaciones.
    
    Ejemplos:
        - TENDER_CREATE
        - TENDER_UPDATE
        - TENDER_DELETE
        - TENDER_VIEW
        - TENDER_ANALYZE
    """
    return await create_audit_log(
        db=db,
        category=AuditCategory.TENDER,
        action=action,
        user_id=user_id,
        workspace_id=workspace_id,
        resource_type="tender",
        resource_id=tender_id,
        payload=kwargs,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )


async def log_document_event(
    db: AsyncSession,
    action: AuditAction,
    document_id: str,  # MongoDB ObjectId as string
    tender_id: str,
    workspace_id: UUID,
    user_id: Optional[UUID] = None,
    **kwargs
) -> AuditLog:
    """
    Registra un evento relacionado con documentos.
    
    Ejemplos:
        - DOCUMENT_UPLOAD
        - DOCUMENT_DELETE
        - DOCUMENT_EXTRACT
    """
    return await create_audit_log(
        db=db,
        category=AuditCategory.DOCUMENT,
        action=action,
        user_id=user_id,
        workspace_id=workspace_id,
        resource_type="document",
        resource_id=document_id,
        payload={
            "tender_id": tender_id,
            **kwargs
        }
    )


async def log_n8n_event(
    db: AsyncSession,
    action: AuditAction,
    workspace_id: Optional[UUID] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    **kwargs
) -> AuditLog:
    """
    Registra un evento de workflows n8n.
    
    Ejemplos:
        - WORKFLOW_START
        - WORKFLOW_COMPLETE
        - WORKFLOW_ERROR
    """
    return await create_audit_log(
        db=db,
        category=AuditCategory.N8N,
        action=action,
        workspace_id=workspace_id,
        payload=kwargs,
        success=success,
        error_message=error_message
    )


# ============================================================================
# AUDIT LOG QUERIES
# ============================================================================

async def get_user_activity(
    db: AsyncSession,
    user_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
) -> List[AuditLog]:
    """
    Obtiene la actividad reciente de un usuario.
    """
    query = select(AuditLog).where(AuditLog.user_id == user_id)
    
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)
    
    query = query.order_by(AuditLog.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_workspace_activity(
    db: AsyncSession,
    workspace_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
) -> List[AuditLog]:
    """
    Obtiene la actividad reciente de un workspace.
    """
    query = select(AuditLog).where(AuditLog.workspace_id == workspace_id)
    
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)
    
    query = query.order_by(AuditLog.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_failed_operations(
    db: AsyncSession,
    category: Optional[AuditCategory] = None,
    start_date: Optional[datetime] = None,
    limit: int = 100
) -> List[AuditLog]:
    """
    Obtiene operaciones fallidas para monitoreo.
    """
    query = select(AuditLog).where(AuditLog.success == False)
    
    if category:
        query = query.where(AuditLog.category == category)
    
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    
    query = query.order_by(AuditLog.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_resource_history(
    db: AsyncSession,
    resource_type: str,
    resource_id: str,
    limit: int = 50
) -> List[AuditLog]:
    """
    Obtiene el historial completo de un recurso específico.
    """
    result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        )
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    
    return result.scalars().all()


async def detect_suspicious_activity(
    db: AsyncSession,
    user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    time_window_minutes: int = 15,
    max_failed_attempts: int = 5
) -> bool:
    """
    Detecta actividad sospechosa (intentos de login fallidos, etc.).
    """
    threshold_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
    
    query = select(func.count(AuditLog.id)).where(
        AuditLog.category == AuditCategory.AUTH,
        AuditLog.success == False,
        AuditLog.created_at >= threshold_time
    )
    
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    
    if ip_address:
        query = query.where(AuditLog.ip_address == ip_address)
    
    result = await db.execute(query)
    failed_attempts = result.scalar()
    
    return failed_attempts >= max_failed_attempts


async def get_activity_stats(
    db: AsyncSession,
    workspace_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Obtiene estadísticas de actividad.
    
    Returns:
        {
            "total_events": 1234,
            "by_category": {"AUTH": 100, "WORKSPACE": 50, ...},
            "by_action": {"LOGIN_SUCCESS": 80, ...},
            "failed_operations": 5,
            "unique_users": 15
        }
    """
    query = select(AuditLog)
    
    if workspace_id:
        query = query.where(AuditLog.workspace_id == workspace_id)
    
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Calcular estadísticas
    total_events = len(logs)
    
    by_category = {}
    by_action = {}
    failed_operations = 0
    unique_users = set()
    
    for log in logs:
        # Por categoría
        by_category[log.category.value] = by_category.get(log.category.value, 0) + 1
        
        # Por acción
        by_action[log.action.value] = by_action.get(log.action.value, 0) + 1
        
        # Operaciones fallidas
        if not log.success:
            failed_operations += 1
        
        # Usuarios únicos
        if log.user_id:
            unique_users.add(str(log.user_id))
    
    return {
        "total_events": total_events,
        "by_category": by_category,
        "by_action": by_action,
        "failed_operations": failed_operations,
        "unique_users": len(unique_users)
    }


async def search_audit_logs(
    db: AsyncSession,
    user_email: Optional[str] = None,
    category: Optional[AuditCategory] = None,
    action: Optional[AuditAction] = None,
    workspace_id: Optional[UUID] = None,
    resource_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    success_only: Optional[bool] = None,
    limit: int = 100
) -> List[AuditLog]:
    """
    Búsqueda avanzada de logs de auditoría.
    """
    query = select(AuditLog)
    
    # Filtro por usuario (requiere join)
    if user_email:
        query = query.join(User).where(User.email.ilike(f"%{user_email}%"))
    
    # Filtros simples
    if category:
        query = query.where(AuditLog.category == category)
    
    if action:
        query = query.where(AuditLog.action == action)
    
    if workspace_id:
        query = query.where(AuditLog.workspace_id == workspace_id)
    
    if resource_id:
        query = query.where(AuditLog.resource_id == resource_id)
    
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)
    
    if success_only is not None:
        query = query.where(AuditLog.success == success_only)
    
    query = query.order_by(AuditLog.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


# ============================================================================
# COMPLIANCE AND EXPORT
# ============================================================================

async def export_audit_logs_to_json(
    db: AsyncSession,
    workspace_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> str:
    """
    Exporta logs de auditoría a JSON para compliance.
    """
    logs = await search_audit_logs(
        db=db,
        workspace_id=workspace_id,
        start_date=start_date,
        end_date=end_date,
        limit=10000  # Sin límite para export
    )
    
    export_data = []
    for log in logs:
        export_data.append({
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "category": log.category.value,
            "action": log.action.value,
            "workspace_id": str(log.workspace_id) if log.workspace_id else None,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "payload": log.payload,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "success": log.success,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat()
        })
    
    return json.dumps(export_data, indent=2, ensure_ascii=False)


async def cleanup_old_logs(
    db: AsyncSession,
    days_to_keep: int = 90
) -> int:
    """
    Limpia logs antiguos según política de retención.
    
    Returns:
        Número de logs eliminados
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    
    result = await db.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.created_at < cutoff_date
        )
    )
    count = result.scalar()
    
    # Eliminar logs antiguos
    await db.execute(
        select(AuditLog).where(AuditLog.created_at < cutoff_date)
    )
    await db.commit()
    
    return count