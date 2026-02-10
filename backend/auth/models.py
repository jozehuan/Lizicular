"""
Database models for the authentication system.
PostgreSQL models for identity, access control, and universal audit logs.
Business data (tenders, documents) lives in MongoDB.
"""
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Index, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""
    pass


class User(Base):
    """
    User model for authentication and identity management.
    Supports both local authentication and OAuth2 third-party providers.
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    full_name = Column(String(255),nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    oauth_provider = Column(String(50), nullable=True,index=True)
    oauth_id = Column(String(255), nullable=True,index=True)
    profile_picture = Column(Text,nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow,nullable=False)
    updated_at = Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow,nullable=False)

    # Relaciones con cascadas explícitas
    owned_workspaces = relationship("Workspace",back_populates="owner",cascade="all, delete-orphan",passive_deletes=True)
    workspace_memberships = relationship("WorkspaceMember",back_populates="user",cascade="all, delete-orphan",passive_deletes=True)
    audit_logs = relationship("AuditLog",back_populates="user",cascade="all, delete-orphan",passive_deletes=True)
    automations = relationship("Automation", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True)

    __table_args__ = (Index('ix_users_email_active', 'email', 'is_active'),
                      Index('ix_users_oauth_provider_id', 'oauth_provider', 'oauth_id'))
    
    @property
    def is_oauth_user(self) -> bool:
        """Check if user is authenticated via OAuth."""
        return self.oauth_provider is not None
    
    def __repr__(self) -> str:
        auth_method = f"OAuth({self.oauth_provider})" if self.is_oauth_user else "Local"
        return f"<User(id={self.id}, email={self.email}, auth={auth_method})>"

class AuditCategory(str, enum.Enum):
    """Categorías de eventos auditables."""
    AUTH = "AUTH"                # Eventos de autenticación
    WORKSPACE = "WORKSPACE"      # Operaciones en workspaces
    TENDER = "TENDER"            # Operaciones con licitaciones
    DOCUMENT = "DOCUMENT"        # Operaciones con documentos
    SYSTEM = "SYSTEM"            # Eventos del sistema
    N8N = "N8N"                  # Eventos de workflows n8n

class AuditAction(str, enum.Enum):
    """Acciones específicas para cada categoría."""
    # AUTH
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    OAUTH_LOGIN = "OAUTH_LOGIN"
    USER_VIEW = "USER_VIEW"
    
    # WORKSPACE
    WORKSPACE_CREATE = "WORKSPACE_CREATE"
    WORKSPACE_UPDATE = "WORKSPACE_UPDATE"
    WORKSPACE_DELETE = "WORKSPACE_DELETE"
    MEMBER_ADD = "MEMBER_ADD"
    MEMBER_REMOVE = "MEMBER_REMOVE"
    ROLE_CHANGE = "ROLE_CHANGE"
    
    # TENDER
    TENDER_CREATE = "TENDER_CREATE"
    TENDER_UPDATE = "TENDER_UPDATE"
    TENDER_DELETE = "TENDER_DELETE"
    TENDER_VIEW = "TENDER_VIEW"
    TENDER_ANALYZE = "TENDER_ANALYZE"
    
    # DOCUMENT
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    DOCUMENT_DELETE = "DOCUMENT_DELETE"
    DOCUMENT_EXTRACT = "DOCUMENT_EXTRACT"
    
    # SYSTEM
    SYSTEM_ERROR = "SYSTEM_ERROR"
    SYSTEM_BACKUP = "SYSTEM_BACKUP"
    
    # N8N
    WORKFLOW_START = "WORKFLOW_START"
    WORKFLOW_COMPLETE = "WORKFLOW_COMPLETE"
    WORKFLOW_ERROR = "WORKFLOW_ERROR"


class AuditLog(Base):
    """
    Sistema de auditoría universal.
    Registra todos los eventos del sistema con contexto completo.
    
    Attributes:
        id: Identificador único del log
        user_id: Usuario que ejecutó la acción (nullable para eventos del sistema)
        category: Categoría del evento (AUTH, WORKSPACE, TENDER, etc.)
        action: Acción específica realizada
        resource_type: Tipo de recurso afectado (workspace, tender, document)
        resource_id: ID del recurso (UUID de Postgres o ObjectId de Mongo como string)
        workspace_id: Workspace relacionado (para filtrado rápido)
        payload: Datos detallados del evento en formato JSON
        ip_address: IP del cliente
        user_agent: User agent del cliente
        success: Si la operación fue exitosa
        error_message: Mensaje de error si falló
        created_at: Timestamp del evento
    """
    __tablename__ = "audit_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Categoría y acción como enums para consistencia
    category = Column(
        Enum(AuditCategory),
        nullable=False,
        index=True
    )
    action = Column(
        Enum(AuditAction),
        nullable=False,
        index=True
    )
    
    # Información del recurso afectado
    resource_type = Column(
        String(50),
        nullable=True,
        index=True
    )
    resource_id = Column(
        String(255),
        nullable=True,
        index=True
    )
    
    # Referencia a workspace para filtrado rápido
    workspace_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    
    # Payload con datos detallados (JSONB permite consultas eficientes)
    payload = Column(
        JSONB,
        nullable=True
    )
    
    # Contexto técnico
    ip_address = Column(
        String(45),  # IPv6 compatible
        nullable=True
    )
    user_agent = Column(
        Text,
        nullable=True
    )
    
    # Estado de la operación
    success = Column(
        Boolean,
        default=True,
        nullable=False
    )
    error_message = Column(
        Text,
        nullable=True
    )
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    # Relación
    user = relationship("User", back_populates="audit_logs")
    
    # Índices compuestos para consultas comunes
    __table_args__ = (
        # Auditoría por usuario
        Index('ix_audit_user_created', 'user_id', 'created_at'),
        
        # Auditoría por categoría y acción
        Index('ix_audit_category_action', 'category', 'action', 'created_at'),
        
        # Auditoría por workspace
        Index('ix_audit_workspace_created', 'workspace_id', 'created_at'),
        
        # Auditoría por recurso
        Index('ix_audit_resource', 'resource_type', 'resource_id'),
        
        # Eventos fallidos
        Index('ix_audit_failures', 'success', 'created_at', postgresql_where=(Column('success') == False)),
        
        # Índice GIN para búsqueda en JSONB
        Index('ix_audit_payload', 'payload', postgresql_using='gin'),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, category={self.category}, action={self.action}, user_id={self.user_id})>"


# ============================================================================
# EJEMPLOS DE ESTRUCTURA DE PAYLOAD PARA AUDIT_LOG
# ============================================================================
"""
Ejemplos de payload según tipo de evento:

1. LOGIN_SUCCESS:
{
    "method": "oauth",
    "provider": "google",
    "location": "Madrid, Spain",
    "device": "Chrome on Windows"
}

2. WORKSPACE_CREATE:
{
    "workspace_name": "Mi Workspace",
    "description": "Workspace de prueba"
}

3. MEMBER_ADD:
{
    "member_email": "user@example.com",
    "role": "EDITOR",
    "added_by": "admin@example.com"
}

4. TENDER_CREATE:
{
    "tender_id": "LIC-2024-001",
    "title": "Construcción de carretera",
    "budget": 1500000.00,
    "source": "n8n_scraper"
}

5. DOCUMENT_EXTRACT:
{
    "document_id": "507f1f77bcf86cd799439011",
    "file_name": "pliego.pdf",
    "extraction_method": "pdf_parser",
    "pages_extracted": 45,
    "duration_seconds": 12.5
}

6. WORKFLOW_COMPLETE:
{
    "workflow_name": "tender_scraper",
    "tenders_processed": 15,
    "success_count": 14,
    "error_count": 1,
    "duration_minutes": 5.2
}
"""


# ============================================================================
# NOTA IMPORTANTE SOBRE MONGODB
# ============================================================================
# Los siguientes datos NO van en PostgreSQL, sino en MongoDB:
#
# 1. Colección "tenders" (Licitaciones):
#    {
#        "_id": ObjectId("..."),
#        "workspace_id": "uuid-string",  # UUID de PostgreSQL
#        "tender_id": "LIC-2024-001",     # ID externo
#        "title": "Construcción de carretera",
#        
#        "raw_data": {
#            "source_url": "https://...",
#            "html_content": "...",
#            "extracted_at": ISODate("2024-01-15T10:00:00Z")
#        },
#        
#        "metrics": {
#            "budget": 1500000.00,
#            "currency": "EUR",
#            "deadline": ISODate("2024-06-30T23:59:59Z"),
#            "category": "Infraestructura",
#            "location": "Madrid, España"
#        },
#        
#        "ai_analysis": {
#            "summary": "Licitación para construcción de 15km de carretera...",
#            "keywords": ["construcción", "carretera", "infraestructura"],
#            "relevance_score": 0.87,
#            "sentiment": "neutral",
#            "risk_level": "medium"
#        },
#        
#        "status": "active",
#        "created_at": ISODate("2024-01-15T10:00:00Z"),
#        "updated_at": ISODate("2024-01-15T12:30:00Z")
#    }
#
# 2. Colección "documents" (Documentos):
#    {
#        "_id": ObjectId("..."),
#        "tender_id": "LIC-2024-001",
#        "workspace_id": "uuid-string",
#        "file_name": "pliego_condiciones.pdf",
#        "file_url": "https://s3.amazonaws.com/...",
#        "file_type": "pdf",
#        "file_size": 2048576,
#        "extraction_status": "success",
#        "extracted_text": "...",
#        "metadata": {},
#        "created_at": ISODate("2024-01-15T10:00:00Z"),
#        "updated_at": ISODate("2024-01-15T11:30:00Z")
#    }
# ============================================================================