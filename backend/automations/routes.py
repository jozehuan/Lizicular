from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict
import uuid

from backend.auth.database import get_db
from backend.automations.models import Automation
from backend.auth.auth_utils import get_current_active_user
from backend.auth.models import User, AuditAction, AuditCategory
from backend.auth.audit_utils import create_audit_log
from fastapi import Request


router = APIRouter(prefix="/automations", tags=["Automations"])

class AutomationCreate(BaseModel):
    name: str
    url: str
    description: str | None = None

class AutomationResponse(BaseModel):
    id: uuid.UUID
    name: str
    url: str
    description: str | None = None
    owner_id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AutomationResponse)
async def create_automation(
    request: Request,
    automation: AutomationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Creates a new automation, setting the owner to the current user."""
    new_automation = Automation(
        id=uuid.uuid4(),
        name=automation.name,
        url=automation.url,
        description=automation.description,
        owner_id=current_user.id,
    )
    db.add(new_automation)
    await db.commit()
    await db.refresh(new_automation)

    # Log the creation of the automation
    await create_audit_log(
        db,
        category=AuditCategory.N8N,
        action=AuditAction.AUTOMATION_CREATE,
        user_id=current_user.id,
        resource_type="automation",
        resource_id=str(new_automation.id),
        payload={
            "name": new_automation.name,
            "url": new_automation.url
        },
        ip_address=request.client.host if request.client else "unknown"
    )

    return new_automation

@router.get("/", response_model=List[AutomationResponse])
async def list_automations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lists all available automations."""
    result = await db.execute(select(Automation))
    automations = result.scalars().all()
    return automations

@router.delete("/{automation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_automation(
    automation_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Deletes an automation by ID and logs the event."""
    automation = await db.get(Automation, automation_id)
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    # Optional: Only owners or admins can delete (for now, any authenticated user)
    # if automation.owner_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="Permission denied")

    await db.delete(automation)
    await db.commit()

    # Log the deletion of the automation
    await create_audit_log(
        db,
        category=AuditCategory.N8N,
        action=AuditAction.AUTOMATION_DELETE,
        user_id=current_user.id,
        resource_type="automation",
        resource_id=str(automation_id),
        payload={
            "name": automation.name
        },
        ip_address=request.client.host if request.client else "unknown"
    )

    return None
