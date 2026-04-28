from mcp.server.fastmcp import FastMCP

PROACTIVE_TYPES = {"context", "reference"}


def register_brain_resources(mcp: FastMCP) -> None:
    from src.services.brain import service as brain_service
    from src.core.config import settings

    @mcp.resource("brain://notes")
    async def list_context_notes() -> str:
        """Lists all notes with type 'context' or 'reference' — proactive background context."""
        notes = await brain_service.list_notes(settings.BRAIN_NOTES_PATH, None, None, None)
        proactive = [n for n in notes if n.type in PROACTIVE_TYPES]
        if not proactive:
            return "No context or reference notes found."
        lines = [f"## Brain Notes (context & reference)\n"]
        for n in proactive:
            tags = ", ".join(n.tags) if n.tags else "none"
            lines.append(f"- [{n.type}] {n.title} — `{n.path}` (tags: {tags})")
        return "\n".join(lines)

    @mcp.resource("brain://notes/{path}")
    async def get_note_resource(path: str) -> str:
        """Read a brain note by path. Returns full markdown content."""
        try:
            note = await brain_service.get_note(settings.BRAIN_NOTES_PATH, path)
            return f"# {note.title}\n\n{note.body}"
        except FileNotFoundError:
            return f"Note not found: {path}"
