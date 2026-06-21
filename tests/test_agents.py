"""
Agent 节点单元测试
- supervisor_node：纯 Python 路由逻辑，无 LLM 调用，可完整测试
- summarizer_node / rag_node：需要 LLM / ChromaDB，仅在有 API Key 时运行
"""

import os
import pytest


def _base_state(**overrides) -> dict:
    state = {
        "messages": [],
        "query": "什么是机器学习？",
        "session_id": "test-session",
        "use_search": False,
        "rag_results": "",
        "search_results": "",
        "final_answer": "",
        "sources": [],
        "agent_path": [],
        "next_agent": "",
        "history": [],
    }
    state.update(overrides)
    return state


# ─── Supervisor 路由逻辑（无 LLM，必须通过）────────────────

@pytest.mark.asyncio
async def test_supervisor_first_call_routes_to_rag():
    """首次调用（agent_path 为空）应路由到 RAG"""
    from app.agents.supervisor import supervisor_node
    result = await supervisor_node(_base_state())
    assert result["next_agent"] == "RAG"


@pytest.mark.asyncio
async def test_supervisor_after_rag_routes_to_summarizer():
    """RAG 完成且无需搜索时，应路由到 SUMMARIZER"""
    from app.agents.supervisor import supervisor_node
    state = _base_state(
        agent_path=["rag_agent"],
        rag_results="找到了相关文档内容",
    )
    result = await supervisor_node(state)
    assert result["next_agent"] == "SUMMARIZER"


@pytest.mark.asyncio
async def test_supervisor_after_rag_miss_with_search_routes_to_search():
    """RAG 未找到内容且 use_search=True，应路由到 SEARCH"""
    from app.agents.supervisor import supervisor_node
    state = _base_state(
        agent_path=["rag_agent"],
        rag_results="未在已上传文档中找到相关内容。",
        use_search=True,
    )
    result = await supervisor_node(state)
    assert result["next_agent"] == "SEARCH"


@pytest.mark.asyncio
async def test_supervisor_after_summarizer_finishes():
    """Summarizer 完成后应返回 FINISH"""
    from app.agents.supervisor import supervisor_node
    state = _base_state(
        agent_path=["rag_agent", "summarizer_agent"],
        rag_results="一些内容",
        final_answer="已生成最终答案",
    )
    result = await supervisor_node(state)
    assert result["next_agent"] == "FINISH"


@pytest.mark.asyncio
async def test_supervisor_no_search_when_use_search_false():
    """use_search=False 时，即使 RAG 无结果也不应路由到 SEARCH"""
    from app.agents.supervisor import supervisor_node
    state = _base_state(
        agent_path=["rag_agent"],
        rag_results="未在已上传文档中找到相关内容。",
        use_search=False,
    )
    result = await supervisor_node(state)
    assert result["next_agent"] == "SUMMARIZER"


# ─── SessionStore（内置 sqlite3，无 LLM）────────────────────

@pytest.mark.asyncio
async def test_session_store_save_and_retrieve(tmp_path):
    """save_turn 写入后，get_history 能正确读回"""
    from app.storage.session_store import SessionStore
    db = SessionStore(db_path=str(tmp_path / "test_sessions.db"))

    db.save_turn("s1", "你好", "你好呀", ["rag_agent"], ["doc.txt"])
    db.save_turn("s1", "再问一个", "好的", ["rag_agent", "summarizer_agent"], [])

    history = db.get_history("s1", limit=10)
    assert len(history) == 4  # 2 轮 × 2 条（user + assistant）
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "你好"
    assert history[1]["role"] == "assistant"
    assert history[1]["sources"] == ["doc.txt"]


@pytest.mark.asyncio
async def test_session_store_limit(tmp_path):
    """get_history limit 参数正确截断"""
    from app.storage.session_store import SessionStore
    db = SessionStore(db_path=str(tmp_path / "test_sessions2.db"))

    for i in range(5):
        db.save_turn("s2", f"q{i}", f"a{i}", [], [])

    # limit=2 → 最多返回 2 轮 = 4 条消息
    history = db.get_history("s2", limit=2)
    assert len(history) == 4


# ─── Summarizer 历史注入（需要 OPENAI_API_KEY）──────────────

@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)
@pytest.mark.asyncio
async def test_summarizer_with_history():
    """有历史上下文时，summarizer_node 不报错并返回 final_answer"""
    from app.agents.summarizer_agent import summarizer_node
    state = _base_state(
        rag_results="机器学习是 AI 的核心技术之一。",
        history=[
            {"role": "user", "content": "什么是 AI？", "agent_path": [], "sources": [], "created_at": ""},
            {"role": "assistant", "content": "AI 是人工智能。", "agent_path": [], "sources": [], "created_at": ""},
        ],
    )
    result = await summarizer_node(state)
    assert result.get("final_answer")
    assert len(result["final_answer"]) > 0
