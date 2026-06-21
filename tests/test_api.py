"""
API 路由基础测试
- health / root：无外部依赖，必须通过
- 文档上传校验：测试 400 / 413，不调用 LLM 或 ChromaDB
- 文档列表分页：只检查响应结构，不假设数据条数
- 聊天接口：需要 OPENAI_API_KEY，无 Key 时自动 skip
"""

import os
from io import BytesIO

import pytest
from fastapi.testclient import TestClient


# ─── 基础接口 ────────────────────────────────────────────────

def test_health(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_root(client: TestClient):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"
    assert "name" in data and "version" in data


# ─── 文档接口 ────────────────────────────────────────────────

def test_upload_invalid_extension(client: TestClient):
    """非法扩展名 (.docx) 应返回 400"""
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("report.docx", BytesIO(b"fake content"), "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert "不支持" in resp.json()["detail"]


def test_upload_no_extension(client: TestClient):
    """无扩展名文件应返回 400"""
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("noext", BytesIO(b"content"), "application/octet-stream")},
    )
    assert resp.status_code == 400


def test_upload_size_limit(client: TestClient, monkeypatch):
    """超过大小限制应返回 413"""
    import app.api.routes.documents as doc_routes
    from app.config import Settings

    # 用 model_construct 构建一个跳过验证的 Settings 实例，MAX_UPLOAD_SIZE_MB=0
    tiny = Settings.model_construct(
        MAX_UPLOAD_SIZE_MB=0,
        UPLOAD_DIR="./data/uploads",
        EMBEDDING_MODEL="BAAI/bge-small-zh-v1.5",
        CHUNK_SIZE=1000,
        CHUNK_OVERLAP=200,
        RETRIEVER_TOP_K=5,
        RETRIEVER_SCORE_THRESHOLD=0.5,
        SESSION_DB_PATH="./data/sessions.db",
        SESSION_HISTORY_LIMIT=3,
    )
    # 替换 documents 路由模块里引用的 get_settings，绕过 lru_cache
    monkeypatch.setattr(doc_routes, "get_settings", lambda: tiny)

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("tiny.txt", BytesIO(b"hello"), "text/plain")},
    )
    assert resp.status_code == 413


def test_list_documents_structure(client: TestClient):
    """/list 应返回分页结构，与数据库中实际文档数无关"""
    resp = client.get("/api/v1/documents/list?page=1&page_size=5")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) >= {"total", "page", "page_size", "items"}
    assert isinstance(data["items"], list)
    assert data["page"] == 1
    assert data["page_size"] == 5


def test_list_documents_invalid_page(client: TestClient):
    """page=0 应触发 FastAPI 参数校验（ge=1）"""
    resp = client.get("/api/v1/documents/list?page=0")
    assert resp.status_code == 422


# ─── 聊天接口（需要 OPENAI_API_KEY）────────────────────────

@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)
def test_chat_basic(client: TestClient):
    resp = client.post(
        "/api/v1/chat/",
        json={"query": "你好", "session_id": "pytest-session", "use_search": False},
        timeout=60,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data and data["answer"]
    assert "agent_path" in data and len(data["agent_path"]) > 0
