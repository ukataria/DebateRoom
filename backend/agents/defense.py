"""Defense agent configuration."""

from backend.agents.base import AgentConfig
from backend.agents.prompts import DEFENSE_CROSS_PROMPT, DEFENSE_SYSTEM_PROMPT
from backend.agents.tools import Citation
from backend.config import DEFENSE_MODELS, MCP_BRAVE_SEARCH


def create_defense_config(citations: Citation) -> AgentConfig:
    """Create the defense agent configuration.

    Uses handoff routing: GPT for tool calls (evidence
    searches), Claude for persuasive argument writing.
    MCP: brave-search for supplemental evidence.
    Local tools: format_evidence so new findings are
    tracked and forwarded to the frontend.
    """
    return AgentConfig(
        role="defense",
        models=DEFENSE_MODELS,
        system_prompt=DEFENSE_SYSTEM_PROMPT,
        mcp_servers=[MCP_BRAVE_SEARCH],
        tools=[citations.make_format_evidence_tool()],
    )


def create_defense_cross_config(citations: Citation) -> AgentConfig:
    """Create the defense cross-examination configuration.

    Same MCP and tools as the opening, but the prompt
    shifts to a conversational rebuttal of the
    Prosecution's challenges.
    """
    return AgentConfig(
        role="defense",
        models=DEFENSE_MODELS,
        system_prompt=DEFENSE_CROSS_PROMPT,
        mcp_servers=[MCP_BRAVE_SEARCH],
        tools=[citations.make_format_evidence_tool()],
    )
