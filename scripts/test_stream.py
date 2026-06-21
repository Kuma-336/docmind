"""
流式输出 + 会话历史验证脚本
用法：python scripts/test_stream.py
需要先启动服务：uvicorn app.main:app --reload --port 8000
"""

import asyncio
import json
import uuid
import sys

try:
    import httpx
except ImportError:
    print("请先安装 httpx：pip install httpx")
    sys.exit(1)

BASE_URL = "http://localhost:8000"
SESSION_ID = f"test-stream-{uuid.uuid4().hex[:8]}"
FIRST_QUERY = "什么是机器学习？"
SECOND_QUERY = "刚才说的内容能再详细一点吗？"


async def stream_chat(client: httpx.AsyncClient, query: str, session_id: str) -> tuple[str, list, list]:
    """发送流式请求，实时打印 token，返回 (完整答案, agent_path, sources)"""
    payload = {"query": query, "session_id": session_id, "use_search": False}
    print(f"\n{'='*60}")
    print(f"[query]  {query}")
    print(f"[session] {session_id}")
    print(f"{'='*60}")

    full_answer_parts: list[str] = []
    agent_path: list = []
    sources: list = []
    event_count = 0

    async with client.stream(
        "POST",
        f"{BASE_URL}/api/v1/chat/stream",
        json=payload,
        timeout=120.0,
    ) as response:
        if response.status_code != 200:
            body = await response.aread()
            print(f"[ERROR] HTTP {response.status_code}: {body.decode()}")
            return "", [], []

        print("[streaming tokens] ", end="", flush=True)

        async for raw_line in response.aiter_lines():
            if not raw_line.startswith("data:"):
                continue
            json_str = raw_line[len("data:"):].strip()
            if not json_str:
                continue

            try:
                event = json.loads(json_str)
            except json.JSONDecodeError:
                continue

            event_count += 1
            event_type = event.get("type", "")

            if event_type == "token":
                content = event.get("content", "")
                full_answer_parts.append(content)
                print(content, end="", flush=True)

            elif event_type == "progress":
                node = event.get("node", "")
                message = event.get("message", "")
                print(f"\n[progress] {node}: {message}", flush=True)
                print("[streaming tokens] ", end="", flush=True)

            elif event_type == "done":
                agent_path = event.get("agent_path", [])
                sources = event.get("sources", [])

            elif event_type == "error":
                print(f"\n[ERROR] {event.get('message')}", flush=True)

    full_answer = "".join(full_answer_parts)
    print(f"\n\n[完整答案]\n{full_answer}")
    print(f"\n[agent_path] {agent_path}")
    print(f"[sources]    {sources}")
    print(f"[事件总数]   {event_count}")
    return full_answer, agent_path, sources


async def main():
    async with httpx.AsyncClient() as client:
        # 健康检查
        try:
            resp = await client.get(f"{BASE_URL}/health", timeout=5.0)
            resp.raise_for_status()
            print(f"[健康检查] OK - {resp.json()}")
        except Exception as e:
            print(f"[健康检查失败] 请确认服务已启动：uvicorn app.main:app --reload --port 8000")
            print(f"  错误: {e}")
            return

        # --- 第一轮对话 ---
        print("\n" + "="*60)
        print("第一轮对话")
        answer1, path1, src1 = await stream_chat(client, FIRST_QUERY, SESSION_ID)

        # --- 第二轮对话（同一 session_id，验证历史上下文）---
        print("\n" + "="*60)
        print("第二轮对话（验证历史上下文是否生效）")
        answer2, path2, src2 = await stream_chat(client, SECOND_QUERY, SESSION_ID)

        # 汇总
        print("\n" + "="*60)
        print("两轮对话汇总")
        print(f"\n[Round 1] Q: {FIRST_QUERY}")
        print(f"          A: {answer1[:200]}{'...' if len(answer1) > 200 else ''}")
        print(f"\n[Round 2] Q: {SECOND_QUERY}")
        print(f"          A: {answer2[:200]}{'...' if len(answer2) > 200 else ''}")

        if answer2:
            overlap_hint = any(
                kw in answer2
                for kw in ["上文", "前面", "刚才", "之前", "上面", "提到", "机器学习"]
            )
            hint_result = "YES (含上下文关键词)" if overlap_hint else "请人工对比两轮答案"
            print(f"\n[上下文验证] {hint_result}")

        print("\n流式 + 会话历史验证完成")


if __name__ == "__main__":
    asyncio.run(main())
