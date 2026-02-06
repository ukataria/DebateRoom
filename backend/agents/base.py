"""Base agent configuration and runner wrapper."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import structlog
from dedalus_labs import DedalusRunner

logger = structlog.get_logger()

# Message dicts follow the OpenAI-compatible format:
# {"role": "system"|"user"|"assistant", "content": "..."}
Message = dict[str, str]


@dataclass
class AgentConfig:
    """Configuration for a single debate agent.

    The `models` field accepts a list for Dedalus handoff routing
    (routes subtasks to different models based on strengths),
    or a single string for no handoff.
    """

    role: str
    models: list[str] | str
    system_prompt: str
    mcp_servers: list[str] = field(default_factory=list)
    tools: list[Callable[..., Any]] = field(default_factory=list)


def build_messages(
    config: AgentConfig,
    history: list[Message],
) -> list[Message]:
    """Build the full message list for an agent call.

    Prepends the agent's system prompt, then appends
    the conversation history (prior agent turns, evidence,
    directives, user input).
    """
    return [
        {"role": "system", "content": config.system_prompt},
        *history,
    ]


def start_agent_stream(
    runner: DedalusRunner,
    config: AgentConfig,
    history: list[Message],
) -> Any:
    """Start a streaming agent run with handoff routing.

    runner.run(stream=True) returns an async iterable
    directly (not a coroutine). The caller iterates with
    `async for chunk in stream` and handles interventions
    between chunks.

    See: https://docs.dedaluslabs.ai/sdk/streaming
    """
    messages = build_messages(config, history)

    logger.debug(
        "agent_stream_start",
        role=config.role,
        models=config.models,
        mcp_servers=config.mcp_servers,
        message_count=len(messages),
    )

    return runner.run(
        messages=messages,
        model=config.models,
        mcp_servers=config.mcp_servers or None,
        tools=config.tools or None,
        stream=True,
    )
