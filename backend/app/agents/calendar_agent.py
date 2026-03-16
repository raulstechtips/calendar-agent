"""ReAct agent definition with Content Safety guard nodes."""

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.language_models import BaseChatModel
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent  # pyright: ignore[reportDeprecated]

from app.agents.guardrails import input_guard, output_guard
from app.agents.prompts import build_prompt
from app.agents.state import AgentState
from app.agents.tools.calendar_tools import calendar_tools
from app.agents.tools.search_tools import search_tools
from app.core.config import settings

_agent: CompiledStateGraph | None = None  # type: ignore[type-arg]


def get_llm() -> AzureChatOpenAI:
    """Create AzureChatOpenAI instance using Entra ID via DefaultAzureCredential."""
    credential = DefaultAzureCredential(
        managed_identity_client_id=settings.azure_managed_identity_client_id or None,
    )
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )
    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        azure_ad_token_provider=token_provider,
        azure_deployment=settings.azure_openai_deployment,
        api_version=settings.azure_openai_api_version,
    )


def create_agent(llm: BaseChatModel | None = None) -> CompiledStateGraph:  # type: ignore[type-arg]
    """Create the guarded agent graph: input_guard -> agent -> output_guard.

    Args:
        llm: Optional LLM override for testing. Uses AzureChatOpenAI by default.
    """
    if llm is None:
        llm = get_llm()

    # Inner ReAct agent (no checkpointer — outer graph owns it)
    all_tools = calendar_tools + search_tools

    react_agent = create_react_agent(  # pyright: ignore[reportDeprecated]
        model=llm,
        tools=all_tools,
        state_schema=AgentState,
        prompt=build_prompt,
    )

    # Wrapper graph with guard nodes
    workflow = StateGraph(AgentState)
    workflow.add_node("input_guard", input_guard)
    workflow.add_node("agent", react_agent)
    workflow.add_node("output_guard", output_guard)

    workflow.add_edge(START, "input_guard")
    workflow.add_conditional_edges(
        "input_guard",
        lambda s: "blocked" if s.get("guardrail_verdict") == "blocked" else "pass",
        {"blocked": END, "pass": "agent"},
    )
    workflow.add_edge("agent", "output_guard")
    workflow.add_edge("output_guard", END)

    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


def get_agent() -> CompiledStateGraph:  # type: ignore[type-arg]
    """Return the singleton agent instance, creating it on first call."""
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


def build_thread_id(user_id: str, session_id: str) -> str:
    """Build a thread ID in the format user-{user_id}:session-{session_id}."""
    return f"user-{user_id}:session-{session_id}"
