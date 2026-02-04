
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import uuid

from backend.auth.models import User
from backend.workspaces.models import Workspace, WorkspaceMember, WorkspaceRole
from backend.workspaces.schemas import (
    WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate,
    WorkspaceMemberAdd, WorkspaceMemberUpdate, WorkspaceMemberResponse,
    WorkspaceWithTendersResponse, TenderSummaryResponse
)
from backend.auth.database import get_db
from backend.auth.auth_utils import get_current_active_user, get_user_by_email
from backend.auth.audit_utils import create_audit_log
from backend.auth.models import AuditAction, AuditCategory
from backend.tenders.tenders_utils import get_tenders_by_workspace
from backend.tenders.tenders_utils import MongoDB

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    new_workspace = Workspace(
        name=workspace_data.name,
        description=workspace_data.description,
        owner_id=current_user.id
    )
    
    member = WorkspaceMember(
        workspace=new_workspace,
        user=current_user,
        role=WorkspaceRole.OWNER
    )
    
    db.add(new_workspace)
    db.add(member)
    await db.commit()
    await db.refresh(new_workspace)
    
    await create_audit_log(
        db,
        category=AuditCategory.WORKSPACE,
        action=AuditAction.WORKSPACE_CREATE,
        user_id=current_user.id,
        workspace_id=new_workspace.id,
        payload={"name": new_workspace.name},
        ip_address=request.client.host
    )
    
    return new_workspace

@router.get("/", response_model=List[WorkspaceResponse])
async def get_user_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(Workspace).join(WorkspaceMember).where(
            WorkspaceMember.user_id == current_user.id
        )
    )
    return result.scalars().all()

@router.get("/detailed/", response_model=List[WorkspaceWithTendersResponse])
async def get_user_workspaces_with_tenders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(WorkspaceMember)
        .where(WorkspaceMember.user_id == current_user.id)
        .options(selectinload(WorkspaceMember.workspace))
    )
    memberships = result.scalars().all()
    
    response_list = []
    
    for member in memberships:
        workspace = member.workspace
        if not workspace:
            continue
            
        tenders_from_mongo = await get_tenders_by_workspace(MongoDB.database, str(workspace.id))
        
        workspace_details = WorkspaceWithTendersResponse(
            id=workspace.id,
            name=workspace.name,
            description=workspace.description,
            owner_id=workspace.owner_id,
            is_active=workspace.is_active,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
            user_role=member.role,
            tenders=[
                TenderSummaryResponse(
                    id=str(t.id),
                    name=t.name,
                    created_at=t.created_at
                ) for t in tenders_from_mongo
            ]
        )
        response_list.append(workspace_details)
        
    return response_list

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(Workspace).join(WorkspaceMember).where(
            Workspace.id == uuid.UUID(workspace_id),
            WorkspaceMember.user_id == current_user.id
        )
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found or access denied")
        
    return workspace

@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    workspace_data: WorkspaceUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == uuid.UUID(workspace_id))
    )
    workspace = result.scalar_one_or_none()

    if not workspace or workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not an owner of the workspace")

    update_data = workspace_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(workspace, key, value)
    
    await db.commit()
    await db.refresh(workspace)
    
    await create_audit_log(
        db,
        category=AuditCategory.WORKSPACE,
        action=AuditAction.WORKSPACE_UPDATE,
        user_id=current_user.id,
        workspace_id=workspace.id,
        payload=update_data,
        ip_address=request.client.host
    )
    
    return workspace

@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == uuid.UUID(workspace_id))
    )
    workspace = result.scalar_one_or_none()

    if not workspace or workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not an owner of the workspace")

    await db.delete(workspace)
    await db.commit()
    
    await create_audit_log(
        db,
        category=AuditCategory.WORKSPACE,
        action=AuditAction.WORKSPACE_DELETE,
        user_id=current_user.id,
        workspace_id=workspace.id,
        ip_address=request.client.host
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_workspace_member(
    workspace_id: str,
    member_data: WorkspaceMemberAdd,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == uuid.UUID(workspace_id), WorkspaceMember.user_id == current_user.id))
    current_member = res.scalar_one_or_none()
    if not current_member or current_member.role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only workspace owners or admins can add members")

    user_to_add = await get_user_by_email(db, member_data.user_email)
    if not user_to_add:
        raise HTTPException(status_code=404, detail=f"User with email {member_data.user_email} not found")
        
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == uuid.UUID(workspace_id), WorkspaceMember.user_id == user_to_add.id))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already a member of this workspace")

    new_member = WorkspaceMember(workspace_id=uuid.UUID(workspace_id), user_id=user_to_add.id, role=member_data.role.upper())
    db.add(new_member)
    await db.commit()
    
    await create_audit_log(
        db,
        category=AuditCategory.WORKSPACE,
        action=AuditAction.MEMBER_ADD,
        user_id=current_user.id,
        workspace_id=uuid.UUID(workspace_id),
        payload={"added_user_email": user_to_add.email, "role": new_member.role},
        ip_address=request.client.host
    )
    
    return WorkspaceMemberResponse(
        user_id=user_to_add.id,
        email=user_to_add.email,
        full_name=user_to_add.full_name,
        role=new_member.role
    )

@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse])
async def list_workspace_members(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == uuid.UUID(workspace_id), WorkspaceMember.user_id == current_user.id))
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="You are not a member of this workspace")
        
    result = await db.execute(
        select(WorkspaceMember).where(WorkspaceMember.workspace_id == uuid.UUID(workspace_id)).options(selectinload(WorkspaceMember.user))
    )
    members = result.scalars().all()
    
    return [
        WorkspaceMemberResponse(
            user_id=member.user.id,
            email=member.user.email,
            full_name=member.user.full_name,
            role=member.role
        ) for member in members
    ]

@router.put("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse)
async def update_workspace_member(
    workspace_id: str,
    user_id: str,
    member_data: WorkspaceMemberUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == uuid.UUID(workspace_id), WorkspaceMember.user_id == current_user.id))
    current_member = res.scalar_one_or_none()
    if not current_member or current_member.role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only workspace owners or admins can update members")

    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == uuid.UUID(workspace_id), WorkspaceMember.user_id == uuid.UUID(user_id)).options(selectinload(WorkspaceMember.user)))
    member_to_update = res.scalar_one_or_none()
    if not member_to_update:
        raise HTTPException(status_code=404, detail="Member not found in this workspace")
        
    member_to_update.role = member_data.role.upper()
    await db.commit()
    
    await create_audit_log(
        db,
        category=AuditCategory.WORKSPACE,
        action=AuditAction.ROLE_CHANGE,
        user_id=current_user.id,
        workspace_id=uuid.UUID(workspace_id),
        payload={"updated_user_id": str(member_to_update.user_id), "new_role": member_to_update.role},
        ip_address=request.client.host
    )
    
    return WorkspaceMemberResponse(
        user_id=member_to_update.user.id,
        email=member_to_update.user.email,
        full_name=member_to_update.user.full_name,
        role=member_to_update.role
    )

@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    workspace_id: str,
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == uuid.UUID(workspace_id), WorkspaceMember.user_id == current_user.id))
    current_member = res.scalar_one_or_none()
    if not current_member or current_member.role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only workspace owners or admins can remove members")
        
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == uuid.UUID(workspace_id), WorkspaceMember.user_id == uuid.UUID(user_id)))
    member_to_remove = res.scalar_one_or_none()
    if not member_to_remove:
        raise HTTPException(status_code=404, detail="Member not found in this workspace")
        
    if member_to_remove.role == WorkspaceRole.OWNER:
        raise HTTPException(status_code=400, detail="Workspace owner cannot be removed")

    await db.delete(member_to_remove)
    await db.commit()
    
    await create_audit_log(
        db,
        category=AuditCategory.WORKSPACE,
        action=AuditAction.MEMBER_REMOVE,
        user_id=current_user.id,
        workspace_id=uuid.UUID(workspace_id),
        payload={"removed_user_id": str(user_id)},
        ip_address=request.client.host
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
