from typing import AsyncGenerator

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionChunk

from src.core.config import settings

# (input_per_1m_usd, output_per_1m_usd)
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "meta-llama/llama-3.1-8b-instruct": (0.055, 0.055),
    "anthropic/claude-opus-4-7":        (15.0,  75.0),
    "anthropic/claude-sonnet-4-6":      (3.0,   15.0),
    "anthropic/claude-haiku-4-5":       (0.8,   4.0),
    "openai/gpt-5":                     (10.0,  30.0),
    "openai/gpt-5.4":                   (5.0,   20.0),
    "openai/gpt-5-mini":                (0.4,   1.6),
    "openai/gpt-4.1":                   (2.0,   8.0),
    "openai/gpt-4.1-mini":              (0.4,   1.6),
    "openai/gpt-4.1-nano":              (0.1,   0.4),
    "openai/gpt-4o":                    (2.5,   10.0),
    "openai/gpt-4o-mini":               (0.15,  0.6),
    "openai/o3":                        (10.0,  40.0),
    "openai/o4-mini":                   (1.1,   4.4),
}
_DEFAULT_PRICING = (2.0, 8.0)


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    input_rate, output_rate = MODEL_PRICING.get(model, _DEFAULT_PRICING)
    return (prompt_tokens * input_rate + completion_tokens * output_rate) / 1_000_000


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
- budget: expenses, transactions, accounts, categories, payees, money, bank statement, spending, overspend, budget, finance, financial, income, savings, balance
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
        stream_options={"include_usage": True},
    )

    async for chunk in response:
        yield chunk
