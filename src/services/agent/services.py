import json
from collections.abc import AsyncGenerator
from datetime import date, timedelta
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.agent import repository
from src.services.agent.llm import DEFAULT_MODEL, classify_domain, stream_agent_response
from src.services.agent.tools import BUDGET_TOOLS, CV_TOOLS, TASK_TOOLS, TOOL_STATUS_MESSAGES
from src.services.agent.tools_executor import execute_tool, write_cv_preset

# ── Domain system prompts ──────────────────────────────────────────────────────

_CV_SYSTEM_PROMPT = """You are a CV tailoring assistant.

When the user provides a job offer (text or URL):
1. Extract the company name.
2. Call search_company to learn about culture, values, and tech stack.
3. Call get_cv_base_preset to read the user's full CV.
4. Call create_cv_preset with a tailored version:
   - 3 most relevant experience bullets per role
   - Drop irrelevant skills
   - Include only relevant sections
   - Preset name format: "{Company} - {Role} YYYY-MM-DD"

Rules:
- Always read the base CV before tailoring. Never modify the base preset.
- After create_cv_preset is called, wait for user confirmation before saving.
- "yes"/"confirm" → saves automatically. "no"/"cancel" → acknowledge and offer to adjust."""


def _budget_system_prompt() -> str:
    today = date.today().isoformat()
    return f"""You are a budget management assistant for Actual Budget. Today is {today}.

Amount format: milliunits integer. 1000 = $1.00. Expenses negative (-10500 = -$10.50). Income positive.

Bank import workflow (user pastes bank statement lines):
1. actual_list_accounts — get account IDs.
2. actual_list_categories — know available categories.
3. actual_list_payees — check existing payees to reuse IDs.
4. Categorize each item intelligently from payee name and amount.
5. actual_batch_create_transactions with learn_categories=true.
6. Report what was imported; flag uncertain categorizations.

For single transactions: actual_create_transaction.
For finding transactions: actual_search_transactions (requires account_id + since_date).
For fixing category: actual_update_transaction."""


def _task_system_prompt() -> str:
    today = date.today()
    week_end = today + timedelta(days=(6 - today.weekday()))
    month_end = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    return f"""You are a task management assistant for Vikunja. Today is {today.isoformat()}.

Filter syntax for vikunja_get_tasks: field comparator value, joined with &&.
Useful date constants:
  - Today: {today.isoformat()}
  - End of week: {week_end.isoformat()}
  - End of month: {month_end.isoformat()}

Common filter patterns:
  - Due today (all tasks due by 23:59:59 today, including overdue): filter='due_date<={today.isoformat()}&&done=false', sort_by='due_date', order_by='asc'
  - Due this week (all tasks due by 23:59:59 on {week_end.strftime("%A, %Y-%m-%d")}): filter='due_date<={week_end.isoformat()}&&done=false', sort_by='due_date', order_by='asc'
  - Due this month (all tasks due by 23:59:59 on {month_end.isoformat()}): filter='due_date<={month_end.isoformat()}&&done=false', sort_by='due_date', order_by='asc'
  - All open: filter='done=false'

When user asks for tasks "today", "this week", or "this month": use the full end-of-period filter above — include all tasks due up to and including the last moment of that period, not just overdue ones.

Task creation with assignees:
1. vikunja_list_projects → get project_id.
2. vikunja_list_users → find user_id by name if needed.
3. vikunja_create_task with assignees=[user_id, ...].

For summaries: fetch tasks with the date filter, group by project or due date in your response."""


_DOMAIN_CONFIGS: dict[str, tuple] = {
    "cv": (lambda: _CV_SYSTEM_PROMPT, CV_TOOLS),
    "budget": (_budget_system_prompt, BUDGET_TOOLS),
    "tasks": (_task_system_prompt, TASK_TOOLS),
}

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

    # Classify intent using last few messages for context
    recent = [{"role": m.role, "content": m.content} for m in all_msgs[-3:] if m.role in ("user", "assistant")]
    try:
        domain = await classify_domain(recent, model)
    except Exception as e:
        yield _sse("error", {"text": str(e)})
        yield _sse("done", {})
        return

    prompt_fn, domain_tools = _DOMAIN_CONFIGS[domain]
    system_prompt = prompt_fn()

    async for chunk in _run_agent_loop(db, redis_client, conversation_id, model, system_prompt, domain_tools):
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

    max_iterations = 8

    for _ in range(max_iterations):
        accumulated_content = ""
        accumulated_tool_calls: dict[int, dict] = {}
        finish_reason = None

        try:
            async for chunk in stream_agent_response(model, messages, tools):
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
