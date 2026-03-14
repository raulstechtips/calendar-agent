"""Chat endpoint with SSE streaming."""

import json
import logging
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, ConfigDict, Field

from app.agents.calendar_agent import build_thread_id, get_agent

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(..., min_length=1, max_length=2000)
    thread_id: str | None = Field(None, max_length=200)


async def _stream_response(
    agent: CompiledStateGraph,  # type: ignore[type-arg]
    message: str,
    thread_id: str,
    user_id: str,
) -> AsyncGenerator[str, None]:
    """Stream agent response as SSE events."""
    try:
        async for chunk, _metadata in agent.astream(
            {
                "messages": [HumanMessage(content=message)],
                "user_id": user_id,
                "pending_confirmation": None,
            },
            config={"configurable": {"thread_id": thread_id}},
            stream_mode="messages",
        ):
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                event = {"type": "token", "content": chunk.content}
                yield f"data: {json.dumps(event)}\n\n"
    except Exception:
        logger.exception("Agent streaming error")
        error_event = {
            "type": "error",
            "content": "An error occurred processing your request.",
        }
        yield f"data: {json.dumps(error_event)}\n\n"

    done_event = {"type": "done", "thread_id": thread_id}
    yield f"data: {json.dumps(done_event)}\n\n"


@router.post("/api/chat")
async def chat(
    request: ChatRequest,
    agent: CompiledStateGraph = Depends(get_agent),  # type: ignore[type-arg]  # noqa: B008
) -> StreamingResponse:
    """Send a message to the agent and receive an SSE stream response."""
    # TODO: Replace with real auth from #9/#10/#11
    user_id = "dev-user"

    if request.thread_id:
        thread_id = request.thread_id
    else:
        session_id = uuid.uuid4().hex[:12]
        thread_id = build_thread_id(user_id, session_id)

    return StreamingResponse(
        _stream_response(agent, request.message, thread_id, user_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
