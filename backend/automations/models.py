from __future__ import annotations
import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from backend.auth.models import Base

class Automation(Base):
    __tablename__ = "autos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
