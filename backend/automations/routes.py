from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.auth.database import get_db
from backend.automations.models import Automation
from backend.auth.auth_utils import get_current_active_user
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/automations", tags=["Automations"])

class AutomationCreate(BaseModel):
    name: str
    url: str
    description: str | None = None

@router.post("/", status_code=status.HTTP_201_CREATED)
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
        owner_id=current_user["id"],
    )
    db.add(new_automation)
    await db.commit()
    await db.refresh(new_automation)
    return new_automation
