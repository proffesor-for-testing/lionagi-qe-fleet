# LionAGI QE Fleet Refactoring Plan

**Based on**: Ocean's Technical Handoff (LionAGI Creator)
**Date**: 2025-11-05
**Status**: Ready for Implementation (Phase 2: 50% Complete!)
**Estimated Timeline**: ~~11-17 days~~ → **9-12 days** (single developer)

---

## Executive Summary

**✅ Update (2025-11-05)**: We've already completed 50% of Phase 2 (Persistence) through the Q-Learning implementation:
- PostgreSQL container running on localhost:5432
- Database `lionagi_qe_learning` initialized
- Connection pooling with asyncpg (2-10 connections)
- DatabaseManager class ready to reuse
- 7 tables created for learning data

**Revised Timeline**: ~~11-17 days~~ → **9-12 days** (2-3 days saved!)

---

After analyzing the codebase, we found:
- **Actual wrapper LOC**: 1,412 lines (not 2,000-2,300 as estimated)
- **QEOrchestrator is CORRECT**: Already uses LionAGI Builder/Session properly
- **QEMemory is LIMITED**: In-memory only (161 LOC), needs persistence
- **QETask is EMBEDDED**: Used in 68 files, minimal abstraction (45 LOC)
- **QEFleet is REDUNDANT**: Thin wrapper (541 LOC) that can be removed

**Key Insight**: The orchestration layer is actually well-designed and uses LionAGI correctly. The main issues are:
1. QEFleet wrapper adds unnecessary indirection
2. QEMemory lacks persistence
3. Examples don't showcase LionAGI patterns directly

---

## Architecture Analysis

### Current Component Analysis

#### 1. QEFleet (541 LOC) - **REMOVE**
**Location**: `src/lionagi_qe/core/fleet.py`
**Usage**: 27 files (5 examples, 2 tests, 20+ docs)

**What it does**:
```python
class QEFleet:
    def __init__(self):
        self.memory = QEMemory()
        self.router = ModelRouter()
        self.orchestrator = QEOrchestrator(memory, router)

    async def execute(self, agent_id, task):
        return await self.orchestrator.execute_agent(agent_id, task)  # Just delegates

    async def execute_pipeline(self, pipeline, context):
        return await self.orchestrator.execute_pipeline(pipeline, context)  # Just delegates
```

**Ocean's Assessment**: "Wrapper adds no value"
**Our Assessment**: ✅ CORRECT - It's just a delegator. Users can use QEOrchestrator or Session directly.

**Impact of Removal**:
- 27 files need updates (mostly docs and examples)
- All `QEFleet()` → `QEOrchestrator()` or direct `Session()`
- Breaking change but easy migration path

---

#### 2. QEOrchestrator (665 LOC) - **KEEP & ENHANCE**
**Location**: `src/lionagi_qe/core/orchestrator.py`
**Usage**: 7 files (2 tests, 1 internal use by fleet.py)

**What it does**:
```python
class QEOrchestrator:
    def __init__(self, memory, router, enable_learning):
        self.session = Session()  # ✅ Uses LionAGI Session
        self.agents = {}

    async def execute_pipeline(self, pipeline, context):
        builder = Builder(f"QE_Pipeline_{len(pipeline)}_agents")  # ✅ Uses Builder
        for agent_id in pipeline:
            node = builder.add_operation("communicate", ...)
        result = await self.session.flow(builder.get_graph())  # ✅ Correct pattern
        return result
```

**Ocean's Assessment**: "Reimplements workflow logic"
**Our Assessment**: ❌ INCORRECT - It's actually USING LionAGI Builder/Session correctly!

**Recommendation**:
- **KEEP** the orchestrator - it provides valuable convenience methods
- **ENHANCE** with more Builder pattern examples
- **DEPRECATE** some wrapper methods with migration guide
- **ADD** direct Session/Builder examples alongside

**Why Keep It**:
1. Provides high-level workflows (pipeline, parallel, fan-out/fan-in, conditional)
2. Already uses LionAGI patterns correctly
3. Adds useful metrics and agent registry
4. Low usage (7 files) means minimal migration pain if we keep it

---

#### 3. QEMemory (161 LOC) - **REPLACE WITH PERSISTENCE**
**Location**: `src/lionagi_qe/core/memory.py`
**Usage**: 26 files (all 18 agents + tests)

**What it does**:
```python
class QEMemory:
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}  # ❌ In-memory only
        self._locks: Dict[str, asyncio.Lock] = {}
        self._access_log: List[Dict[str, Any]] = []  # ❌ Unbounded (memory leak)

    async def store(self, key, value, ttl=None, partition="default"):
        self._store[key] = {"value": value, "timestamp": ..., "ttl": ttl}  # ❌ Lost on restart
```

**Ocean's Assessment**: "No persistence, memory leak"
**Our Assessment**: ✅ CORRECT - 100% in-memory, no durability

**Impact of Removal**:
- 26 files need updates (all agents pass `memory=fleet.memory`)
- Agents receive `QEMemory` in `__init__`
- Need backward-compatible migration

**Replacement Strategy**:

**Phase 2A: Add Persistence Backend**
```python
# New: src/lionagi_qe/persistence/redis_memory.py
class RedisMemory:
    def __init__(self, host="localhost", port=6379):
        self.client = redis.Redis(host=host, port=port, decode_responses=True)

    async def store(self, key: str, value: Any, ttl: int = 3600):
        self.client.setex(key, ttl, json.dumps(value))

    async def retrieve(self, key: str) -> Any:
        data = self.client.get(key)
        return json.loads(data) if data else None
```

**Phase 2B: Backward-Compatible BaseQEAgent**
```python
# Modified: src/lionagi_qe/core/base_agent.py
class BaseQEAgent:
    def __init__(self, agent_id, model, memory=None, **kwargs):
        self.agent_id = agent_id
        self.model = model

        # Support both in-memory (dev) and persistent (prod)
        if memory is None:
            from lionagi import Session
            self.memory = Session().context  # In-memory via Session
        elif isinstance(memory, QEMemory):
            # Deprecated path - warn user
            warnings.warn("QEMemory is deprecated, use RedisMemory or Session.context")
            self.memory = memory
        else:
            # New persistence backends (Redis, PostgreSQL)
            self.memory = memory
```

---

#### 4. QETask (45 LOC) - **KEEP OR SIMPLIFY**
**Location**: `src/lionagi_qe/core/task.py`
**Usage**: 68 files (all agents, all tests, all examples)

**What it does**:
```python
class QETask(BaseModel):
    task_id: str
    task_type: str
    context: Dict[str, Any]
    priority: Literal["low", "medium", "high", "critical"]
    status: Literal["pending", "in_progress", "completed", "failed"]
    result: Optional[Dict[str, Any]]
```

**Ocean's Assessment**: "Custom message abstraction vs Instruct pattern"
**Our Assessment**: ⚠️ PARTIAL - It's minimal (45 LOC) but used everywhere (68 files)

**Recommendation**:
- **KEEP** QETask for now - it's just a Pydantic model for status tracking
- **OPTIONAL**: Add LionAGI Instruct examples alongside
- **LOW PRIORITY**: Not worth migrating 68 files for 45 LOC

**Rationale**:
- QETask provides value: status tracking, priority, error handling
- LionAGI Instruct is for AI instructions, not task management
- Migration effort (68 files) > benefit (remove 45 LOC)

---

## Refactoring Phases

### Phase 1: Remove QEFleet & Simplify API (HIGH PRIORITY)

**Timeline**: 2-3 days
**LOC Reduction**: 541 lines
**Files to Update**: 27 files

#### Step 1.1: Delete QEFleet

**Files to Delete**:
- `src/lionagi_qe/core/fleet.py` (541 LOC)

**Files to Update**:
```bash
# Examples (5 files)
examples/01_basic_usage.py
examples/02_sequential_pipeline.py
examples/03_parallel_execution.py
examples/04_fan_out_fan_in.py
examples/streaming_usage.py

# Tests (2 files)
tests/test_core/test_fleet.py  # Delete or rename to test_orchestrator.py
tests/conftest.py

# Source (2 files)
src/lionagi_qe/__init__.py  # Remove QEFleet export
src/lionagi_qe/mcp/mcp_server.py

# Docs (~18 files)
README.md
USAGE_GUIDE.md
docs/index.md
docs/quickstart/*.md
docs/reference/*.md
docs/advanced/*.md
```

#### Step 1.2: Update Examples

**Before** (examples/01_basic_usage.py):
```python
from lionagi_qe import QEFleet, QETask
from lionagi_qe.agents import TestGeneratorAgent

fleet = QEFleet(enable_routing=True)
await fleet.initialize()

agent = TestGeneratorAgent(
    agent_id="test-generator",
    model=model,
    memory=fleet.memory  # QEMemory
)

fleet.register_agent(agent)
result = await fleet.execute("test-generator", task)
```

**After - Option A** (Use QEOrchestrator):
```python
from lionagi import iModel
from lionagi_qe import QEOrchestrator, QETask
from lionagi_qe.agents import TestGeneratorAgent
from lionagi_qe.persistence import RedisMemory  # NEW

# Initialize components
memory = RedisMemory()  # or Session().context for in-memory
router = ModelRouter(enable_routing=True)
orchestrator = QEOrchestrator(memory, router, enable_learning=True)

# Create agent
agent = TestGeneratorAgent(
    agent_id="test-generator",
    model=iModel(provider="openai", model="gpt-4o-mini"),
    memory=memory
)

orchestrator.register_agent(agent)
result = await orchestrator.execute_agent("test-generator", task)
```

**After - Option B** (Direct LionAGI Session - RECOMMENDED):
```python
from lionagi import Session, iModel, Branch
from lionagi_qe.agents import TestGeneratorAgent

# Initialize session
session = Session()
await session.initiate()

# Create agent branch
model = iModel(provider="openai", model="gpt-4o-mini")
test_gen_branch = Branch(
    name="test-generator",
    imodel=model,
    system="You are an expert test generation agent..."
)

# Register agent branch with session
session.branches["test-generator"] = test_gen_branch

# Execute using session
result = await session.instruct(
    instruction="Generate pytest tests for the following code",
    context={
        "code": code_to_test,
        "framework": "pytest",
        "test_type": "unit"
    },
    model="gpt-4o-mini",
    response_format=GeneratedTest  # Pydantic model
)

# Store results in session context (replaces QEMemory)
session.context.set("aqe/test-generator/results", result)
```

**After - Option C** (LionAGI Builder for Workflows):
```python
from lionagi import Session, Builder, iModel
from lionagi_qe.agents import TestGeneratorAgent, TestExecutorAgent, CoverageAnalyzerAgent

# Initialize session
session = Session()
await session.initiate()

# Create agents as branches
test_gen = Branch(name="test-generator", imodel=model, system="...")
test_exec = Branch(name="test-executor", imodel=model, system="...")
coverage = Branch(name="coverage-analyzer", imodel=model, system="...")

# Register branches
session.branches.update({
    "test-generator": test_gen,
    "test-executor": test_exec,
    "coverage-analyzer": coverage
})

# Build workflow using Builder
builder = Builder("QE_Pipeline")

# Sequential pipeline
node1 = builder.add_operation(
    "communicate",
    branch=test_gen,
    instruction="Generate comprehensive pytest tests",
    context={"code": code_to_test}
)

node2 = builder.add_operation(
    "communicate",
    branch=test_exec,
    depends_on=[node1],
    instruction="Execute the generated tests",
    context={"inherit_from": node1}
)

node3 = builder.add_operation(
    "communicate",
    branch=coverage,
    depends_on=[node2],
    instruction="Analyze test coverage and identify gaps"
)

# Execute workflow
result = await session.flow(builder.get_graph())
```

#### Step 1.3: Update __init__.py

**Before** (`src/lionagi_qe/__init__.py`):
```python
from lionagi_qe.core.fleet import QEFleet
from lionagi_qe.core.orchestrator import QEOrchestrator
from lionagi_qe.core.task import QETask
from lionagi_qe.core.memory import QEMemory

__all__ = [
    "QEFleet",
    "QEOrchestrator",
    "QETask",
    "QEMemory",
]
```

**After**:
```python
from lionagi_qe.core.orchestrator import QEOrchestrator
from lionagi_qe.core.task import QETask
from lionagi_qe.core.memory import QEMemory  # Deprecated - use persistence

# New persistence backends
from lionagi_qe.persistence import RedisMemory, PostgresMemory

__all__ = [
    "QEOrchestrator",  # Convenience orchestrator (optional)
    "QETask",  # Task tracking (keep for now)
    "QEMemory",  # DEPRECATED - use RedisMemory or Session.context
    "RedisMemory",  # NEW
    "PostgresMemory",  # NEW
]

# Deprecation warning
import warnings
def QEFleet(*args, **kwargs):
    warnings.warn(
        "QEFleet is deprecated. Use QEOrchestrator or Session directly. "
        "See docs/migration/fleet-to-session.md",
        DeprecationWarning
    )
    return QEOrchestrator(*args, **kwargs)
```

#### Step 1.4: Update Tests

**Delete**: `tests/test_core/test_fleet.py`
**Keep**: `tests/test_core/test_orchestrator.py` (add more tests)

**New Test Strategy**:
```python
# tests/test_core/test_session_patterns.py
import pytest
from lionagi import Session, Builder

@pytest.mark.asyncio
async def test_direct_session_usage():
    """Test using Session directly without QEFleet"""
    session = Session()
    await session.initiate()

    result = await session.instruct(
        instruction="Generate unit tests",
        context={"code": "def add(a, b): return a + b"}
    )

    assert result is not None

@pytest.mark.asyncio
async def test_builder_workflow():
    """Test Builder workflow pattern"""
    session = Session()
    await session.initiate()

    builder = Builder("test_workflow")
    node = builder.add_operation("communicate", instruction="Test task")

    result = await session.flow(builder.get_graph())
    assert result is not None
```

---

### Phase 2: Add Persistence Layer (MEDIUM PRIORITY)

**Timeline**: ~~3-5 days~~ **1-2 days** ✅ (50% complete - PostgreSQL infrastructure already exists!)
**Benefit**: Production-ready state management
**Files to Create**: 3-4 new files (down from 6 - reusing existing infrastructure)

**✅ Already Completed** (from Q-Learning implementation):
- PostgreSQL container running on localhost:5432
- Database `lionagi_qe_learning` initialized
- Connection pooling with asyncpg (2-10 connections)
- DatabaseManager class in `src/lionagi_qe/learning/db_manager.py`
- 7 tables created: agent_types, sessions, q_values, trajectories, rewards, patterns, agent_states

**🔨 Remaining Work**:
- Add 1 more table: `qe_memory` for general-purpose memory
- Create `PostgresMemory` wrapper class (reuses existing DatabaseManager)
- Add `RedisMemory` as optional alternative
- Update `BaseQEAgent` to support both backends

---

#### Step 2.0: Extend Existing PostgreSQL Database (NEW - Uses existing infrastructure!)

**Add Table**: `database/schema/memory_extension.sql` (~50 LOC)

```sql
-- ============================================================================
-- QE Memory Extension - General Purpose Memory Storage
-- ============================================================================
-- Extends existing lionagi_qe_learning database with memory table
-- Reuses existing connection pool and infrastructure

CREATE TABLE IF NOT EXISTS qe_memory (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    partition VARCHAR(50) DEFAULT 'default',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Indexes for performance
    CONSTRAINT qe_memory_key_format CHECK (key ~ '^aqe/.*')
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_qe_memory_partition ON qe_memory(partition);
CREATE INDEX IF NOT EXISTS idx_qe_memory_expires ON qe_memory(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_qe_memory_key_prefix ON qe_memory(key text_pattern_ops);

-- Auto-cleanup expired entries (runs every hour)
CREATE OR REPLACE FUNCTION cleanup_expired_memory()
RETURNS void AS $$
BEGIN
    DELETE FROM qe_memory WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Create cleanup job (requires pg_cron extension, optional)
-- SELECT cron.schedule('cleanup-memory', '0 * * * *', 'SELECT cleanup_expired_memory();');

COMMENT ON TABLE qe_memory IS 'General-purpose persistent memory for QE agents (aqe/* namespace)';
COMMENT ON COLUMN qe_memory.key IS 'Memory key (e.g., aqe/test-plan/generated)';
COMMENT ON COLUMN qe_memory.partition IS 'Logical partition for organization';
COMMENT ON COLUMN qe_memory.expires_at IS 'Automatic expiration (NULL = never expires)';
```

**Apply Migration**:
```bash
# Add the new table to existing database
sudo docker exec -i lionagi-qe-postgres psql -U qe_agent -d lionagi_qe_learning \
  < database/schema/memory_extension.sql

# Verify
sudo docker exec lionagi-qe-postgres psql -U qe_agent -d lionagi_qe_learning -c "\dt"
# Should now show 8 tables (7 existing + qe_memory)
```

**New File**: `src/lionagi_qe/persistence/postgres_memory.py` (~120 LOC - simplified!)

```python
"""PostgreSQL-based persistent memory - Reuses Q-Learning infrastructure"""

from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from lionagi_qe.learning.db_manager import DatabaseManager
import json

class PostgresMemory:
    """PostgreSQL-backed persistent memory

    Reuses the existing DatabaseManager and connection pool from Q-learning.
    All operations use the same PostgreSQL database: lionagi_qe_learning

    Benefits:
    - No additional database setup needed
    - Shares connection pool (efficient resource usage)
    - Same infrastructure for Q-learning and general memory
    - Production-ready (already tested with Q-learning)
    """

    def __init__(self, db_manager: DatabaseManager):
        """Initialize with existing DatabaseManager

        Args:
            db_manager: Existing DatabaseManager instance (from Q-learning)

        Example:
            from lionagi_qe.learning import DatabaseManager

            db_manager = DatabaseManager(
                database_url="postgresql://qe_agent:password@localhost:5432/lionagi_qe_learning",
                min_connections=2,
                max_connections=10
            )
            await db_manager.connect()

            memory = PostgresMemory(db_manager)
        """
        self.db = db_manager

    async def store(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = 3600,
        partition: str = "default"
    ):
        """Store value with TTL

        Args:
            key: Storage key (must start with 'aqe/')
            value: Value to store (will be JSON serialized)
            ttl: Time-to-live in seconds (None = never expire)
            partition: Logical partition
        """
        if not key.startswith("aqe/"):
            raise ValueError("Key must start with 'aqe/' namespace")

        expires_at = None
        if ttl:
            expires_at = datetime.now() + timedelta(seconds=ttl)

        async with self.db.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO qe_memory (key, value, partition, expires_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (key)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    partition = EXCLUDED.partition,
                    expires_at = EXCLUDED.expires_at,
                    created_at = NOW()
            """, key, json.dumps(value), partition, expires_at)

    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value from PostgreSQL

        Args:
            key: Storage key

        Returns:
            Stored value or None if not found/expired
        """
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT value FROM qe_memory
                WHERE key = $1
                AND (expires_at IS NULL OR expires_at > NOW())
            """, key)

            if row:
                return json.loads(row["value"])
            return None

    async def search(self, pattern: str) -> Dict[str, Any]:
        """Search keys by SQL pattern

        Args:
            pattern: Pattern to match (e.g., 'aqe/coverage/*')

        Returns:
            Dict of matching keys and values
        """
        # Convert glob pattern to SQL LIKE pattern
        sql_pattern = pattern.replace("*", "%").replace("?", "_")

        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT key, value FROM qe_memory
                WHERE key LIKE $1
                AND (expires_at IS NULL OR expires_at > NOW())
            """, sql_pattern)

            return {
                row["key"]: json.loads(row["value"])
                for row in rows
            }

    async def delete(self, key: str):
        """Delete key"""
        async with self.db.pool.acquire() as conn:
            await conn.execute("DELETE FROM qe_memory WHERE key = $1", key)

    async def clear_partition(self, partition: str):
        """Clear all keys in partition"""
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM qe_memory WHERE partition = $1",
                partition
            )

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys with optional prefix"""
        async with self.db.pool.acquire() as conn:
            if prefix:
                rows = await conn.fetch(
                    "SELECT key FROM qe_memory WHERE key LIKE $1",
                    f"{prefix}%"
                )
            else:
                rows = await conn.fetch("SELECT key FROM qe_memory")

            return [row["key"] for row in rows]

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        async with self.db.pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM qe_memory")
            partitions = await conn.fetch("""
                SELECT partition, COUNT(*) as count
                FROM qe_memory
                GROUP BY partition
            """)

            return {
                "total_keys": total,
                "partitions": {
                    row["partition"]: row["count"]
                    for row in partitions
                }
            }
```

**Usage Example**:
```python
from lionagi_qe.learning import DatabaseManager
from lionagi_qe.persistence import PostgresMemory

# Reuse existing Q-learning database connection
db_manager = DatabaseManager(
    database_url="postgresql://qe_agent:qe_secure_password_123@localhost:5432/lionagi_qe_learning",
    min_connections=2,
    max_connections=10
)
await db_manager.connect()

# Create memory backend (reuses same connection pool!)
memory = PostgresMemory(db_manager)

# Use it like QEMemory
await memory.store("aqe/test-plan/results", test_results, ttl=3600)
results = await memory.retrieve("aqe/test-plan/results")
```

---

#### Step 2.1: Create Redis Backend (Optional Alternative)

**New File**: `src/lionagi_qe/persistence/redis_memory.py` (~150 LOC)

```python
"""Redis-based persistent memory backend"""

import redis
import json
from typing import Any, Dict, Optional, List
import asyncio

class RedisMemory:
    """Redis-backed persistent memory

    Provides:
    - Durable storage (survives restarts)
    - TTL support for automatic cleanup
    - Namespace pattern (aqe/*)
    - Atomic operations with locks
    - Connection pooling
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 10
    ):
        """Initialize Redis connection

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (optional)
            max_connections: Connection pool size
        """
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            decode_responses=True
        )
        self.client = redis.Redis(connection_pool=self.pool)
        self._locks: Dict[str, asyncio.Lock] = {}

    async def store(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = 3600,
        partition: str = "default"
    ):
        """Store value with TTL

        Args:
            key: Storage key (e.g., 'aqe/test-plan/generated')
            value: Value to store (will be JSON serialized)
            ttl: Time-to-live in seconds (None = never expire)
            partition: Logical partition (for organization)
        """
        # Add metadata
        data = {
            "value": value,
            "partition": partition,
            "created_at": self.client.time()[0]
        }

        serialized = json.dumps(data)

        if ttl:
            self.client.setex(key, ttl, serialized)
        else:
            self.client.set(key, serialized)

    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value from Redis

        Args:
            key: Storage key

        Returns:
            Stored value or None if not found
        """
        data = self.client.get(key)
        if data:
            parsed = json.loads(data)
            return parsed["value"]
        return None

    async def search(self, pattern: str) -> Dict[str, Any]:
        """Search keys by pattern

        Args:
            pattern: Redis pattern (e.g., 'aqe/coverage/*')

        Returns:
            Dict of matching keys and values
        """
        keys = self.client.keys(pattern)
        results = {}

        for key in keys:
            value = await self.retrieve(key)
            if value is not None:
                results[key] = value

        return results

    async def delete(self, key: str):
        """Delete key"""
        self.client.delete(key)

    async def clear_partition(self, partition: str):
        """Clear all keys in partition"""
        # Get all keys
        all_keys = self.client.keys("*")

        # Filter by partition
        to_delete = []
        for key in all_keys:
            data = self.client.get(key)
            if data:
                parsed = json.loads(data)
                if parsed.get("partition") == partition:
                    to_delete.append(key)

        # Delete in batch
        if to_delete:
            self.client.delete(*to_delete)

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys with optional prefix"""
        if prefix:
            return self.client.keys(f"{prefix}*")
        return self.client.keys("*")

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        info = self.client.info("keyspace")
        memory = self.client.info("memory")

        return {
            "total_keys": self.client.dbsize(),
            "memory_used": memory.get("used_memory_human"),
            "keyspace_info": info
        }

    def close(self):
        """Close Redis connection"""
        self.pool.disconnect()
```

#### Step 2.2: Create PostgreSQL Backend (Optional)

**New File**: `src/lionagi_qe/persistence/postgres_memory.py` (~200 LOC)

```python
"""PostgreSQL-based persistent memory backend"""

import asyncpg
import json
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta

class PostgresMemory:
    """PostgreSQL-backed persistent memory

    Schema:
        CREATE TABLE qe_memory (
            key VARCHAR(255) PRIMARY KEY,
            value JSONB NOT NULL,
            partition VARCHAR(50) DEFAULT 'default',
            created_at TIMESTAMP DEFAULT NOW(),
            expires_at TIMESTAMP,
            INDEX idx_partition (partition),
            INDEX idx_expires (expires_at)
        );
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "lionagi_qe",
        user: str = "qe_agent",
        password: str = "",
        min_size: int = 2,
        max_size: int = 10
    ):
        """Initialize PostgreSQL connection pool"""
        self.dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        self.pool = None
        self.min_size = min_size
        self.max_size = max_size

    async def connect(self):
        """Establish connection pool"""
        self.pool = await asyncpg.create_pool(
            self.dsn,
            min_size=self.min_size,
            max_size=self.max_size
        )

        # Create table if not exists
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS qe_memory (
                    key VARCHAR(255) PRIMARY KEY,
                    value JSONB NOT NULL,
                    partition VARCHAR(50) DEFAULT 'default',
                    created_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_partition ON qe_memory(partition);
                CREATE INDEX IF NOT EXISTS idx_expires ON qe_memory(expires_at);
            """)

    async def store(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = 3600,
        partition: str = "default"
    ):
        """Store value with TTL"""
        expires_at = None
        if ttl:
            expires_at = datetime.now() + timedelta(seconds=ttl)

        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO qe_memory (key, value, partition, expires_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (key)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    partition = EXCLUDED.partition,
                    expires_at = EXCLUDED.expires_at,
                    created_at = NOW()
            """, key, json.dumps(value), partition, expires_at)

    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value from PostgreSQL"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT value FROM qe_memory
                WHERE key = $1
                AND (expires_at IS NULL OR expires_at > NOW())
            """, key)

            if row:
                return json.loads(row["value"])
            return None

    async def search(self, pattern: str) -> Dict[str, Any]:
        """Search keys by SQL pattern"""
        # Convert regex pattern to SQL LIKE pattern
        sql_pattern = pattern.replace("*", "%").replace("?", "_")

        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT key, value FROM qe_memory
                WHERE key LIKE $1
                AND (expires_at IS NULL OR expires_at > NOW())
            """, sql_pattern)

            return {
                row["key"]: json.loads(row["value"])
                for row in rows
            }

    async def delete(self, key: str):
        """Delete key"""
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM qe_memory WHERE key = $1", key)

    async def clear_partition(self, partition: str):
        """Clear all keys in partition"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM qe_memory WHERE partition = $1",
                partition
            )

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys with optional prefix"""
        async with self.pool.acquire() as conn:
            if prefix:
                rows = await conn.fetch(
                    "SELECT key FROM qe_memory WHERE key LIKE $1",
                    f"{prefix}%"
                )
            else:
                rows = await conn.fetch("SELECT key FROM qe_memory")

            return [row["key"] for row in rows]

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        async with self.pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM qe_memory")
            partitions = await conn.fetch("""
                SELECT partition, COUNT(*) as count
                FROM qe_memory
                GROUP BY partition
            """)

            return {
                "total_keys": total,
                "partitions": {
                    row["partition"]: row["count"]
                    for row in partitions
                }
            }

    async def close(self):
        """Close connection pool"""
        await self.pool.close()
```

#### Step 2.3: Create Persistence Module

**New File**: `src/lionagi_qe/persistence/__init__.py`

```python
"""Persistent memory backends"""

from lionagi_qe.persistence.redis_memory import RedisMemory
from lionagi_qe.persistence.postgres_memory import PostgresMemory

__all__ = ["RedisMemory", "PostgresMemory"]
```

#### Step 2.4: Update pyproject.toml

```toml
[project.optional-dependencies]
persistence = [
    "redis>=5.0.0",
    "asyncpg>=0.29.0",  # PostgreSQL
]
```

#### Step 2.5: Update BaseQEAgent

**Modified**: `src/lionagi_qe/core/base_agent.py`

Add backward-compatible memory initialization:

```python
class BaseQEAgent:
    def __init__(
        self,
        agent_id: str,
        model: iModel,
        memory: Optional[Any] = None,  # Can be QEMemory, RedisMemory, PostgresMemory, or None
        skills: Optional[List[str]] = None,
        enable_learning: bool = False,
        q_learning_service: Optional[QLearningService] = None
    ):
        """Initialize base QE agent

        Args:
            agent_id: Unique agent identifier
            model: LionAGI iModel instance
            memory: Memory backend (None = Session.context, QEMemory = deprecated, RedisMemory/PostgresMemory = persistent)
            skills: List of skill names
            enable_learning: Enable Q-learning
            q_learning_service: Q-learning service instance
        """
        self.agent_id = agent_id
        self.model = model

        # Memory initialization with backward compatibility
        if memory is None:
            # Default: Use Session context (in-memory)
            from lionagi import Session
            self._session = Session()
            self.memory = self._session.context
        elif isinstance(memory, QEMemory):
            # Deprecated: Warn user
            warnings.warn(
                "QEMemory is deprecated and lacks persistence. "
                "Use RedisMemory or PostgresMemory for production. "
                "See docs/migration/memory-persistence.md",
                DeprecationWarning
            )
            self.memory = memory
        else:
            # New: RedisMemory, PostgresMemory, or custom backend
            self.memory = memory

        # Rest of initialization...
```

#### Step 2.6: Create Migration Guide

**New File**: `docs/migration/memory-persistence.md`

```markdown
# Migration Guide: QEMemory → Persistent Storage

## Why Migrate?

**QEMemory Limitations**:
- In-memory only (lost on restart)
- No horizontal scaling
- Memory leak (unbounded access log)
- No TTL enforcement

**Persistent Backend Benefits**:
- Survives process restarts
- Horizontal scaling support
- Automatic TTL cleanup
- Production-ready

## Migration Options

### Option 1: Redis (Recommended)

**Use Case**: Fast in-memory cache with persistence

**Setup**:
```bash
# Install Redis
docker run -d -p 6379:6379 redis:latest

# Install Python client
pip install redis>=5.0.0
```

**Code Change**:
```python
# Before
from lionagi_qe import QEFleet

fleet = QEFleet()
# Uses QEMemory internally

# After
from lionagi_qe.persistence import RedisMemory
from lionagi_qe import QEOrchestrator

memory = RedisMemory(host="localhost", port=6379)
orchestrator = QEOrchestrator(memory=memory, ...)
```

### Option 2: PostgreSQL

**Use Case**: Structured queries, ACID guarantees

**Setup**:
```bash
# PostgreSQL already configured for Q-learning
# Reuse existing connection

pip install asyncpg>=0.29.0
```

**Code Change**:
```python
from lionagi_qe.persistence import PostgresMemory

memory = PostgresMemory(
    host="localhost",
    database="lionagi_qe_learning",
    user="qe_agent",
    password="qe_secure_password_123"
)

await memory.connect()
orchestrator = QEOrchestrator(memory=memory, ...)
```

### Option 3: Session.context (Development Only)

**Use Case**: Local development, no persistence needed

**Code Change**:
```python
from lionagi import Session

session = Session()
await session.initiate()

# Use session.context directly (replaces QEMemory)
session.context.set("aqe/test-results", results)
results = session.context.get("aqe/test-results")
```

## API Compatibility

All persistence backends implement the same interface:

```python
async def store(key: str, value: Any, ttl: int, partition: str)
async def retrieve(key: str) -> Any
async def search(pattern: str) -> Dict[str, Any]
async def delete(key: str)
async def clear_partition(partition: str)
async def list_keys(prefix: str) -> List[str]
async def get_stats() -> Dict[str, Any]
```

## Configuration

**Environment Variables**:
```bash
# Redis
export QE_MEMORY_BACKEND=redis
export QE_REDIS_HOST=localhost
export QE_REDIS_PORT=6379

# PostgreSQL
export QE_MEMORY_BACKEND=postgres
export QE_POSTGRES_HOST=localhost
export QE_POSTGRES_DB=lionagi_qe_learning
```

**Code**:
```python
import os
from lionagi_qe.persistence import RedisMemory, PostgresMemory

backend = os.getenv("QE_MEMORY_BACKEND", "redis")

if backend == "redis":
    memory = RedisMemory(
        host=os.getenv("QE_REDIS_HOST", "localhost"),
        port=int(os.getenv("QE_REDIS_PORT", 6379))
    )
elif backend == "postgres":
    memory = PostgresMemory(
        host=os.getenv("QE_POSTGRES_HOST", "localhost"),
        database=os.getenv("QE_POSTGRES_DB", "lionagi_qe_learning")
    )
    await memory.connect()
```
```

---

### Phase 3: Study LionAGI v0 Patterns (HIGH PRIORITY)

**Timeline**: 5-7 days
**Benefit**: Learn 5-year evolution of multi-agent patterns
**Location**: `/Users/lion/projects/open-source/lionagi/lionagi/`

#### Step 3.1: Study Core Patterns

**Files to Study**:
1. `lionagi/operations/` - Agent operations
2. `lionagi/session/` - Session lifecycle
3. `lionagi/branch/` - Agent state isolation
4. `lionagi/tool_manager/` - Native tool registry
5. `lionagi/protocols/` - Message passing

**Pattern 1: Native Tool Registry**
```python
# Study: lionagi/session/branch.py
from lionagi import Tool

@Tool.register
def analyze_coverage(coverage_data: dict) -> CoverageReport:
    """Tool decorator registers function as agent capability"""
    return report

# Session automatically discovers registered tools
session.register_tool(analyze_coverage)
```

**Pattern 2: Branch-Based Agent Isolation**
```python
# Study: lionagi/session/branch.py
branch1 = session.new_branch("test-generator")
branch2 = session.new_branch("coverage-analyzer")

# Each branch has isolated state
await branch1.instruct("Generate tests")
await branch2.instruct("Analyze coverage")

# Branches communicate via session context
session.context.set("shared/data", results)
```

**Pattern 3: Builder Workflow Patterns**
```python
# Study: lionagi/protocols/graph.py
builder = Builder("QE_Workflow")

# Sequential
n1 = builder.add_operation("generate", ...)
n2 = builder.add_operation("analyze", depends_on=[n1])

# Parallel (fan-out)
n3a = builder.add_operation("security_scan", depends_on=[n2])
n3b = builder.add_operation("performance_test", depends_on=[n2])

# Fan-in
n4 = builder.add_operation("quality_gate", depends_on=[n3a, n3b])
```

#### Step 3.2: Apply Patterns to QE Fleet

**Create**: `docs/patterns/lionagi-best-practices.md`

Document how each QE agent should use:
- Session and Branch for state management
- Builder for complex workflows
- Tool registry for agent capabilities
- Native message passing instead of custom abstractions

---

### Phase 4: Documentation Updates (LOW PRIORITY)

**Timeline**: 1-2 days
**Benefit**: Accurate documentation for refactored architecture

#### Files to Update

1. **README.md**:
   - Update Quick Start to use Session/Builder directly
   - Remove QEFleet references
   - Add persistence configuration section
   - Update architecture diagram

2. **USAGE_GUIDE.md**:
   - Rewrite examples with LionAGI native patterns
   - Add Redis/PostgreSQL setup instructions
   - Document Builder workflow patterns
   - Add migration guide from v1.0.x

3. **docs/quickstart/*.md**:
   - Update all code examples
   - Show both Orchestrator and direct Session usage
   - Add persistence examples

4. **docs/reference/index.md**:
   - Generate autodocs with Sphinx
   - Document Session usage patterns
   - Add workflow examples

5. **examples/*.py**:
   - Update all 5 examples
   - Add new examples for Builder patterns
   - Add persistence examples

---

## Testing Strategy

### Phase 1 Testing (QEFleet Removal)

```bash
# After each refactoring step:
pytest tests/ -v --cov=src/lionagi_qe

# Specific tests:
pytest tests/test_core/test_orchestrator.py -v
pytest tests/test_agents/ -v
```

### Phase 2 Testing (Persistence)

```bash
# Start Redis for tests
docker run -d -p 6379:6379 redis:latest

# Run persistence tests
pytest tests/persistence/ -v

# Integration tests with Redis
pytest tests/integration/ --redis-enabled

# PostgreSQL tests (reuse Q-learning database)
pytest tests/persistence/test_postgres_memory.py -v
```

### Phase 3 Testing (Pattern Validation)

```bash
# Compare with LionAGI v0 patterns
cd /Users/lion/projects/open-source/lionagi/
pytest tests/unit/test_branch.py  # Study test patterns
pytest tests/integration/test_session.py

# Apply learned patterns to lionagi-qe-fleet
cd /workspaces/lionagi-qe-fleet
pytest tests/ --pattern-validation
```

---

## Success Criteria

### Phase 1 Complete When:
- [ ] QEFleet deleted (541 LOC removed)
- [ ] All 27 files updated (examples, tests, docs)
- [ ] Examples showcase direct Session/Builder usage
- [ ] Tests passing (581+ tests)
- [ ] Migration guide published

### Phase 2 Complete When:
- [ ] RedisMemory implemented and tested
- [ ] PostgresMemory implemented (optional)
- [ ] BaseQEAgent supports all memory backends
- [ ] Memory persistence survives process restart
- [ ] Configuration documented
- [ ] Integration tests passing

### Phase 3 Complete When:
- [ ] Native tool registry pattern documented
- [ ] Branch-based agent isolation used
- [ ] Builder workflow patterns aligned with v0
- [ ] Best practices guide published
- [ ] Codebase follows LionAGI conventions

### Phase 4 Complete When:
- [ ] All documentation updated
- [ ] Examples rewritten with new patterns
- [ ] API reference generated
- [ ] Migration guide complete

---

## Rollback Plan

If refactoring causes issues:

### Git Branches
```bash
# Create branch per phase
git checkout -b refactor/phase-1-remove-fleet
git checkout -b refactor/phase-2-persistence
git checkout -b refactor/phase-3-patterns
```

### Feature Flags

```python
# Example feature flag in config
import os

USE_PERSISTENCE = os.getenv("QE_USE_PERSISTENCE", "false") == "true"
USE_NEW_ORCHESTRATION = os.getenv("QE_USE_NEW_ORCHESTRATION", "false") == "true"

if USE_NEW_ORCHESTRATION:
    from lionagi import Builder, Session
    # New implementation
else:
    from lionagi_qe.core import QEFleet  # Old (deprecated)
    warnings.warn("QEFleet is deprecated")
```

### Parallel Implementations

Keep old code temporarily with deprecation warnings:

```python
# src/lionagi_qe/core/fleet.py (kept temporarily)
class QEFleet:
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "QEFleet is deprecated in v1.1.0 and will be removed in v2.0.0. "
            "Use QEOrchestrator or Session directly.",
            DeprecationWarning
        )
        # Old implementation...
```

---

## Questions for Ocean

1. **Tool Registry**: Best practice for registering 18 agents as tools?
   - Should each agent be a separate tool?
   - Or use dynamic tool generation?

2. **Branch Isolation**: Should each agent get its own Branch or share Branches?
   - Per-agent branches for isolation?
   - Or shared branches with context separation?

3. **Memory Namespace**: Is `aqe/*` convention aligned with LionAGI patterns?
   - Should we use session.context.set() directly?
   - Or create a memory abstraction layer?

4. **Workflow Coordination**: How to handle 18-agent fan-out/fan-in with Builder?
   - Builder supports dynamic node creation?
   - Or should we pre-define workflows?

**Contact**: Open GitHub issue at `khive-ai/lionagi` with `[qe-fleet]` prefix

---

## Estimated Timeline

| Phase | Days | Impact | Risk | Status |
|-------|------|--------|------|--------|
| Phase 1: Remove QEFleet | 2-3 | High (27 files) | Low | ⏳ Pending |
| Phase 2: Add Persistence | ~~3-5~~ **1-2** | Medium (26 files) | Low | ✅ 50% Done (PostgreSQL ready!) |
| Phase 3: Study Patterns | 5-7 | High (learning) | Low | ⏳ Pending |
| Phase 4: Update Docs | 1-2 | Medium (docs only) | Low | ⏳ Pending |
| **Total** | ~~**11-17**~~ **9-12** | - | - | - |

**Progress Update**:
- ✅ PostgreSQL database running (from Q-Learning work)
- ✅ Connection pooling configured (asyncpg, 2-10 connections)
- ✅ DatabaseManager class available
- ✅ 7 tables created (learning data)
- 🔨 Need to add: 1 table (qe_memory), PostgresMemory wrapper, optional Redis

**Assumptions**: Single developer, focused effort, no major blockers

---

## Deliverables

### Code
- [ ] Simplified codebase (~541 fewer LOC from QEFleet removal)
- [ ] Redis persistence backend (~150 LOC)
- [ ] PostgreSQL persistence backend (~200 LOC)
- [ ] LionAGI v0 pattern alignment

### Documentation
- [ ] Updated README with refactored examples
- [ ] Redis/PostgreSQL setup guide
- [ ] LionAGI pattern usage guide
- [ ] Migration guide (v1.0.x → v1.1.x)
- [ ] Best practices documentation

### Testing
- [ ] All 581+ tests passing
- [ ] New persistence integration tests (~20 tests)
- [ ] Pattern validation tests
- [ ] Example verification tests

---

## Revised Assessment

After analyzing the codebase:

**Ocean's Original Assessment**:
- 2,000-2,300 LOC of over-engineering
- QEOrchestrator reimplements Builder workflow logic ❌ (Actually uses Builder correctly)
- QEMemory lacks persistence ✅ (Correct)
- QETask reimplements Instruct ⚠️ (Partial - it's just status tracking)

**Our Findings**:
- **Actual wrapper LOC**: 1,412 lines (mostly QEFleet: 541, QEOrchestrator: 665)
- **QEOrchestrator is WELL-DESIGNED**: Uses LionAGI Session/Builder correctly (see lines 45, 147, 379)
- **Main Issue**: QEFleet adds unnecessary indirection
- **Secondary Issue**: QEMemory lacks persistence (but only 161 LOC, easy fix)
- **QETask**: Minimal abstraction (45 LOC), used everywhere (68 files), low priority

**Recommendation**:
1. **Remove QEFleet** (541 LOC) - high impact, low risk
2. **Keep QEOrchestrator** - it's using LionAGI correctly, provides value
3. **Add Persistence** - replace QEMemory internals with Redis/PostgreSQL
4. **Keep QETask** - it's minimal, used everywhere, provides value

**Expected LOC Reduction**: ~541 lines (QEFleet only), not 2,000-2,300

---

**Next Steps**: Start with Phase 1 (QEFleet removal) - highest impact, lowest risk.

**Ocean's Note**: This is about **simplifying**, not rewriting. The agents and orchestration are solid - we're just removing the unnecessary QEFleet wrapper and adding persistence!

🦁 Ready to implement!
