import json
import logging
import traceback
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.request import ChatRequest
from app.models.response import ChatResponse
from app.graph.builder import run_graph, stream_graph

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid.uuid4())
    logger.info(f"收到聊天请求，session_id={session_id}，query='{request.query[:50]}'")

    try:
        final_state = await run_graph(
            query=request.query,
            session_id=session_id,
            use_search=request.use_search,
        )
        return ChatResponse(
            answer=final_state["final_answer"],
            sources=final_state["sources"],
            agent_path=final_state["agent_path"],
            session_id=session_id,
        )
    except Exception as e:
        logger.error(f"图执行异常: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"图执行失败: {e}")


@router.post("/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    session_id = request.session_id or str(uuid.uuid4())
    logger.info(f"收到流式聊天请求，session_id={session_id}，query='{request.query[:50]}'")

    async def event_generator():
        try:
            async for event_dict in stream_graph(
                query=request.query,
                session_id=session_id,
                use_search=request.use_search,
            ):
                yield f"data: {json.dumps(event_dict, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"SSE 生成器异常: {e}\n{traceback.format_exc()}")
            error_payload = json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False)
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
