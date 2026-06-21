import logging
from typing import List

from app.graph.state import AgentState
from app.rag.retriever import get_vector_store

logger = logging.getLogger(__name__)


async def rag_node(state: AgentState) -> dict:
    query = state["query"]
    logger.info(f"rag_node 开始检索，query='{query[:50]}'")

    results = get_vector_store().retrieve(query)

    if not results:
        logger.info("未检索到相关内容")
        return {
            "rag_results": "未在已上传文档中找到相关内容。",
            "sources": [],
            "agent_path": state["agent_path"] + ["rag_agent"],
        }

    parts: List[str] = []
    for doc in results:
        source = doc.metadata.get("file_name", "未知来源")
        parts.append(f"来源: {source}\n内容: {doc.page_content}")

    rag_results = "\n---\n".join(parts)

    sources = list(
        {doc.metadata.get("file_name", "") for doc in results if doc.metadata.get("file_name")}
    )

    logger.info(f"rag_node 完成，返回 {len(results)} 条结果，来源: {sources}")
    return {
        "rag_results": rag_results,
        "sources": sources,
        "agent_path": state["agent_path"] + ["rag_agent"],
    }
