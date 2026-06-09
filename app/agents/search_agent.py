from app.graph.state import AgentState


class SearchAgent:
    """调用 Tavily 进行网络搜索并填入 search_results。"""

    def run(self, state: AgentState) -> AgentState:
        # TODO: 阶段三实现 — 集成 TavilySearchResults 工具
        state["search_results"] = ""
        state["agent_path"].append("search_agent")
        return state
