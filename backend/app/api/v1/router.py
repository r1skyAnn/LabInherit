"""Aggregate /api/v1 router — import all v1 endpoints here."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.upload import router as upload_router
from app.modules.auth.router import router as auth_router
from app.modules.invites.router import router as invites_router
from app.modules.users.router import router as users_router
from app.modules.audit.router import router as audit_router
from app.modules.projects.router import router as projects_router
from app.modules.announcements.router import router as announcements_router
from app.modules.members.router import router as members_router
from app.modules.categories.router import router as categories_router
from app.modules.notes.router import router as notes_router
from app.modules.comments.router import router as comments_router
from app.modules.notifications.router import router as notifications_router
from app.modules.admin.router import router as admin_router
from app.modules.showcase.router import router as showcase_router
from app.modules.guides.router import router as guides_router
from app.modules.alumni_posts.router import router as alumni_posts_router
from app.api.v1.search import router as search_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(upload_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(invites_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(projects_router)
api_v1_router.include_router(announcements_router)
api_v1_router.include_router(members_router)
api_v1_router.include_router(categories_router)
api_v1_router.include_router(notes_router)
api_v1_router.include_router(comments_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(showcase_router)
api_v1_router.include_router(guides_router)
api_v1_router.include_router(alumni_posts_router)
api_v1_router.include_router(search_router)
