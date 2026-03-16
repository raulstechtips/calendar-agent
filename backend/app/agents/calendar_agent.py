"""ReAct agent definition using create_react_agent with AzureChatOpenAI."""

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.language_models import BaseChatModel
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent  # pyright: ignore[reportDeprecated]

from app.agents.prompts import build_prompt
from app.agents.state import AgentState
from app.agents.tools.calendar_tools import calendar_tools
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
    """Create and compile the ReAct agent graph.

    Args:
        llm: Optional LLM override for testing. Uses AzureChatOpenAI by default.
    """
    if llm is None:
        llm = get_llm()
    checkpointer = MemorySaver()
    return create_react_agent(  # pyright: ignore[reportDeprecated]
        model=llm,
        tools=calendar_tools,
        checkpointer=checkpointer,
        state_schema=AgentState,
        prompt=build_prompt,
    )


def get_agent() -> CompiledStateGraph:  # type: ignore[type-arg]
    """Return the singleton agent instance, creating it on first call."""
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


def build_thread_id(user_id: str, session_id: str) -> str:
    """Build a thread ID in the format user-{user_id}:session-{session_id}."""
    return f"user-{user_id}:session-{session_id}"
