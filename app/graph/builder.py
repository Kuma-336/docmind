from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes import supervisor_node, rag_node, search_node, summarizer_node


def build_graph():
    # TODO: 阶段三实现完整 Agent 路由图
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("rag", rag_node)
    graph.add_node("search", search_node)
    graph.add_node("summarizer", summarizer_node)

    graph.set_entry_point("supervisor")
    graph.add_edge("supervisor", END)

    return graph.compile()
