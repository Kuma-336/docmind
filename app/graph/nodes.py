from app.graph.state import AgentState


def supervisor_node(state: AgentState) -> AgentState:
    # TODO: 阶段三实现 — 调用 Supervisor Agent 决策路由
    return state


def rag_node(state: AgentState) -> AgentState:
    # TODO: 阶段二实现 — 调用 RAG Agent 检索文档
    return state


def search_node(state: AgentState) -> AgentState:
    # TODO: 阶段三实现 — 调用 Search Agent 进行网络搜索
    return state


def summarizer_node(state: AgentState) -> AgentState:
    # TODO: 阶段三实现 — 调用 Summarizer Agent 整合结果
    return state
