"""Prosecution agent configuration."""

from backend.agents.base import AgentConfig
from backend.agents.prompts import PROSECUTION_SYSTEM_PROMPT
from backend.agents.tools import Citation
from backend.config import MCP_BRAVE_SEARCH, PROSECUTION_MODELS


def create_prosecution_config(citations: Citation) -> AgentConfig:
    """Create the prosecution agent configuration.

    Uses handoff routing: GPT for tool calls (evidence
    searches), Claude for persuasive argument writing.
    MCP: brave-search for supplemental evidence.
    Local tools: format_evidence so new findings are
    tracked and forwarded to the frontend.
    """
    return AgentConfig(
        role="prosecution",
        models=PROSECUTION_MODELS,
        system_prompt=PROSECUTION_SYSTEM_PROMPT,
        mcp_servers=[MCP_BRAVE_SEARCH],
        tools=[citations.make_format_evidence_tool()],
    )
