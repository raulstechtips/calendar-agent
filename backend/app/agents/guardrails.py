"""Prompt injection defense: input regex guard and canary leak detection."""

import re
from typing import NamedTuple

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
        re.compile(r"\bDAN\b", re.IGNORECASE),
        "dan_mode",
    ),
    (
        re.compile(r"\[INST\]|\[system\]|<\|im_start\|>", re.IGNORECASE),
        "format_injection",
    ),
]


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
