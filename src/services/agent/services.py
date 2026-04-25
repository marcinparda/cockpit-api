import json
from collections.abc import AsyncGenerator
from datetime import date, timedelta
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.agent import repository
from src.services.agent.llm import calculate_cost, stream_agent_response
from src.services.agent.tools import TOOLS, TOOL_STATUS_MESSAGES
from src.services.agent.tools_executor import execute_tool, write_cv_preset

BUDGET_LIMIT_USD = 0.10


def _abort_key(conversation_id: UUID) -> str:
    return f"agent:abort:{conversation_id}"

# ── Planner system prompt ──────────────────────────────────────────────────────

def _planner_system_prompt() -> str:
    today = date.today()
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=(6 - today.weekday()))
    week_end_excl = week_end + timedelta(days=1)
    month_end = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    month_end_excl = month_end + timedelta(days=1)
    return f"""You are a personal assistant with tools for three systems:
- Actual Budget (personal finance): accounts, transactions, categories, payees
- Vikunja (task management): projects, tasks, users, assignments
- CV tailoring: resume presets, company research

Today: {today.isoformat()}

## Workflow — follow for every request

### Step 1: PLAN
Before calling any tool, output a short plan:
<plan>
1. tool_name — reason
2. tool_name — reason (parallel with 1 / after 1)
</plan>
If no tool can fulfill the request, say so immediately without a plan.

### Step 2: EXECUTE (read-only tools only)
Run read-only tools from the plan. Call independent tools in parallel. For dependent steps, wait.

### Step 3: CONFIRM WRITES
If the plan includes any write operations (create, update, delete, patch): STOP. Present a summary of all planned writes to the user — show the exact data that will be written. Ask: "Proceed?" Do not call any write tool until the user explicitly confirms (yes/ok/confirm/go ahead/do it/save).

### Step 4: RESPOND
After all tools complete (or after write confirmation and execution):
- Success → present results only. No commentary, no offers, no "if you want more" sentences.
- Partial failure → diagnose, retry with corrected args if fixable without user input.
- Missing tool → say "I can't do X — I don't have a tool for it."

---

## Domain knowledge

### Actual Budget
Amount format: milliunits integer. 1000 = 1.00 PLN. Expenses negative (-10500 = -10.50 PLN). Income positive.
Polish CSV format: comma is decimal separator, space is thousands separator. Convert steps: (1) remove spaces, (2) replace comma with dot, (3) parse float, (4) multiply by 1000, (5) round to integer. Examples: "-21,50 PLN" → -21500; "-1 890,62 PLN" → -1890620; "-149,00 PLN" → -149000.
Finding transactions: actual_list_accounts first (get account_id by name), then actual_search_transactions.
Bank import (user pastes statement lines): actual_list_accounts → actual_list_categories → actual_list_payees → show parsed transactions table (date, description, amount in PLN, amount in milliunits, category) → wait for confirmation (Step 3) → actual_batch_create_transactions (learn_categories=true, payee_name="AI Agent") → report imported items, flag uncertain categories.
Payee rule: always set payee_name="AI Agent" on all imported/created transactions. Never use real merchant/payee names.
Single transaction: actual_create_transaction. Update/fix category: actual_update_transaction.

### Vikunja
Filter syntax for vikunja_get_tasks: field comparator value joined with &&.
Date filters are exclusive of time — use next day's date to include tasks due on a given day.
  - Due today: filter='due_date<={tomorrow.isoformat()}&&done=false', sort_by='due_date', order_by='asc'
  - Due this week: filter='due_date<={week_end_excl.isoformat()}&&done=false', sort_by='due_date', order_by='asc'
  - Due this month: filter='due_date<={month_end_excl.isoformat()}&&done=false', sort_by='due_date', order_by='asc'
Task with assignees: vikunja_list_projects → vikunja_list_users → vikunja_create_task with assignees=[user_id].

### CV tailoring
Always call get_cv_base_preset before tailoring. Never modify the base preset.
After create_cv_preset: wait for user confirmation ("yes"/"confirm") before saving.
Preset name format: "{{Company}} - {{Role}} YYYY-MM-DD"."""

# ── Confirmation phrases (CV-specific) ────────────────────────────────────────

_CONFIRM_PHRASES = {"yes", "y", "ok", "confirm", "do it", "yes please", "go ahead", "save it", "save"}
_CANCEL_PHRASES = {"no", "n", "cancel", "stop", "don't", "abort", "nope"}


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ── Main entry point ───────────────────────────────────────────────────────────

async def stream_message(
    db: AsyncSession,
    redis_client: Redis,
    conversation_id: UUID,
    user_id: UUID,
    user_content: str,
) -> AsyncGenerator[str, None]:
    conversation = await repository.get_conversation(db, conversation_id, user_id)
    if conversation is None:
        yield _sse("error", {"text": "Conversation not found."})
        yield _sse("done", {})
        return

    await repository.save_message(db, conversation_id, "user", user_content)

    # Check for pending CV confirmation from previous turn
    pending = None
    all_msgs = await repository.get_messages(db, conversation_id)
    for msg in reversed(all_msgs[:-1]):  # skip just-saved user message
        if msg.role == "assistant" and msg.extra_data and msg.extra_data.get("pending_preset"):
            pending = msg.extra_data["pending_preset"]
            break

    if pending:
        lower = user_content.strip().lower()
        if lower in _CONFIRM_PHRASES:
            async for chunk in _execute_pending_preset(db, redis_client, conversation_id, pending):
                yield chunk
            return
        if lower in _CANCEL_PHRASES:
            text = "Understood — preset creation cancelled. Let me know if you'd like to adjust the CV."
            await repository.save_message(db, conversation_id, "assistant", text)
            yield _sse("chunk", {"text": text})
            yield _sse("done", {})
            return

    model = conversation.model
    if "/" not in model:
        model = f"anthropic/{model}"

    async for chunk in _run_agent_loop(db, redis_client, conversation_id, model, _planner_system_prompt(), TOOLS):
        yield chunk


# ── Agent loop ─────────────────────────────────────────────────────────────────

async def _run_agent_loop(
    db: AsyncSession,
    redis_client: Redis,
    conversation_id: UUID,
    model: str,
    system_prompt: str,
    tools: list,
) -> AsyncGenerator[str, None]:
    db_messages = await repository.get_messages(db, conversation_id)
    messages = [{"role": "system", "content": system_prompt}]
    for m in db_messages:
        messages.append({"role": m.role, "content": m.content})

    max_iterations = 1000
    total_cost = 0.0

    for _ in range(max_iterations):
        if await redis_client.get(_abort_key(conversation_id)):
            await redis_client.delete(_abort_key(conversation_id))
            yield _sse("error", {"text": "Stopped by user."})
            yield _sse("done", {})
            return

        if total_cost >= BUDGET_LIMIT_USD:
            yield _sse("error", {"text": f"Budget exceeded. Cost so far: ${total_cost:.4f} (limit: ${BUDGET_LIMIT_USD:.2f})."})
            yield _sse("done", {})
            return

        accumulated_content = ""
        accumulated_tool_calls: dict[int, dict] = {}
        finish_reason = None
        aborted = False

        try:
            chunk_count = 0
            async for chunk in stream_agent_response(model, messages, tools):
                if not chunk.choices:
                    if chunk.usage:
                        total_cost += calculate_cost(
                            model,
                            chunk.usage.prompt_tokens,
                            chunk.usage.completion_tokens,
                        )
                    continue

                chunk_count += 1
                if chunk_count % 10 == 0 and await redis_client.get(_abort_key(conversation_id)):
                    await redis_client.delete(_abort_key(conversation_id))
                    aborted = True
                    break

                choice = chunk.choices[0]
                if choice.finish_reason:
                    finish_reason = choice.finish_reason
                delta = choice.delta

                if delta.content:
                    accumulated_content += delta.content
                    yield _sse("chunk", {"text": delta.content})

                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in accumulated_tool_calls:
                            accumulated_tool_calls[idx] = {
                                "id": tc.id or "",
                                "type": "function",
                                "function": {"name": tc.function.name or "", "arguments": ""},
                            }
                        if tc.id:
                            accumulated_tool_calls[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                accumulated_tool_calls[idx]["function"]["name"] = tc.function.name
                            if tc.function.arguments:
                                accumulated_tool_calls[idx]["function"]["arguments"] += tc.function.arguments
        except Exception as e:
            yield _sse("error", {"text": str(e)})
            yield _sse("done", {})
            return

        if aborted:
            yield _sse("error", {"text": "Stopped by user."})
            yield _sse("done", {})
            return

        if finish_reason == "tool_calls" or accumulated_tool_calls:
            tool_calls = [accumulated_tool_calls[i] for i in sorted(accumulated_tool_calls)]

            messages.append({
                "role": "assistant",
                "content": accumulated_content or None,
                "tool_calls": tool_calls,
            })

            tool_results = []
            for tc in tool_calls:
                tool_name = tc["function"]["name"]
                tool_args = json.loads(tc["function"]["arguments"] or "{}")

                status_text = TOOL_STATUS_MESSAGES.get(tool_name, f"Running {tool_name}...")
                yield _sse("status", {"text": status_text})

                result = await execute_tool(tool_name, tool_args, redis_client)

                if tool_name == "create_cv_preset" and result.get("confirm_required"):
                    assistant_text = (
                        f"I've prepared a tailored CV preset: **{result['preset_name']}**. "
                        "Review the preview below and confirm to save it."
                    )
                    await repository.save_message(
                        db,
                        conversation_id,
                        "assistant",
                        assistant_text,
                        metadata={"pending_preset": {"name": result["preset_name"], "sections": result["sections"]}},
                    )
                    yield _sse("confirm_required", {
                        "action": "create_cv_preset",
                        "preset_name": result["preset_name"],
                        "preview": result["sections"],
                    })
                    yield _sse("done", {})
                    return

                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": tool_name,
                    "content": json.dumps(result),
                })

            messages.extend(tool_results)

        else:
            final_text = accumulated_content or ""
            await repository.save_message(db, conversation_id, "assistant", final_text)
            yield _sse("done", {})
            return

    yield _sse("error", {"text": "Agent reached maximum iterations without completing."})
    yield _sse("done", {})


async def _execute_pending_preset(
    db: AsyncSession,
    redis_client: Redis,
    conversation_id: UUID,
    pending: dict,
) -> AsyncGenerator[str, None]:
    preset_name = pending["name"]
    sections = pending["sections"]

    yield _sse("status", {"text": f"Saving preset '{preset_name}' to Redis..."})

    try:
        await write_cv_preset(preset_name, sections, redis_client)
        text = f"Done! Preset **{preset_name}** has been saved. You can now select it in the CV editor."
    except Exception as e:
        text = f"Failed to save preset: {e}"

    await repository.save_message(db, conversation_id, "assistant", text)
    yield _sse("chunk", {"text": text})
    yield _sse("done", {})
