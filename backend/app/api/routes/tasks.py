import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import false, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Folder, Task, TaskVersion, TeamMember, User
from app.models.enums import VisibilityType
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.schemas.task_version import TaskVersionCreate, TaskVersionRead

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]


async def _get_user_team_ids(user_id: uuid.UUID, db: AsyncSession) -> list[uuid.UUID]:
    result = await db.execute(
        select(TeamMember.team_id).where(TeamMember.user_id == user_id)
    )
    return list(result.scalars().all())


async def _user_can_access_task(
    user_id: uuid.UUID, task_id: uuid.UUID, db: AsyncSession
) -> bool:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        return False

    if task.visibility_type == VisibilityType.public:
        return True
    if task.visibility_type == VisibilityType.private:
        return task.created_by == user_id

    # team visibility
    if task.visibility_type == VisibilityType.team and task.folder_id is not None:
        folder_result = await db.execute(select(Folder).where(Folder.id == task.folder_id))
        folder = folder_result.scalar_one_or_none()
        if folder is not None:
            folder_team_ids = set(folder.team_ids or [])
            user_team_ids = await _get_user_team_ids(user_id, db)
            return bool(folder_team_ids.intersection(user_team_ids))
    return task.created_by == user_id


async def _assert_task_owner(
    task_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.created_by != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can modify this task")
    return task


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    folder_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[TaskRead]:
    """List tasks visible to the current user."""
    user_team_ids = await _get_user_team_ids(current_user.id, db)

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
            Task.visibility_type == VisibilityType.public,
            Task.created_by == current_user.id,
            Task.folder_id.in_(visible_folder_ids_subq),
        )
    ]

    if folder_id is not None:
        conditions.append(Task.folder_id == folder_id)

    query = (
        select(Task)
        .where(*conditions)
        .order_by(Task.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    tasks = result.scalars().all()
    return [TaskRead.model_validate(t) for t in tasks]


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> TaskRead:
    """Create a task. A first TaskVersion is created automatically."""
    task = Task(
        title=body.title,
        folder_id=body.folder_id,
        visibility_type=body.visibility_type,
        created_by=current_user.id,
        current_version_id=None,
    )
    db.add(task)
    await db.flush()

    # Create first version with empty prompt list
    version = TaskVersion(
        task_id=task.id,
        ordered_prompt_version_ids=[],
        default_model="gpt-4o",
        allow_model_override_per_step=False,
        version_number=1,
    )
    db.add(version)
    await db.flush()

    task.current_version_id = version.id
    await db.flush()

    return TaskRead.model_validate(task)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> TaskRead:
    """Get a single task. Permission check applied."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if not await _user_can_access_task(current_user.id, task_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: uuid.UUID,
    body: TaskUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> TaskRead:
    """Update task title/visibility/folder. Owner only."""
    task = await _assert_task_owner(task_id, current_user.id, db)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.flush()
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a task. Owner only."""
    task = await _assert_task_owner(task_id, current_user.id, db)
    await db.delete(task)


@router.get("/{task_id}/versions", response_model=list[TaskVersionRead])
async def list_task_versions(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[TaskVersionRead]:
    """List all versions of a task. Permission check on task."""
    if not await _user_can_access_task(current_user.id, task_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = await db.execute(
        select(TaskVersion)
        .where(TaskVersion.task_id == task_id)
        .order_by(TaskVersion.version_number.asc())
        .limit(limit)
        .offset(offset)
    )
    versions = result.scalars().all()
    return [TaskVersionRead.model_validate(v) for v in versions]


@router.post(
    "/{task_id}/versions",
    response_model=TaskVersionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task_version(
    task_id: uuid.UUID,
    body: TaskVersionCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> TaskVersionRead:
    """Create a new immutable TaskVersion. Owner only."""
    task = await _assert_task_owner(task_id, current_user.id, db)

    count_result = await db.execute(
        select(func.max(TaskVersion.version_number)).where(
            TaskVersion.task_id == task_id
        )
    )
    max_version = count_result.scalar() or 0

    version = TaskVersion(
        task_id=task_id,
        ordered_prompt_version_ids=body.ordered_prompt_version_ids,
        default_model=body.default_model,
        allow_model_override_per_step=body.allow_model_override_per_step,
        version_number=max_version + 1,
    )
    db.add(version)
    await db.flush()

    task.current_version_id = version.id
    await db.flush()

    return TaskVersionRead.model_validate(version)
