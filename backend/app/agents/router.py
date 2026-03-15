"""Chat and confirmation endpoints with SSE streaming."""

import json
import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from pydantic import BaseModel, ConfigDict, Field

from app.agents.calendar_agent import build_thread_id, get_agent
from app.agents.guardrails import check_canary_leak, check_input
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(..., min_length=1, max_length=2000)
    thread_id: str | None = Field(None, max_length=200)


class ConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    thread_id: str = Field(..., max_length=200)
    action_id: str = Field(..., max_length=200)
    approved: bool


class ConfirmResponse(BaseModel):
    status: str


def _is_valid_thread_id(thread_id: str, user_id: str) -> bool:
    """Check that thread_id belongs to user and has a non-empty session suffix."""
    prefix = f"user-{user_id}:session-"
    return thread_id.startswith(prefix) and len(thread_id) > len(prefix)


def _resolve_thread_id(user_id: str, provided: str | None) -> str:
    """Resolve or generate a thread ID, enforcing ownership."""
    if provided and _is_valid_thread_id(provided, user_id):
        return provided
    session_id = uuid.uuid4().hex[:12]
    return build_thread_id(user_id, session_id)


async def _blocked_response(thread_id: str) -> AsyncGenerator[str, None]:
    """Yield SSE events for a blocked prompt injection attempt."""
    blocked_event = {
        "type": "blocked",
        "content": "I can only help with calendar and scheduling tasks.",
    }
    yield f"data: {json.dumps(blocked_event)}\n\n"

    done_event = {"type": "done", "thread_id": thread_id}
    yield f"data: {json.dumps(done_event)}\n\n"


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
                content = str(chunk.content)
                if settings.canary_token:
                    content, leaked = check_canary_leak(content, settings.canary_token)
                    if leaked:
                        logger.warning("Canary token detected in agent output")
                if content:
                    event: dict[str, Any] = {"type": "token", "content": content}
                    yield f"data: {json.dumps(event)}\n\n"
    except Exception:
        logger.exception("Agent streaming error")
        error_event: dict[str, Any] = {
            "type": "error",
            "content": "An error occurred processing your request.",
        }
        yield f"data: {json.dumps(error_event)}\n\n"

    done_event: dict[str, Any] = {"type": "done", "thread_id": thread_id}
    yield f"data: {json.dumps(done_event)}\n\n"


_SSE_HEADERS = {"Cache-Control": "no-cache", "Connection": "keep-alive"}


@router.post("/api/chat")
async def chat(
    request: ChatRequest,
    agent: CompiledStateGraph = Depends(get_agent),  # type: ignore[type-arg]  # noqa: B008
) -> StreamingResponse:
    """Send a message to the agent and receive an SSE stream response."""
    user_id = "dev-user"  # stub until auth wired in #9/#10/#11
    thread_id = _resolve_thread_id(user_id, request.thread_id)

    guard_result = check_input(request.message)
    if guard_result.blocked:
        logger.warning("Prompt injection blocked: pattern=%s", guard_result.pattern)
        return StreamingResponse(
            _blocked_response(thread_id),
            media_type="text/event-stream",
            headers=_SSE_HEADERS,
        )

    return StreamingResponse(
        _stream_response(agent, request.message, thread_id, user_id),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@router.post("/api/chat/confirm", response_model=ConfirmResponse)
async def confirm(
    request: ConfirmRequest,
    agent: CompiledStateGraph = Depends(get_agent),  # type: ignore[type-arg]  # noqa: B008
) -> ConfirmResponse:
    """Confirm or reject a pending write operation."""
    user_id = "dev-user"  # stub until auth wired in #9/#10/#11

    if not _is_valid_thread_id(request.thread_id, user_id):
        raise HTTPException(status_code=403, detail="Thread ID ownership mismatch")

    if not request.approved:
        return ConfirmResponse(status="cancelled")

    try:
        await agent.ainvoke(
            Command(resume=True),
            config={"configurable": {"thread_id": request.thread_id}},
        )
    except Exception:
        logger.exception(
            "Confirmation execution error for thread=%s",
            request.thread_id,
        )
        raise HTTPException(
            status_code=500, detail="Failed to execute confirmed action"
        ) from None

    return ConfirmResponse(status="executed")
