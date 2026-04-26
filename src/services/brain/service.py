import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import frontmatter

from src.services.brain import search as search_index
from src.services.brain.schemas import Note, NoteCreate, NoteMeta, NoteSearchResult, NoteUpdate

logger = logging.getLogger(__name__)


def _note_file(notes_path: str, path: str) -> Path:
    full = Path(notes_path) / path
    if not path.endswith(".md"):
        full = full.with_suffix(".md")
    return full


def _parse_note(notes_path: str, file_path: Path) -> Note:
    post = frontmatter.load(str(file_path))
    rel = str(file_path.relative_to(notes_path))
    fm = post.metadata
    return Note(
        path=rel,
        title=fm.get("title", file_path.stem),
        tags=fm.get("tags", []),
        type=fm.get("type", "note"),
        aliases=fm.get("aliases", []),
        created_at=fm.get("created_at", datetime.now(timezone.utc)),
        updated_at=fm.get("updated_at", datetime.now(timezone.utc)),
        body=post.content,
    )


def _write_note(file_path: Path, meta: dict[str, Any], body: str) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.Post(body, **meta)
    file_path.write_text(frontmatter.dumps(post))


def _git_commit_push_sync(notes_path: str, message: str) -> None:
    try:
        import git
        repo = git.Repo(notes_path)
        repo.git.add(A=True)
        if repo.is_dirty(untracked_files=True):
            repo.index.commit(message)
            try:
                repo.remotes.origin.push()
            except Exception:
                pass
    except Exception as e:
        logger.warning("git commit/push failed: %s", e)


async def _git_commit_push(notes_path: str, message: str) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _git_commit_push_sync, notes_path, message)


async def list_notes(notes_path: str, path_filter: str | None, type_filter: str | None, tag_filter: str | None) -> list[NoteMeta]:
    base = Path(notes_path)
    if path_filter:
        base = base / path_filter
    results = []
    for f in sorted(base.rglob("*.md")):
        if ".index" in f.parts:
            continue
        try:
            note = _parse_note(notes_path, f)
            if type_filter and note.type != type_filter:
                continue
            if tag_filter and tag_filter not in note.tags:
                continue
            results.append(NoteMeta(**note.model_dump(exclude={"body"})))
        except Exception as e:
            logger.warning("Failed to parse %s: %s", f, e)
    return results


async def get_note(notes_path: str, path: str) -> Note:
    f = _note_file(notes_path, path)
    if not f.exists():
        raise FileNotFoundError(path)
    return _parse_note(notes_path, f)


async def create_note(notes_path: str, path: str, content: NoteCreate) -> Note:
    f = _note_file(notes_path, path)
    if f.exists():
        raise FileExistsError(path)
    now = datetime.now(timezone.utc)
    meta: dict[str, Any] = {
        "title": content.title,
        "tags": content.tags,
        "type": content.type,
        "aliases": content.aliases,
        "created_at": now,
        "updated_at": now,
    }
    _write_note(f, meta, content.body)
    note = _parse_note(notes_path, f)
    await search_index.upsert_note(notes_path, {"path": note.path, "title": note.title, "body": content.body, "tags": note.tags, "type": note.type})
    asyncio.create_task(_git_commit_push(notes_path, f"feat: add {path}"))
    return note


async def update_note(notes_path: str, path: str, content: NoteUpdate) -> Note:
    f = _note_file(notes_path, path)
    if not f.exists():
        raise FileNotFoundError(path)
    existing = _parse_note(notes_path, f)
    now = datetime.now(timezone.utc)
    meta: dict[str, Any] = {
        "title": content.title if content.title is not None else existing.title,
        "tags": content.tags if content.tags is not None else existing.tags,
        "type": content.type if content.type is not None else existing.type,
        "aliases": content.aliases if content.aliases is not None else existing.aliases,
        "created_at": existing.created_at,
        "updated_at": now,
    }
    body = content.body if content.body is not None else existing.body
    _write_note(f, meta, body)
    note = _parse_note(notes_path, f)
    await search_index.upsert_note(notes_path, {"path": note.path, "title": note.title, "body": body, "tags": note.tags, "type": note.type})
    asyncio.create_task(_git_commit_push(notes_path, f"feat: update {path}"))
    return note


async def delete_note(notes_path: str, path: str) -> None:
    f = _note_file(notes_path, path)
    if not f.exists():
        raise FileNotFoundError(path)
    f.unlink()
    await search_index.delete_note(notes_path, path if path.endswith(".md") else path + ".md")
    asyncio.create_task(_git_commit_push(notes_path, f"feat: delete {path}"))


async def search_notes(notes_path: str, query: str, type_filter: str | None, tag_filter: str | None) -> list[NoteSearchResult]:
    rows = await search_index.search(notes_path, query, type_filter, tag_filter)
    results = []
    for row in rows:
        f = Path(notes_path) / row["path"]
        try:
            note = _parse_note(notes_path, f)
            results.append(NoteSearchResult(**note.model_dump(exclude={"body"}), excerpt=row["excerpt"]))
        except Exception:
            pass
    return results


async def rebuild_search_index(notes_path: str) -> None:
    base = Path(notes_path)
    notes = []
    for f in base.rglob("*.md"):
        if ".index" in f.parts:
            continue
        try:
            note = _parse_note(notes_path, f)
            notes.append({"path": note.path, "title": note.title, "body": note.body, "tags": note.tags, "type": note.type})
        except Exception as e:
            logger.warning("Skipping %s during index rebuild: %s", f, e)
    await search_index.rebuild_index(notes_path, notes)
    logger.info("Search index rebuilt with %d notes", len(notes))


async def list_folders(notes_path: str) -> list[str]:
    base = Path(notes_path)
    folders = set()
    for f in base.rglob("*.md"):
        if ".index" in f.parts:
            continue
        rel = f.parent.relative_to(base)
        if str(rel) != ".":
            folders.add(str(rel))
    return sorted(folders)
