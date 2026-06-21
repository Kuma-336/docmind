"""
验证脚本：测试 LangGraph 多 Agent 编排（阶段三）
运行方式：在项目根目录执行 python scripts/test_graph.py
"""
import asyncio
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s")

from app.rag.loader import DocumentLoader
from app.rag.splitter import TextSplitter
from app.rag.retriever import get_vector_store
from app.graph.builder import run_graph

TEST_FILE = Path("data/uploads/test_doc.txt")

AI_CONTENT = """\
人工智能（AI）是计算机科学的一个分支，旨在创建能够模拟人类智能行为的机器系统。\
人工智能的目标是让机器能够执行通常需要人类智能的任务，例如视觉感知、语音识别、自然语言理解和决策制定。\
自20世纪50年代图灵提出"机器能否思考"的问题以来，人工智能经历了多次发展浪潮，如今已渗透到医疗、教育、金融等各个领域。

机器学习是人工智能最重要的子领域之一，它使计算机能够在没有被明确编程的情况下，通过数据训练自动改善性能。\
机器学习算法通过分析大量训练样本来识别数据中的规律和模式，并基于这些模式对新数据做出预测或决策。\
常见的机器学习方法包括监督学习、无监督学习和强化学习，每种方法都有其特定的适用场景。

深度学习是机器学习的一个特殊分支，以多层人工神经网络为核心，能够自动从原始数据中提取层次化特征。\
深度学习在图像识别、语音识别、自然语言生成等领域取得了突破性进展，被广泛应用于自动驾驶、医学影像诊断、智能推荐等场景。\
卷积神经网络（CNN）和Transformer架构是深度学习中最具代表性的两种模型结构。

自然语言处理（NLP）是人工智能与语言学交叉的研究领域，专注于让计算机理解、解析和生成人类语言。\
NLP技术广泛应用于机器翻译、情感分析、文本摘要、智能问答等场景。近年来，以GPT和BERT为代表的大型语言模型（LLM）\
大幅提升了NLP系统的能力，使机器在语言理解和对话生成方面达到接近人类的水平。

计算机视觉是人工智能领域中专注于使机器"看懂"图像和视频的分支学科。计算机视觉系统可以识别物体、检测人脸、\
分析医学影像，甚至理解视频中的动态场景。在自动驾驶领域，计算机视觉与激光雷达数据融合，帮助车辆实时感知周围环境。\
深度学习模型尤其是卷积神经网络的发展，极大地推动了计算机视觉技术的实用化进程。
"""


def ensure_test_data():
    TEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEST_FILE.write_text(AI_CONTENT, encoding="utf-8")
    print(f"[准备] 已写入测试文件: {TEST_FILE}")

    loader = DocumentLoader()
    documents = loader.load(str(TEST_FILE))
    splitter = TextSplitter()
    chunks = splitter.split(documents)

    vs = get_vector_store()
    count = vs.add_documents(chunks, "test-graph-001")
    print(f"[准备] 已写入向量库，共 {count} 个 chunk\n")


async def run_scenario(label: str, query: str, use_search: bool):
    print(f"{'='*60}")
    print(f"场景: {label}")
    print(f"Query: {query}")
    print(f"use_search: {use_search}")
    print("-" * 60)

    t0 = time.time()
    result = await run_graph(query=query, session_id=f"test-{label}", use_search=use_search)
    elapsed = time.time() - t0

    print(f"agent_path  : {result['agent_path']}")
    print(f"sources     : {result['sources']}")
    print(f"final_answer: {result['final_answer'][:300]}{'...' if len(result['final_answer']) > 300 else ''}")
    print(f"耗时        : {elapsed:.2f}s")
    print()
    return result


async def main():
    print("\n[步骤 1] 确保 ChromaDB 中有测试数据")
    ensure_test_data()

    print("[步骤 2] 场景测试\n")

    result1 = await run_scenario(
        label="文档内问题",
        query="什么是机器学习？",
        use_search=False,
    )

    result2 = await run_scenario(
        label="需要联网的问题",
        query="今天北京天气怎么样？明天会下雨吗？",
        use_search=True,
    )

    print("=" * 60)
    print("验证结论")
    print("-" * 60)

    path1 = result1["agent_path"]
    assert "rag_agent" in path1, "场景一应包含 rag_agent"
    assert "summarizer_agent" in path1, "场景一应包含 summarizer_agent"
    print(f"[PASS] 场景一 agent_path 正确: {path1}")

    path2 = result2["agent_path"]
    assert "rag_agent" in path2, "场景二应包含 rag_agent"
    assert "search_agent" in path2, "场景二应包含 search_agent（use_search=True 且文档无相关内容）"
    assert "summarizer_agent" in path2, "场景二应包含 summarizer_agent"
    print(f"[PASS] 场景二 agent_path 正确: {path2}")

    print("\nGraph 编排验证完成")


if __name__ == "__main__":
    asyncio.run(main())
