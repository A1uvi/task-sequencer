import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Conversation, User
from app.schemas.conversation import ConversationRead

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=list[ConversationRead])
async def list_conversations(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    prompt_version_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ConversationRead]:
    """List conversations. Optionally filter by prompt_version_id.

    Access control: conversations are returned for all prompt versions the user
    can reference (no per-row user ownership on conversations — they are system
    records created by the worker). For now we list all and allow filtering.
    """
    query = select(Conversation).order_by(Conversation.created_at.desc())

    if prompt_version_id is not None:
        query = query.where(Conversation.prompt_version_id == prompt_version_id)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    conversations = result.scalars().all()
    return [ConversationRead.model_validate(c) for c in conversations]


@router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ConversationRead:
    """Get a single conversation by ID (read-only)."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    return ConversationRead.model_validate(conversation)
