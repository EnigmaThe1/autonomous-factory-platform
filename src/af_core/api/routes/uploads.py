"""File and zip upload endpoints."""

import os
import shutil
import zipfile
from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from af_core.config import settings
from af_core.database import get_db
from af_core.models.mission import Mission
from af_core.models.report import Artifact
from af_core.services.event_bus import event_bus
from af_core.services.tool_gateway import ToolGateway

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
MAX_ZIP_SIZE = 500 * 1024 * 1024  # 500MB


def _get_gateway() -> ToolGateway:
    return ToolGateway(settings.workspace_root)


def _safe_dest(workspace_root: str, relative_path: str) -> str:
    """Resolve and validate that the destination is within the workspace."""
    abs_path = os.path.normpath(os.path.join(workspace_root, relative_path))
    abs_root = os.path.normpath(workspace_root)
    if not abs_path.startswith(abs_root + os.sep) and abs_path != abs_root:
        raise HTTPException(status_code=400, detail=f"Path escapes workspace: {relative_path}")
    return abs_path


@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    dest: str = Form(default=""),
    mission_id: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload a single file to the workspace.

    - file: The file to upload
    - dest: Destination directory relative to workspace root (default: root)
    - mission_id: Optional mission to associate the upload with
    """
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(content)} bytes). Max: {MAX_UPLOAD_SIZE}",
        )

    workspace = os.path.abspath(settings.workspace_root)
    os.makedirs(workspace, exist_ok=True)

    # Build destination path
    filename = file.filename or "uploaded_file"
    # Sanitize filename — strip path separators to prevent traversal
    filename = os.path.basename(filename)
    rel_path = os.path.join(dest, filename) if dest else filename
    abs_path = _safe_dest(workspace, rel_path)

    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(content)

    result = {
        "filename": filename,
        "path": os.path.relpath(abs_path, workspace),
        "size": len(content),
        "content_type": file.content_type,
    }

    # Record as artifact if mission_id given
    if mission_id:
        mission = await db.get(Mission, mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        artifact = Artifact(
            mission_id=mission_id,
            artifact_type="uploaded_file",
            name=filename,
            path=result["path"],
            extra={"size": len(content), "content_type": file.content_type},
        )
        db.add(artifact)
        await db.commit()
        result["artifact_id"] = artifact.id

        await event_bus.emit(
            "upload.file",
            {
                "mission_id": mission_id,
                "filename": filename,
                "path": result["path"],
                "size": len(content),
            },
        )

    return result


@router.post("/files")
async def upload_multiple_files(
    files: list[UploadFile] = File(...),
    dest: str = Form(default=""),
    mission_id: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload multiple files to the workspace."""
    workspace = os.path.abspath(settings.workspace_root)
    os.makedirs(workspace, exist_ok=True)
    results = []

    for file in files:
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            results.append(
                {
                    "filename": file.filename,
                    "error": f"Too large ({len(content)} bytes)",
                }
            )
            continue

        filename = os.path.basename(file.filename or "uploaded_file")
        rel_path = os.path.join(dest, filename) if dest else filename
        abs_path = _safe_dest(workspace, rel_path)

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(content)

        entry = {
            "filename": filename,
            "path": os.path.relpath(abs_path, workspace),
            "size": len(content),
        }

        if mission_id:
            artifact = Artifact(
                mission_id=mission_id,
                artifact_type="uploaded_file",
                name=filename,
                path=entry["path"],
                extra={"size": len(content), "content_type": file.content_type},
            )
            db.add(artifact)
            entry["artifact_id"] = artifact.id

        results.append(entry)

    if mission_id:
        await db.commit()

    return {"uploaded": len([r for r in results if "error" not in r]), "files": results}


@router.post("/zip")
async def upload_and_extract_zip(
    file: UploadFile = File(...),
    dest: str = Form(default=""),
    mission_id: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload a zip archive and extract it into the workspace.

    - file: The zip file to upload
    - dest: Destination directory relative to workspace root (default: root)
    - mission_id: Optional mission to associate the upload with
    """
    content = await file.read()
    if len(content) > MAX_ZIP_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Zip too large ({len(content)} bytes). Max: {MAX_ZIP_SIZE}",
        )

    # Validate it's actually a zip
    if not zipfile.is_zipfile(BytesIO(content)):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid zip archive")

    workspace = os.path.abspath(settings.workspace_root)
    extract_dir = _safe_dest(workspace, dest) if dest else workspace
    os.makedirs(extract_dir, exist_ok=True)

    extracted_files = []
    skipped_files = []

    with zipfile.ZipFile(BytesIO(content)) as zf:
        for member in zf.infolist():
            # Skip directories
            if member.is_dir():
                continue

            # Security: reject paths that escape the workspace
            member_path = os.path.normpath(member.filename)
            if member_path.startswith("..") or os.path.isabs(member_path):
                skipped_files.append({"name": member.filename, "reason": "path traversal"})
                continue

            # Security: skip hidden OS metadata
            if "__MACOSX" in member.filename or member.filename.startswith("."):
                skipped_files.append({"name": member.filename, "reason": "metadata"})
                continue

            target = os.path.join(extract_dir, member_path)
            # Double-check resolved path is within workspace
            if not os.path.normpath(target).startswith(workspace):
                skipped_files.append({"name": member.filename, "reason": "path traversal"})
                continue

            os.makedirs(os.path.dirname(target), exist_ok=True)
            with zf.open(member) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)

            rel = os.path.relpath(target, workspace)
            extracted_files.append({"name": member.filename, "path": rel, "size": member.file_size})

    result = {
        "archive": file.filename,
        "archive_size": len(content),
        "dest": dest or ".",
        "extracted_count": len(extracted_files),
        "skipped_count": len(skipped_files),
        "files": extracted_files,
    }

    if skipped_files:
        result["skipped"] = skipped_files

    # Record as artifact if mission_id given
    if mission_id:
        mission = await db.get(Mission, mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        artifact = Artifact(
            mission_id=mission_id,
            artifact_type="uploaded_zip",
            name=file.filename or "archive.zip",
            path=dest or ".",
            extra={
                "archive_size": len(content),
                "extracted_count": len(extracted_files),
                "files": [f["path"] for f in extracted_files],
            },
        )
        db.add(artifact)
        await db.commit()
        result["artifact_id"] = artifact.id

        await event_bus.emit(
            "upload.zip",
            {
                "mission_id": mission_id,
                "archive": file.filename,
                "extracted_count": len(extracted_files),
                "dest": dest or ".",
            },
        )

    return result
