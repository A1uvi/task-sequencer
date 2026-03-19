import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import false, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.encryption import encrypt_api_key
from app.core.security import get_current_user
from app.models import APIKey, TeamMember, User
from app.models.enums import APIKeyOwnerType, APIKeyStatus
from app.schemas.api_key import APIKeyCreate, APIKeyRead
from app.services.audit import log_event
from app.services.permissions import user_can_use_api_key

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]


class ShareRequest(BaseModel):
    user_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None


async def _get_user_team_ids(user_id: uuid.UUID, db: AsyncSession) -> list[uuid.UUID]:
    result = await db.execute(
        select(TeamMember.team_id).where(TeamMember.user_id == user_id)
    )
    return list(result.scalars().all())


@router.get("", response_model=list[APIKeyRead])
async def list_api_keys(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[APIKeyRead]:
    """List API keys the user owns or has access to."""
    user_team_ids = await _get_user_team_ids(current_user.id, db)

    result = await db.execute(
        select(APIKey)
        .where(
            or_(
                # Direct user owner
                (
                    (APIKey.owner_type == APIKeyOwnerType.user)
                    & (APIKey.owner_id == current_user.id)
                ),
                # Team owner
                (
                    (APIKey.owner_type == APIKeyOwnerType.team)
                    & APIKey.owner_id.in_(user_team_ids)
                )
                if user_team_ids
                else false(),
                # Shared with user directly
                APIKey.shared_with_users.any(current_user.id),
                # Shared with user's teams
                APIKey.shared_with_teams.overlap(user_team_ids) if user_team_ids else false(),
            )
        )
        .order_by(APIKey.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    keys = result.scalars().all()
    return [APIKeyRead.from_orm_with_mask(k) for k in keys]


@router.post("", response_model=APIKeyRead, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: APIKeyCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> APIKeyRead:
    """Create a new API key. Encrypts the raw key before storing.
    Returns masked_key (last 4 chars of plaintext), never the encrypted value.
    """
    plaintext_key = body.key
    encrypted = encrypt_api_key(plaintext_key)

    api_key = APIKey(
        provider=body.provider,
        encrypted_key=encrypted,
        owner_type=body.owner_type,
        owner_id=body.owner_id,
        shared_with_users=body.shared_with_users,
        shared_with_teams=body.shared_with_teams,
        status=body.status,
    )
    db.add(api_key)
    await db.flush()

    await log_event(
        db=db,
        user_id=current_user.id,
        event_type="api_key.created",
        resource_id=api_key.id,
        metadata={"provider": body.provider},
    )

    # Build response with masked_key from plaintext (last 4 chars)
    read_data = APIKeyRead(
        id=api_key.id,
        provider=api_key.provider,
        owner_type=api_key.owner_type,
        owner_id=api_key.owner_id,
        shared_with_users=api_key.shared_with_users,
        shared_with_teams=api_key.shared_with_teams,
        status=api_key.status,
        masked_key=plaintext_key[-4:] if len(plaintext_key) >= 4 else "****",
        created_at=api_key.created_at,
    )
    return read_data


@router.get("/{api_key_id}", response_model=APIKeyRead)
async def get_api_key(
    api_key_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> APIKeyRead:
    """Get a single API key. Permission check applied."""
    result = await db.execute(select(APIKey).where(APIKey.id == api_key_id))
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    if not await user_can_use_api_key(current_user.id, api_key_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return APIKeyRead.from_orm_with_mask(api_key)


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    api_key_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke an API key (set status=revoked). Owner only."""
    result = await db.execute(select(APIKey).where(APIKey.id == api_key_id))
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    # Only user-type owner with matching id can revoke
    if not (
        api_key.owner_type == APIKeyOwnerType.user and api_key.owner_id == current_user.id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can revoke this API key")

    api_key.status = APIKeyStatus.revoked
    await db.flush()

    await log_event(
        db=db,
        user_id=current_user.id,
        event_type="api_key.revoked",
        resource_id=api_key_id,
    )


@router.post("/{api_key_id}/share", response_model=APIKeyRead)
async def share_api_key(
    api_key_id: uuid.UUID,
    body: ShareRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> APIKeyRead:
    """Add a user or team to the API key's shared list. Owner only."""
    result = await db.execute(select(APIKey).where(APIKey.id == api_key_id))
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    if not (
        api_key.owner_type == APIKeyOwnerType.user and api_key.owner_id == current_user.id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can share this API key")

    if body.user_id is not None:
        current_users = list(api_key.shared_with_users or [])
        if body.user_id not in current_users:
            current_users.append(body.user_id)
        api_key.shared_with_users = current_users

    if body.team_id is not None:
        current_teams = list(api_key.shared_with_teams or [])
        if body.team_id not in current_teams:
            current_teams.append(body.team_id)
        api_key.shared_with_teams = current_teams

    await db.flush()

    await log_event(
        db=db,
        user_id=current_user.id,
        event_type="api_key.shared",
        resource_id=api_key_id,
        metadata={
            "user_id": str(body.user_id) if body.user_id else None,
            "team_id": str(body.team_id) if body.team_id else None,
        },
    )

    return APIKeyRead.from_orm_with_mask(api_key)


@router.delete("/{api_key_id}/share", response_model=APIKeyRead)
async def unshare_api_key(
    api_key_id: uuid.UUID,
    body: ShareRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> APIKeyRead:
    """Remove a user or team from the API key's shared list. Owner only."""
    result = await db.execute(select(APIKey).where(APIKey.id == api_key_id))
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    if not (
        api_key.owner_type == APIKeyOwnerType.user and api_key.owner_id == current_user.id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can unshare this API key")

    if body.user_id is not None:
        current_users = list(api_key.shared_with_users or [])
        api_key.shared_with_users = [u for u in current_users if u != body.user_id]

    if body.team_id is not None:
        current_teams = list(api_key.shared_with_teams or [])
        api_key.shared_with_teams = [t for t in current_teams if t != body.team_id]

    await db.flush()

    await log_event(
        db=db,
        user_id=current_user.id,
        event_type="api_key.unshared",
        resource_id=api_key_id,
        metadata={
            "user_id": str(body.user_id) if body.user_id else None,
            "team_id": str(body.team_id) if body.team_id else None,
        },
    )

    return APIKeyRead.from_orm_with_mask(api_key)
