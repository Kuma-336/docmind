import uuid
import os
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import get_settings
from app.models.response import UploadResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    settings = get_settings()
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    suffix = Path(file.filename).suffix
    dest = upload_dir / f"{file_id}{suffix}"

    content = await file.read()
    dest.write_bytes(content)

    # TODO: 阶段二实现 — 调用 RAG loader/splitter/embedder 进行向量化并存入 ChromaDB
    # chunk_count = await process_document(dest, file_id)

    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        chunk_count=0,
        status="uploaded",
    )


@router.get("/list")
async def list_documents() -> List[dict]:
    settings = get_settings()
    upload_dir = Path(settings.UPLOAD_DIR)
    if not upload_dir.exists():
        return []

    files = []
    for f in upload_dir.iterdir():
        if f.is_file():
            files.append({"file_id": f.stem, "filename": f.name, "size": f.stat().st_size})
    return files


@router.delete("/{file_id}")
async def delete_document(file_id: str) -> dict:
    settings = get_settings()
    upload_dir = Path(settings.UPLOAD_DIR)

    matches = list(upload_dir.glob(f"{file_id}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail="File not found")

    for f in matches:
        f.unlink()

    return {"file_id": file_id, "status": "deleted"}
