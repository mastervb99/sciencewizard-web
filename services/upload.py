"""
Velvet Research - File Upload Service
"""
import os
import uuid
import json
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import List
from fastapi import UploadFile, HTTPException

from config import settings


async def save_uploaded_files(
    user_id: str,
    files: List[UploadFile]
) -> tuple[str, str, List[dict]]:
    """
    Save uploaded files and return upload metadata.

    Returns:
        (upload_id, upload_path, file_list)
    """
    upload_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    upload_path = Path(settings.upload_dir) / user_id / f"{timestamp}_{upload_id}"

    # Create directory
    upload_path.mkdir(parents=True, exist_ok=True)

    file_list = []
    total_size = 0

    for file in files:
        # Validate extension
        ext = Path(file.filename).suffix.lower()
        if ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {ext} not allowed. Allowed: {settings.allowed_extensions}"
            )

        # Read content
        content = await file.read()
        file_size = len(content)
        total_size += file_size

        # Check size limits
        if file_size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} exceeds {settings.max_file_size_mb}MB limit"
            )

        if total_size > settings.max_upload_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"Total upload exceeds {settings.max_upload_size_mb}MB limit"
            )

        # Save file
        file_path = upload_path / file.filename
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        file_list.append({
            "name": file.filename,
            "size": file_size,
            "type": ext,
            "path": str(file_path)
        })

    return upload_id, str(upload_path), file_list


def get_upload_files(upload_path: str) -> List[dict]:
    """Get list of files in upload directory."""
    path = Path(upload_path)
    if not path.exists():
        return []

    files = []
    for f in path.iterdir():
        if f.is_file():
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "type": f.suffix.lower(),
                "path": str(f)
            })
    return files


def cleanup_upload(upload_path: str):
    """Remove upload directory and files."""
    import shutil
    path = Path(upload_path)
    if path.exists():
        shutil.rmtree(path)
