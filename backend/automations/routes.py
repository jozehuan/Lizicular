"""
Endpoints para procedimientos de n8n y análisis de licitaciones.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from typing import List, Dict, Any
from datetime import datetime, timedelta
import httpx
import os
import logging

from backend.auth.auth_utils import get_current_active_user
from backend.auth.models import User
from backend.tenders.tenders_utils import MongoDB
from backend.tenders.schemas import Tender, AnalysisResult
from .models import (
    LizProcedure,
    LizProcedureCreate,
    LizProcedureUpdate,
    AnalysisExecution,
    AnalysisExecutionCreate,
    AnalysisExecutionResponse,
    WebhookPayload,
    RequestPayload,
    ProcedureStatus,
    ProceduresCollection,
    ExecutionsCollection,
    TenderAnalysisHelper
)
from .websocket.manager import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/n8n", tags=["N8N Procedures"])

# URL base de tu backend para callbacks
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")


# ========================================
# ENDPOINTS DE PROCEDIMIENTOS (CRUD)
# ========================================

@router.post("/procedures", response_model=LizProcedure, status_code=status.HTTP_201_CREATED)
async def create_procedure(
    procedure: LizProcedureCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Crear un nuevo procedimiento de n8n.
    Solo administradores pueden crear procedimientos.
    """
    procedures_coll = ProceduresCollection.get_collection()
    
    # Verificar que no exista un procedimiento con el mismo nombre
    existing = await procedures_coll.find_one({"name": procedure.name})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un procedimiento con el nombre '{procedure.name}'"
        )
    
    # Crear el procedimiento
    procedure_data = LizProcedure(**procedure.model_dump())
    
    await procedures_coll.insert_one(procedure_data.model_dump())
    
    logger.info(f"Procedimiento creado: {procedure_data.name} (ID: {procedure_data.id})")
    
    return procedure_data


@router.get("/procedures", response_model=List[LizProcedure])
async def list_procedures(
    active_only: bool = True,
    current_user: User = Depends(get_current_active_user)
):
    """
    Listar todos los procedimientos de n8n disponibles.
    """
    procedures_coll = ProceduresCollection.get_collection()
    
    query = {"is_active": True} if active_only else {}
    
    procedures = await procedures_coll.find(query).to_list(length=100)
    
    return [LizProcedure(**proc) for proc in procedures]


@router.get("/procedures/{procedure_id}", response_model=LizProcedure)
async def get_procedure(
    procedure_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener un procedimiento específico.
    """
    procedures_coll = ProceduresCollection.get_collection()
    
    procedure = await procedures_coll.find_one({"id": procedure_id})
    
    if not procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Procedimiento '{procedure_id}' no encontrado"
        )
    
    return LizProcedure(**procedure)


@router.patch("/procedures/{procedure_id}", response_model=LizProcedure)
async def update_procedure(
    procedure_id: str,
    procedure_update: LizProcedureUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Actualizar un procedimiento.
    """
    procedures_coll = ProceduresCollection.get_collection()
    
    # Verificar que existe
    existing = await procedures_coll.find_one({"id": procedure_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Procedimiento '{procedure_id}' no encontrado"
        )
    
    # Actualizar
    update_data = {
        k: v for k, v in procedure_update.model_dump(exclude_unset=True).items()
        if v is not None
    }
    update_data["updated_at"] = datetime.utcnow()
    
    await procedures_coll.update_one(
        {"id": procedure_id},
        {"$set": update_data}
    )
    
    # Obtener actualizado
    updated = await procedures_coll.find_one({"id": procedure_id})
    return LizProcedure(**updated)


@router.delete("/procedures/{procedure_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_procedure(
    procedure_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Eliminar un procedimiento (soft delete - marca como inactivo).
    """
    procedures_coll = ProceduresCollection.get_collection()
    
    result = await procedures_coll.update_one(
        {"id": procedure_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Procedimiento '{procedure_id}' no encontrado"
        )


# ========================================
# ENDPOINTS DE EJECUCIÓN DE ANÁLISIS
# ========================================

async def call_n8n_webhook(
    procedure: LizProcedure,
    execution: AnalysisExecution,
    tender_data: Dict[str, Any]
):
    """
    Llamar al webhook de n8n para iniciar el procedimiento.
    Esta función se ejecuta en background.
    """
    callback_url = f"{BACKEND_BASE_URL}/n8n/webhooks/callback"
    
    payload = RequestPayload(
        execution_id=execution.id,
        tender_data=tender_data,
        procedure_type=procedure.type.value,
        callback_url=callback_url,
        user_id=execution.user_id,
        workspace_id=execution.workspace_id,
        metadata=execution.metadata
    )
    
    executions_coll = ExecutionsCollection.get_collection()
    
    try:
        logger.info(f"Llamando a n8n webhook: {procedure.n8n_webhook_url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                str(procedure.n8n_webhook_url),
                json=payload.model_dump(mode='json')
            )
            response.raise_for_status()
            
            # Actualizar con ID de n8n si lo devuelve
            response_data = response.json()
            n8n_execution_id = response_data.get("execution_id") or response_data.get("id")
            
            await executions_coll.update_one(
                {"id": execution.id},
                {
                    "$set": {
                        "status": ProcedureStatus.PROCESSING,
                        "n8n_execution_id": n8n_execution_id,
                        "metadata.n8n_response": response_data
                    }
                }
            )
            
            logger.info(f"N8N webhook llamado exitosamente. Execution: {execution.id}")
            
            # Notificar por WebSocket
            await websocket_manager.send_to_user(
                execution.user_id,
                {
                    "type": "analysis_status_update",
                    "execution_id": execution.id,
                    "tender_id": execution.tender_id,
                    "status": ProcedureStatus.PROCESSING,
                    "message": f"Análisis '{procedure.name}' en progreso..."
                }
            )
            
    except httpx.HTTPError as e:
        logger.error(f"Error llamando a n8n: {str(e)}")
        
        # Error al llamar a n8n
        await executions_coll.update_one(
            {"id": execution.id},
            {
                "$set": {
                    "status": ProcedureStatus.FAILED,
                    "error_message": f"Error al llamar a n8n: {str(e)}",
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        # Notificar error
        await websocket_manager.send_to_user(
            execution.user_id,
            {
                "type": "analysis_status_update",
                "execution_id": execution.id,
                "tender_id": execution.tender_id,
                "status": ProcedureStatus.FAILED,
                "message": f"Error al iniciar el análisis: {str(e)}"
            }
        )


@router.post("/execute", response_model=AnalysisExecutionResponse)
async def execute_analysis(
    execution_request: AnalysisExecutionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Iniciar la ejecución de un procedimiento de n8n sobre una licitación.
    
    Este endpoint NO espera a que n8n termine. Retorna inmediatamente
    indicando que el proceso ha iniciado. El resultado llegará por webhook.
    """
    procedures_coll = ProceduresCollection.get_collection()
    executions_coll = ExecutionsCollection.get_collection()
    tenders_coll = MongoDB.db["tenders"]
    
    # 1. Verificar que el procedimiento existe y está activo
    procedure = await procedures_coll.find_one({
        "id": execution_request.procedure_id,
        "is_active": True
    })
    
    if not procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Procedimiento '{execution_request.procedure_id}' no encontrado o inactivo"
        )
    
    procedure = LizProcedure(**procedure)
    
    # 2. Verificar que la licitación existe
    tender = await tenders_coll.find_one({"_id": execution_request.tender_id})
    
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Licitación '{execution_request.tender_id}' no encontrada"
        )
    
    # 3. Verificar campos requeridos
    if procedure.required_fields:
        missing_fields = [
            field for field in procedure.required_fields
            if field not in tender or not tender.get(field)
        ]
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Faltan campos requeridos en la licitación: {', '.join(missing_fields)}"
            )
    
    # 4. Crear la ejecución
    execution = AnalysisExecution(
        tender_id=execution_request.tender_id,
        procedure_id=execution_request.procedure_id,
        user_id=str(current_user.id),
        workspace_id=tender.get("workspace_id", ""),
        status=ProcedureStatus.PENDING,
        metadata=execution_request.metadata
    )
    
    await executions_coll.insert_one(execution.model_dump())
    
    logger.info(f"Ejecución creada: {execution.id} para licitación {execution.tender_id}")
    
    # 5. Iniciar la llamada a n8n en background
    background_tasks.add_task(
        call_n8n_webhook,
        procedure,
        execution,
        tender
    )
    
    # 6. Calcular tiempo estimado de finalización
    estimated_completion = None
    if procedure.estimated_duration_minutes:
        estimated_completion = datetime.utcnow() + timedelta(
            minutes=procedure.estimated_duration_minutes
        )
    
    # 7. Retornar respuesta inmediata
    return AnalysisExecutionResponse(
        execution_id=execution.id,
        status=ProcedureStatus.PENDING,
        message=f"Análisis '{procedure.name}' iniciado. Recibirás una notificación cuando termine.",
        estimated_completion=estimated_completion
    )


@router.get("/executions/{execution_id}", response_model=AnalysisExecution)
async def get_execution(
    execution_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener el estado de una ejecución específica.
    """
    executions_coll = ExecutionsCollection.get_collection()
    
    execution = await executions_coll.find_one({"id": execution_id})
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ejecución '{execution_id}' no encontrada"
        )
    
    execution_obj = AnalysisExecution(**execution)
    
    # Verificar permisos (el usuario debe ser el creador)
    if execution_obj.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver esta ejecución"
        )
    
    return execution_obj


@router.get("/tenders/{tender_id}/executions", response_model=List[AnalysisExecution])
async def list_tender_executions(
    tender_id: str,
    status_filter: ProcedureStatus = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Listar todas las ejecuciones de análisis de una licitación.
    """
    executions_coll = ExecutionsCollection.get_collection()
    
    query = {"tender_id": tender_id}
    if status_filter:
        query["status"] = status_filter
    
    executions = await executions_coll.find(query).sort("started_at", -1).to_list(length=100)
    
    return [AnalysisExecution(**exec) for exec in executions]


@router.get("/tenders/{tender_id}/analyses", response_model=Tender)
async def get_tender_with_analyses(
    tender_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener una licitación con todos sus análisis completados.
    """
    tenders_coll = MongoDB.db["tenders"]
    executions_coll = ExecutionsCollection.get_collection()
    procedures_coll = ProceduresCollection.get_collection()
    
    # Obtener licitación
    tender = await tenders_coll.find_one({"_id": tender_id})
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Licitación '{tender_id}' no encontrada"
        )
    
    # Obtener todas las ejecuciones
    executions = await executions_coll.find({"tender_id": tender_id}).to_list(length=100)
    
    # Construir análisis con información del procedimiento
    analyses = []
    pending_count = 0
    completed_count = 0
    failed_count = 0
    
    for exec_data in executions:
        exec_obj = AnalysisExecution(**exec_data)
        
        # Contar por estado
        if exec_obj.status == ProcedureStatus.COMPLETED:
            completed_count += 1
        elif exec_obj.status == ProcedureStatus.FAILED:
            failed_count += 1
        elif exec_obj.status in [ProcedureStatus.PENDING, ProcedureStatus.PROCESSING]:
            pending_count += 1
        
        # Solo incluir completados en la lista
        if exec_obj.status == ProcedureStatus.COMPLETED:
            procedure = await procedures_coll.find_one({"id": exec_obj.procedure_id})
            if procedure:
                analyses.append(AnalysisResult(
                    id=exec_obj.id,
                    procedure_id=procedure["id"],
                    procedure_name=procedure["name"],
                    created_at=exec_obj.started_at,
                    created_by=exec_obj.user_id,
                    status=exec_obj.status,
                    error_message = exec_obj.error_message,
                    data=exec_obj.result,
                    result_summary=exec_obj.result_summary,
                    completed_at=exec_obj.completed_at
                ))

    return Tender(
        # tender_id=tender_id,
        # tender_title=tender.get("title", "Sin título"),
        # analyses=analyses,
        # pending_count=pending_count,
        # completed_count=completed_count,
        # failed_count=failed_count
    )


@router.delete("/executions/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_execution(
    execution_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Cancelar una ejecución en proceso (solo si está pending o processing).
    """
    executions_coll = ExecutionsCollection.get_collection()
    
    execution = await executions_coll.find_one({"id": execution_id})
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ejecución '{execution_id}' no encontrada"
        )
    
    execution_obj = AnalysisExecution(**execution)
    
    # Verificar permisos
    if execution_obj.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para cancelar esta ejecución"
        )
    
    # Solo se puede cancelar si está pending o processing
    if execution_obj.status not in [ProcedureStatus.PENDING, ProcedureStatus.PROCESSING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede cancelar una ejecución en estado '{execution_obj.status}'"
        )
    
    # Actualizar a cancelado
    await executions_coll.update_one(
        {"id": execution_id},
        {
            "$set": {
                "status": ProcedureStatus.CANCELLED,
                "completed_at": datetime.utcnow(),
                "error_message": "Cancelado por el usuario"
            }
        }
    )
    
    logger.info(f"Ejecución cancelada: {execution_id}")
    
    # Notificar
    await websocket_manager.send_to_user(
        execution_obj.user_id,
        {
            "type": "analysis_status_update",
            "execution_id": execution_id,
            "tender_id": execution_obj.tender_id,
            "status": ProcedureStatus.CANCELLED,
            "message": "Análisis cancelado"
        }
    )


# ========================================
# WEBHOOK PARA RECIBIR RESULTADOS DE N8N
# ========================================

@router.post("/webhooks/callback", status_code=status.HTTP_200_OK)
async def n8n_webhook_callback(
    payload: WebhookPayload,
    request: Request
):
    """
    Webhook que recibe los resultados de n8n cuando termina un procedimiento.
    
    Este endpoint es llamado por n8n, no por usuarios.
    
    Acciones:
    1. Actualizar ejecución en ExecutionsCollection
    2. Guardar resultado en la licitación (MongoDB)
    3. Notificar al usuario por WebSocket
    """
    executions_coll = ExecutionsCollection.get_collection()
    procedures_coll = ProceduresCollection.get_collection()
    
    logger.info(f"Webhook callback recibido para ejecución: {payload.execution_id}")
    
    # Buscar la ejecución
    execution = await executions_coll.find_one({"id": payload.execution_id})
    
    if not execution:
        logger.error(f"Ejecución no encontrada: {payload.execution_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ejecución '{payload.execution_id}' no encontrada"
        )
    
    execution_obj = AnalysisExecution(**execution)
    
    # Buscar el procedimiento para obtener su nombre
    procedure = await procedures_coll.find_one({"id": execution_obj.procedure_id})
    procedure_name = procedure["name"] if procedure else "Análisis"
    procedure_type = procedure["type"] if procedure else "custom"
    
    # Actualizar la ejecución con el resultado
    update_data = {
        "status": payload.status,
        "completed_at": datetime.utcnow(),
        "result": payload.result,
        "result_summary": payload.result_summary,
        "error_message": payload.error_message,
        "metadata.webhook_received_at": datetime.utcnow().isoformat()
    }
    
    if payload.n8n_execution_id:
        update_data["n8n_execution_id"] = payload.n8n_execution_id
    
    if payload.metadata:
        update_data["metadata.n8n_metadata"] = payload.metadata
    
    await executions_coll.update_one(
        {"id": payload.execution_id},
        {"$set": update_data}
    )
    
    logger.info(f"Ejecución actualizada: {payload.execution_id} con estado {payload.status}")
    
    # Si el análisis fue exitoso, guardarlo en la licitación
    if payload.status == ProcedureStatus.COMPLETED and payload.result:
        try:
            await TenderAnalysisHelper.save_analysis_to_tender(
                tender_id=execution_obj.tender_id,
                execution_id=payload.execution_id,
                procedure_name=procedure_name,
                procedure_type=procedure_type,
                result=payload.result,
                result_summary=payload.result_summary,
                user_id=execution_obj.user_id
            )
            logger.info(f"Resultado guardado en licitación: {execution_obj.tender_id}")
        except Exception as e:
            logger.error(f"Error guardando resultado en licitación: {str(e)}")
    
    # Notificar al usuario por WebSocket
    notification_message = {
        "type": "analysis_completed",
        "execution_id": payload.execution_id,
        "tender_id": execution_obj.tender_id,
        "procedure_name": procedure_name,
        "status": payload.status,
        "result": payload.result,
        "result_summary": payload.result_summary,
        "error_message": payload.error_message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await websocket_manager.send_to_user(
        execution_obj.user_id,
        notification_message
    )
    
    logger.info(f"Notificación enviada al usuario: {execution_obj.user_id}")
    
    return {
        "message": "Resultado recibido y procesado correctamente",
        "execution_id": payload.execution_id,
        "status": payload.status,
        "saved_to_tender": payload.status == ProcedureStatus.COMPLETED
    }