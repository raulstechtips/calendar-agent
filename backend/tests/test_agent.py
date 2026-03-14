"""Tests for LangGraph ReAct agent."""

import json
from collections.abc import AsyncGenerator

import httpx
import pytest
from httpx import ASGITransport
from langchain_core.language_models import GenericFakeChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
)

from app.agents.calendar_agent import (
    build_thread_id,
    create_agent,
    get_agent,
)
from app.agents.prompts import (
    SYSTEM_INSTRUCTIONS,
    SYSTEM_REMINDER,
    build_prompt,
)
from app.agents.state import AgentState
from app.main import app


class FakeAgent:
    """Mock agent that yields predefined chunks from astream."""

    def __init__(self, chunks: list[tuple]):
        self._chunks = chunks

    async def astream(self, *args, **kwargs):
        for chunk in self._chunks:
            yield chunk


class ErrorAgent:
    """Mock agent that raises during streaming."""

    async def astream(self, *args, **kwargs):
        raise RuntimeError("LLM connection failed")
        yield  # noqa: RUF027 — unreachable yield makes this an async generator


def _parse_sse_events(body: str) -> list[dict]:
    """Parse SSE body text into a list of event dicts."""
    events = []
    for line in body.strip().split("\n"):
        if line.startswith("data: "):
            events.append(json.loads(line[len("data: ") :]))
    return events


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


class TestAgentState:
    def test_state_accepts_required_fields(self) -> None:
        state: AgentState = {
            "messages": [],
            "user_id": "test-user",
            "pending_confirmation": None,
            "remaining_steps": 25,
        }
        assert state["messages"] == []
        assert state["user_id"] == "test-user"
        assert state["pending_confirmation"] is None

    def test_state_accepts_pending_confirmation(self) -> None:
        state: AgentState = {
            "messages": [],
            "user_id": "test-user",
            "pending_confirmation": {"action": "create_event", "details": {}},
            "remaining_steps": 25,
        }
        assert state["pending_confirmation"]["action"] == "create_event"


class TestPrompts:
    def test_system_instructions_defines_calendar_role(self) -> None:
        assert "calendar assistant" in SYSTEM_INSTRUCTIONS.lower()

    def test_system_instructions_has_canary_token(self) -> None:
        assert "KALEIDOSCOPE" in SYSTEM_INSTRUCTIONS

    def test_system_instructions_forbids_revealing_prompt(self) -> None:
        assert "never reveal" in SYSTEM_INSTRUCTIONS.lower()

    def test_system_instructions_restricts_to_calendar_topics(self) -> None:
        lower = SYSTEM_INSTRUCTIONS.lower()
        assert "calendar" in lower
        assert "scheduling" in lower

    def test_system_instructions_requires_write_confirmation(self) -> None:
        assert "confirmation" in SYSTEM_INSTRUCTIONS.lower()

    def test_system_instructions_treats_event_content_as_untrusted(self) -> None:
        assert "untrusted" in SYSTEM_INSTRUCTIONS.lower()

    def test_system_reminder_states_instruction_hierarchy(self) -> None:
        lower = SYSTEM_REMINDER.lower()
        assert "system instructions" in lower
        assert "user" in lower

    def test_build_prompt_wraps_messages_in_sandwich(self) -> None:
        state = {
            "messages": [HumanMessage(content="What's on my calendar?")],
            "user_id": "test-user",
            "pending_confirmation": None,
        }
        result = build_prompt(state)

        assert isinstance(result[0], SystemMessage)
        assert isinstance(result[-1], SystemMessage)
        assert isinstance(result[1], HumanMessage)

    def test_build_prompt_preserves_conversation_history(self) -> None:
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi!"),
            HumanMessage(content="Schedule a meeting"),
        ]
        state = {"messages": messages, "user_id": "u", "pending_confirmation": None}
        result = build_prompt(state)

        assert len(result) == len(messages) + 2
        assert result[1:-1] == messages


class TestThreadId:
    def test_format_matches_spec(self) -> None:
        assert build_thread_id("u1", "s1") == "user-u1:session-s1"

    def test_different_ids(self) -> None:
        assert build_thread_id("alice", "abc123") == "user-alice:session-abc123"


class TestAgentCreation:
    def test_create_agent_with_fake_llm(self) -> None:
        fake_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="Here are your events")])
        )
        agent = create_agent(llm=fake_llm)
        assert hasattr(agent, "ainvoke")
        assert hasattr(agent, "astream")

    async def test_agent_responds_to_message(self) -> None:
        fake_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="Here are your upcoming events.")])
        )
        agent = create_agent(llm=fake_llm)

        result = await agent.ainvoke(
            {
                "messages": [HumanMessage(content="What's on my calendar?")],
                "user_id": "test-user",
                "pending_confirmation": None,
            },
            config={"configurable": {"thread_id": "user-test:session-001"}},
        )
        last_message = result["messages"][-1]
        assert isinstance(last_message, AIMessage)
        assert len(last_message.content) > 0


class TestChatEndpoint:
    @pytest.fixture(autouse=True)
    def _default_agent_override(self):
        """Set a default agent override so get_agent() never hits Azure."""
        fake = FakeAgent(
            [(AIMessageChunk(content="default"), {"langgraph_node": "agent"})]
        )
        app.dependency_overrides[get_agent] = lambda: fake
        yield
        app.dependency_overrides.pop(get_agent, None)

    def _override_agent(self, fake):
        app.dependency_overrides[get_agent] = lambda: fake

    async def test_should_reject_empty_message(self, client: httpx.AsyncClient) -> None:
        response = await client.post("/api/chat", json={"message": ""})
        assert response.status_code == 422

    async def test_should_reject_oversized_message(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.post("/api/chat", json={"message": "a" * 2001})
        assert response.status_code == 422

    async def test_should_accept_max_length_message(
        self, client: httpx.AsyncClient
    ) -> None:
        self._override_agent(
            FakeAgent([(AIMessageChunk(content="OK"), {"langgraph_node": "agent"})])
        )
        response = await client.post("/api/chat", json={"message": "a" * 2000})
        assert response.status_code == 200

    async def test_should_return_sse_content_type(
        self, client: httpx.AsyncClient
    ) -> None:
        self._override_agent(
            FakeAgent([(AIMessageChunk(content="Hi"), {"langgraph_node": "agent"})])
        )
        response = await client.post("/api/chat", json={"message": "Hello"})
        assert response.headers["content-type"].startswith("text/event-stream")

    async def test_should_stream_token_events(self, client: httpx.AsyncClient) -> None:
        self._override_agent(
            FakeAgent(
                [
                    (AIMessageChunk(content="Here"), {"langgraph_node": "agent"}),
                    (AIMessageChunk(content=" are"), {"langgraph_node": "agent"}),
                ]
            )
        )
        response = await client.post(
            "/api/chat", json={"message": "What's on my calendar?"}
        )
        events = _parse_sse_events(response.text)
        token_events = [e for e in events if e["type"] == "token"]

        assert len(token_events) == 2
        assert token_events[0]["content"] == "Here"
        assert token_events[1]["content"] == " are"

    async def test_should_end_stream_with_done_event(
        self, client: httpx.AsyncClient
    ) -> None:
        self._override_agent(
            FakeAgent([(AIMessageChunk(content="Hi"), {"langgraph_node": "agent"})])
        )
        response = await client.post("/api/chat", json={"message": "Hello"})
        events = _parse_sse_events(response.text)

        assert events[-1]["type"] == "done"
        assert "thread_id" in events[-1]

    async def test_should_generate_thread_id_matching_spec_format(
        self, client: httpx.AsyncClient
    ) -> None:
        self._override_agent(
            FakeAgent([(AIMessageChunk(content="Hi"), {"langgraph_node": "agent"})])
        )
        response = await client.post("/api/chat", json={"message": "Hello"})
        events = _parse_sse_events(response.text)
        thread_id = events[-1]["thread_id"]

        assert thread_id.startswith("user-")
        assert ":session-" in thread_id

    async def test_should_use_provided_thread_id(
        self, client: httpx.AsyncClient
    ) -> None:
        self._override_agent(
            FakeAgent([(AIMessageChunk(content="Hi"), {"langgraph_node": "agent"})])
        )
        response = await client.post(
            "/api/chat",
            json={"message": "Hello", "thread_id": "user-abc:session-xyz"},
        )
        events = _parse_sse_events(response.text)

        assert events[-1]["thread_id"] == "user-abc:session-xyz"

    async def test_should_skip_empty_content_chunks(
        self, client: httpx.AsyncClient
    ) -> None:
        self._override_agent(
            FakeAgent(
                [
                    (AIMessageChunk(content=""), {"langgraph_node": "agent"}),
                    (AIMessageChunk(content="Hello"), {"langgraph_node": "agent"}),
                ]
            )
        )
        response = await client.post("/api/chat", json={"message": "Hi"})
        events = _parse_sse_events(response.text)
        token_events = [e for e in events if e["type"] == "token"]

        assert len(token_events) == 1
        assert token_events[0]["content"] == "Hello"

    async def test_should_handle_agent_error_gracefully(
        self, client: httpx.AsyncClient
    ) -> None:
        self._override_agent(ErrorAgent())
        response = await client.post("/api/chat", json={"message": "Hello"})

        assert response.status_code == 200
        events = _parse_sse_events(response.text)

        assert any(e["type"] == "error" for e in events)
        assert events[-1]["type"] == "done"

    async def test_should_reject_extra_fields(self, client: httpx.AsyncClient) -> None:
        response = await client.post(
            "/api/chat", json={"message": "Hello", "extra": "bad"}
        )
        assert response.status_code == 422
