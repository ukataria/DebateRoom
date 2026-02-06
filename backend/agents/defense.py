"""Defense agent configuration."""

from backend.agents.base import AgentConfig
from backend.agents.prompts import DEFENSE_SYSTEM_PROMPT
from backend.config import DEFENSE_MODELS, MCP_BRAVE_SEARCH


def create_defense_config() -> AgentConfig:
    """Create the defense agent configuration.

    Uses handoff routing: GPT for tool calls (evidence
    searches), Claude for persuasive argument writing.
    MCP: brave-search for supplemental evidence.
    """
    return AgentConfig(
        role="defense",
        models=DEFENSE_MODELS,
        system_prompt=DEFENSE_SYSTEM_PROMPT,
        mcp_servers=[MCP_BRAVE_SEARCH],
    )
