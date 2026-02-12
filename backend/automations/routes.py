from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.auth.database import get_db
from backend.automations.models import Automation
from backend.auth.auth_utils import get_current_active_user
from pydantic import BaseModel, ConfigDict, Field
import uuid

router = APIRouter(prefix="/automations", tags=["Automations"])

class AutomationCreate(BaseModel):
    name: str
    url: str
    description: str | None = None
    owner_id: str = Field(..., description="ID del propietario del automatismo.")

class AutomationResponse(BaseModel):
    id: uuid.UUID
    name: str
    url: str
    description: str | None = None
    owner_id: uuid.UUID # Changed from str to uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AutomationResponse)
async def create_automation(
    automation: AutomationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    """Creates a new automation."""
    new_automation = Automation(
        id=uuid.uuid4(),
        name=automation.name,
        url=automation.url,
        description=automation.description,
        owner_id=automation.owner_id,
    )
    db.add(new_automation)
    await db.commit()
    await db.refresh(new_automation)
    return new_automation

@router.get("/", response_model=List[AutomationResponse])
async def list_automations(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    """Lists all available automations."""
    result = await db.execute(select(Automation))
    automations = result.scalars().all()
    return automations
