"""Logging configuration — structlog with file + console output.

Creates a per-server-instance directory under ~/logs/ and
supports per-session log files within it.

Directory layout:
    ~/logs/courtroom_2026-02-06_14-30-00/
        server.log                  # all events for this instance
        sessions/
            test-session-001.log    # events for one debate
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import structlog

_LOG_DIR: Path | None = None
_session_handlers: dict[str, logging.Handler] = {}


def setup_logging() -> Path:
    """Configure structlog with console + file output.

    Creates ~/logs/courtroom_<timestamp>/ for this server
    instance. Call once at startup.
    Returns the log directory path.
    """
    global _LOG_DIR

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    _LOG_DIR = Path.home() / "logs" / f"courtroom_{timestamp}"
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    (_LOG_DIR / "sessions").mkdir(exist_ok=True)

    # --- Formatters ---

    console_formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(),
        ],
    )

    file_formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    # --- Root stdlib logger ---

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    # Clear any existing handlers (e.g. uvicorn defaults)
    root.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    root.addHandler(console_handler)

    server_handler = logging.FileHandler(_LOG_DIR / "server.log")
    server_handler.setLevel(logging.DEBUG)
    server_handler.setFormatter(file_formatter)
    root.addHandler(server_handler)

    # --- structlog → stdlib bridge ---

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )

    structlog.get_logger().info(
        "logging_configured",
        log_dir=str(_LOG_DIR),
    )
    return _LOG_DIR


def get_log_dir() -> Path:
    """Return the per-instance log directory."""
    assert _LOG_DIR is not None, "Call setup_logging() first"
    return _LOG_DIR


def get_session_logger(
    session_id: str,
) -> structlog.stdlib.BoundLogger:
    """Get a logger that writes to both server.log and sessions/<id>.log.

    The session file handler is created on first call for a
    given session_id. The returned logger has session= bound.
    """
    if session_id not in _session_handlers:
        assert _LOG_DIR is not None, "Call setup_logging() first"
        session_file = _LOG_DIR / "sessions" / f"{session_id}.log"

        file_formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ],
        )

        handler = logging.FileHandler(session_file)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(file_formatter)

        stdlib_logger = logging.getLogger(f"courtroom.session.{session_id}")
        stdlib_logger.addHandler(handler)
        stdlib_logger.setLevel(logging.DEBUG)

        _session_handlers[session_id] = handler

    return structlog.get_logger(f"courtroom.session.{session_id}").bind(
        session=session_id
    )


def cleanup_session_logger(session_id: str) -> None:
    """Close and remove the file handler for a finished session."""
    handler = _session_handlers.pop(session_id, None)
    if handler:
        handler.close()
        stdlib_logger = logging.getLogger(f"courtroom.session.{session_id}")
        stdlib_logger.removeHandler(handler)
