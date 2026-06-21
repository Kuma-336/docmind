from typing import Annotated, List
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    query: str
    session_id: str
    rag_results: str
    search_results: str
    final_answer: str
    sources: List[str]
    agent_path: List[str]
    next_agent: str
    use_search: bool
    history: List[dict]
