"""File management endpoints."""

import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from api.models import FileListResponse, FileContentResponse, FileInfo


router = APIRouter(prefix="/files", tags=["File Management"])


def get_session_directory(session_id: str) -> Path:
    """Get the session directory path."""
    base_dir = Path(__file__).parent.parent.parent / "sessions" / session_id
    return base_dir


@router.get("/{session_id}", response_model=FileListResponse)
async def list_session_files(session_id: str):
    """List all files in a session directory."""
    session_dir = get_session_directory(session_id)

    if not session_dir.exists():
        return {"files": [], "session_id": session_id}

    files = []

    # Walk through directory
    for root, dirs, filenames in os.walk(session_dir):
        for filename in filenames:
            file_path = Path(root) / filename
            relative_path = file_path.relative_to(session_dir)

            try:
                stat = file_path.stat()
                files.append(FileInfo(
                    path=str(relative_path),
                    size=stat.st_size,
                    modified=stat.st_mtime,
                    is_directory=False
                ))
            except Exception:
                continue

    return {"files": files, "session_id": session_id}


@router.get("/{session_id}/content")
async def get_file_content(
    session_id: str,
    path: str = Query(..., description="Relative file path")
):
    """Get file content as text."""
    session_dir = get_session_directory(session_id)
    file_path = session_dir / path

    # Security: Ensure path is within session directory
    try:
        file_path = file_path.resolve()
        session_dir = session_dir.resolve()
        if not str(file_path).startswith(str(session_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid path")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    try:
        content = file_path.read_text()
        return FileContentResponse(
            path=path,
            content=content,
            size=file_path.stat().st_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@router.get("/{session_id}/download")
async def download_file(
    session_id: str,
    path: str = Query(..., description="Relative file path")
):
    """Download a file."""
    session_dir = get_session_directory(session_id)
    file_path = session_dir / path

    # Security check
    try:
        file_path = file_path.resolve()
        session_dir = session_dir.resolve()
        if not str(file_path).startswith(str(session_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid path")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream"
    )
