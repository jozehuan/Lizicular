"""
MongoDB utilities for tender management.
CRUD operations for tenders, documents, and analysis results.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId, Binary # Import Binary
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException, status, UploadFile # Import UploadFile

from .schemas import (
    Tender, TenderCreate, TenderUpdate,
    TenderDocument, AnalysisResult,
    TenderResponse, AnalysisStatus
)

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

class MongoDB:
    """MongoDB connection manager."""
    
    client: Any = None
    database: Any = None
    
    @classmethod
    async def connect_to_database(cls, mongodb_url: str, database_name: str):
        """Connect to MongoDB."""
        cls.client = AsyncIOMotorClient(mongodb_url)
        cls.database = cls.client[database_name]
        
        # Create indexes
        await cls.create_indexes()
    
    @classmethod
    async def close_database_connection(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
    
    @classmethod
    async def create_indexes(cls):
        """Create MongoDB indexes."""
        tenders = cls.database.tenders
        
        # 1. Búsqueda por workspace
        await tenders.create_index("workspace_id")
        
        # 2. Unicidad de nombre dentro del workspace
        await tenders.create_index(
            [("workspace_id", 1), ("name", 1)],
            unique=True
        )
        
        # 3. Búsqueda de texto completo
        await tenders.create_index([("search_text", "text")])
        
        # 4. Ordenar por fecha
        await tenders.create_index([("created_at", -1)])
        
        # 5. Búsqueda por estado de extracción
        await tenders.create_index("documents.extraction_status")
        
        # 6. Búsqueda por resultados
        await tenders.create_index("analysis_results.id")


async def get_mongo_db() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency to get the MongoDB database instance.
    Raises a 503 error if the database is not available.
    """
    if MongoDB.database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is not available."
        )
    return MongoDB.database


# ============================================================================
# TENDER CRUD OPERATIONS
# ============================================================================

async def create_tender(
    db: Any,
    tender_data: TenderCreate,
    files: List[UploadFile],
    created_by: str # Add created_by parameter
) -> Tender:
    """
    Crea una nueva licitación.
    
    Args:
        db: Base de datos MongoDB
        tender_data: Datos de la licitación
        files: Lista de archivos a subir
        created_by: ID del usuario creador
        
    Returns:
        Licitación creada
        
    Raises:
        HTTPException 400: Si el nombre ya existe en el workspace
    """
    # Create the full tender dictionary
    tender_dict = tender_data.model_dump(by_alias=True, exclude_unset=True) # Start with data from TenderCreate
    tender_dict.update({
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": created_by, # Add created_by here
        "analysis_results": [],
        "search_text": f"{tender_data.name} {tender_data.description or ''}".lower()
    })
    
    uploaded_files_info = []
    for file in files:
        file_content = await file.read()
        file_document = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_content),
            "upload_date": datetime.utcnow(),
            "data": Binary(file_content) # Store file content as binary
        }
        # Insert file into a separate 'tender_files' collection
        file_result = await db.tender_files.insert_one(file_document)
        
        uploaded_files_info.append(TenderDocument(
            id=str(file_result.inserted_id),
            filename=file.filename,
            content_type=file.content_type,
            size=len(file_content),
            extraction_status="pending" # Default status
        ).model_dump())
        
    tender_dict["documents"] = uploaded_files_info
    
    try:
        result = await db.tenders.insert_one(tender_dict)
        
        # Obtener el documento creado
        created_tender = await db.tenders.find_one({"_id": result.inserted_id})
        created_tender["id"] = str(created_tender["_id"]) # Map _id to id for Pydantic model
        
        return Tender(**created_tender)
        
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una licitación con el nombre '{tender_data.name}' en este workspace"
        )


async def get_tender_by_id(
    db: Any,
    tender_id: str
) -> Optional[Tender]:
    """
    Obtiene una licitación por su ID.
    
    Args:
        db: Base de datos MongoDB
        tender_id: ID de la licitación (ObjectId como string)
        
    Returns:
        Licitación si existe, None si no
    """
    try:
        tender = await db.tenders.find_one({"_id": ObjectId(tender_id)})
        
        if tender:
            tender["id"] = str(tender["_id"])
            return Tender(**tender)
        
        return None
        
    except InvalidId:
        return None


async def get_tenders_by_workspace(
    db: Any,
    workspace_id: str,
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "created_at",
    sort_order: int = -1,  # -1 descendente, 1 ascendente
    name: str | None = None # NEW PARAMETER
) -> List[Tender]:
    """
    Obtiene todas las licitaciones de un workspace, con opción de filtrar por nombre.
    
    Args:
        db: Base de datos MongoDB
        workspace_id: UUID del workspace
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros a devolver
        sort_by: Campo por el que ordenar
        sort_order: Orden (1 ascendente, -1 descendente)
        name: Opcional, filtra licitaciones por nombre (búsqueda parcial insensible a mayúsculas/minúsculas)
        
    Returns:
        Lista de licitaciones
    """
    query_filter = {"workspace_id": workspace_id}
    if name:
        # Añadir filtro por nombre con expresión regular insensible a mayúsculas/minúsculas
        query_filter["name"] = {"$regex": name, "$options": "i"} # Case-insensitive partial match

    cursor = db.tenders.find(
        query_filter
    ).sort(sort_by, sort_order).skip(skip).limit(limit)
    
    tenders = []
    async for tender in cursor:
        tender["id"] = str(tender["_id"]) # Map _id to id for Pydantic model
        tenders.append(Tender(**tender))
    
    return tenders


async def update_tender(
    db: Any,
    tender_id: str,
    update_data: TenderUpdate
) -> Optional[Tender]:
    """
    Actualiza una licitación.
    
    Args:
        db: Base de datos MongoDB
        tender_id: ID de la licitación
        update_data: Datos a actualizar
        
    Returns:
        Licitación actualizada
        
    Raises:
        HTTPException 404: Si la licitación no existe
        HTTPException 400: Si el nuevo nombre ya existe
    """
    # Construir el update dict solo con campos no None
    update_dict = {"updated_at": datetime.utcnow()}
    
    if update_data.name is not None:
        update_dict["name"] = update_data.name
    
    if update_data.description is not None:
        update_dict["description"] = update_data.description
    
    if update_data.documents is not None:
        update_dict["documents"] = [doc.model_dump() for doc in update_data.documents]
    
    # Actualizar search_text si cambia el nombre
    if update_data.name is not None:
        tender = await get_tender_by_id(db, tender_id)
        if tender:
            update_dict["search_text"] = f"{update_data.name} {tender.description or ''}".lower()
    
    try:
        result = await db.tenders.find_one_and_update(
            {"_id": ObjectId(tender_id)},
            {"$set": update_dict},
            return_document=True
        )
        
        if result:
            result["id"] = str(result["_id"])
            return Tender(**result)
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licitación no encontrada"
        )
        
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una licitación con el nombre '{update_data.name}' en este workspace"
        )


async def delete_tender(
    db: Any,
    tender_id: str
) -> bool:
    """
    Elimina una licitación y sus documentos asociados.
    
    Args:
        db: Base de datos MongoDB
        tender_id: ID de la licitación
        
    Returns:
        True si se eliminó, False si no existía
    """
    # 1. Obtener la licitación para conseguir los IDs de sus documentos
    tender = await get_tender_by_id(db, tender_id)
    if not tender:
        return False # Tender no encontrado
        
    # 2. Extraer los IDs de los documentos asociados
    document_ids_to_delete = [ObjectId(doc.id) for doc in tender.documents]
    
    # 3. Eliminar los documentos de la colección 'tender_files'
    if document_ids_to_delete:
        await db.tender_files.delete_many({"_id": {"$in": document_ids_to_delete}})
        
    # 4. Eliminar la licitación de la colección 'tenders'
    result = await db.tenders.delete_one({"_id": ObjectId(tender_id)})
    return result.deleted_count > 0


async def delete_tenders_by_workspace(
    db: Any,
    workspace_id: str
) -> None:
    """
    Elimina todas las licitaciones y sus documentos asociados para un workspace
    de forma eficiente y escalable usando una pipeline de agregación.
    
    Args:
        db: Base de datos MongoDB
        workspace_id: UUID del workspace
    """
    # 1. Obtener todos los IDs de archivos y de análisis para limpiar las colecciones separadas
    pipeline = [
        {"$match": {"workspace_id": workspace_id}},
        {"$project": {
            "doc_ids": "$documents.id",
            "analysis_ids": "$analysis_results.id"
        }}
    ]
    cursor = db.tenders.aggregate(pipeline)
    
    file_ids_to_delete = []
    analysis_ids_to_delete = []
    
    async for doc in cursor:
        if "doc_ids" in doc and doc["doc_ids"]:
            file_ids_to_delete.extend([ObjectId(did) for did in doc["doc_ids"]])
        if "analysis_ids" in doc and doc["analysis_ids"]:
            analysis_ids_to_delete.extend(doc["analysis_ids"])
            
    # 2. Eliminar archivos binarios
    if file_ids_to_delete:
        await db.tender_files.delete_many({"_id": {"$in": file_ids_to_delete}})
        
    # 3. Eliminar resultados de análisis detallados
    if analysis_ids_to_delete:
        await db.analysis_results.delete_many({"_id": {"$in": analysis_ids_to_delete}})
        
    # 4. Eliminar todas las licitaciones del workspace
    await db.tenders.delete_many({"workspace_id": workspace_id})


async def count_tenders_in_workspace(
    db: Any,
    workspace_id: str
) -> int:
    """
    Cuenta el número de licitaciones en un workspace.
    
    Args:
        db: Base de datos MongoDB
        workspace_id: UUID del workspace
        
    Returns:
        Número de licitaciones
    """
    count = await db.tenders.count_documents({"workspace_id": workspace_id})
    return count


# ============================================================================
# DOCUMENT OPERATIONS
# ============================================================================

async def add_documents_to_existing_tender(
    db: Any,
    tender_id: str,
    files: List[UploadFile]
) -> Tender:
    """
    Añade documentos a una licitación existente de forma atómica para evitar condiciones de carrera.
    
    Args:
        db: Base de datos MongoDB
        tender_id: ID de la licitación
        files: Lista de archivos a subir
        
    Returns:
        Licitación actualizada con los nuevos documentos.
        
    Raises:
        HTTPException 400: Si se excede el límite de 5 documentos.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron archivos para agregar."
        )

    # 1. Subir archivos y preparar metadatos
    uploaded_files_info = []
    inserted_file_ids = []
    try:
        for file in files:
            file_content = await file.read()
            file_document = {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(file_content),
                "upload_date": datetime.utcnow(),
                "data": Binary(file_content)
            }
            file_result = await db.tender_files.insert_one(file_document)
            inserted_file_ids.append(file_result.inserted_id)
            
            uploaded_files_info.append(TenderDocument(
                id=str(file_result.inserted_id),
                filename=file.filename,
                content_type=file.content_type,
                size=len(file_content),
                extraction_status="pending"
            ).model_dump())
    except Exception as e:
        # Si falla la subida de archivos, no continuamos
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar los archivos: {e}"
        )

    # 2. Realizar la actualización atómica
    atomic_filter = {
        "_id": ObjectId(tender_id),
        "$expr": {"$lte": [{"$add": [{"$size": "$documents"}, len(files)]}, 5]}
    }
    
    update_operation = {
        "$push": {"documents": {"$each": uploaded_files_info}},
        "$set": {"updated_at": datetime.utcnow()}
    }

    result = await db.tenders.find_one_and_update(
        atomic_filter,
        update_operation,
        return_document=True
    )

    # 3. Manejar el resultado de la operación
    if result:
        result["id"] = str(result["_id"])
        return Tender(**result)
    else:
        # La actualización falló, probablemente por el límite de documentos.
        # Realizar limpieza de los archivos subidos para evitar datos huérfanos.
        if inserted_file_ids:
            await db.tender_files.delete_many({"_id": {"$in": inserted_file_ids}})
        
        # Verificar si la licitación existe para dar un error más preciso
        tender_exists = await check_tender_exists(db, tender_id)
        if not tender_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Licitación no encontrada."
            )
        
        # Si la licitación existe, el fallo fue por la condición de tamaño
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden agregar más de 5 documentos a la licitación."
        )


async def delete_document(
    db: Any,
    tender_id: str,
    document_id: str
) -> Optional[Tender]:
    """
    Elimina un documento de una licitación.
    
    Args:
        db: Base de datos MongoDB
        tender_id: ID de la licitación
        document_id: ID del documento
        
    Returns:
        Licitación actualizada
        
    Raises:
        HTTPException 400: Si es el último documento
        HTTPException 404: Si la licitación no existe
    """
    # Verificar que no es el último documento
    tender = await get_tender_by_id(db, tender_id)
    
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licitación no encontrada"
        )
    
    if len(tender.documents) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar el último documento. Debe haber al menos 1 documento."
        )
    
    # 1. Eliminar el contenido del archivo de la colección 'tender_files'
    file_delete_result = await db.tender_files.delete_one({"_id": ObjectId(document_id)})
    if file_delete_result.deleted_count == 0:
        # If the file content itself wasn't found, it might be an inconsistency,
        # but we should still proceed to remove the reference from the tender.
        print(f"Warning: File content for document_id {document_id} not found in tender_files collection.")

    # 2. Eliminar el documento de la licitación
    result = await db.tenders.find_one_and_update(
        {"_id": ObjectId(tender_id)},
        {
            "$pull": {"documents": {"id": document_id}},
            "$set": {"updated_at": datetime.utcnow()}
        },
        return_document=True
    )
    
    if result:
        result["id"] = str(result["_id"])
        return Tender(**result)
    
    return None


async def check_for_existing_analysis(
    db: Any,
    tender_id: str,
    automation_id: str
) -> bool:
    """
    Checks if an analysis for a given tender and automation is already
    in a PENDING or PROCESSING state.
    """
    query = {
        "_id": ObjectId(tender_id),
        "analysis_results": {
            "$elemMatch": {
                "procedure_id": automation_id,
                "status": {"$in": [AnalysisStatus.PENDING, AnalysisStatus.PROCESSING]}
            }
        }
    }
    existing = await db.tenders.find_one(query)
    return existing is not None


# ============================================================================
# ANALYSIS RESULT OPERATIONS
# ============================================================================

async def add_analysis_result_to_tender(
    db: Any,
    tender_id: str,
    analysis_result: AnalysisResult
) -> Optional[Tender]:
    """
    Agrega un resultado de análisis a una licitación.
    
    Args:
        db: Base de datos MongoDB
        tender_id: ID de la licitación
        analysis_result: Resultado a agregar
        
    Returns:
        Licitación actualizada
        
    Raises:
        HTTPException 404: Si la licitación no existe
    """
    result = await db.tenders.find_one_and_update(
        {"_id": ObjectId(tender_id)},
        {
            "$push": {"analysis_results": analysis_result.model_dump()},
            "$set": {"updated_at": datetime.utcnow()}
        },
        return_document=True
    )
    
    if result:
        result["id"] = str(result["_id"])
        return Tender(**result)
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Licitación no encontrada"
    )


async def delete_analysis_result(
    db: Any,
    tender_id: str,
    result_id: str
) -> Optional[Tender]:
    """
    Elimina un resultado de análisis tanto del documento Tender como de la
    colección 'analysis_results'.
    
    Args:
        db: Base de datos MongoDB
        tender_id: ID de la licitación
        result_id: ID del resultado
        
    Returns:
        Licitación actualizada
    """
    # 1. Eliminar el documento de la colección 'analysis_results'
    # Se asume que el `result_id` es el campo `_id` en esa colección.
    await db.analysis_results.delete_one({"_id": result_id})
    
    # 2. Eliminar la referencia del array en el documento de la licitación
    result = await db.tenders.find_one_and_update(
        {"_id": ObjectId(tender_id)},
        {
            "$pull": {"analysis_results": {"id": result_id}},
            "$set": {"updated_at": datetime.utcnow()}
        },
        return_document=True
    )
    
    if result:
        result["id"] = str(result["_id"])
        return Tender(**result)
    
    return None

async def create_placeholder_analysis(
    db: Any,
    tender_id: str,
    automation_id: str,
    user_id: str,
    name: str | None = None
) -> Optional[AnalysisResult]:
    """
    Creates a placeholder analysis result in a tender.
    If a name is not provided, it defaults to the automation name + current datetime.
    
    Args:
        db: MongoDB database
        tender_id: ID of the tender
        automation_id: ID of the automation
        user_id: ID of the user
        name: Optional name for the analysis
        
    Returns:
        The created analysis result
    """
    from backend.automations.models import Automation
    from backend.auth.database import get_db
    import uuid

    automation_name = "Unknown Automation"
    # Safely get the automation name from PostgreSQL
    try:
        async for db_session in get_db():
            automation = await db_session.get(Automation, uuid.UUID(automation_id))
            if automation:
                automation_name = automation.name
    except Exception as e:
        # Log the error but proceed with a default name
        print(f"Could not retrieve automation name: {e}")

    # Determine the final analysis name
    final_name = name if name else f"{automation_name} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"

    analysis_result = AnalysisResult(
        id=str(uuid.uuid4()),
        name=final_name,
        procedure_id=automation_id,
        procedure_name=automation_name,
        created_by=user_id,
        status=AnalysisStatus.PENDING,
        pending_since=datetime.utcnow(),
    )
    
    result = await db.tenders.find_one_and_update(
        {"_id": ObjectId(tender_id)},
        {
            "$push": {"analysis_results": analysis_result.model_dump()},
            "$set": {"updated_at": datetime.utcnow()}
        },
        return_document=True
    )
    
    if result:
        return analysis_result
    
    return None

async def update_analysis_result(
    db: Any,
    tender_id: str,
    analysis_id: str,
    status: str,
    data: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    processing_time: Optional[float] = None,
    clear_pending_since: bool = False
) -> bool:
    """
    Updates an analysis result in a tender.
    
    Args:
        db: MongoDB database
        tender_id: ID of the tender
        analysis_id: ID of the analysis result
        status: The new status
        data: The analysis data
        error_message: An error message if the analysis failed
        processing_time: Time spent processing in seconds
        clear_pending_since: Whether to set pending_since to null
        
    Returns:
        True if the analysis result was updated, False otherwise.
    """
    update_fields = {
        "analysis_results.$.status": status,
        "analysis_results.$.updated_at": datetime.utcnow(),
    }
    if data:
        update_fields["analysis_results.$.data"] = data
    if error_message:
        update_fields["analysis_results.$.error_message"] = error_message
    if processing_time is not None:
        update_fields["analysis_results.$.processing_time"] = processing_time
    if clear_pending_since:
        update_fields["analysis_results.$.pending_since"] = None
    
    result = await db.tenders.update_one(
        {"_id": ObjectId(tender_id), "analysis_results.id": analysis_id},
        {"$set": update_fields}
    )
    return result.modified_count > 0


async def update_analysis_name(
    db: Any,
    analysis_id: str,
    new_name: str,
) -> bool:
    """
    Updates the name of an analysis result in both the `tenders` collection (embedded)
    and the separate `analysis_results` collection for consistency.

    Args:
        db: MongoDB database
        analysis_id: The ID of the analysis result to update.
        new_name: The new name for the analysis.

    Returns:
        True if the name was updated in the parent tender, False otherwise.
    """
    # 1. Update the name in the `tenders` collection (primary operation)
    result_in_tender = await db.tenders.update_one(
        {"analysis_results.id": analysis_id},
        {"$set": {"analysis_results.$.name": new_name}}
    )

    # 2. Update the name in the separate `analysis_results` collection (secondary, for consistency)
    # This is a "fire and forget" update. The primary success indicator is the
    # update in the `tenders` collection.
    await db.analysis_results.update_one(
        {"_id": analysis_id},
        {"$set": {"name": new_name}}
    )
    
    return result_in_tender.modified_count > 0

async def get_tender_by_analysis_id(
    db: Any,
    analysis_id: str
) -> Optional[Tender]:
    """
    Finds a tender by one of its analysis_results IDs.

    Args:
        db: MongoDB database
        analysis_id: The ID of the analysis result to find.

    Returns:
        The full tender document if found, otherwise None.
    """
    tender_doc = await db.tenders.find_one({"analysis_results.id": analysis_id})
    if tender_doc:
        tender_doc["id"] = str(tender_doc["_id"])
        return Tender(**tender_doc)
    return None


async def get_analysis_by_id(
    db: Any,
    tender_id: str,
    analysis_id: str
) -> Optional[AnalysisResult]:
    """
    Gets an analysis result by its ID.
    
    Args:
        db: MongoDB database
        tender_id: ID of the tender
        analysis_id: ID of the analysis result
        
    Returns:
        The analysis result if found, otherwise None
    """
    tender = await db.tenders.find_one(
        {"_id": ObjectId(tender_id), "analysis_results.id": analysis_id},
        {"analysis_results.$": 1}
    )
    
    if tender and "analysis_results" in tender:
        return AnalysisResult(**tender["analysis_results"][0])
    
    return None




# ============================================================================
# SEARCH AND QUERY OPERATIONS
# ============================================================================

async def search_tenders(
    db: Any,
    workspace_id: str,
    search_query: str,
    skip: int = 0,
    limit: int = 100
) -> List[Tender]:
    """
    Busca licitaciones por texto.
    
    Args:
        db: Base de datos MongoDB
        workspace_id: UUID del workspace
        search_query: Texto a buscar
        skip: Número de registros a saltar
        limit: Número máximo de registros
        
    Returns:
        Lista de licitaciones que coinciden
    """
    cursor = db.tenders.find(
        {
            "workspace_id": workspace_id,
            "$text": {"$search": search_query}
        },
        {"score": {"$meta": "textScore"}}
    ).sort([("score", {"$meta": "textScore"})]).skip(skip).limit(limit)
    
    tenders = []
    async for tender in cursor:
        tender["id"] = str(tender["_id"])
        tenders.append(Tender(**tender))
    
    return tenders


async def get_tenders_by_extraction_status(
    db: Any,
    workspace_id: str,
    extraction_status: str
) -> List[Tender]:
    """
    Obtiene licitaciones por estado de extracción de documentos.
    
    Args:
        db: Base de datos MongoDB
        workspace_id: UUID del workspace
        extraction_status: Estado a filtrar (pending, processing, completed, failed)
        
    Returns:
        Lista de licitaciones
    """
    query_filter = {
        "workspace_id": workspace_id,
        "documents.extraction_status": extraction_status
    }
    
    cursor = db.tenders.find(query_filter).sort([("created_at", -1)]) # Default sort for consistency
    
    tenders = []
    async for tender in cursor:
        tender["id"] = str(tender["_id"])
        tenders.append(Tender(**tender))
    
    return tenders


# Add new imports for get_all_tenders_for_user
from sqlalchemy.ext.asyncio import AsyncSession as SQLAlchemyAsyncSession # Use alias to avoid conflict
from sqlalchemy import select as SQLAlchemySelect # Use alias to avoid conflict
from backend.workspaces.models import WorkspaceMember # Needed to get user's workspaces
# import uuid # Already imported at the top

from pydantic import ValidationError

async def get_all_tenders_for_user(
    db_session: SQLAlchemyAsyncSession, # Use alias
    user_id: Any, # Should be uuid.UUID
    mongo_db: Any, # Should be AsyncIOMotorDatabase
    name: str | None = None,
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "created_at",
    sort_order: int = -1,
) -> List[Tender]:
    """
    Obtiene todas las licitaciones a las que un usuario tiene acceso, con opción de filtrar por nombre.
    
    Args:
        db_session: Sesión de base de datos PostgreSQL (para obtener workspaces del usuario)
        user_id: ID del usuario actual
        mongo_db: Instancia de la base de datos MongoDB
        name: Opcional, filtra licitaciones por nombre (búsqueda parcial insensible a mayúsculas/minúsculas)
        # ... (otros parámetros de paginación/ordenación)
        
    Returns:
        Lista de licitaciones
    """
    # 1. Obtener todos los IDs de workspaces a los que el usuario tiene acceso
    result = await db_session.execute(
        SQLAlchemySelect(WorkspaceMember.workspace_id) # Use alias
        .where(WorkspaceMember.user_id == user_id)
    )
    user_workspace_ids = [str(uuid_obj) for uuid_obj in result.scalars().all()] # Convert UUIDs to strings

    if not user_workspace_ids:
        return [] # No workspaces, no tenders

    # 2. Construir el filtro para MongoDB
    query_filter = {"workspace_id": {"$in": user_workspace_ids}}
    if name:
        query_filter["name"] = {"$regex": name, "$options": "i"} # Case-insensitive partial match

    # 3. Ejecutar la consulta en MongoDB
    cursor = mongo_db.tenders.find(
        query_filter
    ).sort(sort_by, sort_order).skip(skip).limit(limit)
    
    tenders = []
    async for tender_doc in cursor:
        try:
            tender_doc["id"] = str(tender_doc["_id"])
            tenders.append(Tender(**tender_doc)) # Use Tender pydantic model for validation/conversion
        except ValidationError as e:
            # If a tender in the DB is malformed and fails validation, log it and skip it
            print(f"WARNING: Skipping tender with ID {tender_doc.get('_id')} due to validation error: {e}")
            continue
    
    return tenders


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def check_tender_exists(
    db: Any,
    tender_id: str
) -> bool:
    """
    Verifica si una licitación existe.
    
    Args:
        db: Base de datos MongoDB
        tender_id: ID de la licitación
        
    Returns:
        True si existe, False si no
    """
    count = await db.tenders.count_documents({"_id": ObjectId(tender_id)})
    return count > 0


async def get_tender_statistics(
    db: Any,
    workspace_id: str
) -> Dict[str, Any]:
    """
    Obtiene estadísticas de un workspace.
    
    Args:
        db: Base de datos MongoDB
        workspace_id: UUID del workspace
        
    Returns:
        Diccionario con estadísticas
    """
    pipeline = [
        {"$match": {"workspace_id": workspace_id}},
        {
            "$group": {
                "_id": None,
                "total_tenders": {"$sum": 1},
                "total_documents": {"$sum": {"$size": "$documents"}},
                "total_results": {"$sum": {"$size": "$analysis_results"}},
                "avg_documents_per_tender": {"$avg": {"$size": "$documents"}},
                "avg_results_per_tender": {"$avg": {"$size": "$analysis_results"}}
            }
        }
    ]
    
    cursor = db.tenders.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    
    if result:
        stats = result[0]
        stats.pop("_id", None)
        return stats
    
    return {
        "total_tenders": 0,
        "total_documents": 0,
        "total_results": 0,
        "avg_documents_per_tender": 0,
        "avg_results_per_tender": 0
    }