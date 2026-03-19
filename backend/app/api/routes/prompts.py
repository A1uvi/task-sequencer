import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import false, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Folder, Prompt, PromptVersion, TeamMember, User
from app.models.enums import VisibilityType
from app.schemas.prompt import PromptCreate, PromptRead, PromptUpdate
from app.schemas.prompt_version import PromptVersionCreate, PromptVersionRead
from app.services.permissions import user_can_access_prompt

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]


async def _get_user_team_ids(user_id: uuid.UUID, db: AsyncSession) -> list[uuid.UUID]:
    result = await db.execute(
        select(TeamMember.team_id).where(TeamMember.user_id == user_id)
    )
    return list(result.scalars().all())


async def _assert_prompt_owner(
    prompt_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> Prompt:
    result = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
    prompt = result.scalar_one_or_none()
    if prompt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
    if prompt.created_by != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can modify this prompt")
    return prompt


@router.get("", response_model=list[PromptRead])
async def list_prompts(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    folder_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[PromptRead]:
    """List prompts visible to the current user, optionally filtered by folder."""
    user_team_ids = await _get_user_team_ids(current_user.id, db)

    # Build folder visibility subquery
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

    conditions = [
        or_(
            Prompt.visibility_type == VisibilityType.public,
            Prompt.created_by == current_user.id,
            # Team-visible prompts whose folder is accessible
            Prompt.folder_id.in_(visible_folder_ids_subq),
        )
    ]

    if folder_id is not None:
        conditions.append(Prompt.folder_id == folder_id)

    query = (
        select(Prompt)
        .where(*conditions)
        .order_by(Prompt.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    prompts = result.scalars().all()
    return [PromptRead.model_validate(p) for p in prompts]


@router.post("", response_model=PromptRead, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    body: PromptCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> PromptRead:
    """Create a prompt. A first PromptVersion (version 1) is created automatically."""
    prompt = Prompt(
        title=body.title,
        folder_id=body.folder_id,
        visibility_type=body.visibility_type,
        created_by=current_user.id,
        current_version_id=None,
    )
    db.add(prompt)
    await db.flush()  # get prompt.id

    # Create the first version automatically with empty content
    version = PromptVersion(
        prompt_id=prompt.id,
        content="",
        version_number=1,
        variables={},
        tags=[],
        created_by=current_user.id,
    )
    db.add(version)
    await db.flush()

    prompt.current_version_id = version.id
    await db.flush()

    return PromptRead.model_validate(prompt)


@router.get("/{prompt_id}", response_model=PromptRead)
async def get_prompt(
    prompt_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> PromptRead:
    """Get a single prompt. Permission check applied."""
    result = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
    prompt = result.scalar_one_or_none()
    if prompt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")

    if not await user_can_access_prompt(current_user.id, prompt_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return PromptRead.model_validate(prompt)


@router.patch("/{prompt_id}", response_model=PromptRead)
async def update_prompt(
    prompt_id: uuid.UUID,
    body: PromptUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> PromptRead:
    """Update prompt title/visibility/folder. Owner only."""
    prompt = await _assert_prompt_owner(prompt_id, current_user.id, db)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prompt, field, value)

    await db.flush()
    return PromptRead.model_validate(prompt)


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a prompt. Owner only."""
    prompt = await _assert_prompt_owner(prompt_id, current_user.id, db)
    await db.delete(prompt)


@router.get("/{prompt_id}/versions", response_model=list[PromptVersionRead])
async def list_prompt_versions(
    prompt_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[PromptVersionRead]:
    """List all versions of a prompt. Permission check on prompt."""
    if not await user_can_access_prompt(current_user.id, prompt_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.version_number.asc())
        .limit(limit)
        .offset(offset)
    )
    versions = result.scalars().all()
    return [PromptVersionRead.model_validate(v) for v in versions]


@router.post(
    "/{prompt_id}/versions",
    response_model=PromptVersionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_prompt_version(
    prompt_id: uuid.UUID,
    body: PromptVersionCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> PromptVersionRead:
    """Create a new immutable PromptVersion. Increments version_number,
    updates prompt.current_version_id. Owner only.
    """
    prompt = await _assert_prompt_owner(prompt_id, current_user.id, db)

    # Determine next version number
    count_result = await db.execute(
        select(func.max(PromptVersion.version_number)).where(
            PromptVersion.prompt_id == prompt_id
        )
    )
    max_version = count_result.scalar() or 0

    version = PromptVersion(
        prompt_id=prompt_id,
        content=body.content,
        usage_notes=body.usage_notes,
        variables=body.variables,
        example_input=body.example_input,
        example_output=body.example_output,
        meta_notes=body.meta_notes,
        tags=body.tags,
        version_number=max_version + 1,
        created_by=current_user.id,
    )
    db.add(version)
    await db.flush()

    prompt.current_version_id = version.id
    await db.flush()

    return PromptVersionRead.model_validate(version)
