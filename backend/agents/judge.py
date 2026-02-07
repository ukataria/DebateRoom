"""Judge agent configuration."""

from backend.agents.base import AgentConfig
from backend.agents.prompts import JUDGE_SYSTEM_PROMPT
from backend.config import JUDGE_MODEL


def create_judge_config() -> AgentConfig:
    """Create the judge agent configuration.

    Uses a single model (no handoff). No MCP servers or
    tools — the judge only analyzes the existing transcript.
    """
    return AgentConfig(
        role="judge",
        models=JUDGE_MODEL,
        system_prompt=JUDGE_SYSTEM_PROMPT,
    )
