from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.agent.models import Conversation, Message


async def get_conversations(db: AsyncSession, user_id: UUID) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_conversation(db: AsyncSession, conversation_id: UUID, user_id: UUID) -> Conversation | None:
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def create_conversation(db: AsyncSession, user_id: UUID, title: str, model: str) -> Conversation:
    conversation = Conversation(user_id=user_id, title=title, model=model)
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def update_conversation_title(db: AsyncSession, conversation: Conversation, title: str) -> Conversation:
    conversation.title = title
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def delete_conversation(db: AsyncSession, conversation: Conversation) -> None:
    await db.delete(conversation)
    await db.commit()


async def get_messages(db: AsyncSession, conversation_id: UUID) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())


async def save_message(
    db: AsyncSession,
    conversation_id: UUID,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        extra_data=metadata,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_last_message(db: AsyncSession, conversation_id: UUID) -> Message | None:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
