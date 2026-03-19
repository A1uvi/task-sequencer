import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import false, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Folder, TeamMember, User
from app.models.enums import VisibilityType
from app.schemas.folder import FolderCreate, FolderRead, FolderUpdate
from app.services.permissions import user_can_access_folder

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]


async def _get_user_team_ids(user_id: uuid.UUID, db: AsyncSession) -> list[uuid.UUID]:
    result = await db.execute(
        select(TeamMember.team_id).where(TeamMember.user_id == user_id)
    )
    return list(result.scalars().all())


@router.get("", response_model=list[FolderRead])
async def list_folders(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[FolderRead]:
    """List all folders visible to the current user:
    public folders + team folders the user belongs to + user's private folders.
    """
    user_team_ids = await _get_user_team_ids(current_user.id, db)

    result = await db.execute(
        select(Folder)
        .where(
            or_(
                Folder.visibility_type == VisibilityType.public,
                Folder.created_by == current_user.id,
                # Team visibility — SQLAlchemy ARRAY overlap operator
                Folder.team_ids.overlap(user_team_ids) if user_team_ids else false(),
            )
        )
        .order_by(Folder.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    folders = result.scalars().all()
    return [FolderRead.model_validate(f) for f in folders]


@router.post("", response_model=FolderRead, status_code=status.HTTP_201_CREATED)
async def create_folder(
    body: FolderCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> FolderRead:
    """Create a new folder owned by the current user."""
    folder = Folder(
        name=body.name,
        visibility_type=body.visibility_type,
        team_ids=body.team_ids,
        created_by=current_user.id,
    )
    db.add(folder)
    await db.flush()
    return FolderRead.model_validate(folder)


@router.get("/{folder_id}", response_model=FolderRead)
async def get_folder(
    folder_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> FolderRead:
    """Get a single folder. Permission check applied."""
    result = await db.execute(select(Folder).where(Folder.id == folder_id))
    folder = result.scalar_one_or_none()
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")

    if not await user_can_access_folder(current_user.id, folder_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return FolderRead.model_validate(folder)


@router.patch("/{folder_id}", response_model=FolderRead)
async def update_folder(
    folder_id: uuid.UUID,
    body: FolderUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> FolderRead:
    """Update a folder. Only the owner (created_by) may update."""
    result = await db.execute(select(Folder).where(Folder.id == folder_id))
    folder = result.scalar_one_or_none()
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")

    if folder.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can update this folder")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(folder, field, value)

    await db.flush()
    return FolderRead.model_validate(folder)


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a folder. Only the owner (created_by) may delete."""
    result = await db.execute(select(Folder).where(Folder.id == folder_id))
    folder = result.scalar_one_or_none()
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")

    if folder.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can delete this folder")

    await db.delete(folder)
