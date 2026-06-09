from app.graph.state import AgentState


class RAGAgent:
    """从向量数据库检索相关文档片段并填入 rag_results。"""

    def run(self, state: AgentState) -> AgentState:
        # TODO: 阶段二实现 — 调用 retriever.py 检索相关 chunks
        state["rag_results"] = ""
        state["agent_path"].append("rag_agent")
        return state
