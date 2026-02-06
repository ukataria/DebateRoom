"""FastAPI application — WebSocket endpoint for debates."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from dedalus_labs import AsyncDedalus, DedalusRunner
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.models import (
    ErrorMessage,
    Intervention,
    new_session_id,
)
from backend.orchestrator import DebateSession, run_debate

logger = structlog.get_logger()

# --- Shared State ---

runner: DedalusRunner | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create the Dedalus client and runner once at startup."""
    global runner
    client = AsyncDedalus()
    runner = DedalusRunner(client)
    logger.info("dedalus_client_ready")
    yield
    logger.info("shutting_down")


app = FastAPI(title="Courtroom", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- WebSocket Endpoint ---


@app.websocket("/ws/{session_id}")
async def handle_ws(
    websocket: WebSocket,
    session_id: str,
) -> None:
    """Handle a single debate session over WebSocket.

    Runs two concurrent tasks:
    1. A listener for client messages (start, intervention)
    2. The debate orchestrator (once started)
    """
    await websocket.accept()
    assert runner is not None, "Runner not initialized"

    session: DebateSession | None = None
    start_event = asyncio.Event()
    dilemma_holder: list[str] = []

    async def listen_for_client() -> None:
        """Listen for client messages and route them."""
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "start" and session is None:
                dilemma_holder.append(data.get("dilemma", ""))
                start_event.set()

            elif msg_type == "intervention" and session:
                await session.intervention_queue.put(
                    Intervention(content=data.get("content", ""))
                )
                logger.info(
                    "intervention_received",
                    session=session_id,
                    content=data.get("content", ""),
                )

    listener = asyncio.create_task(listen_for_client())

    try:
        # Wait for the client to send a start message
        await start_event.wait()
        dilemma = dilemma_holder[0]

        session = DebateSession(
            session_id=session_id,
            dilemma=dilemma,
        )
        logger.info(
            "debate_started",
            session=session_id,
            dilemma=dilemma,
        )

        await run_debate(session, runner, websocket)

    except WebSocketDisconnect:
        logger.info("client_disconnected", session=session_id)
    except Exception as e:
        logger.error(
            "debate_error",
            session=session_id,
            error=str(e),
        )
        try:
            msg = ErrorMessage(message=str(e))
            await websocket.send_json(msg.model_dump())
        except Exception:
            pass
    finally:
        listener.cancel()


# --- Health Check ---


@app.get("/health")
async def health() -> dict[str, str]:
    """Simple health check."""
    return {"status": "ok"}
