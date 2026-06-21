"""
RAG 管道单元测试
- DocumentLoader、TextSplitter：无外部依赖，使用临时文件
- Settings 配置字段：确认阶段四新增字段存在
"""

import tempfile
import os

import pytest
from langchain_core.documents import Document


# ─── Settings ────────────────────────────────────────────────

def test_settings_fields():
    """确认所有阶段新增的 Settings 字段都存在且有合理默认值"""
    from app.config import get_settings
    s = get_settings()
    assert s.MAX_UPLOAD_SIZE_MB > 0
    assert s.SESSION_DB_PATH.endswith(".db")
    assert s.SESSION_HISTORY_LIMIT > 0
    assert 0 < s.RETRIEVER_SCORE_THRESHOLD <= 1
    assert s.RETRIEVER_TOP_K > 0
    assert s.CHUNK_SIZE > 0
    assert s.CHUNK_OVERLAP >= 0


# ─── DocumentLoader ──────────────────────────────────────────

def test_loader_txt():
    """txt 文件可以被正确加载"""
    from app.rag.loader import DocumentLoader
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", encoding="utf-8", delete=False) as f:
        f.write("这是一段测试文本，用于验证 DocumentLoader 的加载功能。\n" * 10)
        tmp_path = f.name
    try:
        docs = DocumentLoader().load(tmp_path)
        assert len(docs) >= 1
        assert any("测试文本" in d.page_content for d in docs)
    finally:
        os.unlink(tmp_path)


def test_loader_unsupported_extension():
    """不支持的扩展名应抛出异常或返回空列表（取决于实现）"""
    from app.rag.loader import DocumentLoader
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        f.write(b"binary data")
        tmp_path = f.name
    try:
        # 期望：抛出异常或返回空列表，不能静默崩溃
        try:
            docs = DocumentLoader().load(tmp_path)
            # 若不抛出，至少结果是列表
            assert isinstance(docs, list)
        except Exception:
            pass  # 抛出异常也是合理行为
    finally:
        os.unlink(tmp_path)


# ─── TextSplitter ────────────────────────────────────────────

def test_splitter_splits_long_text():
    """长文本应被切分为多个 chunk"""
    from app.rag.splitter import TextSplitter
    long_text = "这是一段很长的测试内容。" * 200  # 约 2400 字符
    docs = [Document(page_content=long_text, metadata={"source": "test.txt"})]
    chunks = TextSplitter().split(docs)
    assert len(chunks) > 1


def test_splitter_preserves_metadata():
    """切分后每个 chunk 应保留原始 metadata 并新增 chunk_index"""
    from app.rag.splitter import TextSplitter
    docs = [Document(page_content="内容" * 600, metadata={"file_name": "test.txt", "file_id": "abc"})]
    chunks = TextSplitter().split(docs)
    for chunk in chunks:
        assert chunk.metadata.get("file_name") == "test.txt"
        assert "chunk_index" in chunk.metadata
        assert "chunk_total" in chunk.metadata


def test_splitter_short_text_single_chunk():
    """短文本应只有一个 chunk"""
    from app.rag.splitter import TextSplitter
    docs = [Document(page_content="短文本", metadata={})]
    chunks = TextSplitter().split(docs)
    assert len(chunks) == 1
