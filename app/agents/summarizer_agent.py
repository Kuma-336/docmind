from app.graph.state import AgentState


class SummarizerAgent:
    """整合 RAG 与搜索结果，生成最终回答。"""

    def run(self, state: AgentState) -> AgentState:
        # TODO: 阶段三实现 — 用 LLM 生成 final_answer
        state["final_answer"] = ""
        state["agent_path"].append("summarizer_agent")
        return state
