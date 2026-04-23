from typing import AsyncGenerator

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionChunk

from src.core.config import settings

AVAILABLE_MODELS = [
    # Meta Llama
    "meta-llama/llama-3.1-8b-instruct",
    # Anthropic
    "anthropic/claude-opus-4-7",
    "anthropic/claude-sonnet-4-6",
    "anthropic/claude-haiku-4-5",
    # OpenAI GPT-5
    "openai/gpt-5",
    "openai/gpt-5.4",
    "openai/gpt-5-mini",
    # OpenAI GPT-4.1
    "openai/gpt-4.1",
    "openai/gpt-4.1-mini",
    "openai/gpt-4.1-nano",
    # OpenAI GPT-4o
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    # OpenAI reasoning
    "openai/o3",
    "openai/o4-mini",
]

DEFAULT_MODEL = "meta-llama/llama-3.1-8b-instruct"

_client = AsyncOpenAI(
    api_key=settings.OPEN_ROUTER_KEY,
    base_url="https://openrouter.ai/api/v1",
)


async def stream_agent_response(
    model: str,
    messages: list,
    tools: list,
) -> AsyncGenerator[ChatCompletionChunk, None]:
    response = await _client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        stream=True,
        max_tokens=4096,
    )

    async for chunk in response:
        yield chunk
