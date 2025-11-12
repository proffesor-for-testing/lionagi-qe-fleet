"""LionAGI QE Fleet - Agentic Quality Engineering powered by LionAGI"""

import warnings
from typing import Optional

from .core.task import QETask
from .core.router import ModelRouter
from .core.orchestrator import QEOrchestrator
from .core.base_agent import BaseQEAgent
from .config import StorageMode, StorageConfig

__version__ = "1.2.1"


def QEFleet(*args, **kwargs):
    """
    DEPRECATED: QEFleet is deprecated as of v1.1.0 and will be removed in v2.0.0.

    Please migrate to QEOrchestrator for direct access to fleet orchestration.

    Migration guide:
        Before:
            from lionagi_qe import QEFleet
            fleet = QEFleet(enable_routing=True)
            await fleet.initialize()
            fleet.register_agent(agent)
            result = await fleet.execute(agent_id, task)

        After:
            from lionagi_qe import QEOrchestrator, ModelRouter
            from lionagi.core import Session

            memory = Session().context  # or use RedisMemory/PostgresMemory
            router = ModelRouter(enable_routing=True)
            orchestrator = QEOrchestrator(memory, router)
            orchestrator.register_agent(agent)
            result = await orchestrator.execute_agent(agent_id, task)

    See docs/migration/fleet-to-orchestrator.md for detailed migration guide.
    """
    warnings.warn(
        "QEFleet is deprecated and will be removed in v2.0.0. "
        "Use QEOrchestrator instead. "
        "See docs/migration/fleet-to-orchestrator.md for migration guide.",
        DeprecationWarning,
        stacklevel=2
    )

    # Import here to avoid circular dependencies
    from .core.fleet import QEFleet as _QEFleet
    return _QEFleet(*args, **kwargs)


def QEMemory(*args, **kwargs):
    """
    DEPRECATED: QEMemory is deprecated as of v1.1.0 and will be removed in v2.0.0.

    Please use LionAGI's native Session.context for in-memory storage or
    persistence backends (RedisMemory, PostgresMemory) for production.

    Migration guide:
        Before:
            from lionagi_qe import QEMemory
            memory = QEMemory()

        After (in-memory):
            from lionagi.core import Session
            memory = Session().context

        After (Redis):
            from lionagi_qe.persistence import RedisMemory
            memory = RedisMemory(host="localhost", port=6379)

        After (PostgreSQL):
            from lionagi_qe.persistence import PostgresMemory
            memory = PostgresMemory(connection_string="postgresql://...")
    """
    warnings.warn(
        "QEMemory is deprecated and will be removed in v2.0.0. "
        "Use Session.context for in-memory or persistence backends (RedisMemory, PostgresMemory) for production. "
        "See docs/migration/fleet-to-orchestrator.md for migration guide.",
        DeprecationWarning,
        stacklevel=2
    )

    # Import here to avoid circular dependencies
    from .core.memory import QEMemory as _QEMemory
    return _QEMemory(*args, **kwargs)


__all__ = [
    "QEFleet",  # Deprecated - returns deprecation warning
    "QEMemory",  # Deprecated - returns deprecation warning
    "QETask",
    "ModelRouter",
    "QEOrchestrator",
    "BaseQEAgent",
    "StorageMode",
    "StorageConfig",
]
