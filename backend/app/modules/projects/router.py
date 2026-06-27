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
from app.modules.users.models import UserStatus

router = APIRouter(prefix="/projects", tags=["projects"])


def _build_out(project: "Project", user_id: int | None = None) -> ProjectOut:
    can_view_all = (
        project.is_public
        or project.created_by == user_id
        or any(v.user_id == user_id for v in project.allowed_viewers)
    )
    return ProjectOut(
        id=project.id,
        title=project.title,
        description=project.description,
        category_id=project.category_id,
        category_name=project.category.name if project.category else None,
        status=project.status,
        priority=project.priority,
        tech_stack=project.tech_stack,
        repo_url=project.repo_url,
        demo_url=project.demo_url,
        zip_url=project.zip_url,
        started_at=project.started_at,
        ended_at=project.ended_at,
        created_by=project.created_by,
        creator_display_name=project.creator.display_name if project.creator else None,
        is_public=project.is_public,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("", response_model=ProjectOut, summary="创建项目（成员）")
async def create_project(
    payload: ProjectCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectOut:
    if user.status != UserStatus.ACTIVE.value:
        from app.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError("只有在读成员可以新建项目")
    project = await service.create_project(
        db,
        created_by=user.id,
        data=payload.model_dump(exclude_unset=True),
    )
    return _build_out(project, user.id)


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
        items=[_build_out(p, user.id) for p in projects],
        total=total,
    )


@router.get("/{project_id}", response_model=ProjectOut, summary="获取项目详情")
async def get_project(
    project_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectOut:
    project = await service.get_project(db, project_id)
    return _build_out(project, user.id)


@router.patch("/{project_id}", response_model=ProjectOut, summary="更新项目")
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectOut:
    project = await service.update_project(
        db, project_id, user.id, user.is_admin_or_above(), payload.model_dump(exclude_unset=True)
    )
    return _build_out(project, user.id)


@router.delete("/{project_id}", summary="删除项目")
async def delete_project(
    project_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await service.delete_project(db, project_id, user.id, user.is_admin_or_above())
    return {"detail": "项目已删除"}
