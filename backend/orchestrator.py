"""Debate orchestrator — state machine and agent turn runner."""

from __future__ import annotations

import asyncio
from enum import Enum

import structlog
from dedalus_labs import DedalusRunner
from fastapi import WebSocket

from backend.agents.base import AgentConfig, Message, start_agent_stream
from backend.agents.defense import create_defense_config
from backend.models import (
    AgentStreamMessage,
    CourtDirective,
    CourtDirectiveMessage,
    Evidence,
    Intervention,
    PhaseChangeMessage,
    TranscriptEntry,
)

logger = structlog.get_logger()


# --- Debate Phases ---


class DebatePhase(str, Enum):
    """Ordered phases of a courtroom debate."""

    INTAKE = "INTAKE"
    CASE_BRIEF = "CASE_BRIEF"
    DISCOVERY = "DISCOVERY"
    DEFENSE_OPENING = "DEFENSE_OPENING"
    PROSECUTION_OPENING = "PROSECUTION_OPENING"
    CROSS_EXAM_1 = "CROSS_EXAM_1"
    CROSS_EXAM_2 = "CROSS_EXAM_2"
    DEFENSE_CLOSING = "DEFENSE_CLOSING"
    PROSECUTION_CLOSING = "PROSECUTION_CLOSING"
    VERDICT = "VERDICT"
    EPISTEMIC_MAP = "EPISTEMIC_MAP"
    COMPLETE = "COMPLETE"


# --- Session State ---


class DebateSession:
    """Mutable state for a single debate.

    Holds asyncio primitives (Queue) so this is not
    a Pydantic model.
    """

    def __init__(self, session_id: str, dilemma: str) -> None:
        self.session_id = session_id
        self.dilemma = dilemma
        self.phase = DebatePhase.INTAKE
        self.transcript: list[TranscriptEntry] = []
        self.evidence: list[Evidence] = []
        self.court_directives: list[CourtDirective] = []
        self.intervention_queue: asyncio.Queue[Intervention] = (
            asyncio.Queue()
        )
        self.defense_score: float = 100.0
        self.prosecution_score: float = 100.0


# --- Helpers ---


async def _send(ws: WebSocket, msg: object) -> None:
    """Send a Pydantic model as JSON over WebSocket."""
    if hasattr(msg, "model_dump"):
        await ws.send_json(msg.model_dump())  # type: ignore[union-attr]


async def _transition(
    session: DebateSession,
    phase: DebatePhase,
    ws: WebSocket,
) -> None:
    """Move to a new phase and notify the frontend."""
    session.phase = phase
    await _send(ws, PhaseChangeMessage(phase=phase.value))
    logger.info(
        "phase_transition",
        session=session.session_id,
        phase=phase.value,
    )


def _build_history(session: DebateSession) -> list[Message]:
    """Build the message history from the transcript.

    Converts transcript entries into the
    system/user/assistant message format that
    the Dedalus SDK expects.
    """
    messages: list[Message] = [
        {
            "role": "user",
            "content": f"DILEMMA: {session.dilemma}",
        },
    ]

    for entry in session.transcript:
        messages.append({
            "role": "assistant",
            "content": (
                f"[{entry.agent.upper()}]: {entry.content}"
            ),
        })

    # Inject any court directives
    for directive in session.court_directives:
        evidence_text = ""
        if directive.new_evidence:
            evidence_text = "\nNew evidence:\n" + "\n".join(
                f"- {e.title}: {e.snippet}"
                for e in directive.new_evidence
            )
        messages.append({
            "role": "user",
            "content": (
                f"COURT DIRECTIVE (from the decision-maker): "
                f'"{directive.content}"{evidence_text}'
            ),
        })

    return messages


# --- Agent Turn Runner ---


async def run_agent_turn(
    session: DebateSession,
    config: AgentConfig,
    runner: DedalusRunner,
    ws: WebSocket,
) -> bool:
    """Run one agent turn, streaming chunks to the frontend.

    Checks the intervention queue between chunks.
    Returns True if the turn completed normally,
    False if it was interrupted by a user intervention.
    """
    history = _build_history(session)

    # runner.run(stream=True) returns an async iterable directly
    stream = start_agent_stream(runner, config, history)

    partial_response = ""

    async for chunk in stream:
        # Check for intervention between chunks
        try:
            intervention = session.intervention_queue.get_nowait()
            # Save partial response
            session.transcript.append(TranscriptEntry(
                agent=config.role,
                content=partial_response,
                phase=session.phase.value,
                interrupted=True,
            ))
            await _send(ws, AgentStreamMessage(
                agent=config.role,
                content="",
                done=True,
                interrupted=True,
            ))
            await _handle_intervention(
                session, intervention, ws
            )
            logger.info(
                "agent_interrupted",
                agent=config.role,
                intervention=intervention.content,
            )
            return False

        except asyncio.QueueEmpty:
            pass

        # Extract and forward content tokens
        if (
            hasattr(chunk, "choices")
            and chunk.choices
            and chunk.choices[0].delta
            and hasattr(chunk.choices[0].delta, "content")
            and chunk.choices[0].delta.content
        ):
            token = chunk.choices[0].delta.content
            partial_response += token
            await _send(ws, AgentStreamMessage(
                agent=config.role,
                content=token,
                done=False,
            ))

    # Completed without interruption
    session.transcript.append(TranscriptEntry(
        agent=config.role,
        content=partial_response,
        phase=session.phase.value,
        interrupted=False,
    ))
    await _send(ws, AgentStreamMessage(
        agent=config.role,
        content="",
        done=True,
    ))
    logger.info(
        "agent_turn_complete",
        agent=config.role,
        length=len(partial_response),
    )
    return True


async def _handle_intervention(
    session: DebateSession,
    intervention: Intervention,
    ws: WebSocket,
) -> None:
    """Process a user intervention. Sends the directive banner.

    For MVP, we store the directive and let the next agent
    address it. Full version would also trigger mini-research.
    """
    directive = CourtDirective(content=intervention.content)
    session.court_directives.append(directive)
    await _send(ws, CourtDirectiveMessage(
        content=intervention.content,
    ))
    logger.info(
        "intervention_handled",
        session=session.session_id,
        content=intervention.content,
    )


# --- Main Debate Flow ---


async def run_debate(
    session: DebateSession,
    runner: DedalusRunner,
    ws: WebSocket,
) -> None:
    """Run the MVP debate flow: defense opening.

    This is the minimal flow to prove the pipeline works.
    Additional phases will be added incrementally.
    """
    # --- Defense Opening ---
    await _transition(session, DebatePhase.DEFENSE_OPENING, ws)
    defense_config = create_defense_config()
    await run_agent_turn(session, defense_config, runner, ws)

    # --- Done (MVP) ---
    await _transition(session, DebatePhase.COMPLETE, ws)
    logger.info(
        "debate_complete",
        session=session.session_id,
    )
