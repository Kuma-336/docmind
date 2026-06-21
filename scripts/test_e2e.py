"""
DocMind 端到端测试脚本
用法：python scripts/test_e2e.py [base_url]
默认 base_url: http://localhost:8000
依赖：pip install httpx
"""

import asyncio
import json
import os
import sys
import time
import uuid
from io import BytesIO
from pathlib import Path

try:
    import httpx
except ImportError:
    print("请先安装 httpx：pip install httpx")
    sys.exit(1)

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"
SESSION_ID = f"e2e-{uuid.uuid4().hex[:8]}"

PASS = "[PASS]"
FAIL = "[FAIL]"

results: list[tuple[str, bool, str]] = []


def record(step: str, ok: bool, detail: str = ""):
    tag = PASS if ok else FAIL
    msg = f"{tag} {step}" + (f" — {detail}" if detail else "")
    print(msg)
    results.append((step, ok, detail))


TEST_DOC_CONTENT = """\
机器学习（Machine Learning）是人工智能的核心分支，使计算机能够从数据中自动学习，
而无需被明确编程每一个规则。主要分为三大类：

1. 监督学习（Supervised Learning）：使用带标签的数据训练模型，典型算法包括线性回归、
   决策树、支持向量机和神经网络。应用场景：图像分类、垃圾邮件过滤、房价预测。

2. 无监督学习（Unsupervised Learning）：在无标签数据中发现隐藏结构，典型算法包括
   K-Means 聚类、主成分分析（PCA）、自编码器。应用场景：用户分群、异常检测。

3. 强化学习（Reinforcement Learning）：Agent 通过与环境交互获取奖励信号来学习策略，
   典型算法包括 Q-Learning、PPO。应用场景：游戏 AI、机器人控制、自动驾驶。

深度学习（Deep Learning）是机器学习的子集，利用多层神经网络（深层架构）自动提取
特征，在图像、语音、自然语言处理任务上取得突破性进展。代表模型：CNN、RNN、Transformer。
"""


async def run():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:

        # ── Step 1: 健康检查 ─────────────────────────────────
        step = "Step 1: GET /health"
        try:
            resp = await client.get("/health")
            ok = resp.status_code == 200 and resp.json().get("status") == "ok"
            record(step, ok, f"HTTP {resp.status_code}")
        except Exception as e:
            record(step, False, str(e))
            print("\n服务未启动，终止测试。请先运行：uvicorn app.main:app --port 8000")
            return

        # ── Step 2: 上传测试文档 ─────────────────────────────
        step = "Step 2: POST /api/v1/documents/upload"
        uploaded_file_id = None
        try:
            resp = await client.post(
                "/api/v1/documents/upload",
                files={"file": ("e2e_test_doc.txt", BytesIO(TEST_DOC_CONTENT.encode()), "text/plain")},
            )
            ok = resp.status_code == 200
            if ok:
                uploaded_file_id = resp.json().get("file_id")
            record(step, ok, f"file_id={uploaded_file_id}")
        except Exception as e:
            record(step, False, str(e))
            uploaded_file_id = None

        # ── Step 3: 等待向量化完成，GET /list 确认文档已列出 ──
        step = "Step 3: GET /api/v1/documents/list (confirm upload)"
        await asyncio.sleep(2)
        try:
            resp = await client.get("/api/v1/documents/list?page=1&page_size=20")
            data = resp.json()
            ok = (
                resp.status_code == 200
                and "total" in data
                and "items" in data
                and isinstance(data["items"], list)
            )
            found = any(
                item.get("file_id") == uploaded_file_id
                for item in data.get("items", [])
            ) if uploaded_file_id else False
            record(step, ok and found, f"total={data.get('total')}, found_upload={found}")
        except Exception as e:
            record(step, False, str(e))

        # ── Step 4: 同步问答，断言 agent_path 含 rag_agent ──
        step = "Step 4: POST /api/v1/chat/ (sync, rag_agent in path)"
        try:
            resp = await client.post(
                "/api/v1/chat/",
                json={"query": "机器学习有哪些主要类型？", "session_id": SESSION_ID, "use_search": False},
            )
            ok = resp.status_code == 200
            if ok:
                data = resp.json()
                has_answer = bool(data.get("answer"))
                has_rag = "rag_agent" in data.get("agent_path", [])
                ok = has_answer and has_rag
                record(step, ok, f"answer_len={len(data.get('answer',''))}, agent_path={data.get('agent_path')}")
            else:
                record(step, False, f"HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            record(step, False, str(e))

        # ── Step 5: 流式问答，至少收到 token + done 事件 ────
        step = "Step 5: POST /api/v1/chat/stream (SSE token+done)"
        try:
            token_count = 0
            got_done = False
            async with client.stream(
                "POST",
                "/api/v1/chat/stream",
                json={"query": "监督学习的典型算法有哪些？", "session_id": SESSION_ID, "use_search": False},
            ) as resp:
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    try:
                        evt = json.loads(line[5:].strip())
                    except Exception:
                        continue
                    if evt.get("type") == "token":
                        token_count += 1
                    elif evt.get("type") == "done":
                        got_done = True
            ok = token_count > 0 and got_done
            record(step, ok, f"tokens={token_count}, got_done={got_done}")
        except Exception as e:
            record(step, False, str(e))

        # ── Step 6: 两轮对话，确认第二轮不报错 ────────────────
        step = "Step 6: Two-turn session history (no error)"
        sid2 = f"e2e-multi-{uuid.uuid4().hex[:6]}"
        try:
            r1 = await client.post(
                "/api/v1/chat/",
                json={"query": "什么是强化学习？", "session_id": sid2, "use_search": False},
            )
            r2 = await client.post(
                "/api/v1/chat/",
                json={"query": "再详细介绍一下", "session_id": sid2, "use_search": False},
            )
            ok = r1.status_code == 200 and r2.status_code == 200
            ans1 = r1.json().get("answer", "")[:60] if r1.status_code == 200 else "ERR"
            ans2 = r2.json().get("answer", "")[:60] if r2.status_code == 200 else "ERR"
            record(step, ok, f"round1='{ans1}...' round2='{ans2}...'")
        except Exception as e:
            record(step, False, str(e))

        # ── Step 7: 删除测试文档 ─────────────────────────────
        step = "Step 7: DELETE /api/v1/documents/{file_id}"
        if uploaded_file_id:
            try:
                resp = await client.delete(f"/api/v1/documents/{uploaded_file_id}")
                ok = resp.status_code == 200 and resp.json().get("status") == "deleted"
                record(step, ok, f"HTTP {resp.status_code}")
            except Exception as e:
                record(step, False, str(e))
        else:
            record(step, False, "跳过：上传步骤失败，无 file_id")

    # ── 汇总 ────────────────────────────────────────────────
    print("\n" + "=" * 50)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    print(f"结果：{passed} PASS / {failed} FAIL / {len(results)} 总计")
    if failed:
        print("失败步骤：")
        for name, ok, detail in results:
            if not ok:
                print(f"  - {name}: {detail}")
    print("=" * 50)
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run())
    sys.exit(0 if success else 1)
