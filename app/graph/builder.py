import logging
from functools import lru_cache
from typing import AsyncGenerator

from langgraph.graph import StateGraph, END

from app.graph.state import AgentState
from app.agents.supervisor import supervisor_node
from app.agents.rag_agent import rag_node
from app.agents.search_agent import search_node
from app.agents.summarizer_agent import summarizer_node

logger = logging.getLogger(__name__)

_PROGRESS_MESSAGES = {
    "rag": "本地文档检索完成",
    "search": "网络搜索完成",
    "supervisor": "路由决策完成",
}


def _route(state: AgentState) -> str:
    decision = state.get("next_agent", "FINISH")
    mapping = {"RAG": "rag", "SEARCH": "search", "SUMMARIZER": "summarizer", "FINISH": END}
    return mapping.get(decision, END)


def _build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("rag", rag_node)
    graph.add_node("search", search_node)
    graph.add_node("summarizer", summarizer_node)

    graph.set_entry_point("supervisor")

    graph.add_conditional_edges(
        "supervisor",
        _route,
        {"rag": "rag", "search": "search", "summarizer": "summarizer", END: END},
    )

    graph.add_edge("rag", "supervisor")
    graph.add_edge("search", "supervisor")
    graph.add_edge("summarizer", "supervisor")

    return graph.compile()


@lru_cache(maxsize=1)
def get_compiled_graph():
    logger.info("编译 LangGraph StateGraph（单例）")
    return _build_graph()


def _build_initial_state(query: str, session_id: str, use_search: bool, history: list) -> AgentState:
    return {
        "messages": [],
        "query": query,
        "session_id": session_id,
        "use_search": use_search,
        "rag_results": "",
        "search_results": "",
        "final_answer": "",
        "sources": [],
        "agent_path": [],
        "next_agent": "",
        "history": history,
    }


async def run_graph(query: str, session_id: str, use_search: bool = False) -> dict:
    from app.storage.session_store import get_session_store

    graph = get_compiled_graph()
    store = get_session_store()
    history = store.get_history(session_id)

    initial_state = _build_initial_state(query, session_id, use_search, history)

    logger.info(f"run_graph 开始，query='{query[:50]}'，use_search={use_search}，history_turns={len(history) // 2}")
    final_state = await graph.ainvoke(initial_state)
    logger.info(f"run_graph 完成，agent_path={final_state.get('agent_path')}")

    store.save_turn(
        session_id=session_id,
        query=query,
        answer=final_state.get("final_answer", ""),
        agent_path=final_state.get("agent_path", []),
        sources=final_state.get("sources", []),
    )

    return final_state


async def stream_graph(
    query: str, session_id: str, use_search: bool = False
) -> AsyncGenerator[dict, None]:
    from app.storage.session_store import get_session_store

    graph = get_compiled_graph()
    store = get_session_store()
    history = store.get_history(session_id)

    initial_state = _build_initial_state(query, session_id, use_search, history)

    logger.info(f"stream_graph 开始，query='{query[:50]}'，use_search={use_search}")

    final_answer_parts: list[str] = []
    final_sources: list[str] = []
    final_agent_path: list[str] = []

    try:
        async for event in graph.astream_events(initial_state, version="v2"):
            event_type: str = event.get("event", "")
            event_name: str = event.get("name", "")
            metadata: dict = event.get("metadata", {})
            langgraph_node: str = metadata.get("langgraph_node", "")

            # LLM token 流：只捕获来自 summarizer 节点的 token
            if event_type == "on_chat_model_stream" and langgraph_node == "summarizer":
                chunk = event.get("data", {}).get("chunk")
                if chunk is not None:
                    content = getattr(chunk, "content", "") or ""
                    if content:
                        final_answer_parts.append(content)
                        yield {"type": "token", "content": content}

            # 节点完成：捕获进度事件 + 收集最终状态数据
            elif event_type == "on_chain_end":
                output = event.get("data", {}).get("output", {})

                # 只处理顶层节点（name == langgraph_node 时是节点自身完成，而非其内部子链）
                if event_name in _PROGRESS_MESSAGES and event_name == langgraph_node:
                    yield {
                        "type": "progress",
                        "node": event_name,
                        "message": _PROGRESS_MESSAGES[event_name],
                    }

                # 从节点输出里提取 sources / agent_path
                if isinstance(output, dict):
                    if "sources" in output:
                        final_sources = output["sources"]
                    if "agent_path" in output:
                        final_agent_path = output["agent_path"]

        # 流结束后持久化本轮对话
        final_answer = "".join(final_answer_parts)
        store.save_turn(
            session_id=session_id,
            query=query,
            answer=final_answer,
            agent_path=final_agent_path,
            sources=final_sources,
        )
        logger.info(f"stream_graph 完成，agent_path={final_agent_path}")

        yield {"type": "done", "agent_path": final_agent_path, "sources": final_sources}

    except Exception as e:
        logger.error(f"stream_graph 异常: {e}", exc_info=True)
        yield {"type": "error", "message": str(e)}
