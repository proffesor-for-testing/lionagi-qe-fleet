"""Storage configuration with environment-based mode selection

This module provides automatic storage backend selection based on environment mode:
- DEV: Session.context (in-memory, zero setup)
- TEST: Session.context (isolated, fast)
- PROD: PostgresMemory (durable, ACID guarantees)

Environment detection automatically checks for:
- AQE_STORAGE_MODE (explicit override)
- ENVIRONMENT, NODE_ENV (common environment variables)
- Defaults to DEV if not specified

Usage:
    # Option 1: Auto-detect from environment
    config = StorageConfig.from_environment()
    orchestrator = QEOrchestrator.from_config(config)

    # Option 2: Explicit mode
    config = StorageConfig(mode=StorageMode.PROD, database_url="postgresql://...")
    orchestrator = QEOrchestrator.from_config(config)

    # Option 3: Direct instantiation
    orchestrator = QEOrchestrator(mode="production")
"""

import os
from enum import Enum
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, field
import logging

logger = logging.getLogger("lionagi_qe.config")


class StorageMode(str, Enum):
    """Storage backend modes for different environments

    Attributes:
        DEV: Development mode - in-memory Session.context, zero setup
        TEST: Testing mode - isolated in-memory storage for fast tests
        PROD: Production mode - PostgreSQL with durability and ACID guarantees
    """
    DEV = "development"
    TEST = "testing"
    PROD = "production"

    @classmethod
    def from_string(cls, value: str) -> "StorageMode":
        """Parse storage mode from string

        Args:
            value: String like "dev", "development", "prod", "production", etc.

        Returns:
            StorageMode enum value

        Raises:
            ValueError: If value doesn't match any mode
        """
        value_lower = value.lower().strip()

        # Handle common aliases
        if value_lower in ("dev", "development", "local"):
            return cls.DEV
        elif value_lower in ("test", "testing", "ci"):
            return cls.TEST
        elif value_lower in ("prod", "production", "live"):
            return cls.PROD
        else:
            raise ValueError(
                f"Invalid storage mode: {value}. "
                f"Valid values: dev, test, prod (or their full names)"
            )


@dataclass
class StorageConfig:
    """Storage configuration with mode-based defaults

    Provides automatic backend selection based on environment mode:

    - DEV mode:
        - Backend: Session.context (in-memory)
        - Setup: None required
        - Persistence: None (lost on restart)
        - Use case: Local development, experimentation

    - TEST mode:
        - Backend: Session.context (isolated in-memory)
        - Setup: None required
        - Persistence: None (isolated per test)
        - Use case: Unit tests, CI/CD pipelines

    - PROD mode:
        - Backend: PostgresMemory (persistent)
        - Setup: PostgreSQL database required
        - Persistence: Full ACID guarantees
        - Use case: Production deployments, multi-agent coordination

    Attributes:
        mode: Environment mode (DEV, TEST, PROD)
        database_url: PostgreSQL connection string (required for PROD)
        redis_host: Redis host (optional, for RedisMemory)
        redis_port: Redis port (optional)
        redis_password: Redis password (optional)
        min_connections: Min database pool connections (PROD only)
        max_connections: Max database pool connections (PROD only)
        connection_timeout: Database connection timeout in seconds
        pool_recycle: Connection recycle time in seconds
        custom_config: Additional custom configuration
    """

    mode: StorageMode = StorageMode.DEV

    # PostgreSQL configuration (PROD mode)
    database_url: Optional[str] = None
    min_connections: int = 2
    max_connections: int = 10
    connection_timeout: int = 30
    pool_recycle: int = 3600

    # Redis configuration (optional high-speed cache)
    redis_host: Optional[str] = None
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0

    # Additional configuration
    custom_config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.mode == StorageMode.PROD and not self.database_url:
            raise ValueError(
                "Production mode requires database_url. "
                "Set DATABASE_URL environment variable or pass database_url parameter."
            )

    @classmethod
    def from_environment(cls) -> "StorageConfig":
        """Create configuration by auto-detecting environment

        Environment detection priority:
        1. AQE_STORAGE_MODE (explicit override)
        2. ENVIRONMENT (common in Docker, cloud platforms)
        3. NODE_ENV (Node.js convention, often used in polyglot projects)
        4. Default to DEV if none set

        Also reads connection parameters from environment:
        - DATABASE_URL: PostgreSQL connection string
        - REDIS_HOST, REDIS_PORT, REDIS_PASSWORD: Redis configuration
        - DB_POOL_SIZE, DB_POOL_MAX_OVERFLOW: Connection pool settings

        Returns:
            StorageConfig instance with environment-based settings

        Example:
            ```bash
            # Development (default)
            config = StorageConfig.from_environment()  # mode=DEV

            # Production
            export AQE_STORAGE_MODE=production
            export DATABASE_URL=postgresql://user:pass@localhost:5432/db
            config = StorageConfig.from_environment()  # mode=PROD

            # Testing
            export ENVIRONMENT=testing
            config = StorageConfig.from_environment()  # mode=TEST
            ```
        """
        # 1. Detect mode from environment
        mode_str = (
            os.getenv("AQE_STORAGE_MODE")
            or os.getenv("ENVIRONMENT")
            or os.getenv("NODE_ENV")
            or "development"
        )

        try:
            mode = StorageMode.from_string(mode_str)
        except ValueError:
            logger.warning(
                f"Invalid environment mode '{mode_str}', defaulting to DEV. "
                f"Valid values: dev, test, prod"
            )
            mode = StorageMode.DEV

        logger.info(f"Storage mode detected: {mode.value} (from: {mode_str})")

        # 2. Read connection parameters from environment
        database_url = os.getenv("DATABASE_URL")

        # PostgreSQL pool configuration
        min_connections = int(os.getenv("DB_POOL_SIZE", "2"))
        max_connections = int(os.getenv("DB_POOL_MAX_OVERFLOW", "10"))
        connection_timeout = int(os.getenv("DB_CONNECTION_TIMEOUT", "30"))
        pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))

        # Redis configuration
        redis_host = os.getenv("REDIS_HOST")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD")
        redis_db = int(os.getenv("REDIS_DB", "0"))

        # 3. Production mode validation
        if mode == StorageMode.PROD and not database_url:
            logger.error(
                "Production mode requires DATABASE_URL environment variable. "
                "Example: postgresql://user:pass@localhost:5432/lionagi_qe"
            )
            raise ValueError(
                "Production mode requires DATABASE_URL environment variable"
            )

        return cls(
            mode=mode,
            database_url=database_url,
            min_connections=min_connections,
            max_connections=max_connections,
            connection_timeout=connection_timeout,
            pool_recycle=pool_recycle,
            redis_host=redis_host,
            redis_port=redis_port,
            redis_password=redis_password,
            redis_db=redis_db,
        )

    @classmethod
    def for_development(cls) -> "StorageConfig":
        """Create development configuration

        Uses Session.context (in-memory) with zero setup required.
        Perfect for local development and experimentation.

        Returns:
            StorageConfig configured for development

        Example:
            ```python
            config = StorageConfig.for_development()
            orchestrator = QEOrchestrator.from_config(config)
            ```
        """
        return cls(mode=StorageMode.DEV)

    @classmethod
    def for_testing(cls) -> "StorageConfig":
        """Create testing configuration

        Uses Session.context (isolated in-memory) for fast, isolated tests.
        No persistence, no external dependencies.

        Returns:
            StorageConfig configured for testing

        Example:
            ```python
            # In your test fixtures
            @pytest.fixture
            def orchestrator():
                config = StorageConfig.for_testing()
                return QEOrchestrator.from_config(config)
            ```
        """
        return cls(mode=StorageMode.TEST)

    @classmethod
    def for_production(
        cls,
        database_url: str,
        min_connections: int = 5,
        max_connections: int = 20
    ) -> "StorageConfig":
        """Create production configuration

        Uses PostgresMemory with full ACID guarantees and persistence.
        Requires PostgreSQL database setup.

        Args:
            database_url: PostgreSQL connection string
            min_connections: Minimum pool size
            max_connections: Maximum pool size

        Returns:
            StorageConfig configured for production

        Example:
            ```python
            config = StorageConfig.for_production(
                database_url="postgresql://qe_agent:pass@localhost:5432/lionagi_qe",
                min_connections=10,
                max_connections=50
            )
            orchestrator = QEOrchestrator.from_config(config)
            ```
        """
        return cls(
            mode=StorageMode.PROD,
            database_url=database_url,
            min_connections=min_connections,
            max_connections=max_connections
        )

    def get_memory_backend_config(self) -> Dict[str, Any]:
        """Get memory backend configuration for BaseQEAgent

        Returns configuration dict suitable for passing to BaseQEAgent's
        memory_config parameter.

        Returns:
            Dict with 'type' and backend-specific parameters

        Example:
            ```python
            config = StorageConfig.from_environment()
            memory_config = config.get_memory_backend_config()

            agent = TestGeneratorAgent(
                agent_id="test-gen",
                model=model,
                memory_config=memory_config
            )
            ```
        """
        if self.mode in (StorageMode.DEV, StorageMode.TEST):
            return {"type": "session"}

        elif self.mode == StorageMode.PROD:
            return {
                "type": "postgres",
                "database_url": self.database_url,
                "min_connections": self.min_connections,
                "max_connections": self.max_connections,
                "connection_timeout": self.connection_timeout,
                "pool_recycle": self.pool_recycle,
            }

        else:
            raise ValueError(f"Unknown storage mode: {self.mode}")

    def get_description(self) -> str:
        """Get human-readable description of current configuration

        Returns:
            Multi-line string describing the configuration
        """
        if self.mode == StorageMode.DEV:
            return (
                "Development Mode (Session.context)\n"
                "- Backend: In-memory (zero setup)\n"
                "- Persistence: None (lost on restart)\n"
                "- Use case: Local development, experimentation"
            )

        elif self.mode == StorageMode.TEST:
            return (
                "Testing Mode (Session.context)\n"
                "- Backend: In-memory (isolated per test)\n"
                "- Persistence: None (clean slate per test)\n"
                "- Use case: Unit tests, CI/CD pipelines"
            )

        elif self.mode == StorageMode.PROD:
            db_host = self._extract_host_from_url(self.database_url)
            return (
                f"Production Mode (PostgresMemory)\n"
                f"- Backend: PostgreSQL ({db_host})\n"
                f"- Persistence: Full ACID guarantees\n"
                f"- Pool size: {self.min_connections}-{self.max_connections} connections\n"
                f"- Use case: Production deployments, multi-agent coordination"
            )

        else:
            return f"Unknown mode: {self.mode}"

    def _extract_host_from_url(self, url: Optional[str]) -> str:
        """Extract host from database URL for display

        Args:
            url: Database connection URL

        Returns:
            Hostname or 'unknown'
        """
        if not url:
            return "unknown"

        try:
            # Simple extraction: postgresql://user:pass@host:port/db
            if "@" in url:
                after_at = url.split("@")[1]
                host_port = after_at.split("/")[0]
                return host_port
            return "unknown"
        except Exception:
            return "unknown"
