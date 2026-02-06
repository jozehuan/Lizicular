"""
Pydantic schemas for MongoDB models (Tenders and Analysis Results).
These schemas validate data structure for the MongoDB collections.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class FileType(str, Enum):
    """Tipos de archivo permitidos para documentos."""
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    MD = "md"
    TXT = "txt"


class ExtractionStatus(str, Enum):
    """Estados de extracción de documentos."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisStatus(str, Enum):
    """Estados de procesamiento de resultados."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# DOCUMENT SCHEMAS (Subdocumentos de Tender)
# ============================================================================

class DocumentMetadata(BaseModel):
    """Metadata adicional del documento."""
    pages: Optional[int] = None
    author: Optional[str] = None
    language: Optional[str] = "es"
    file_hash: Optional[str] = None  # Para detectar duplicados


class TenderDocument(BaseModel):
    """
    Documento asociado a una licitación.
    
    Representa un archivo (PDF, Word, Excel, etc.) que forma parte de una licitación.
    """
    id: str = Field(..., description="ID único del documento (MongoDB ObjectId)")
    filename: str = Field(..., min_length=1, max_length=255, description="Nombre original del archivo")
    content_type: str = Field(..., description="Tipo MIME del archivo")
    size: int = Field(..., gt=0, description="Tamaño en bytes")
    
    file_url: Optional[str] = Field(None, description="URL del archivo en almacenamiento externo (S3/Supabase)")
    
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    uploaded_by: Optional[str] = Field(None, description="UUID del usuario que subió el archivo")
    
    extraction_status: ExtractionStatus = Field(default=ExtractionStatus.PENDING)
    extracted_text: Optional[str] = Field(None, max_length=50000, description="Texto extraído (limitado)")
    
    metadata: Optional[DocumentMetadata] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "doc-123e4567-e89b-12d3",
                "filename": "Pliego de condiciones.pdf",
                "content_type": "application/pdf",
                "size": 2048576,
                "file_url": "s3://bucket/tenders/workspace-1/tender-1/pliego.pdf",
                "uploaded_at": "2024-01-15T10:00:00Z",
                "uploaded_by": "user-uuid-123",
                "extraction_status": "completed",
                "extracted_text": "Texto extraído del PDF...",
                "metadata": {
                    "pages": 45,
                    "author": "Ministerio de Obras Públicas",
                    "language": "es"
                }
            }
        }
    )


# ============================================================================
# ANALYSIS RESULT SCHEMAS (Subdocumentos de Tender)
# ============================================================================

class InformacionGeneral(BaseModel):
    """Item de información general."""
    requisito: str = Field(..., description="Nombre del requisito")
    detalle: str = Field(..., description="Detalle del requisito")
    referencia: str = Field(..., description="Referencia al documento fuente")


class Requisito(BaseModel):
    """Item de requisito."""
    requisito: str = Field(..., description="Nombre del requisito")
    detalle: str = Field(..., description="Detalle del requisito")
    referencia: str = Field(..., description="Referencia al documento fuente")


class OtroRequisito(BaseModel):
    """Item de otro requisito."""
    requisito: str = Field(..., description="Nombre del requisito")
    detalle: str = Field(..., description="Detalle del requisito")
    referencia: str = Field(..., description="Referencia al documento fuente")


class Subcriterio(BaseModel):
    """Subcriterio de un criterio no matemático."""
    nombre: str = Field(..., description="Nombre del subcriterio")
    detalle: str = Field(..., description="Descripción del subcriterio")
    puntuacion: float = Field(..., ge=0, description="Puntuación del subcriterio")
    referencia: str = Field(..., description="Referencia al documento fuente")


class CriterioNoMatematico(BaseModel):
    """Criterio de evaluación no matemático."""
    nombre: str = Field(..., description="Nombre del criterio")
    detalle: str = Field(..., description="Descripción del criterio")
    puntuacion_total: float = Field(..., ge=0, description="Puntuación total del criterio")
    referencia: str = Field(..., description="Referencia al documento fuente")
    subcriterios: List[Subcriterio] = Field(default_factory=list, description="Lista de subcriterios")


class Variable(BaseModel):
    """Variable de una fórmula matemática."""
    simbolo: str = Field(..., description="Símbolo de la variable (ej: 'P', 'Pmin')")
    detalle: str = Field(..., description="Descripción de la variable")


class Formula(BaseModel):
    """Fórmula matemática para un criterio."""
    formula: str = Field(..., description="Fórmula matemática (ej: 'P = 60 * (Pmin / Po)')")
    detalle_formula: str = Field(..., description="Explicación de la fórmula")
    variables: List[Variable] = Field(..., description="Lista de variables de la fórmula")


class CriterioMatematico(BaseModel):
    """Criterio de evaluación matemático."""
    nombre: str = Field(..., description="Nombre del criterio")
    detalle: str = Field(..., description="Descripción del criterio")
    puntuacion: float = Field(..., ge=0, description="Puntuación del criterio")
    referencia: str = Field(..., description="Referencia al documento fuente")
    formula: Formula = Field(..., description="Fórmula de cálculo")


class AnalysisData(BaseModel):
    """
    Datos del análisis de una licitación.
    
    Contiene los 5 JSONs extraídos del análisis del pliego.
    """
    informacion_general: List[InformacionGeneral] = Field(
        default_factory=list,
        description="Información general de la licitación"
    )
    requisitos: List[Requisito] = Field(
        default_factory=list,
        description="Requisitos de la licitación"
    )
    otros_requisitos: List[OtroRequisito] = Field(
        default_factory=list,
        description="Otros requisitos adicionales"
    )
    criterios_no_matematicos: List[CriterioNoMatematico] = Field(
        default_factory=list,
        description="Criterios de evaluación no matemáticos"
    )
    criterios_matematicos: List[CriterioMatematico] = Field(
        default_factory=list,
        description="Criterios de evaluación matemáticos"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "informacion_general": [
                    {
                        "requisito": "Plazo de ejecución",
                        "detalle": "18 meses desde la firma del contrato",
                        "referencia": "Página 12, apartado 3.1"
                    }
                ],
                "requisitos": [
                    {
                        "requisito": "Clasificación de contratista",
                        "detalle": "Grupo V, Subgrupo 4, Categoría e",
                        "referencia": "Página 15, apartado 4.2"
                    }
                ],
                "otros_requisitos": [],
                "criterios_no_matematicos": [
                    {
                        "nombre": "Memoria técnica",
                        "detalle": "Valoración de la propuesta técnica",
                        "puntuacion_total": 40,
                        "referencia": "Página 22, apartado 6.1",
                        "subcriterios": [
                            {
                                "nombre": "Metodología de trabajo",
                                "detalle": "Descripción del proceso constructivo",
                                "puntuacion": 15,
                                "referencia": "Página 22, apartado 6.1.1"
                            }
                        ]
                    }
                ],
                "criterios_matematicos": [
                    {
                        "nombre": "Oferta económica",
                        "detalle": "Precio ofertado",
                        "puntuacion": 60,
                        "referencia": "Página 25, apartado 6.2",
                        "formula": {
                            "formula": "P = 60 * (Pmin / Po)",
                            "detalle_formula": "Fórmula inversa de precio",
                            "variables": [
                                {
                                    "simbolo": "P",
                                    "detalle": "Puntuación obtenida (0-60 puntos)"
                                },
                                {
                                    "simbolo": "Pmin",
                                    "detalle": "Precio más bajo de todas las ofertas"
                                },
                                {
                                    "simbolo": "Po",
                                    "detalle": "Precio ofertado por el licitador"
                                }
                            ]
                        }
                    }
                ]
            }
        }
    )


class AnalysisResult(BaseModel):
    """
    Resultado de análisis de una licitación.
    
    Representa el resultado de aplicar un procedimiento de análisis
    sobre los documentos de una licitación.
    """
    id: str = Field(..., description="ID único del resultado")
    name: str = Field(..., min_length=1, max_length=255, description="Nombre dado por el usuario")
    
    procedure_id: str = Field(..., description="ID del procedimiento que generó este resultado")
    procedure_name: str = Field(..., description="Nombre del procedimiento")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="UUID del usuario que creó el análisis")
    
    processing_time: Optional[float] = Field(None, ge=0, description="Tiempo de procesamiento en segundos")
    status: AnalysisStatus = Field(default=AnalysisStatus.PENDING)
    
    error_message: Optional[str] = None
    
    data: AnalysisData = Field(..., description="Los 5 JSONs del análisis")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "result-uuid-123",
                "name": "Análisis Inicial",
                "procedure_id": "proc-uuid-456",
                "procedure_name": "Extracción Básica GPT-4",
                "created_at": "2024-01-15T14:00:00Z",
                "created_by": "user-uuid-789",
                "processing_time": 12.5,
                "status": "completed",
                "data": {
                    "informacion_general": [],
                    "requisitos": [],
                    "otros_requisitos": [],
                    "criterios_no_matematicos": [],
                    "criterios_matematicos": []
                }
            }
        }
    )


# ============================================================================
# TENDER SCHEMAS (Documento principal de MongoDB)
# ============================================================================

class TenderCreate(BaseModel):
    """Schema para crear una nueva licitación."""
    workspace_id: str = Field(..., description="UUID del workspace (debe existir en PostgreSQL)")
    name: str = Field(..., min_length=1, max_length=255, description="Nombre de la licitación")
    description: Optional[str] = Field(None, max_length=1000, description="Descripción opcional")
    
    # created_by will be set by backend from current_user
    # documents will be handled by create_tender function
    # Status is implicit 'draft' for creation


class TenderUpdate(BaseModel):
    """Schema para actualizar una licitación."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Actualizar documentos (mantener límite de 5)
    documents: Optional[List[TenderDocument]] = Field(None, min_length=1, max_length=5)


class Tender(BaseModel):
    """
    Modelo completo de una licitación en MongoDB.
    
    Representa una licitación con todos sus documentos y resultados de análisis.
    """
    id: str = Field(..., description="MongoDB ObjectId como string")
    workspace_id: str = Field(..., description="UUID del workspace (PostgreSQL)")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    
    status: str = Field("draft", description="Estado de la licitación") # Default status
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="UUID del usuario creador")
    
    # Documentos
    documents: List[TenderDocument] = Field(default_factory=list) # No min_length here, can be empty
    
    # Resultados (opcional, se agregan bajo demanda)
    analysis_results: List[AnalysisResult] = Field(default_factory=list)
    
    # Campo para búsqueda de texto
    search_text: Optional[str] = None
    
    model_config = ConfigDict(
        populate_by_name=True,
        # alias_generator=lambda field_name: "_id" if field_name == "id" else field_name, # Not needed if mapping in utils
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "workspace_id": "workspace-uuid-123",
                "name": "Construcción Carretera M-30",
                "description": "Licitación para construcción de 15km de carretera",
                "status": "draft",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T12:30:00Z",
                "created_by": "user-uuid-456",
                "documents": [
                    {
                        "id": "doc-uuid-1",
                        "filename": "Pliego de condiciones.pdf",
                        "content_type": "application/pdf",
                        "size": 2048576,
                        "file_url": "s3://bucket/tender-1/pliego.pdf",
                        "uploaded_at": "2024-01-15T10:00:00Z",
                        "uploaded_by": "user-uuid-456",
                        "extraction_status": "completed"
                    }
                ],
                "analysis_results": [],
                "search_text": "construcción carretera m-30 infraestructura madrid"
            }
        }
    )
    
    # Removed documents validator as min_length is no longer on Tender
    # @field_validator('documents')
    # @classmethod
    # def validate_documents_count(cls, v):
    #     """Validar que haya entre 1 y 5 documentos."""
    #     if not (1 <= len(v) <= 5):
    #         raise ValueError('Debe haber entre 1 y 5 documentos')
    #     return v

class TenderResponse(BaseModel):
    """Schema para respuestas de licitaciones."""
    id: str = Field(...)
    workspace_id: str
    name: str
    description: Optional[str]
    status: str # Add status
    created_at: datetime
    updated_at: datetime
    created_by: str
    documents: List[TenderDocument] # Add documents
    analysis_results: List[AnalysisResult] # Add analysis results
    
    # Removed documents_count and analysis_results_count

    model_config = ConfigDict(populate_by_name=True)


class TenderWithDetails(Tender):
    """Schema completo con todos los detalles."""
    pass


# ============================================================================
# HELPER SCHEMAS
# ============================================================================

class AddAnalysisResult(BaseModel):
    """Schema para agregar un resultado de análisis a una licitación."""
    tender_id: str = Field(..., description="ID de la licitación (MongoDB ObjectId)")
    result: AnalysisResult = Field(..., description="Resultado a agregar")


class DocumentUpload(BaseModel):
    """Schema para subir un documento a una licitación existente."""
    tender_id: str = Field(..., description="ID de la licitación")
    document: TenderDocument = Field(..., description="Documento a agregar")
    
    @field_validator('tender_id')
    @classmethod
    def validate_tender_id(cls, v):
        """Validar que el ID no esté vacío."""
        if not v or len(v) == 0:
            raise ValueError('tender_id no puede estar vacío')
        return v