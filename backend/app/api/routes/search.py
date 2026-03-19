import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import false, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Folder, Prompt, Task, TeamMember, User
from app.models.enums import VisibilityType

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]


class SearchResult(BaseModel):
    type: str
    id: uuid.UUID
    title: str
    snippet: str
    created_at: datetime


async def _get_user_team_ids(user_id: uuid.UUID, db: AsyncSession) -> list[uuid.UUID]:
    result = await db.execute(
        select(TeamMember.team_id).where(TeamMember.user_id == user_id)
    )
    return list(result.scalars().all())


@router.get("", response_model=list[SearchResult])
async def search(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    q: str = Query(..., min_length=1, description="Search query"),
    type: Literal["prompt", "task", "all"] = Query(default="all"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[SearchResult]:
    """Full-text search across prompts and tasks using PostgreSQL tsvector.

    All results respect visibility permissions for the current user.
    """
    user_team_ids = await _get_user_team_ids(current_user.id, db)

    results: list[SearchResult] = []

    # Visibility conditions helper for folder-backed team visibility
    visible_folder_ids_subq = (
        select(Folder.id)
        .where(
            or_(
                Folder.visibility_type == VisibilityType.public,
                Folder.created_by == current_user.id,
                Folder.team_ids.overlap(user_team_ids) if user_team_ids else false(),
            )
        )
        .scalar_subquery()
    )

    prompt_visibility = or_(
        Prompt.visibility_type == VisibilityType.public,
        Prompt.created_by == current_user.id,
        Prompt.folder_id.in_(visible_folder_ids_subq),
    )

    task_visibility = or_(
        Task.visibility_type == VisibilityType.public,
        Task.created_by == current_user.id,
        Task.folder_id.in_(visible_folder_ids_subq),
    )

    if type in ("prompt", "all"):
        prompt_results = await db.execute(
            select(Prompt)
            .where(
                prompt_visibility,
                text("to_tsvector('english', title) @@ plainto_tsquery('english', :q)").bindparams(q=q),
            )
            .order_by(Prompt.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        for p in prompt_results.scalars().all():
            results.append(
                SearchResult(
                    type="prompt",
                    id=p.id,
                    title=p.title,
                    snippet=p.title,
                    created_at=p.created_at,
                )
            )

    if type in ("task", "all"):
        task_results = await db.execute(
            select(Task)
            .where(
                task_visibility,
                text("to_tsvector('english', title) @@ plainto_tsquery('english', :q)").bindparams(q=q),
            )
            .order_by(Task.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        for t in task_results.scalars().all():
            results.append(
                SearchResult(
                    type="task",
                    id=t.id,
                    title=t.title,
                    snippet=t.title,
                    created_at=t.created_at,
                )
            )

    # Sort combined results by created_at descending, apply limit
    results.sort(key=lambda r: r.created_at, reverse=True)
    return results[:limit]
