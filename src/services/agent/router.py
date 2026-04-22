from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.agent import repository, services
from src.services.agent.llm import AVAILABLE_MODELS, DEFAULT_MODEL
from src.services.agent.schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageResponse,
    ModelInfo,
    ModelListResponse,
    SendMessageRequest,
)
from src.services.authentication.dependencies import get_current_user
from src.services.authorization.permissions.dependencies import require_permission
from src.services.authorization.permissions.enums import Actions, Features
from src.services.redis_store.dependencies import get_redis_client
from src.services.users.models import User

router = APIRouter(tags=["agent"])


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    _: User = Depends(require_permission(Features.AGENT, Actions.READ)),
) -> ModelListResponse:
    model_labels = {
        # Anthropic
        "anthropic/claude-opus-4-7": "Claude Opus 4.7 | price: high | speed: medium | quality: very high",
        "anthropic/claude-sonnet-4-6": "Claude Sonnet 4.6 | price: medium | speed: high | quality: high",
        "anthropic/claude-haiku-4-5": "Claude Haiku 4.5 | price: low | speed: very high | quality: medium",
        # OpenAI GPT-5
        "openai/gpt-5": "GPT-5 | price: very high | speed: medium | quality: very high",
        "openai/gpt-5-mini": "GPT-5 Mini | price: medium | speed: high | quality: high",
        # OpenAI GPT-4.1
        "openai/gpt-4.1": "GPT-4.1 | price: medium | speed: high | quality: high",
        "openai/gpt-4.1-mini": "GPT-4.1 Mini | price: low | speed: very high | quality: medium",
        "openai/gpt-4.1-nano": "GPT-4.1 Nano | price: very low | speed: very high | quality: medium",
        # OpenAI GPT-4o
        "openai/gpt-4o": "GPT-4o | price: medium | speed: high | quality: high",
        "openai/gpt-4o-mini": "GPT-4o Mini | price: low | speed: very high | quality: medium",
        # OpenAI reasoning
        "openai/o3": "o3 | price: very high | speed: low | quality: very high",
        "openai/o4-mini": "o4-mini | price: medium | speed: medium | quality: very high",
    }
    return ModelListResponse(
        models=[ModelInfo(id=m, label=model_labels.get(m, m)) for m in AVAILABLE_MODELS],
        default=DEFAULT_MODEL,
    )


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(require_permission(Features.AGENT, Actions.READ)),
    db: AsyncSession = Depends(get_db),
) -> list[ConversationResponse]:
    conversations = await repository.get_conversations(db, current_user.id)
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreate,
    current_user: User = Depends(require_permission(Features.AGENT, Actions.CREATE)),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    if body.model not in AVAILABLE_MODELS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown model: {body.model}")
    conversation = await repository.create_conversation(db, current_user.id, body.title, body.model)
    return ConversationResponse.model_validate(conversation)


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def rename_conversation(
    conversation_id: UUID,
    body: ConversationUpdate,
    current_user: User = Depends(require_permission(Features.AGENT, Actions.UPDATE)),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    conversation = await repository.get_conversation(db, conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    updated = await repository.update_conversation_title(db, conversation, body.title)
    return ConversationResponse.model_validate(updated)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(require_permission(Features.AGENT, Actions.DELETE)),
    db: AsyncSession = Depends(get_db),
) -> None:
    conversation = await repository.get_conversation(db, conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    await repository.delete_conversation(db, conversation)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: UUID,
    current_user: User = Depends(require_permission(Features.AGENT, Actions.READ)),
    db: AsyncSession = Depends(get_db),
) -> list[MessageResponse]:
    conversation = await repository.get_conversation(db, conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    messages = await repository.get_messages(db, conversation_id)
    return [MessageResponse.model_validate(m) for m in messages]


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: UUID,
    body: SendMessageRequest,
    current_user: User = Depends(require_permission(Features.AGENT, Actions.CREATE)),
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis_client),
):
    conversation = await repository.get_conversation(db, conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    return StreamingResponse(
        services.stream_message(db, redis_client, conversation_id, current_user.id, body.content),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
