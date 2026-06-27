"""Project business logic."""

from __future__ import annotations

from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import PermissionDeniedError, NotFoundError
from app.modules.projects.models import Project, ProjectStatus, ProjectViewer


async def create_project(
    db: AsyncSession,
    created_by: int,
    data: dict,
) -> Project:
    allowed_viewer_ids = data.pop("allowed_viewer_ids", [])
    project = Project(created_by=created_by, **data)
    db.add(project)
    await db.flush()

    for user_id in allowed_viewer_ids:
        viewer = ProjectViewer(project_id=project.id, user_id=user_id)
        db.add(viewer)

    await db.commit()
    await db.refresh(project, attribute_names=["creator", "category", "allowed_viewers"])
    return project


async def list_projects(
    db: AsyncSession,
    user_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Project], int]:
    base = (
        select(Project)
        .options(selectinload(Project.creator), selectinload(Project.category), selectinload(Project.allowed_viewers))
        .order_by(Project.created_at.desc())
    )

    if user_id is not None:
        base = base.where(
            or_(
                Project.is_public == True,
                Project.created_by == user_id,
                Project.allowed_viewers.any(ProjectViewer.user_id == user_id)
            )
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
        .options(selectinload(Project.creator), selectinload(Project.category), selectinload(Project.allowed_viewers))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("项目不存在")
    return project


def _can_view_project(project: Project, user_id: int | None) -> bool:
    if project.is_public:
        return True
    if user_id is None:
        return False
    if project.created_by == user_id:
        return True
    return any(v.user_id == user_id for v in project.allowed_viewers)


async def update_project(
    db: AsyncSession,
    project_id: int,
    user_id: int,
    is_owner: bool,
    data: dict,
) -> Project:
    project = await get_project(db, project_id)

    if not _can_view_project(project, user_id):
        raise PermissionDeniedError("无权修改此项目")

    if project.created_by != user_id and not is_owner:
        raise PermissionDeniedError("只有项目负责人可以修改项目信息")

    allowed_viewer_ids = data.pop("allowed_viewer_ids", None)

    for key, value in data.items():
        if value is not None or key in (
            "description", "tech_stack", "repo_url", "demo_url",
        ):
            setattr(project, key, value)

    if allowed_viewer_ids is not None:
        for viewer in project.allowed_viewers:
            await db.delete(viewer)
        for vid in allowed_viewer_ids:
            db.add(ProjectViewer(project_id=project.id, user_id=vid))

    await db.commit()
    await db.refresh(project, attribute_names=["allowed_viewers"])
    return project


async def delete_project(
    db: AsyncSession,
    project_id: int,
    user_id: int,
    is_owner: bool,
) -> None:
    project = await get_project(db, project_id)
    if project.created_by != user_id and not is_owner:
        raise PermissionDeniedError("只有项目负责人可以删除项目")
    await db.delete(project)
    await db.commit()
