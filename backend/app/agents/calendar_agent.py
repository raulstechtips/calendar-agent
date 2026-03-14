"""ReAct agent definition using create_react_agent with AzureChatOpenAI."""

from langchain_core.language_models import BaseChatModel
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from app.agents.prompts import build_prompt
from app.agents.state import AgentState
from app.core.config import settings

_agent = None


def get_llm() -> AzureChatOpenAI:
    """Create AzureChatOpenAI instance configured from settings."""
    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        azure_deployment=settings.azure_openai_deployment,
        api_version=settings.azure_openai_api_version,
    )


def create_agent(llm: BaseChatModel | None = None):
    """Create and compile the ReAct agent graph.

    Args:
        llm: Optional LLM override for testing. Uses AzureChatOpenAI by default.
    """
    if llm is None:
        llm = get_llm()
    checkpointer = MemorySaver()
    return create_react_agent(
        model=llm,
        tools=[],  # Tools added in #17
        checkpointer=checkpointer,
        state_schema=AgentState,
        prompt=build_prompt,
    )


def get_agent():
    """Return the singleton agent instance, creating it on first call."""
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


def build_thread_id(user_id: str, session_id: str) -> str:
    """Build a thread ID in the format user-{user_id}:session-{session_id}."""
    return f"user-{user_id}:session-{session_id}"
