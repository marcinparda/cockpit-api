from typing import Any

from mcp.server.fastmcp import FastMCP


def register_brain_tools(mcp: FastMCP) -> None:
    from src.services.brain import service as brain_service
    from src.services.brain.schemas import NoteCreate, NoteUpdate
    from src.core.config import settings

    @mcp.tool()
    async def brain_search_notes(
        query: str,
        type_filter: str | None = None,
        tag_filter: str | None = None,
    ) -> Any:
        """Full-text search across brain notes. Returns matching notes with excerpts.

        Args:
            query: Search query string
            type_filter: Filter by note type: 'context', 'reference', or 'note'
            tag_filter: Filter by tag
        """
        results = await brain_service.search_notes(settings.BRAIN_NOTES_PATH, query, type_filter, tag_filter)
        return [r.model_dump() for r in results]

    @mcp.tool()
    async def brain_get_note(path: str) -> Any:
        """Read a brain note by its path (relative to notes root, e.g. 'health/sleep.md').

        Args:
            path: Note path relative to notes root
        """
        try:
            note = await brain_service.get_note(settings.BRAIN_NOTES_PATH, path)
            return note.model_dump()
        except FileNotFoundError:
            return {"error": f"Note not found: {path}"}

    @mcp.tool()
    async def brain_list_notes(
        path_filter: str | None = None,
        type_filter: str | None = None,
        tag_filter: str | None = None,
    ) -> Any:
        """List brain notes with optional filters. Returns metadata without body content.

        Args:
            path_filter: Subfolder to list (e.g. 'health')
            type_filter: Filter by type: 'context', 'reference', or 'note'
            tag_filter: Filter by tag
        """
        notes = await brain_service.list_notes(settings.BRAIN_NOTES_PATH, path_filter, type_filter, tag_filter)
        return [n.model_dump() for n in notes]

    @mcp.tool()
    async def brain_list_folders() -> Any:
        """List all folders in the brain notes directory."""
        folders = await brain_service.list_folders(settings.BRAIN_NOTES_PATH)
        return {"folders": folders}

    @mcp.tool()
    async def brain_create_note(
        path: str,
        title: str,
        body: str,
        type: str = "note",
        tags: list[str] | None = None,
        aliases: list[str] | None = None,
    ) -> Any:
        """Create a new brain note. Commits and pushes to git automatically.

        Args:
            path: Note path relative to notes root, e.g. 'health/new-note.md'
            title: Note title
            body: Note body in markdown
            type: Note type - 'context', 'reference', or 'note'
            tags: Optional list of tags
            aliases: Optional list of aliases
        """
        content = NoteCreate(
            title=title,
            body=body,
            type=type,
            tags=tags or [],
            aliases=aliases or [],
        )
        try:
            note = await brain_service.create_note(settings.BRAIN_NOTES_PATH, path, content)
            return note.model_dump()
        except FileExistsError:
            return {"error": f"Note already exists: {path}"}

    @mcp.tool()
    async def brain_update_note(
        path: str,
        title: str | None = None,
        body: str | None = None,
        type: str | None = None,
        tags: list[str] | None = None,
        aliases: list[str] | None = None,
    ) -> Any:
        """Update an existing brain note. Only provided fields are changed. Commits and pushes to git.

        Args:
            path: Note path relative to notes root
            title: New title (optional)
            body: New body (optional)
            type: New type (optional)
            tags: New tags (optional)
            aliases: New aliases (optional)
        """
        content = NoteUpdate(title=title, body=body, type=type, tags=tags, aliases=aliases)
        try:
            note = await brain_service.update_note(settings.BRAIN_NOTES_PATH, path, content)
            return note.model_dump()
        except FileNotFoundError:
            return {"error": f"Note not found: {path}"}

    @mcp.tool()
    async def brain_delete_note(path: str) -> Any:
        """Delete a brain note. Commits and pushes to git automatically.

        Args:
            path: Note path relative to notes root
        """
        try:
            await brain_service.delete_note(settings.BRAIN_NOTES_PATH, path)
            return {"success": True, "path": path}
        except FileNotFoundError:
            return {"error": f"Note not found: {path}"}
