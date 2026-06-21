import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.config import get_settings
from app.models.response import UploadResponse
from app.rag.loader import DocumentLoader
from app.rag.retriever import get_vector_store
from app.rag.splitter import TextSplitter

logger = logging.getLogger(__name__)
router = APIRouter()

_ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    settings = get_settings()

    # 格式校验
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式：{suffix or '（无扩展名）'}，仅支持 .pdf、.txt、.md",
        )

    content = await file.read()

    # 大小校验
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小（{len(content) / 1024 / 1024:.1f}MB）超出限制（最大 {settings.MAX_UPLOAD_SIZE_MB}MB）",
        )

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    saved_name = f"{file_id}_{file.filename}"
    dest = upload_dir / saved_name
    dest.write_bytes(content)
    logger.info(f"文件保存至: {dest}")

    try:
        documents = DocumentLoader().load(str(dest))
        chunks = TextSplitter().split(documents)
        chunk_count = get_vector_store().add_documents(chunks, file_id)
    except Exception as e:
        logger.error(f"处理文件失败，file_id={file_id}: {e}", exc_info=True)
        if dest.exists():
            dest.unlink()
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")

    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        chunk_count=chunk_count,
        status="success",
    )


@router.get("/list")
async def list_documents(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
) -> dict:
    settings = get_settings()
    upload_dir = Path(settings.UPLOAD_DIR)
    if not upload_dir.exists():
        return {"total": 0, "page": page, "page_size": page_size, "items": []}

    files: List[dict] = []
    for f in upload_dir.iterdir():
        if not f.is_file():
            continue
        parts = f.name.split("_", 1)
        if len(parts) == 2:
            file_id, original_name = parts
        else:
            file_id = f.stem
            original_name = f.name
        stat = f.stat()
        files.append(
            {
                "file_id": file_id,
                "filename": original_name,
                "size": stat.st_size,
                "uploaded_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }
        )

    # 按上传时间倒序（最新在前）
    files.sort(key=lambda x: x["uploaded_at"], reverse=True)

    total = len(files)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": files[start:end],
    }


@router.delete("/{file_id}")
async def delete_document(file_id: str) -> dict:
    settings = get_settings()
    upload_dir = Path(settings.UPLOAD_DIR)

    matches = list(upload_dir.glob(f"{file_id}_*"))
    if not matches:
        raise HTTPException(status_code=404, detail="File not found")

    for f in matches:
        f.unlink()
        logger.info(f"已删除文件: {f.name}")

    get_vector_store().delete_by_file_id(file_id)

    return {"file_id": file_id, "status": "deleted"}
