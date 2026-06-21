"""API 集成测试脚本"""
import urllib.request
import json
import sys

def test(label, query, use_search, session_id):
    body = json.dumps(
        {"query": query, "session_id": session_id, "use_search": use_search},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/chat/",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.loads(r.read().decode("utf-8"))
    print(f"=== {label} ===")
    print("agent_path:", data["agent_path"])
    print("sources   :", data["sources"])
    print("answer    :", data["answer"][:300])
    print("session_id:", data["session_id"])
    print()
    return data


if __name__ == "__main__":
    r1 = test("场景一：文档内问题", "什么是机器学习？", False, "test-001")
    r2 = test("场景二：搜索场景", "今天北京天气怎么样？", True, "test-002")

    print("=== 验证 ===")
    assert r1["agent_path"] == ["rag_agent", "summarizer_agent"], f"场景一路径错误: {r1['agent_path']}"
    print("[PASS] 场景一 agent_path 正确")
    assert "search_agent" in r2["agent_path"], f"场景二缺少 search_agent: {r2['agent_path']}"
    print("[PASS] 场景二 agent_path 包含 search_agent")
    print("\nAPI 集成测试通过")
