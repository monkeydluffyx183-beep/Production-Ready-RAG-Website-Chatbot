from __future__ import annotations
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.models import ChatRequest, ChatResponse
from app.services.rag import answer_question, stream_answer, build_context
from app.services.embeddings import get_collection

router = APIRouter(prefix="/chat", tags=["chat"])


def _require_session(session_id: str):
    # Ensure collection exists
    try:
        store = get_collection(session_id)
        if store._collection.count() == 0:
            raise HTTPException(400, "No content indexed for this session. Ingest a URL first.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Session not found: {e}")


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    _require_session(req.session_id)
    answer, sources = answer_question(req.session_id, req.question)
    return ChatResponse(
        answer=answer,
        sources=[
            {"url": s["url"], "title": s["title"],
             "snippet": s["snippet"], "score": s["score"]}
            for s in sources
        ],
    )


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    _require_session(req.session_id)

    # First, send sources as an SSE event, then stream tokens
    async def event_gen():
        _, sources = build_context(req.session_id, req.question)
        yield {"event": "sources", "data": json.dumps(sources)}
        async for token in stream_answer(req.session_id, req.question):
            yield {"event": "token", "data": token}
        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_gen())
