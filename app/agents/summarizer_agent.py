import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import get_settings
from app.graph.state import AgentState

logger = logging.getLogger(__name__)


def _get_llm() -> ChatOpenAI:
    settings = get_settings()
    kwargs = dict(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.7,
    )
    if settings.OPENAI_BASE_URL:
        kwargs["base_url"] = settings.OPENAI_BASE_URL
    return ChatOpenAI(**kwargs)


async def summarizer_node(state: AgentState) -> dict:
    query = state["query"]
    rag_results = state.get("rag_results", "")
    search_results = state.get("search_results", "")
    history = state.get("history", [])

    logger.info(f"summarizer_node 开始，query='{query[:50]}'")

    # 历史上下文：最多取最近 3 轮（6 条消息）
    history_block = ""
    if history:
        recent = history[-6:]
        lines = []
        for msg in recent:
            label = "用户" if msg["role"] == "user" else "助手"
            lines.append(f"{label}：{msg['content']}")
        history_block = "历史对话：\n" + "\n".join(lines) + "\n\n"

    context_parts = []
    if rag_results and "未在已上传文档中找到相关内容" not in rag_results:
        context_parts.append(f"【文档检索结果】\n{rag_results}")
    if search_results and "网络搜索暂时不可用" not in search_results:
        context_parts.append(f"【网络搜索结果】\n{search_results}")

    if context_parts:
        context_block = "\n\n".join(context_parts)
        user_content = (
            f"{history_block}"
            f"请根据以下参考信息回答用户的问题。\n\n"
            f"{context_block}\n\n"
            f"用户问题：{query}"
        )
    else:
        user_content = (
            f"{history_block}"
            f"用户问题：{query}\n\n"
            f"（文档检索和网络搜索均未找到相关内容，请如实告知用户。）"
        )

    system_content = (
        "你是一个专业的知识问答助手。请综合所有参考信息，用中文简洁清晰地回答用户问题。"
        "如果参考信息中没有相关内容，请诚实告知用户，不要编造信息。"
    )

    prompt_len = len(system_content) + len(user_content)
    logger.info(f"summarizer_node 构造 prompt 完成，总长度={prompt_len}")

    llm = _get_llm()
    messages = [SystemMessage(content=system_content), HumanMessage(content=user_content)]
    response = await llm.ainvoke(messages)
    final_answer = response.content

    logger.info(f"summarizer_node 完成，final_answer 长度={len(final_answer)}")

    return {
        "final_answer": final_answer,
        "agent_path": state["agent_path"] + ["summarizer_agent"],
    }
