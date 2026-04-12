"""Workspace browsing, selection, and file viewing endpoints."""

from __future__ import annotations

import mimetypes
import os
import stat
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from af_core.config import settings

router = APIRouter(prefix="/api/workspace", tags=["workspace"])

# Max file size we'll return content for (1 MB)
_MAX_VIEW_SIZE = 1 * 1024 * 1024

# Extensions we treat as text (viewable in the UI)
_TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml",
    ".toml", ".cfg", ".ini", ".md", ".txt", ".rst", ".html", ".css",
    ".xml", ".csv", ".sh", ".bash", ".zsh", ".env", ".gitignore",
    ".dockerfile", ".sql", ".graphql", ".proto", ".go", ".rs",
    ".java", ".kt", ".c", ".cpp", ".h", ".hpp", ".rb", ".php",
    ".swift", ".r", ".lua", ".pl", ".ex", ".exs", ".erl",
    ".hs", ".ml", ".scala", ".clj", ".vim", ".conf", ".log",
    ".lock", ".editorconfig",
}


class FileEntry(BaseModel):
    name: str
    path: str  # relative to workspace root
    is_dir: bool
    size: int | None = None
    modified: str | None = None
    extension: str | None = None
    is_text: bool = False


class WorkspaceInfo(BaseModel):
    path: str
    exists: bool
    total_files: int = 0
    total_dirs: int = 0
    total_size: int = 0


class FileContent(BaseModel):
    path: str
    name: str
    content: str
    size: int
    extension: str | None = None
    mime_type: str | None = None
    lines: int = 0


def _get_workspace() -> str:
    """Return the current effective workspace root."""
    return os.path.abspath(settings.workspace_root)


def _validate_inside_workspace(workspace: str, path: str) -> str:
    """Resolve path and ensure it's within the workspace. Returns abs path."""
    abs_path = os.path.normpath(os.path.join(workspace, path))
    if not abs_path.startswith(workspace + os.sep) and abs_path != workspace:
        raise HTTPException(
            status_code=400, detail=f"Path escapes workspace: {path}"
        )
    return abs_path


def _is_text_file(name: str) -> bool:
    ext = os.path.splitext(name)[1].lower()
    if ext in _TEXT_EXTENSIONS:
        return True
    # Files without extension that are common text files
    if name.lower() in {
        "makefile", "dockerfile", "procfile", "gemfile",
        "rakefile", "license", "readme", "changelog",
    }:
        return True
    return False


def _stat_entry(
    workspace: str, abs_path: str, name: str
) -> FileEntry:
    """Build a FileEntry from a filesystem path."""
    try:
        st = os.stat(abs_path)
    except OSError:
        return FileEntry(
            name=name,
            path=os.path.relpath(abs_path, workspace),
            is_dir=False,
        )
    is_dir = stat.S_ISDIR(st.st_mode)
    ext = os.path.splitext(name)[1].lower() if not is_dir else None
    return FileEntry(
        name=name,
        path=os.path.relpath(abs_path, workspace),
        is_dir=is_dir,
        size=st.st_size if not is_dir else None,
        modified=datetime.fromtimestamp(
            st.st_mtime, tz=UTC
        ).isoformat(),
        extension=ext,
        is_text=_is_text_file(name) if not is_dir else False,
    )


@router.get("/info")
async def workspace_info() -> WorkspaceInfo:
    """Get info about the current workspace."""
    workspace = _get_workspace()
    if not os.path.isdir(workspace):
        return WorkspaceInfo(path=workspace, exists=False)

    total_files = 0
    total_dirs = 0
    total_size = 0
    for root, dirs, files in os.walk(workspace):
        # Skip hidden dirs and common noise
        dirs[:] = [
            d for d in dirs
            if not d.startswith(".") and d not in {"node_modules", "__pycache__", ".venv", "venv"}
        ]
        total_dirs += len(dirs)
        for f in files:
            if f.startswith("."):
                continue
            total_files += 1
            try:
                total_size += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass

    return WorkspaceInfo(
        path=workspace,
        exists=True,
        total_files=total_files,
        total_dirs=total_dirs,
        total_size=total_size,
    )


@router.get("/browse")
async def browse(
    path: str = Query(default="", description="Relative path within workspace"),
) -> dict:
    """Browse files and directories at the given path within the workspace."""
    workspace = _get_workspace()
    if not os.path.isdir(workspace):
        raise HTTPException(
            status_code=404,
            detail=f"Workspace directory does not exist: {workspace}",
        )

    if path:
        abs_path = _validate_inside_workspace(workspace, path)
    else:
        abs_path = workspace

    if not os.path.isdir(abs_path):
        raise HTTPException(
            status_code=404,
            detail=f"Directory not found: {path}",
        )

    entries: list[FileEntry] = []
    try:
        for name in sorted(os.listdir(abs_path)):
            # Skip hidden files/dirs
            if name.startswith("."):
                continue
            child = os.path.join(abs_path, name)
            entries.append(_stat_entry(workspace, child, name))
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Sort: dirs first, then files
    entries.sort(key=lambda e: (not e.is_dir, e.name.lower()))

    return {
        "workspace_root": workspace,
        "current_path": path or ".",
        "parent": os.path.dirname(path) if path else None,
        "entries": [e.model_dump() for e in entries],
    }


@router.get("/file")
async def view_file(
    path: str = Query(..., description="Relative path to file within workspace"),
) -> FileContent:
    """Read a file's content (text files only, up to 1MB)."""
    workspace = _get_workspace()
    abs_path = _validate_inside_workspace(workspace, path)

    if not os.path.isfile(abs_path):
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    size = os.path.getsize(abs_path)
    if size > _MAX_VIEW_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large to view ({size} bytes, max {_MAX_VIEW_SIZE})",
        )

    name = os.path.basename(abs_path)
    if not _is_text_file(name):
        # Try reading anyway — might be text without a known extension
        pass

    try:
        content = Path(abs_path).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cannot read file: {e}")

    ext = os.path.splitext(name)[1].lower() or None
    mime, _ = mimetypes.guess_type(name)

    return FileContent(
        path=path,
        name=name,
        content=content,
        size=size,
        extension=ext,
        mime_type=mime,
        lines=content.count("\n") + 1,
    )


@router.get("/tree")
async def file_tree(
    max_depth: int = Query(default=3, ge=1, le=10),
) -> dict:
    """Return a recursive tree of the workspace (up to max_depth levels)."""
    workspace = _get_workspace()
    if not os.path.isdir(workspace):
        return {"workspace_root": workspace, "tree": []}

    skip_dirs = {
        ".git", ".venv", "venv", "node_modules",
        "__pycache__", ".mypy_cache", ".pytest_cache",
        ".ruff_cache", "dist", "build", ".eggs",
    }

    def _build_tree(dir_path: str, depth: int) -> list[dict]:
        if depth > max_depth:
            return []
        items = []
        try:
            names = sorted(os.listdir(dir_path))
        except PermissionError:
            return []
        for name in names:
            if name.startswith(".") and name not in {".env.example"}:
                continue
            full = os.path.join(dir_path, name)
            rel = os.path.relpath(full, workspace)
            if os.path.isdir(full):
                if name in skip_dirs:
                    continue
                children = _build_tree(full, depth + 1)
                items.append({
                    "name": name,
                    "path": rel,
                    "is_dir": True,
                    "children": children,
                })
            else:
                try:
                    size = os.path.getsize(full)
                except OSError:
                    size = 0
                items.append({
                    "name": name,
                    "path": rel,
                    "is_dir": False,
                    "size": size,
                    "is_text": _is_text_file(name),
                })
        return items

    tree = _build_tree(workspace, 1)
    return {"workspace_root": workspace, "tree": tree}


@router.put("/set-root")
async def set_workspace_root(
    path: str = Query(..., description="New workspace root path"),
) -> dict:
    """Set the active workspace root directory.

    The path must exist and be a directory. This updates the runtime
    config — it takes effect immediately for all subsequent operations.
    """
    abs_path = os.path.abspath(os.path.expanduser(path))
    if not os.path.isdir(abs_path):
        raise HTTPException(
            status_code=400,
            detail=f"Directory does not exist: {abs_path}",
        )

    # Update the runtime singleton
    settings.workspace_root = abs_path
    return {
        "status": "ok",
        "workspace_root": abs_path,
        "message": f"Workspace root set to {abs_path}",
    }


@router.post("/create-dir")
async def create_directory(
    path: str = Query(..., description="Relative path for new directory"),
) -> dict:
    """Create a directory within the workspace."""
    workspace = _get_workspace()
    abs_path = _validate_inside_workspace(workspace, path)

    try:
        os.makedirs(abs_path, exist_ok=True)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Cannot create directory: {e}")

    return {
        "path": os.path.relpath(abs_path, workspace),
        "created": True,
    }


@router.get("/mission/{mission_id}")
async def mission_workspace(mission_id: str) -> dict:
    """Get the workspace directory for a specific mission.

    Each mission gets an isolated subdirectory under the workspace root.
    Creates it if it doesn't exist.
    """
    workspace = _get_workspace()
    mission_dir = os.path.join(workspace, "missions", mission_id)
    existed = os.path.isdir(mission_dir)
    os.makedirs(mission_dir, exist_ok=True)

    entries: list[FileEntry] = []
    for name in sorted(os.listdir(mission_dir)):
        if name.startswith("."):
            continue
        child = os.path.join(mission_dir, name)
        entries.append(_stat_entry(workspace, child, name))

    return {
        "mission_id": mission_id,
        "path": os.path.relpath(mission_dir, workspace),
        "abs_path": mission_dir,
        "existed": existed,
        "entries": [e.model_dump() for e in entries],
    }


@router.get("/validate-path")
async def validate_path(
    path: str = Query(..., description="Path to validate"),
) -> dict:
    """Validate whether a path is a valid workspace root."""
    abs_path = os.path.abspath(os.path.expanduser(path))
    exists = os.path.exists(abs_path)
    is_dir = os.path.isdir(abs_path) if exists else False
    writable = os.access(abs_path, os.W_OK) if exists else False

    # Check parent if path doesn't exist yet
    can_create = False
    if not exists:
        parent = os.path.dirname(abs_path)
        can_create = os.path.isdir(parent) and os.access(parent, os.W_OK)

    return {
        "path": abs_path,
        "exists": exists,
        "is_directory": is_dir,
        "writable": writable,
        "can_create": can_create,
        "valid": is_dir and writable,
    }
