import logging
import os

from app.graph.state import AgentState

logger = logging.getLogger(__name__)


async def search_node(state: AgentState) -> dict:
    query = state["query"]
    logger.info(f"search_node 开始，query='{query[:50]}'")

    tavily_key = os.environ.get("TAVILY_API_KEY", "").strip()

    try:
        if tavily_key:
            from langchain_community.tools.tavily_search import TavilySearchResults
            tool = TavilySearchResults(max_results=5)
            logger.info("使用 TavilySearchResults 进行网络搜索")
            raw = tool.invoke(query)
            if isinstance(raw, list):
                parts = []
                for item in raw:
                    if isinstance(item, dict):
                        title = item.get("title", "")
                        content = item.get("content", "")
                        url = item.get("url", "")
                        parts.append(f"标题: {title}\n内容: {content}\n链接: {url}")
                    else:
                        parts.append(str(item))
                search_results = "\n---\n".join(parts)
            else:
                search_results = str(raw)
        else:
            from langchain_community.tools import DuckDuckGoSearchRun
            logger.warning(
                "未检测到 TAVILY_API_KEY，降级使用 DuckDuckGoSearchRun（免费方案，无需 API Key）"
            )
            tool = DuckDuckGoSearchRun()
            search_results = tool.invoke(query)

        logger.info(f"search_node 完成，结果长度={len(search_results)}")
    except Exception as e:
        logger.error(f"search_node 搜索失败: {e}", exc_info=True)
        search_results = f"网络搜索暂时不可用：{e}"

    return {
        "search_results": search_results,
        "agent_path": state["agent_path"] + ["search_agent"],
    }
