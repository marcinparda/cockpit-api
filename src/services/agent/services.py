import json
from collections.abc import AsyncGenerator
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.agent import repository
from src.services.agent.llm import DEFAULT_MODEL, stream_agent_response
from src.services.agent.tools import TOOL_STATUS_MESSAGES, TOOLS
from src.services.agent.tools_executor import execute_tool, write_cv_preset

SYSTEM_PROMPT = """You are an AI assistant specialized in tailoring CVs for specific job offers.

When the user provides a job offer (text or URL):
1. Extract the company name from the job offer.
2. Call search_company to learn about the company's culture, values, and tech stack.
3. Call get_cv_base_preset to read the user's full CV.
4. Analyze the job requirements and the CV.
5. Call create_cv_preset with a tailored version — reduce experience bullets to 3 most relevant per role, drop irrelevant skills, include only relevant sections.

Rules:
- Always read the base CV before tailoring.
- Never modify the base preset.
- Preset name format: "{Company} - {Role} {YYYY-MM-DD}".
- After create_cv_preset is called, wait for the user to confirm before proceeding.
- If user says "yes" or "confirm" after a confirmation request, the preset will be saved automatically.
- If user says "no" or "cancel", acknowledge and offer to adjust."""

_CONFIRM_PHRASES = {"yes", "y", "ok", "confirm", "do it", "yes please", "go ahead", "save it", "save"}
_CANCEL_PHRASES = {"no", "n", "cancel", "stop", "don't", "abort", "nope"}


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


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

    # Check for pending confirmation from previous turn
    last_msg = await repository.get_last_message(db, conversation_id)
    pending = None
    if last_msg and last_msg.role == "user":
        # Look at the message before user's — the previous assistant message
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
    async for chunk in _run_agent_loop(db, redis_client, conversation_id, model):
        yield chunk


async def _run_agent_loop(
    db: AsyncSession,
    redis_client: Redis,
    conversation_id: UUID,
    model: str,
) -> AsyncGenerator[str, None]:
    db_messages = await repository.get_messages(db, conversation_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in db_messages:
        messages.append({"role": m.role, "content": m.content})

    max_iterations = 8

    for _ in range(max_iterations):
        accumulated_content = ""
        accumulated_tool_calls: dict[int, dict] = {}
        finish_reason = None

        try:
            async for chunk in stream_agent_response(model, messages, TOOLS):
                choice = chunk.choices[0]
                if choice.finish_reason:
                    finish_reason = choice.finish_reason
                delta = choice.delta

                if delta.content:
                    accumulated_content += delta.content

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
            yield _sse("chunk", {"text": final_text})
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
