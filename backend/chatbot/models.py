from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any

# General Chatbot Models
class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class Message(BaseModel):
    role: Role
    content: str | None # TODO: Remove optional None, temp patch for production nulls
    date: datetime = None

class QuestionRequest(BaseModel):
    messages: List[Message] = []

class APIResponse(BaseModel):
    answer: str
    status: str = "success"

class BotSettings(BaseModel):
    user_token: str = None
    is_automated: bool = False

# Engine/VectorStore Configuration Models
class VectorStoreType(str, Enum):
    AZURE = "azure"

class EngineType(str, Enum):
    AZURE = "azure"

class ReaderType(str, Enum):
    AZURE = "azure"
    LOCAL = "local"

class IndexItem:
    def __init__(self, name: str, description: str, container: str = None):
        self.name = name
        self.description = description
        self.container = container

# Other Request/Response Models (potentially for other services)
class IngestRequest(BaseModel):
    pass

class OCRIngestRequest(BaseModel):
    ocr: bool
    default_pdf: bool

class OCAIngestRequest(BaseModel):
    container_name: str
    reader_type: str
    processor_type: str

class WebhookRequest(BaseModel):
    event: Dict[str, Any]
