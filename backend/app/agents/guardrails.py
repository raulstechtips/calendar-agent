"""Prompt injection defense and content safety guardrails.

Provides regex-based injection detection, Azure AI Content Safety integration,
and LangGraph guard nodes for input/output filtering.
"""

import asyncio
import logging
import re
from typing import Any, NamedTuple

from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory
from azure.identity import DefaultAzureCredential
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, RemoveMessage

from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

_INJECTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"ignore\b.{0,20}\b(?:previous|above|prior|all)\b.{0,20}"
            r"\b(?:instructions|rules|prompt)",
            re.IGNORECASE,
        ),
        "ignore_instructions",
    ),
    (
        re.compile(r"\byou are now\b", re.IGNORECASE),
        "role_override",
    ),
    (
        re.compile(
            r"(?:reveal|repeat|show|print|output)\b.{0,30}"
            r"\b(?:system prompt|instructions|rules)",
            re.IGNORECASE,
        ),
        "reveal_prompt",
    ),
    (
        re.compile(
            r"\bforget\b.{0,20}\b(?:rules|instructions|everything|all)\b",
            re.IGNORECASE,
        ),
        "forget_rules",
    ),
    (
        re.compile(
            r"(?:pretend|act as if)\b.{0,20}\byou\b",
            re.IGNORECASE,
        ),
        "impersonation",
    ),
    (
        re.compile(
            r"(?:do not follow|disregard|override)\b.{0,20}"
            r"\b(?:instructions|rules|above)",
            re.IGNORECASE,
        ),
        "override",
    ),
    (
        re.compile(
            r"\b(?:jailbreak|developer mode|unrestricted mode)\b",
            re.IGNORECASE,
        ),
        "jailbreak",
    ),
    (
        re.compile(
            r"\b(?:DAN\s+mode|do\s+anything\s+now|respond\s+as\s+DAN"
            r"|as\s+DAN\s+from\s+now)\b",
            re.IGNORECASE,
        ),
        "dan_mode",
    ),
    (
        re.compile(r"\[INST\]|\[system\]|<\|im_start\|>", re.IGNORECASE),
        "format_injection",
    ),
]

_BLOCKED_INPUT_MSG = "I can only help with calendar and scheduling tasks."
_BLOCKED_OUTPUT_MSG = (
    "I'm unable to provide that response. How can I help with your calendar?"
)

SEVERITY_THRESHOLD = 2  # Block severity >= 2 (on 0/2/4/6 scale)


class GuardResult(NamedTuple):
    """Result of an input guard check."""

    blocked: bool
    pattern: str | None


def _normalize(text: str) -> str:
    """Collapse all whitespace (including newlines) into single spaces."""
    return re.sub(r"\s+", " ", text)


def check_input(text: str) -> GuardResult:
    """Check user input for known prompt injection patterns."""
    normalized = _normalize(text)
    for compiled, name in _INJECTION_PATTERNS:
        if compiled.search(normalized):
            return GuardResult(blocked=True, pattern=name)
    return GuardResult(blocked=False, pattern=None)


def check_canary_leak(text: str, canary: str) -> tuple[str, bool]:
    """Strip canary token from text if present.

    Returns:
        Tuple of (sanitized text, whether a leak was detected).
    """
    if not canary:
        return text, False
    if canary not in text:
        return text, False
    return text.replace(canary, ""), True


# ---------------------------------------------------------------------------
# Azure AI Content Safety client
# ---------------------------------------------------------------------------

_client: ContentSafetyClient | None = None


def get_content_safety_client() -> ContentSafetyClient:
    """Return singleton ContentSafetyClient using DefaultAzureCredential."""
    global _client
    if _client is None:
        credential = DefaultAzureCredential(
            managed_identity_client_id=(
                settings.azure_managed_identity_client_id or None
            ),
        )
        _client = ContentSafetyClient(
            endpoint=settings.azure_content_safety_endpoint,
            credential=credential,
        )
    return _client


def reset_content_safety_client() -> None:
    """Reset the singleton client (for test isolation)."""
    global _client
    if _client is not None:
        _client.close()
    _client = None


async def analyze_content_safety(text: str) -> GuardResult:
    """Analyze text for harmful content using Azure AI Content Safety.

    Falls back to a non-blocking result on API errors (fail-open).
    """
    try:
        client = get_content_safety_client()
        result = await asyncio.to_thread(
            client.analyze_text,
            AnalyzeTextOptions(
                text=text,
                categories=[
                    TextCategory.HATE,
                    TextCategory.SELF_HARM,
                    TextCategory.SEXUAL,
                    TextCategory.VIOLENCE,
                ],
            ),
        )
        for analysis in result.categories_analysis:
            if (
                analysis.severity is not None
                and analysis.severity >= SEVERITY_THRESHOLD
            ):
                return GuardResult(
                    blocked=True, pattern=f"content_safety:{analysis.category}"
                )
        return GuardResult(blocked=False, pattern=None)
    except Exception:
        logger.warning(
            "Content Safety API error — falling back to regex only",
            exc_info=True,
        )
        return GuardResult(blocked=False, pattern=None)


# ---------------------------------------------------------------------------
# LangGraph guard nodes
# ---------------------------------------------------------------------------


def _last_human_content(messages: list[BaseMessage]) -> str:
    """Extract text content from the last HumanMessage."""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) and isinstance(msg.content, str):
            return msg.content
    return ""


def _last_ai_message(messages: list[BaseMessage]) -> AIMessage | None:
    """Return the last AIMessage, or None."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            return msg
    return None


async def input_guard(state: AgentState) -> dict[str, Any]:
    """LangGraph node: check user input for injection and harmful content.

    Runs regex first (fast, no network). If regex passes, calls Content Safety API.
    On block: sets guardrail_verdict="blocked" and appends a safe AIMessage.
    On pass: sets guardrail_verdict="pass".
    """
    text = _last_human_content(state["messages"])

    # Fast-path: regex injection detection
    regex_result = check_input(text)
    if regex_result.blocked:
        logger.warning("Input guard blocked (regex): pattern=%s", regex_result.pattern)
        return {
            "guardrail_verdict": "blocked",
            "messages": [AIMessage(content=_BLOCKED_INPUT_MSG)],
        }

    # Second layer: Content Safety API
    safety_result = await analyze_content_safety(text)
    if safety_result.blocked:
        logger.warning(
            "Input guard blocked (content_safety): pattern=%s", safety_result.pattern
        )
        return {
            "guardrail_verdict": "blocked",
            "messages": [AIMessage(content=_BLOCKED_INPUT_MSG)],
        }

    return {"guardrail_verdict": "pass"}


async def output_guard(state: AgentState) -> dict[str, Any]:
    """LangGraph node: check agent output for harmful content.

    On block: replaces the last AIMessage with a safe fallback.
    On pass or API error: returns empty (no state change).
    """
    last_msg = _last_ai_message(state["messages"])
    if last_msg is None or not isinstance(last_msg.content, str):
        return {}

    safety_result = await analyze_content_safety(last_msg.content)
    if safety_result.blocked:
        logger.warning("Output guard blocked: pattern=%s", safety_result.pattern)
        messages_update: list[AIMessage | RemoveMessage] = []
        if last_msg.id:
            messages_update.append(RemoveMessage(id=last_msg.id))
        messages_update.append(AIMessage(content=_BLOCKED_OUTPUT_MSG))
        return {"messages": messages_update}

    return {}
