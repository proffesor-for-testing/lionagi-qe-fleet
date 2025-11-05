"""
LionAGI QE Fleet - Python Database Connection Examples

This module demonstrates various ways to connect to PostgreSQL and Redis
from Python applications for Q-Learning development.

Usage:
    python python-examples.py [command]

Commands:
    test-postgres   Test PostgreSQL connection
    test-redis      Test Redis connection
    load-env        Load environment variables and show connection strings
    create-tables   Create example tables (requires running container)
"""

import os
import asyncio
import json
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import psycopg2
    from psycopg2 import pool
except ImportError:
    psycopg2 = None

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
except ImportError:
    create_engine = None

try:
    from sqlalchemy.pool import NullPool, QueuePool
except ImportError:
    NullPool = QueuePool = None

try:
    import redis
except ImportError:
    redis = None

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


class PostgresqlConnector:
    """PostgreSQL connection helper"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "lionagi_qe_learning",
        user: str = "qe_agent",
        password: str = "qe_secure_password_123",
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

    @property
    def connection_string(self) -> str:
        """Get standard connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def async_connection_string(self) -> str:
        """Get async connection string for asyncpg"""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def psycopg2_params(self) -> Dict[str, Any]:
        """Get psycopg2 connection parameters"""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
        }

    def create_engine(self, **kwargs):
        """Create SQLAlchemy engine with recommended settings"""
        if create_engine is None:
            raise ImportError("SQLAlchemy not installed")

        defaults = {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_recycle": 3600,
            "pool_pre_ping": True,
            "echo": False,
        }
        defaults.update(kwargs)

        return create_engine(self.connection_string, **defaults)

    def create_async_engine(self, **kwargs):
        """Create async SQLAlchemy engine"""
        if create_async_engine is None:
            raise ImportError("SQLAlchemy[asyncio] not installed")

        defaults = {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_recycle": 3600,
            "echo": False,
        }
        defaults.update(kwargs)

        return create_async_engine(self.async_connection_string, **defaults)

    def test_connection(self) -> bool:
        """Test connection with psycopg2"""
        if psycopg2 is None:
            print("ERROR: psycopg2 not installed")
            return False

        try:
            conn = psycopg2.connect(**self.psycopg2_params)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result[0] == 1
        except Exception as e:
            print(f"Connection failed: {e}")
            return False


class RedisConnector:
    """Redis connection helper"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str = "redis_secure_password_123",
        db: int = 0,
    ):
        self.host = host
        self.port = port
        self.password = password
        self.db = db

    @property
    def connection_string(self) -> str:
        """Get connection string"""
        return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"

    def create_client(self):
        """Create Redis client"""
        if redis is None:
            raise ImportError("redis-py not installed")

        return redis.Redis(
            host=self.host,
            port=self.port,
            password=self.password,
            db=self.db,
            decode_responses=True,
        )

    def test_connection(self) -> bool:
        """Test connection"""
        if redis is None:
            print("ERROR: redis-py not installed")
            return False

        try:
            client = self.create_client()
            pong = client.ping()
            return pong == True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False


class Config:
    """Configuration loader from environment"""

    @staticmethod
    def load_from_env(env_file: Optional[str] = None) -> tuple:
        """Load configuration from environment or .env file"""

        if env_file and load_dotenv:
            load_dotenv(env_file)
        elif load_dotenv:
            # Try to load .env from current directory or parent
            if Path(".env").exists():
                load_dotenv(".env")
            elif Path("../.env").exists():
                load_dotenv("../.env")
            elif Path("docker/.env").exists():
                load_dotenv("docker/.env")

        postgres = PostgresqlConnector(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            database=os.getenv("POSTGRES_DB", "lionagi_qe_learning"),
            user=os.getenv("POSTGRES_USER", "qe_agent"),
            password=os.getenv("POSTGRES_PASSWORD", "qe_secure_password_123"),
        )

        redis_conn = RedisConnector(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD", "redis_secure_password_123"),
            db=int(os.getenv("REDIS_DB", 0)),
        )

        return postgres, redis_conn


# ============================================================================
# Usage Examples
# ============================================================================


def example_basic_sqlalchemy():
    """Basic SQLAlchemy connection"""
    print("\n=== SQLAlchemy Basic Example ===")

    postgres = PostgresqlConnector()
    engine = postgres.create_engine(echo=False)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✓ Query result: {row}")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        engine.dispose()


async def example_async_sqlalchemy():
    """Async SQLAlchemy example"""
    print("\n=== SQLAlchemy Async Example ===")

    postgres = PostgresqlConnector()
    engine = postgres.create_async_engine()

    try:
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✓ Query result: {row}")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await engine.dispose()


def example_redis_basic():
    """Basic Redis connection"""
    print("\n=== Redis Basic Example ===")

    redis_conn = RedisConnector()

    try:
        client = redis_conn.create_client()

        # Store a Q-value
        q_value = {
            "agent_id": "qe-test-generator",
            "state": "s1",
            "values": [0.5, 0.3, 0.2],
        }
        client.set(f"q_value:{q_value['agent_id']}:{q_value['state']}", json.dumps(q_value))
        print(f"✓ Stored Q-value")

        # Retrieve the Q-value
        stored = client.get(f"q_value:{q_value['agent_id']}:{q_value['state']}")
        retrieved = json.loads(stored)
        print(f"✓ Retrieved Q-value: {retrieved}")

        # Set expiration (24 hours)
        client.expire(f"q_value:{q_value['agent_id']}:{q_value['state']}", 86400)
        print(f"✓ Set expiration to 24 hours")
    except Exception as e:
        print(f"✗ Error: {e}")


def example_postgres_queries():
    """PostgreSQL query examples"""
    print("\n=== PostgreSQL Query Examples ===")

    postgres = PostgresqlConnector()
    engine = postgres.create_engine()

    try:
        with engine.connect() as conn:
            # Check database size
            result = conn.execute(
                text("SELECT pg_size_pretty(pg_database_size('lionagi_qe_learning')) as size")
            )
            print(f"✓ Database size: {result.fetchone()[0]}")

            # Count tables
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'qlearning'"
                )
            )
            count = result.fetchone()[0]
            print(f"✓ Q-Learning tables: {count}")

            # List schemas
            result = conn.execute(text("SELECT schema_name FROM information_schema.schemata"))
            schemas = [row[0] for row in result.fetchall()]
            print(f"✓ Schemas: {', '.join(schemas)}")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        engine.dispose()


def main():
    """Run examples"""
    import sys

    print("LionAGI QE Fleet - Python Connection Examples")
    print("=" * 50)

    # Load configuration
    postgres, redis_conn = Config.load_from_env()

    print("\nConnection Strings:")
    print(f"PostgreSQL: {postgres.connection_string}")
    print(f"PostgreSQL (Async): {postgres.async_connection_string}")
    print(f"Redis: {redis_conn.connection_string}")

    # Run tests if requested
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "test-postgres":
            print("\nTesting PostgreSQL connection...")
            if postgres.test_connection():
                print("✓ PostgreSQL connection successful!")
            else:
                print("✗ PostgreSQL connection failed")

        elif command == "test-redis":
            print("\nTesting Redis connection...")
            if redis_conn.test_connection():
                print("✓ Redis connection successful!")
            else:
                print("✗ Redis connection failed")

        elif command == "load-env":
            print("\nEnvironment Variables Loaded")

        elif command == "examples":
            example_basic_sqlalchemy()
            example_postgres_queries()
            example_redis_basic()
            # Run async example
            asyncio.run(example_async_sqlalchemy())

        else:
            print(f"Unknown command: {command}")
            print("Available commands: test-postgres, test-redis, load-env, examples")

    else:
        # Run all examples
        print("\nRunning examples...")
        try:
            example_basic_sqlalchemy()
            example_postgres_queries()
            example_redis_basic()
            asyncio.run(example_async_sqlalchemy())
        except Exception as e:
            print(f"Error running examples: {e}")


if __name__ == "__main__":
    main()
