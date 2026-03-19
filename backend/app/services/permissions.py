import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import APIKey, Folder, Prompt, TeamMember
from app.models.enums import APIKeyOwnerType, VisibilityType


async def _get_user_team_ids(user_id: uuid.UUID, db: AsyncSession) -> list[uuid.UUID]:
    """Return a list of team IDs that the user is a member of."""
    result = await db.execute(
        select(TeamMember.team_id).where(TeamMember.user_id == user_id)
    )
    return list(result.scalars().all())


async def user_can_use_api_key(
    user_id: uuid.UUID,
    api_key_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    """Check all 4 access paths:
    1. user is direct owner (owner_type=user, owner_id=user_id)
    2. user is in shared_with_users[]
    3. user's team owns the key (owner_type=team, owner_id in user's team_ids)
    4. user's team is in shared_with_teams[]
    """
    result = await db.execute(select(APIKey).where(APIKey.id == api_key_id))
    api_key = result.scalar_one_or_none()
    if api_key is None:
        return False

    # Path 1: direct user owner
    if api_key.owner_type == APIKeyOwnerType.user and api_key.owner_id == user_id:
        return True

    # Path 2: user in shared_with_users
    shared_users = api_key.shared_with_users or []
    if user_id in shared_users:
        return True

    team_ids = await _get_user_team_ids(user_id, db)

    # Path 3: one of the user's teams owns the key
    if api_key.owner_type == APIKeyOwnerType.team and api_key.owner_id in team_ids:
        return True

    # Path 4: one of the user's teams is in shared_with_teams
    shared_teams = api_key.shared_with_teams or []
    for tid in team_ids:
        if tid in shared_teams:
            return True

    return False


async def user_can_access_folder(
    user_id: uuid.UUID,
    folder_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    """Check visibility_type:
    - public: always True
    - team: user must be member of a team in folder.team_ids
    - private: user must be created_by
    """
    result = await db.execute(select(Folder).where(Folder.id == folder_id))
    folder = result.scalar_one_or_none()
    if folder is None:
        return False

    if folder.visibility_type == VisibilityType.public:
        return True

    if folder.visibility_type == VisibilityType.private:
        return folder.created_by == user_id

    # team visibility
    if folder.visibility_type == VisibilityType.team:
        folder_team_ids = set(folder.team_ids or [])
        if not folder_team_ids:
            # No teams configured — only creator can access
            return folder.created_by == user_id
        user_team_ids = await _get_user_team_ids(user_id, db)
        return bool(folder_team_ids.intersection(user_team_ids))

    return False


async def user_can_access_prompt(
    user_id: uuid.UUID,
    prompt_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    """Check prompt visibility and, if in a folder, folder access.
    - public prompt: always True
    - team prompt: user must be in a team listed in the prompt's containing folder
    - private prompt: user must be created_by
    """
    result = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
    prompt = result.scalar_one_or_none()
    if prompt is None:
        return False

    if prompt.visibility_type == VisibilityType.public:
        return True

    if prompt.visibility_type == VisibilityType.private:
        return prompt.created_by == user_id

    # team visibility — check folder membership if prompt has a folder
    if prompt.visibility_type == VisibilityType.team:
        if prompt.folder_id is not None:
            return await user_can_access_folder(user_id, prompt.folder_id, db)
        # No folder — fall back to creator check
        return prompt.created_by == user_id

    return False
