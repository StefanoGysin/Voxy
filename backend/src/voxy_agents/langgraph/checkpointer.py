"""
LangGraph Checkpointer Utilities

Provides factory functions for creating LangGraph checkpointers:
- InMemorySaver: For POC, testing, and development
- SqliteSaver: For production single-instance persistence
- (Future) PostgresSaver: For multi-instance Supabase persistence

Reference: LangGraph Persistence documentation
https://langchain-ai.github.io/langgraph/concepts/persistence/
"""

import os
from enum import Enum
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver


class CheckpointerType(str, Enum):
    """Supported checkpointer types."""

    MEMORY = "memory"
    SQLITE = "sqlite"
    POSTGRES = "postgres"  # Future implementation


def create_checkpointer(
    checkpointer_type: CheckpointerType | str = CheckpointerType.SQLITE,
    db_path: str | None = None,
) -> "BaseCheckpointSaver[Any]":
    """
    Factory function to create LangGraph checkpointers.

    Phase 4C: Default changed from MEMORY to SQLITE for persistent checkpoints.

    Args:
        checkpointer_type: Type of checkpointer (memory, sqlite, postgres)
                           Default: SQLITE (Phase 4C)
        db_path: Database path for persistent checkpointers (SQLite/Postgres)
                 Default: from LANGGRAPH_DB_PATH env var or "data/voxy_langgraph.db"

    Returns:
        BaseCheckpointSaver instance

    Raises:
        ValueError: If checkpointer_type is invalid
        ImportError: If required checkpoint package is not installed

    Environment Variables:
        LANGGRAPH_DB_PATH: Path to SQLite database file (relative to backend/)
                          Default: "data/voxy_langgraph.db"

    Examples:
        >>> # Phase 4C Default - SQLite checkpointer (persistent)
        >>> checkpointer = create_checkpointer()  # Uses env var or default path

        >>> # Development/Testing - In-memory checkpointer (non-persistent)
        >>> checkpointer = create_checkpointer(CheckpointerType.MEMORY)

        >>> # Custom SQLite path
        >>> checkpointer = create_checkpointer(
        ...     CheckpointerType.SQLITE,
        ...     db_path="custom/path/checkpoints.db"
        ... )

        >>> # Production - PostgreSQL (future)
        >>> checkpointer = create_checkpointer(
        ...     CheckpointerType.POSTGRES,
        ...     db_path="postgresql://user:pass@localhost/voxy"
        ... )
    """
    checkpointer_type = CheckpointerType(checkpointer_type)

    if checkpointer_type == CheckpointerType.MEMORY:
        logger.bind(event="CHECKPOINTER|INIT").info(
            "Creating InMemorySaver checkpointer (non-persistent)"
        )
        from langgraph.checkpoint.memory import InMemorySaver

        return InMemorySaver()

    elif checkpointer_type == CheckpointerType.SQLITE:
        # Model-Agnostic: Read from environment variable or use default
        resolved_db_path: str = (
            db_path
            if db_path
            else os.getenv("LANGGRAPH_DB_PATH", "data/voxy_langgraph.db")
        )
        logger.bind(event="CHECKPOINTER|INIT").info(
            "Creating SqliteSaver checkpointer", db_path=resolved_db_path
        )
        try:
            import sqlite3

            from langgraph.checkpoint.sqlite import SqliteSaver
        except ImportError as e:
            raise ImportError(
                "langgraph-checkpoint-sqlite not installed. "
                "Run: poetry add langgraph-checkpoint-sqlite"
            ) from e

        # Phase 4E Fix: Create connection manually and pass to SqliteSaver
        # This avoids context manager issues and keeps connection open
        conn = sqlite3.connect(resolved_db_path, check_same_thread=False)
        checkpointer = SqliteSaver(conn)

        logger.bind(event="CHECKPOINTER|SETUP").debug(
            "Initializing SQLite checkpointer schema"
        )
        checkpointer.setup()

        return checkpointer

    elif checkpointer_type == CheckpointerType.POSTGRES:
        if not db_path:
            raise ValueError("db_path required for PostgreSQL checkpointer")

        logger.bind(event="CHECKPOINTER|INIT").info(
            "Creating PostgresSaver checkpointer (future implementation)",
            db_uri=db_path,
        )
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
        except ImportError as e:
            raise ImportError(
                "langgraph-checkpoint-postgres not installed. "
                "Run: poetry add langgraph-checkpoint-postgres"
            ) from e

        # PostgresSaver.from_conn_string for Supabase Postgres
        return PostgresSaver.from_conn_string(db_path)

    else:
        raise ValueError(
            f"Invalid checkpointer_type: {checkpointer_type}. "
            f"Supported: {[t.value for t in CheckpointerType]}"
        )


def get_checkpoint_config(thread_id: str, checkpoint_id: str | None = None) -> dict:
    """
    Create LangGraph config dict for checkpoint invocation.

    Args:
        thread_id: Thread ID for checkpoint isolation (maps to session_id)
        checkpoint_id: Optional specific checkpoint ID for time-travel

    Returns:
        Config dict for graph.invoke(..., config=...)

    Examples:
        >>> # Standard invocation (latest checkpoint)
        >>> config = get_checkpoint_config(thread_id="session-123")
        >>> graph.invoke({"messages": [...]}, config=config)

        >>> # Time-travel to specific checkpoint
        >>> config = get_checkpoint_config(
        ...     thread_id="session-123",
        ...     checkpoint_id="1ef4f797-8335-6428-8001-8a1503f9b875"
        ... )
        >>> graph.invoke(None, config=config)  # Resume from checkpoint
    """
    config: dict = {"configurable": {"thread_id": thread_id}}

    if checkpoint_id:
        config["configurable"]["checkpoint_id"] = checkpoint_id
        logger.bind(event="CHECKPOINTER|TIME_TRAVEL").debug(
            "Time-travel config created",
            thread_id=thread_id,
            checkpoint_id=checkpoint_id,
        )

    return config
