import uuid
from fastapi import APIRouter
from app.models.request import ChatRequest
from app.models.response import ChatResponse

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid.uuid4())

    # TODO: 阶段三实现 — 调用 build_graph() 并 invoke AgentState
    # graph = build_graph()
    # result = await graph.ainvoke({
    #     "query": request.query,
    #     "session_id": session_id,
    #     "use_search": request.use_search,
    #     "messages": [],
    #     "rag_results": "",
    #     "search_results": "",
    #     "final_answer": "",
    #     "sources": [],
    #     "agent_path": [],
    #     "next_agent": "",
    # })
    # return ChatResponse(
    #     answer=result["final_answer"],
    #     sources=result["sources"],
    #     agent_path=result["agent_path"],
    #     session_id=session_id,
    # )

    return ChatResponse(
        answer="Agent graph not yet implemented",
        sources=[],
        agent_path=[],
        session_id=session_id,
    )
