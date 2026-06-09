from app.graph.state import AgentState


class SupervisorAgent:
    """路由决策 Agent，决定将请求分发给 RAG、Search 还是 Summarizer。"""

    def run(self, state: AgentState) -> AgentState:
        # TODO: 阶段三实现 — 用 LLM 解析 query 并设置 next_agent
        state["next_agent"] = "rag"
        state["agent_path"].append("supervisor")
        return state
