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

DEFAULT_MODEL = "openai/gpt-5-mini"

_client = AsyncOpenAI(
    api_key=settings.OPEN_ROUTER_KEY,
    base_url="https://openrouter.ai/api/v1",
)


_CLASSIFIER_SYSTEM = """Classify the user's intent into exactly one domain.
Reply with exactly one word — no punctuation, no explanation.

Domains:
- cv: CV tailoring, resume editing, job applications, company research for a job offer
- budget: expenses, transactions, accounts, categories, payees, money, bank statement, spending
- tasks: tasks, todos, deadlines, projects, assignments, schedule, due dates, what to do"""

_DOMAIN_FALLBACK = "tasks"


async def classify_domain(recent_messages: list[dict], model: str) -> str:
    messages = [
        {"role": "system", "content": _CLASSIFIER_SYSTEM},
        *recent_messages,
    ]
    response = await _client.chat.completions.create(
        model=model,
        messages=messages,
        stream=False,
        max_tokens=16,
    )
    text = (response.choices[0].message.content or "").strip().lower()
    for domain in ("cv", "budget", "tasks"):
        if domain in text:
            return domain
    return _DOMAIN_FALLBACK


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
