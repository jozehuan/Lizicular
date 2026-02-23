from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
import uuid

from backend.auth.models import User
from backend.workspaces.models import Workspace, WorkspaceMember, WorkspaceRole
from backend.workspaces.schemas import (
    WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate,
    WorkspaceMemberAdd, WorkspaceMemberUpdate, WorkspaceMemberResponse,
    WorkspaceWithTendersResponse, TenderSummaryResponse, WorkspaceDetailResponse,
    AnalysisResultSummary
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
    return await create_workspace(workspace_data, request, db, current_user)


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
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
    db.add(member)
    await db.flush() # Flush to get new_workspace.id

    for collaborator_data in workspace_data.collaborators:
        collaborator_user = await get_user_by_email(db, collaborator_data.email)
        if collaborator_user and collaborator_user.id != current_user.id:
            existing_member_res = await db.execute(
                select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == new_workspace.id,
                    WorkspaceMember.user_id == collaborator_user.id
                )
            )
            if not existing_member_res.scalar_one_or_none():
                collaborator_member = WorkspaceMember(
                    workspace_id=new_workspace.id,
                    user_id=collaborator_user.id,
                    role=collaborator_data.role
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
        ip_address=request.client.host if request.client else "unknown"
    )
    
    return new_workspace

@router.get("/", response_model=List[WorkspaceResponse])
async def get_user_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    name: str = Query(None, description="Optional filter by workspace name.")
):
    query = select(Workspace).join(WorkspaceMember).where(
        WorkspaceMember.user_id == current_user.id
    )
    if name:
        query = query.where(Workspace.name.ilike(f"%{name}%"))
        
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
        .options(selectinload(WorkspaceMember.workspace).selectinload(Workspace.members).selectinload(WorkspaceMember.user))
    )
    memberships = result.scalars().all()
    
    response_list = []
    
    for member in memberships:
        workspace = member.workspace
        if not workspace:
            continue
            
        workspace_members_response = [
            WorkspaceMemberResponse(
                user_id=mem.user.id, 
                email=mem.user.email, 
                full_name=mem.user.full_name, 
                role=mem.role.value,
                profile_picture=mem.user.profile_picture
            )
            for mem in workspace.members
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
            user_role=member.role.value,
            tenders=[
                TenderSummaryResponse(
                    id=str(t.id),
                    name=t.name,
                    created_at=t.created_at,
                    workspace_id=workspace.id,
                    workspace_name=workspace.name,
                    analysis_results=[
                        AnalysisResultSummary(status=ar.status) for ar in t.analysis_results
                    ] if t.analysis_results else []
                )
                for t in tenders_from_mongo
            ],
            members=workspace_members_response
        )
        response_list.append(workspace_details)
        
    return response_list

@router.get("/{workspace_id}", response_model=WorkspaceDetailResponse)
async def get_workspace(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    membership_check = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
    )
    if not membership_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workspace not found or access denied")

    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id).options(selectinload(Workspace.members).selectinload(WorkspaceMember.user))
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    member_responses = [
        WorkspaceMemberResponse(
            user_id=member.user.id, 
            email=member.user.email, 
            full_name=member.user.full_name, 
            role=member.role.value,
            profile_picture=member.user.profile_picture
        )
        for member in workspace.members
    ]
    
    return WorkspaceDetailResponse(
        id=workspace.id, name=workspace.name, description=workspace.description, owner_id=workspace.owner_id,
        is_active=workspace.is_active, created_at=workspace.created_at, updated_at=workspace.updated_at,
        members=member_responses
    )

@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: uuid.UUID,
    workspace_data: WorkspaceUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = result.scalar_one_or_none()

    if not workspace or workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not an owner of the workspace")

    update_data = workspace_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(workspace, key, value)
    
    await db.commit()
    await db.refresh(workspace)
    
    await create_audit_log(
        db, category=AuditCategory.WORKSPACE, action=AuditAction.WORKSPACE_UPDATE, user_id=current_user.id,
        workspace_id=workspace.id, payload=update_data, ip_address=request.client.host if request.client else "unknown"
    )
    
    return workspace

@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = result.scalar_one_or_none()

    if not workspace or workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not an owner of the workspace")

    try:
        # 1. Perform PostgreSQL deletions first
        await db.execute(
            delete(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
        )
        await db.delete(workspace)
        await db.commit()

    except Exception:
        # If SQL fails, rollback and do not touch MongoDB
        await db.rollback()
        raise

    # 2. Only after the SQL transaction is successful, perform the MongoDB deletion
    await delete_tenders_by_workspace(MongoDB.database, str(workspace.id))
    
    # 3. Create the audit log after all operations are successful
    await create_audit_log(
        db, category=AuditCategory.WORKSPACE, action=AuditAction.WORKSPACE_DELETE,
        user_id=current_user.id, workspace_id=workspace_id, ip_address=request.client.host if request.client else "unknown"
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{workspace_id}/members", status_code=status.HTTP_201_CREATED, response_model=WorkspaceMemberResponse)
async def add_workspace_member(
    workspace_id: uuid.UUID,
    member_data: WorkspaceMemberAdd,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == current_user.id))
    current_member = res.scalar_one_or_none()
    if not current_member or current_member.role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only workspace owners or admins can add members")

    user_to_add = await get_user_by_email(db, member_data.user_email)
    if not user_to_add:
        raise HTTPException(status_code=404, detail=f"User with email {member_data.user_email} not found.")
        
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_to_add.id))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already a member of this workspace")

    new_member = WorkspaceMember(workspace_id=workspace_id, user_id=user_to_add.id, role=member_data.role)
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    
    await create_audit_log(
        db, category=AuditCategory.WORKSPACE, action=AuditAction.MEMBER_ADD, user_id=current_user.id,
        workspace_id=workspace_id, payload={"added_user_email": user_to_add.email, "role": new_member.role.value},
        ip_address=request.client.host if request.client else "unknown"
    )
    
    # Manually load the user relationship to return the full name
    await db.refresh(new_member, attribute_names=['user'])
    return WorkspaceMemberResponse(
        user_id=new_member.user.id, 
        email=new_member.user.email,
        full_name=new_member.user.full_name, 
        role=new_member.role.value,
        profile_picture=new_member.user.profile_picture
    )

@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse])
async def list_workspace_members(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == current_user.id))
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="You are not a member of this workspace")
        
    result = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id).options(selectinload(WorkspaceMember.user)))
    members = result.scalars().all()
    
    return [
        WorkspaceMemberResponse(
            user_id=member.user.id, 
            email=member.user.email, 
            full_name=member.user.full_name, 
            role=member.role.value,
            profile_picture=member.user.profile_picture
        )
        for member in members
    ]

@router.put("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse)
async def update_workspace_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    member_data: WorkspaceMemberUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == current_user.id))
    current_member = res.scalar_one_or_none()
    if not current_member or current_member.role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only workspace owners or admins can update members")

    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id).options(selectinload(WorkspaceMember.user)))
    member_to_update = res.scalar_one_or_none()
    if not member_to_update:
        raise HTTPException(status_code=404, detail="Member not found in this workspace")
        
    if current_member.role == WorkspaceRole.ADMIN:
        if member_to_update.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
            raise HTTPException(status_code=403, detail="Admins cannot change the role of an Owner or another Admin.")
        if member_data.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
            raise HTTPException(status_code=403, detail="Admins cannot assign an Owner or Admin role.")

    member_to_update.role = member_data.role
    await db.commit()
    
    await create_audit_log(
        db, category=AuditCategory.WORKSPACE, action=AuditAction.ROLE_CHANGE, user_id=current_user.id,
        workspace_id=workspace_id, payload={"updated_user_id": str(member_to_update.user_id), "new_role": member_to_update.role.value},
        ip_address=request.client.host if request.client else "unknown"
    )
    
    return WorkspaceMemberResponse(
        user_id=member_to_update.user.id, 
        email=member_to_update.user.email,
        full_name=member_to_update.user.full_name, 
        role=member_to_update.role.value,
        profile_picture=member_to_update.user.profile_picture
    )

@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == current_user.id))
    current_member = res.scalar_one_or_none()
    if not current_member or current_member.role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only workspace owners or admins can remove members")
        
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id))
    member_to_remove = res.scalar_one_or_none()
    if not member_to_remove:
        raise HTTPException(status_code=404, detail="Member not found in this workspace")
        
    if member_to_remove.role == WorkspaceRole.OWNER:
        raise HTTPException(status_code=400, detail="Workspace owner cannot be removed")

    await db.delete(member_to_remove)
    await db.commit()
    
    await create_audit_log(
        db, category=AuditCategory.WORKSPACE, action=AuditAction.MEMBER_REMOVE,
        user_id=current_user.id, workspace_id=workspace_id, payload={"removed_user_id": str(user_id)},
        ip_address=request.client.host if request.client else "unknown"
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
