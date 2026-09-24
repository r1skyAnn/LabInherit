"""Project HTTP routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.db.session import get_db
from app.modules.projects import service
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectListResponse,
    ProjectOut,
    ProjectUpdate,
)
from app.modules.users.models import UserRole, UserStatus

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, summary="创建项目（成员）")
async def create_project(
    payload: ProjectCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectOut:
    # Allow ACTIVE members or owner to create projects
    if user.status != UserStatus.ACTIVE.value and user.role != UserRole.OWNER.value:
        from app.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError("只有在读成员或导师可以新建项目")
    project = await service.create_project(
        db,
        created_by=user.id,
        data=payload.model_dump(exclude_unset=True),
    )
    return ProjectOut.model_validate(project)


@router.get("", response_model=ProjectListResponse, summary="列出项目")
async def list_projects(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ProjectListResponse:
    projects, total = await service.list_projects(
        db, user_id=user.id, status=status, page=page, page_size=page_size
    )
    return ProjectListResponse(
        items=[ProjectOut.model_validate(p) for p in projects],
        total=total,
    )


@router.get("/{project_id}", response_model=ProjectOut, summary="获取项目详情")
async def get_project(
    project_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectOut:
    project = await service.get_project(db, project_id)
    if not service._can_view_project(project, user.id):
        from app.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError("无权查看此项目")
    return ProjectOut.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectOut, summary="更新项目")
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectOut:
    project = await service.update_project(
        db, project_id, user.id, user.is_owner(), payload.model_dump(exclude_unset=True)
    )
    return ProjectOut.model_validate(project)


@router.delete("/{project_id}", summary="删除项目")
async def delete_project(
    project_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await service.delete_project(db, project_id, user.id, user.is_owner())
    return {"detail": "项目已删除"}
