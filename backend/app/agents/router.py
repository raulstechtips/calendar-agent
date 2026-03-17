"""Chat and confirmation endpoints with SSE streaming."""

import json
import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from pydantic import BaseModel, ConfigDict, Field
from starlette.requests import Request

from app.agents.calendar_agent import build_thread_id, get_agent
from app.agents.guardrails import check_canary_leak
from app.agents.tools.calendar_tools import CALENDAR_EVENTS_SCOPE, SCOPE_ERROR_SENTINEL
from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.middleware import limiter
from app.users.schemas import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter()

_GUARD_NODES = frozenset({"input_guard", "output_guard"})


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


def _emit_token(content: str) -> str:
    """Format a token SSE event."""
    event: dict[str, Any] = {"type": "token", "content": content}
    return f"data: {json.dumps(event)}\n\n"


async def _stream_response(
    agent: CompiledStateGraph,  # type: ignore[type-arg]
    message: str,
    thread_id: str,
    user_id: str,
) -> AsyncGenerator[str, None]:
    """Stream agent response as SSE events.

    Uses a trailing buffer to detect canary tokens split across chunks.
    """
    canary = settings.canary_token
    # Hold back the last (len(canary)-1) chars so a split canary is caught
    buf_size = max(len(canary) - 1, 0) if canary else 0
    buf = ""

    try:
        async for _ns, (chunk, _metadata) in agent.astream(  # type: ignore[misc]
            {
                "messages": [HumanMessage(content=message)],
                "user_id": user_id,
                "pending_confirmation": None,
                "guardrail_verdict": "",
            },
            config={"configurable": {"thread_id": thread_id}},
            stream_mode="messages",
            subgraphs=True,
        ):
            # Short-circuit on scope error from calendar tools (#94)
            if (
                isinstance(chunk, ToolMessage)
                and isinstance(chunk.content, str)
                and SCOPE_ERROR_SENTINEL in chunk.content
            ):
                yield _emit_token(
                    "I don't have access to your calendar yet. "
                    "Please grant calendar permissions below, then try again."
                )
                scope_event: dict[str, Any] = {
                    "type": "scope_required",
                    "scope": CALENDAR_EVENTS_SCOPE,
                }
                yield f"data: {json.dumps(scope_event)}\n\n"
                scope_done: dict[str, Any] = {
                    "type": "done",
                    "thread_id": thread_id,
                }
                yield f"data: {json.dumps(scope_done)}\n\n"
                return

            if not (isinstance(chunk, AIMessage) and chunk.content):
                continue

            # Emit "blocked" event for guard node responses
            node_name = (
                _metadata.get("langgraph_node") if isinstance(_metadata, dict) else None
            )
            if node_name in _GUARD_NODES:
                blocked_event: dict[str, Any] = {
                    "type": "blocked",
                    "content": str(chunk.content),
                }
                yield f"data: {json.dumps(blocked_event)}\n\n"
                continue

            text = buf + str(chunk.content)
            if canary:
                text, leaked = check_canary_leak(text, canary)
                if leaked:
                    logger.warning("Canary token detected in agent output")

            if buf_size and len(text) > buf_size:
                emit, buf = text[:-buf_size], text[-buf_size:]
                if emit:
                    yield _emit_token(emit)
            elif buf_size:
                buf = text
            elif text:
                yield _emit_token(text)

        # Flush remaining buffer
        if buf:
            if canary:
                buf, leaked = check_canary_leak(buf, canary)
                if leaked:
                    logger.warning("Canary token detected in agent output")
            if buf:
                yield _emit_token(buf)

        # Check for pending human-in-the-loop interrupts after stream ends
        try:
            cfg = {"configurable": {"thread_id": thread_id}}
            snapshot = await agent.aget_state(cfg)  # type: ignore[arg-type]
            for task in snapshot.tasks:
                if task.interrupts:
                    val = task.interrupts[0].value
                    is_confirmation = (
                        isinstance(val, dict) and "action" in val
                    )
                    if is_confirmation:
                        action_id = uuid.uuid4().hex[:12]
                        confirmation_event: dict[str, Any] = {
                            "type": "confirmation",
                            "action": val["action"],
                            "action_id": action_id,
                            "details": val,
                        }
                        yield f"data: {json.dumps(confirmation_event)}\n\n"
                    break
        except Exception:
            logger.exception(
                "Failed to check interrupt state for thread=%s",
                thread_id,
            )

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
@limiter.limit("20/minute")  # pyright: ignore[reportUntypedFunctionDecorator]
async def chat(
    request: Request,
    body: ChatRequest,
    user: UserResponse = Depends(get_current_user),  # noqa: B008
    agent: CompiledStateGraph = Depends(get_agent),  # type: ignore[type-arg]  # noqa: B008
) -> StreamingResponse:
    """Send a message to the agent and receive an SSE stream response."""
    user_id = user.id
    thread_id = _resolve_thread_id(user_id, body.thread_id)

    return StreamingResponse(
        _stream_response(agent, body.message, thread_id, user_id),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@router.post("/api/chat/confirm", response_model=ConfirmResponse)
async def confirm(
    request: Request,
    body: ConfirmRequest,
    user: UserResponse = Depends(get_current_user),  # noqa: B008
    agent: CompiledStateGraph = Depends(get_agent),  # type: ignore[type-arg]  # noqa: B008
) -> ConfirmResponse:
    """Confirm or reject a pending write operation."""
    user_id = user.id

    if not _is_valid_thread_id(body.thread_id, user_id):
        raise HTTPException(status_code=403, detail="Thread ID ownership mismatch")

    if not body.approved:
        return ConfirmResponse(status="cancelled")

    try:
        await agent.ainvoke(
            Command(resume=True),
            config={"configurable": {"thread_id": body.thread_id}},
        )
    except Exception:
        logger.exception(
            "Confirmation execution error for thread=%s",
            body.thread_id,
        )
        raise HTTPException(
            status_code=500, detail="Failed to execute confirmed action"
        ) from None

    return ConfirmResponse(status="executed")
