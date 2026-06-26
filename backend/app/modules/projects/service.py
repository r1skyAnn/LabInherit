"""Project business logic."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import PermissionDeniedError, NotFoundError
from app.modules.projects.models import Project, ProjectStatus


async def create_project(
    db: AsyncSession,
    created_by: int,
    data: dict,
) -> Project:
    project = Project(created_by=created_by, **data)
    db.add(project)
    await db.commit()
    await db.refresh(project, attribute_names=["creator", "category"])
    return project


async def list_projects(
    db: AsyncSession,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Project], int]:
    base = (
        select(Project)
        .options(selectinload(Project.creator), selectinload(Project.category))
        .order_by(Project.created_at.desc())
    )
    if status:
        base = base.where(Project.status == status)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one() or 0

    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    projects = list(result.scalars().all())
    return projects, total


async def get_project(db: AsyncSession, project_id: int) -> Project:
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.creator), selectinload(Project.category))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("项目不存在")
    return project


async def update_project(
    db: AsyncSession,
    project_id: int,
    user_id: int,
    is_admin: bool,
    data: dict,
) -> Project:
    project = await get_project(db, project_id)
    if project.created_by != user_id and not is_admin:
        raise PermissionDeniedError("只有项目负责人可以修改项目信息")
    for key, value in data.items():
        if value is not None or key in (
            "description", "tech_stack", "repo_url", "demo_url",
        ):
            setattr(project, key, value)
    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(
    db: AsyncSession,
    project_id: int,
    user_id: int,
    is_admin: bool,
) -> None:
    project = await get_project(db, project_id)
    if project.created_by != user_id and not is_admin:
        raise PermissionDeniedError("只有项目负责人可以删除项目")
    await db.delete(project)
    await db.commit()
