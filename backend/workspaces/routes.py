
from typing import List, Any, Union
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import uuid

from backend.auth.models import User
from backend.workspaces.models import Workspace, WorkspaceMember, WorkspaceRole
from backend.workspaces.schemas import (
    WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate,
    WorkspaceMemberAdd, WorkspaceMemberUpdate, WorkspaceMemberResponse,
    WorkspaceWithTendersResponse, TenderSummaryResponse, WorkspaceDetailResponse
)
from backend.auth.database import get_db
from backend.auth.auth_utils import get_current_active_user, get_user_by_email
from backend.auth.audit_utils import create_audit_log
from backend.auth.models import AuditAction, AuditCategory
from backend.tenders.tenders_utils import get_tenders_by_workspace, MongoDB, delete_tenders_by_workspace


router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_workspace_no_slash(
    workspace_data: WorkspaceCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    This endpoint is a workaround for clients that might not be adding the trailing slash,
    causing a 307 redirect and losing the Authorization header.
    """
    return await create_workspace(workspace_data, request, db, current_user)


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check for duplicate workspace name for the current user
    existing_workspace = await db.execute(
        select(Workspace).where(
            Workspace.owner_id == current_user.id,
            Workspace.name == workspace_data.name
        )
    )
    if existing_workspace.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workspace with name '{workspace_data.name}' already exists for this user."
        )

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
    db.add(member) # This is the owner member

    # Add collaborators if provided
    for collaborator_data in workspace_data.collaborators:
        collaborator_user = await get_user_by_email(db, collaborator_data.email)
        
        if collaborator_user:
            # Ensure the collaborator is not already the owner
            if collaborator_user.id == current_user.id:
                continue

            # Check if collaborator is already a member
            existing_member_res = await db.execute(
                select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == new_workspace.id,
                    WorkspaceMember.user_id == collaborator_user.id
                )
            )
            if existing_member_res.scalar_one_or_none():
                continue

            collaborator_member = WorkspaceMember(
                workspace_id=new_workspace.id,
                user=collaborator_user,
                role=collaborator_data.role  # Use the role from the collaborator_data
            )
            db.add(collaborator_member)
            
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
    current_user: User = Depends(get_current_active_user),
    name: str = Query(None, description="Optional filter by workspace name.") # NEW PARAMETER
):
    query = select(Workspace).join(WorkspaceMember).where(
        WorkspaceMember.user_id == current_user.id
    )
    if name:
        query = query.where(Workspace.name.ilike(f"%{name}%")) # Add name filter
        
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/detailed", response_model=List[WorkspaceWithTendersResponse])
async def get_user_workspaces_with_tenders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(WorkspaceMember)
        .where(WorkspaceMember.user_id == current_user.id)
        .options(
            selectinload(WorkspaceMember.workspace).selectinload(Workspace.members).selectinload(WorkspaceMember.user)
        )
    )
    memberships = result.scalars().all()
    
    response_list = []
    
    for member in memberships:
        workspace = member.workspace
        if not workspace:
            continue
            
        # Get members for the current workspace and format them
        workspace_members_response = [
            WorkspaceMemberResponse(
                user_id=mem.user.id,
                email=mem.user.email,
                full_name=mem.user.full_name,
                role=mem.role
            ) for mem in workspace.members
        ]

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
                    created_at=t.created_at,
                    workspace_id=workspace.id,
                    workspace_name=workspace.name
                ) for t in tenders_from_mongo
            ],
            members=workspace_members_response
        )
        response_list.append(workspace_details)
        
    return response_list

@router.get("/{workspace_id}", response_model=WorkspaceDetailResponse)
async def get_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # First, verify if the user is a member of the workspace.
    membership_check = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == uuid.UUID(workspace_id),
            WorkspaceMember.user_id == current_user.id
        )
    )
    if not membership_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workspace not found or access denied")

    # If the user is a member, fetch the workspace and its members.
    result = await db.execute(
        select(Workspace)
        .where(Workspace.id == uuid.UUID(workspace_id))
        .options(selectinload(Workspace.members).selectinload(WorkspaceMember.user))
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # Manually construct the response to ensure correct serialization
    member_responses = [
        WorkspaceMemberResponse(
            user_id=member.user.id,
            email=member.user.email,
            full_name=member.user.full_name,
            role=member.role
        ) for member in workspace.members
    ]
    
    return WorkspaceDetailResponse(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        owner_id=workspace.owner_id,
        is_active=workspace.is_active,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        members=member_responses
    )

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

    # Delete associated tenders and their documents from MongoDB
    await delete_tenders_by_workspace(MongoDB.database, str(workspace.id))

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

@router.post("/{workspace_id}/members", status_code=status.HTTP_201_CREATED)
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
        # Omit the collaborator if not found, as per request
        return Response(status_code=status.HTTP_200_OK, media_type="text/plain", content=f"User with email {member_data.user_email} not found and was omitted.")
        
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
    
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "user_id": str(user_to_add.id),
            "email": user_to_add.email,
            "full_name": user_to_add.full_name,
            "role": new_member.role
        }
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
        
    # Permission check for ADMINs trying to change OWNER/ADMIN roles
    if current_member.role == WorkspaceRole.ADMIN:
        if member_to_update.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
            raise HTTPException(status_code=403, detail="Admins cannot change the role of an Owner or another Admin.")
        if member_data.role.upper() in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
            raise HTTPException(status_code=403, detail="Admins cannot assign an Owner or Admin role.")

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
