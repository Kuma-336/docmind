import logging

from app.graph.state import AgentState

logger = logging.getLogger(__name__)


async def supervisor_node(state: AgentState) -> dict:
    agent_path = state.get("agent_path", [])
    rag_results = state.get("rag_results", "")
    use_search = state.get("use_search", False)

    has_rag = "rag_agent" in agent_path
    has_search = "search_agent" in agent_path
    has_summarizer = "summarizer_agent" in agent_path

    if not has_rag:
        decision = "RAG"
        reason = "首次调用，先检索已上传文档"
    elif (
        has_rag
        and not has_search
        and use_search
        and "未在已上传文档中找到相关内容" in rag_results
    ):
        decision = "SEARCH"
        reason = "RAG 未找到相关内容且 use_search=True，启动网络搜索"
    elif (has_rag or has_search) and not has_summarizer:
        decision = "SUMMARIZER"
        reason = "已有检索结果，交由 Summarizer 整合生成最终回答"
    elif has_summarizer:
        decision = "FINISH"
        reason = "Summarizer 已完成，结束流程"
    else:
        decision = "SUMMARIZER"
        reason = "兜底路由到 Summarizer"

    logger.info(f"supervisor_node 路由决策: {decision}（原因: {reason}，当前 agent_path={agent_path}）")

    return {
        "next_agent": decision,
        "agent_path": agent_path,
    }
