"""
Modelos para procedimientos de n8n y análisis de licitaciones.
"""
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

from backend.tenders.tenders_utils import MongoDB

class ProcedureStatus(str, Enum):
    """Estados de un procedimiento de análisis."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcedureType(str, Enum):
    """Tipos de procedimientos disponibles en n8n."""
    TECHNICAL_ANALYSIS = "technical_analysis"
    FINANCIAL_ANALYSIS = "financial_analysis"
    LEGAL_COMPLIANCE = "legal_compliance"
    RISK_ASSESSMENT = "risk_assessment"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    TENDER_EXTRACTION = "tender_extraction"  
    CUSTOM = "custom"

# ========================================
# Modelos de procedimientos
# ========================================

class LizProcedure(BaseModel):
    """
    Definición de un procedimiento de n8n disponible.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Nombre del procedimiento")
    description: Optional[str] = Field(None, description="Descripción del procedimiento")
    type: ProcedureType = Field(..., description="Tipo de procedimiento")
    webhook_url: HttpUrl = Field(..., description="URL del webhook de n8n que ejecuta el procedimiento")
    estimated_duration_minutes: Optional[int] = Field(None, description="Duración estimada en minutos")
    is_active: bool = Field(default=True, description="Si el procedimiento está activo")
    required_fields: List[str] = Field(default_factory=list, description="Campos requeridos de la licitación")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Extracción de Criterios de Licitación",
                "description": "Extrae información estructurada de la licitación",
                "type": "tender_extraction",
                "webhook_url": "https://n8n.example.com/webhook/tender-extraction",
                "estimated_duration_minutes": 15,
                "required_fields": ["title", "description", "documents"]
            }
        }


class LizProcedureCreate(BaseModel):
    """Schema para crear un nuevo procedimiento de n8n."""
    name: str
    description: Optional[str] = None
    type: ProcedureType
    webhook_url: HttpUrl
    estimated_duration_minutes: Optional[int] = None
    required_fields: List[str] = Field(default_factory=list)


class LizProcedureUpdate(BaseModel):
    """Schema para actualizar un procedimiento de n8n."""
    name: Optional[str] = None
    description: Optional[str] = None
    webhook_url: Optional[HttpUrl] = None
    estimated_duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None
    required_fields: Optional[List[str]] = None


# ========================================
# Modelos de ejecución
# ========================================

class AnalysisExecution(BaseModel):
    """
    Representa una ejecución de un procedimiento sobre una licitación.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tender_id: str = Field(..., description="ID de la licitación")
    procedure_id: str = Field(..., description="ID del procedimiento ejecutado")
    user_id: str = Field(..., description="ID del usuario que inició el análisis")
    status: ProcedureStatus = Field(default=ProcedureStatus.PENDING)
    
    # Datos de ejecución
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Resultado del análisis - puede ser TenderAnalysisResult u otro formato
    result: Optional[Dict[str, Any]] = Field(None, description="Resultado del análisis de n8n")
    result_summary: Optional[str] = Field(None, description="Resumen del resultado")
    
    # Metadata
    execution_id: Optional[str] = Field(None, description="ID del proceso ejecutado")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "tender_id": "123e4567-e89b-12d3-a456-426614174000",
                "procedure_id": "proc-123",
                "user_id": "user-456",
                "workspace_id": "ws-789",
                "status": "processing"
            }
        }


class AnalysisExecutionCreate(BaseModel):
    """Schema para iniciar una ejecución de análisis."""
    tender_id: str
    procedure_id: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AnalysisExecutionResponse(BaseModel):
    """Respuesta al iniciar un análisis."""
    execution_id: str
    status: ProcedureStatus
    message: str
    estimated_completion: Optional[datetime] = None


class WebhookPayload(BaseModel):
    """
    Payload que n8n enviará de vuelta con el resultado.
    """
    execution_id: str = Field(..., description="ID de la ejecución que creamos")
    execution_id: Optional[str] = Field(None, description="ID de ejecución en n8n")
    status: ProcedureStatus = Field(..., description="Estado final del procedimiento")
    result: Optional[Dict[str, Any]] = Field(None, description="Resultado del análisis (TenderAnalysisResult u otro)")
    result_summary: Optional[str] = Field(None, description="Resumen del resultado")
    error_message: Optional[str] = Field(None, description="Mensaje de error si falló")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "execution_id": "exec-123",
                "execution_id": "n8n-exec-456",
                "status": "completed",
                "result": {
                    "informacion_general": [
                        {
                            "requisito": "Plazo de ejecución",
                            "detalle": "18 meses desde la firma del contrato",
                            "referencia": "Página 12, apartado 3.1"
                        }
                    ],
                    "requisitos": [],
                    "otros_requisitos": [],
                    "criterios_no_matematicos": [],
                    "criterios_matematicos": []
                },
                "result_summary": "Análisis completado. Se extrajeron 5 criterios y 3 requisitos."
            }
        }


class RequestPayload(BaseModel):
    """
    Payload que enviamos a n8n para iniciar el procedimiento.
    """
    execution_id: str = Field(..., description="ID de la ejecución")
    tender_data: Dict[str, Any] = Field(..., description="Datos de la licitación")
    procedure_type: str = Field(..., description="Tipo de procedimiento")
    callback_url: HttpUrl = Field(..., description="URL donde n8n enviará el resultado")
    user_id: str = Field(..., description="ID del usuario")
    workspace_id: str = Field(..., description="ID del workspace")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "execution_id": "exec-123",
                "tender_data": {
                    "id": "tender-456",
                    "title": "Licitación para desarrollo de software",
                    "budget": 100000,
                    "deadline": "2024-12-31",
                    "documents": [
                        {
                            "url": "https://example.com/pliego.pdf",
                            "type": "pliego_tecnico"
                        }
                    ]
                },
                "procedure_type": "tender_extraction",
                "callback_url": "https://api.example.com/n8n/webhooks/callback",
                "user_id": "user-789",
                "workspace_id": "ws-012"
            }
        }

# ========================================
# Modelos MongoDB para procedimientos de análisis
# ========================================

class ProceduresCollection:
    """Colección de procedimientos de n8n."""
    
    @staticmethod
    def get_collection():
        """Obtener la colección de procedimientos."""
        return MongoDB.db["n8n_procedures"]
    
    @staticmethod
    async def create_indexes():
        """Crear índices para la colección."""
        collection = ProceduresCollection.get_collection()
        await collection.create_index("type")
        await collection.create_index("is_active")
        await collection.create_index([("name", 1)], unique=True)


class ExecutionsCollection:
    """Colección de ejecuciones de análisis."""
    
    @staticmethod
    def get_collection():
        """Obtener la colección de ejecuciones."""
        return MongoDB.db["analysis_executions"]
    
    @staticmethod
    async def create_indexes():
        """Crear índices para la colección."""
        collection = ExecutionsCollection.get_collection()
        await collection.create_index("tender_id")
        await collection.create_index("procedure_id")
        await collection.create_index("user_id")
        await collection.create_index("workspace_id")
        await collection.create_index("status")
        await collection.create_index([("tender_id", 1), ("status", 1)])
        await collection.create_index([("user_id", 1), ("started_at", -1)])
        await collection.create_index("started_at")
        # TTL index: eliminar ejecuciones completadas después de 90 días
        await collection.create_index(
            "completed_at",
            expireAfterSeconds=90 * 24 * 60 * 60,
            partialFilterExpression={"status": {"$in": ["completed", "failed", "cancelled"]}}
        )


class TenderAnalysisHelper:
    """
    Helper para guardar resultados de análisis directamente en la licitación.
    """
    
    @staticmethod
    async def save_analysis_to_tender(
        tender_id: str,
        execution_id: str,
        procedure_name: str,
        procedure_type: str,
        result: Dict[str, Any],
        result_summary: str,
        user_id: str
    ):
        """
        Guardar el resultado de un análisis en el documento de la licitación.
        
        Args:
            tender_id: ID de la licitación
            execution_id: ID de la ejecución
            procedure_name: Nombre del procedimiento
            procedure_type: Tipo de procedimiento
            result: Resultado estructurado del análisis
            result_summary: Resumen del resultado
            user_id: ID del usuario que ejecutó el análisis
        """
        tenders_coll = MongoDB.db["tenders"]
        
        analysis_data = {
            "id": execution_id,
            "procedure_name": procedure_name,
            "procedure_type": procedure_type,
            "result": result,
            "result_summary": result_summary,
            "created_at": datetime.utcnow(),
            "created_by": user_id,
            "status": "completed"
        }
        
        # Agregar al array de análisis de la licitación
        await tenders_coll.update_one(
            {"_id": tender_id},
            {
                "$push": {"analyses": analysis_data},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
    
    @staticmethod
    async def get_tender_analyses(tender_id: str) -> List[Dict[str, Any]]:
        """
        Obtener todos los análisis de una licitación.
        
        Args:
            tender_id: ID de la licitación
            
        Returns:
            Lista de análisis
        """
        tenders_coll = MongoDB.db["tenders"]
        
        tender = await tenders_coll.find_one(
            {"_id": tender_id},
            {"analyses": 1}
        )
        
        if tender and "analyses" in tender:
            return tender["analyses"]
        
        return []
    
    @staticmethod
    async def update_analysis_status(
        tender_id: str,
        execution_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """
        Actualizar el estado de un análisis en la licitación.
        
        Args:
            tender_id: ID de la licitación
            execution_id: ID de la ejecución
            status: Nuevo estado
            error_message: Mensaje de error si aplica
        """
        tenders_coll = MongoDB.db["tenders"]
        
        update_data = {
            "analyses.$.status": status,
            "analyses.$.updated_at": datetime.utcnow()
        }
        
        if error_message:
            update_data["analyses.$.error_message"] = error_message
        
        await tenders_coll.update_one(
            {"_id": tender_id, "analyses.id": execution_id},
            {"$set": update_data}
        )
