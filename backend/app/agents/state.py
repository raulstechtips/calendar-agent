"""LangGraph agent state definition."""

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State for the calendar agent graph.

    Attributes:
        messages: Conversation history with add_messages reducer for deduplication.
        user_id: Google sub claim identifying the authenticated user.
        pending_confirmation: Details of a write action awaiting user approval.
    """

    messages: Annotated[list, add_messages]
    user_id: str
    pending_confirmation: dict | None
    remaining_steps: int
