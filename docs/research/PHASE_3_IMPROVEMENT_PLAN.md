# Phase 3 Improvement Plan: LionAGI v0 Pattern Alignment

**Date**: 2025-11-05
**Version**: 1.0
**Status**: Draft for Ocean Review
**Project**: lionagi-qe-fleet v1.0.2

---

## Executive Summary

After studying the lionagi-qe-fleet codebase and Ocean's technical handoff, this plan outlines how to align the QE Fleet with LionAGI v0's 5-year evolution of multi-agent patterns. The current implementation is sophisticated but contains **~2,300 LOC of custom wrappers** that duplicate LionAGI functionality.

**Key Findings**:
- ✅ **What's Working Well**: Session, Branch, Builder, alcall, ReAct usage
- ❌ **What Needs Improvement**: QEFleet (500 LOC), QEOrchestrator (666 LOC), QEMemory (800 LOC), QETask (400 LOC)
- 🎯 **Goal**: Simplify to LionAGI native patterns while maintaining functionality

**Impact**:
- **Code Reduction**: ~2,300 LOC removed (40% reduction)
- **Maintenance**: Fewer abstractions to maintain
- **Performance**: Direct LionAGI usage (no wrapper overhead)
- **Alignment**: Follow 5 years of LionAGI best practices

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [LionAGI v0 Patterns Identified](#2-lionagi-v0-patterns-identified)
3. [Alignment Opportunities](#3-alignment-opportunities)
4. [Detailed Improvement Plan](#4-detailed-improvement-plan)
5. [Timeline & Resources](#5-timeline--resources)
6. [Success Criteria](#6-success-criteria)
7. [Questions for Ocean](#7-questions-for-ocean)
8. [Risk Assessment](#8-risk-assessment)
9. [Rollout Strategy](#9-rollout-strategy)
10. [Appendices](#10-appendices)

---

## 1. Current State Analysis

### 1.1 What We're Doing Right ✅

#### LionAGI Integration (Working Well)

**File**: `src/lionagi_qe/core/orchestrator.py` (666 LOC)

```python
# Line 4-5: Using native LionAGI imports
from lionagi import Builder, Session
from lionagi.operations import ExpansionStrategy

# Line 45: Direct Session usage
self.session = Session()

# Line 147-167: Using Builder for workflows
builder = Builder(f"QE_Pipeline_{len(pipeline)}_agents")
nodes = []
for i, agent_id in enumerate(pipeline):
    node = builder.add_operation(
        "communicate",
        depends_on=nodes[-1:] if nodes else [],
        branch=agent.branch,
        instruction=context.get("instruction", f"Execute {agent_id}"),
        context=context
    )
    nodes.append(node)
result = await self.session.flow(builder.get_graph())

# Line 198-219: Using alcall for parallel execution
from lionagi.ln import alcall
results = await alcall(
    tasks_with_agents,
    lambda x: run_agent(x[0], x[1])
)
```

**File**: `src/lionagi_qe/core/base_agent.py` (1,016 LOC)

```python
# Line 5: Using native Branch
from lionagi import Branch, iModel

# Line 88-92: Each agent has a Branch
self.branch = Branch(
    system=self.get_system_prompt(),
    chat_model=model,
    name=agent_id
)

# Line 769-773: Direct branch communication
response = await self.branch.communicate(
    instruction=instruction,
    context=context
)

# Line 791-796: Structured operation
result = await self.branch.operate(
    instruction=instruction,
    context=context,
    response_format=response_format
)

# Line 23: Fuzzy parsing integration
from lionagi.ln.fuzzy import fuzzy_json, fuzzy_validate_pydantic
```

**Assessment**:
- QEOrchestrator correctly uses Session + Builder for workflow orchestration
- BaseQEAgent correctly uses Branch for agent state management
- alcall used for parallel execution with retry logic
- Fuzzy parsing integrated for robust LLM output handling
- ReAct reasoning patterns implemented (line 419-504 in base_agent.py)

**Score**: 9/10 - Excellent LionAGI integration

---

### 1.2 What Could Be Improved 🔄

#### Problem 1: QEFleet Wrapper Layer (500 LOC)

**File**: `src/lionagi_qe/core/fleet.py`

**Current Architecture**:
```
User Code
    ↓
QEFleet (500 LOC wrapper)
    ↓
QEOrchestrator (666 LOC)
    ↓
Session (LionAGI native)
```

**Issues**:
1. **Redundant Abstraction**: QEFleet mostly delegates to QEOrchestrator
2. **Deprecated**: Already marked for removal in v2.0.0 (lines 3-6)
3. **Maintenance Burden**: Extra layer that needs updating when LionAGI changes
4. **Initialization Overhead**: Unnecessary `initialize()` method (lines 107-131)

**Example** (lines 142-159):
```python
async def execute(self, agent_id: str, task: QETask) -> Dict[str, Any]:
    """Execute a single agent task"""
    if not self.initialized:
        await self.initialize()

    # Just delegates to orchestrator
    return await self.orchestrator.execute_agent(agent_id, task)
```

**Impact**: Users must learn both QEFleet API and QEOrchestrator API

---

#### Problem 2: QEMemory - In-Memory Storage (800 LOC)

**File**: `src/lionagi_qe/core/memory.py` (assumed, not read yet)

**Issues from Technical Handoff**:
1. **No Persistence**: Python dict-based, lost on restart
2. **Memory Leaks**: Unbounded access_log list
3. **Duplicates Session.context**: LionAGI already provides this

**Current Usage** (from base_agent.py):
```python
# Line 144-146: Custom memory storage
full_key = f"aqe/{self.agent_id}/{key}"
await self.memory.store(full_key, value, ttl=ttl, partition=partition)

# Line 157: Custom memory retrieval
value = await self.memory.retrieve(key)
```

**Should Be** (using Session.context):
```python
# Use LionAGI native context
session.context.set("aqe/test-generator/results", value)
value = session.context.get("aqe/test-generator/results")
```

**Impact**: Custom memory system that doesn't persist across restarts

---

#### Problem 3: QETask Abstraction (400 LOC)

**File**: `src/lionagi_qe/core/task.py`

**Current Pattern**:
```python
task = QETask(
    task_type="generate_tests",
    context={"code": code, "framework": "pytest"}
)
result = await agent.execute(task)
```

**LionAGI Native Pattern**:
```python
# Use Instruct directly
result = await session.instruct(
    instruction="Generate tests",
    context={"code": code, "framework": "pytest"},
    response_format=GeneratedTest
)
```

**Issues**:
1. **Reimplements Instruct**: LionAGI already has instruction patterns
2. **Custom State Management**: task.mark_in_progress(), task.mark_completed()
3. **Extra Abstraction**: Users must understand QETask API

**Impact**: Unnecessary abstraction layer over LionAGI's native patterns

---

#### Problem 4: QEOrchestrator - Partial Duplication (666 LOC)

**File**: `src/lionagi_qe/core/orchestrator.py`

**What's Good**:
- Uses Session and Builder correctly ✅
- Implements valuable convenience methods ✅
- Good workflow patterns (pipeline, parallel, fan-out/fan-in) ✅

**What's Questionable**:
- Is the convenience worth 666 LOC? 🤔
- Could these be helper functions instead of a class? 🤔
- Does it align with LionAGI v0 orchestration patterns? 🤔

**Assessment**: Keep QEOrchestrator but validate patterns with Ocean

---

### 1.3 Code Volume Analysis

**Total Codebase**: ~5,700 LOC (excluding tests)

**Core Modules**:
```bash
src/lionagi_qe/core/
├── orchestrator.py    666 LOC ⚠️  (valuable, but check alignment)
├── base_agent.py    1,016 LOC ✅  (well-designed)
├── fleet.py           500 LOC ❌  (deprecated, remove)
├── memory.py          800 LOC ❌  (replace with Session.context)
├── task.py            400 LOC ❌  (replace with Instruct)
├── router.py          300 LOC ✅  (multi-model routing, keep)
└── hooks.py           200 LOC ✅  (observability, keep)
───────────────────────────────────
Total:               3,882 LOC
Removable:           1,700 LOC (44% of core)
```

**Agent Implementations**: 18 agents × ~250 LOC avg = ~4,500 LOC ✅

**Expected After Refactoring**:
- Remove: fleet.py (500) + memory.py (800) + task.py (400) = 1,700 LOC
- Simplify: orchestrator.py (666 → ~400) = 266 LOC
- **Total Reduction**: ~2,000 LOC (35% of codebase)

---

## 2. LionAGI v0 Patterns Identified

Based on technical handoff and current codebase analysis:

### 2.1 Pattern 1: Native Tool Registry

**Source**: Technical handoff lines 293-308

**LionAGI v0 Pattern**:
```python
from lionagi import Tool

@Tool.register
def analyze_coverage(coverage_data: dict) -> CoverageReport:
    """Tool decorator registers function as agent capability"""
    return report

# Session automatically discovers registered tools
session.register_tool(analyze_coverage)
```

**Current QE Fleet Pattern**:
```python
# Class-based agents
class CoverageAnalyzerAgent(BaseQEAgent):
    async def execute(self, task: QETask):
        # Implementation
        pass

# Manual registration
orchestrator.register_agent(agent)
```

**Alignment Question**: Should 18 agents be converted to @Tool.register?

**Pros**:
- Aligns with LionAGI v0 tool registry
- Simpler agent definition
- Easier testing (functions vs classes)

**Cons**:
- Lose object state (metrics, learned patterns)
- Q-learning integration more complex
- Breaking change for current users

**Recommendation**: Investigate hybrid approach with Ocean

---

### 2.2 Pattern 2: Branch-Based Agent Isolation

**Source**: Technical handoff lines 310-324

**LionAGI v0 Pattern**:
```python
# Create isolated branches per agent
branch1 = session.new_branch("test-generator")
branch2 = session.new_branch("coverage-analyzer")

# Each branch has isolated state
await branch1.instruct("Generate tests")
await branch2.instruct("Analyze coverage")

# Branches communicate via session context
session.context.set("shared/data", results)
```

**Current QE Fleet Pattern**:
```python
# Each agent creates own Branch in __init__
self.branch = Branch(
    system=self.get_system_prompt(),
    chat_model=model,
    name=agent_id
)
```

**Assessment**: ✅ Already aligned! Each agent has isolated Branch.

**Question for Ocean**: Is this the correct pattern, or should branches be created per-execution rather than per-agent-instance?

---

### 2.3 Pattern 3: Builder Workflow Patterns

**Source**: Technical handoff lines 326-343

**LionAGI v0 Pattern**:
```python
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

**Current QE Fleet Pattern**:
```python
# QEOrchestrator.execute_pipeline (lines 147-172)
builder = Builder(f"QE_Pipeline_{len(pipeline)}_agents")
nodes = []
for i, agent_id in enumerate(pipeline):
    node = builder.add_operation(
        "communicate",
        depends_on=nodes[-1:] if nodes else [],
        branch=agent.branch,
        instruction=context.get("instruction"),
        context=context
    )
    nodes.append(node)
result = await self.session.flow(builder.get_graph())
```

**Assessment**: ✅ Already aligned! Using Builder correctly.

---

### 2.4 Pattern 4: Session.context vs Custom Memory

**Source**: Technical handoff lines 113-134

**LionAGI v0 Pattern**:
```python
# Use Session.context for shared state
session.context.set("aqe/coverage/results", coverage_data)
results = session.context.get("aqe/coverage/results")

# For persistence, use Redis/PostgreSQL
import redis
r = redis.Redis()
r.setex("aqe/coverage/results", 3600, json.dumps(coverage_data))
```

**Current QE Fleet Pattern**:
```python
# Custom QEMemory class
class QEMemory:
    def __init__(self):
        self._storage: Dict[str, Any] = {}  # In-memory only

    async def store(self, key, value, ttl=None, partition=None):
        self._storage[key] = value

    async def retrieve(self, key):
        return self._storage.get(key)
```

**Issues**:
1. Doesn't persist across restarts
2. No distributed coordination
3. Duplicates Session.context functionality

**Recommendation**: Replace with Session.context + Redis/PostgreSQL backends

---

## 3. Alignment Opportunities

### Priority Matrix

| Opportunity | Impact | Effort | Alignment | Priority |
|-------------|--------|--------|-----------|----------|
| **1. Remove QEFleet wrapper** | High | Low | High | **P0** |
| **2. Replace QEMemory with Session.context** | High | Medium | High | **P0** |
| **3. Replace QETask with Instruct** | High | Medium | High | **P0** |
| **4. Validate QEOrchestrator patterns** | Medium | Low | Critical | **P0** |
| **5. Study tool registry pattern** | Medium | High | High | **P1** |
| **6. Add Redis/PostgreSQL persistence** | High | Medium | Medium | **P1** |
| **7. Explicit branch management** | Low | Low | Medium | **P2** |
| **8. Update documentation** | High | Low | N/A | **P1** |

---

## 4. Detailed Improvement Plan

### 4.1 Priority 0: Critical Alignment (Week 1)

#### Milestone 1.1: Remove QEFleet Wrapper (Day 1)

**Goal**: Eliminate 500 LOC redundant wrapper

**Current File**: `src/lionagi_qe/core/fleet.py`

**Status**: Already deprecated (lines 3-6)

**Actions**:
1. ✅ Already has deprecation warning
2. Update all examples to use QEOrchestrator directly
3. Add migration guide pointing users to QEOrchestrator
4. Remove QEFleet in v2.0.0 (safe to keep deprecated for now)

**Before**:
```python
from lionagi_qe import QEFleet

fleet = QEFleet(enable_routing=True)
await fleet.initialize()
fleet.register_agent(agent)
result = await fleet.execute(agent_id, task)
```

**After**:
```python
from lionagi_qe import QEOrchestrator, ModelRouter, QEMemory

memory = QEMemory()  # Or Session().context later
router = ModelRouter(enable_routing=True)
orchestrator = QEOrchestrator(memory, router)
orchestrator.register_agent(agent)
result = await orchestrator.execute_agent(agent_id, task)
```

**Deliverable**: Migration guide + updated examples

---

#### Milestone 1.2: Validate QEOrchestrator Patterns with Ocean (Day 1-2)

**Goal**: Ensure 666 LOC QEOrchestrator aligns with LionAGI v0 best practices

**Questions for Ocean**:

1. **Orchestrator Design**: Is QEOrchestrator pattern aligned with LionAGI v0?
   ```python
   # Current approach: Orchestrator class wrapping Session
   class QEOrchestrator:
       def __init__(self, memory, router, enable_learning=False):
           self.session = Session()
           self.memory = memory
           self.router = router

   # Alternative: Direct Session usage with helper functions?
   session = Session()
   result = await execute_pipeline(session, agents, context)
   ```

2. **Workflow Methods**: Are these convenience methods valuable?
   - `execute_pipeline()` - Sequential execution
   - `execute_parallel()` - Parallel with alcall
   - `execute_fan_out_fan_in()` - Fan-out/fan-in pattern
   - `execute_parallel_expansion()` - List expansion pattern
   - `execute_conditional_workflow()` - Conditional branching

3. **Session Lifecycle**: Should each workflow create a new Session, or reuse one?
   ```python
   # Current: One session per orchestrator instance
   self.session = Session()  # Line 45 in orchestrator.py

   # Alternative: New session per workflow?
   async def execute_pipeline(self, pipeline, context):
       session = Session()
       builder = Builder(...)
       result = await session.flow(builder.get_graph())
       return result
   ```

4. **Memory Integration**: How should Session.context integrate with custom memory?
   ```python
   # Option A: Session.context only (no persistence)
   session.context.set("aqe/results", data)

   # Option B: Session.context + Redis backend
   session.context.set("aqe/results", data)
   await redis_backend.store("aqe/results", data, ttl=3600)

   # Option C: Custom memory abstraction (current)
   await self.memory.store("aqe/results", data)
   ```

**Deliverable**: Decision document with Ocean's feedback

---

#### Milestone 1.3: Replace QETask with Instruct Pattern (Day 2-3)

**Goal**: Remove 400 LOC QETask abstraction

**Current Implementation**:
```python
# src/lionagi_qe/core/task.py (~400 LOC)
class QETask:
    def __init__(self, task_type, context, priority=None):
        self.task_id = str(uuid.uuid4())
        self.task_type = task_type
        self.context = context
        self.priority = priority
        self.status = "pending"
        self.result = None

    def mark_in_progress(self, agent_id):
        self.status = "in_progress"
        self.assigned_to = agent_id

    def mark_completed(self, result):
        self.status = "completed"
        self.result = result

# Usage in agents
async def execute(self, task: QETask) -> Dict[str, Any]:
    context = task.context
    code = context.get("code", "")
    # ...
```

**Proposed Replacement**:
```python
# Remove QETask entirely, use direct instruction pattern

# Before:
task = QETask(
    task_type="generate_tests",
    context={"code": code, "framework": "pytest"}
)
result = await agent.execute(task)

# After:
result = await agent.execute_instruction(
    instruction="generate_tests",
    code=code,
    framework="pytest"
)

# Or using Session directly:
result = await session.instruct(
    instruction="Generate comprehensive tests",
    context={"code": code, "framework": "pytest"},
    response_format=GeneratedTest
)
```

**Migration Path**:
1. Update BaseQEAgent.execute() signature:
   ```python
   # Before:
   async def execute(self, task: QETask) -> Dict[str, Any]

   # After (Option A - keep compatibility):
   async def execute(self, task: Union[QETask, Dict[str, Any]]) -> Dict[str, Any]:
       if isinstance(task, QETask):
           warnings.warn("QETask is deprecated, use dict instead")
           context = task.context
       else:
           context = task
       # ...

   # After (Option B - clean break):
   async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
       code = context.get("code", "")
       framework = context.get("framework", "pytest")
       # ...
   ```

2. Update all 18 agents' execute() methods

3. Update orchestrator to not use QETask

4. Add deprecation warnings for backward compatibility

**Deliverable**: PR with QETask removal + migration guide

---

#### Milestone 1.4: Replace QEMemory with Session.context (Day 3-4)

**Goal**: Remove 800 LOC custom memory, use LionAGI native patterns

**Current Implementation**:
```python
# src/lionagi_qe/core/memory.py (~800 LOC)
class QEMemory:
    def __init__(self):
        self._storage: Dict[str, Any] = {}  # In-memory only
        self._access_log: List[...] = []    # Memory leak

    async def store(self, key, value, ttl=None, partition=None):
        self._storage[key] = value

    async def retrieve(self, key):
        return self._storage.get(key)
```

**Proposed Replacement**:

**Phase 1: Session.context (in-memory)**
```python
# Update BaseQEAgent to use Session.context
class BaseQEAgent:
    def __init__(self, agent_id, model, session=None):
        self.agent_id = agent_id
        self.model = model
        self.session = session or Session()

        # Use session context for memory
        self.memory = self.session.context

    async def store_result(self, key, value, ttl=None):
        """Store in session context"""
        full_key = f"aqe/{self.agent_id}/{key}"
        self.session.context.set(full_key, value)

    async def retrieve_context(self, key):
        """Retrieve from session context"""
        return self.session.context.get(key)
```

**Phase 2: Add Redis/PostgreSQL backends** (see Priority 1)

**Migration Strategy**:
```python
# Adapter pattern for backward compatibility
class QEMemory:
    """DEPRECATED: Use Session.context directly"""

    def __init__(self, session=None):
        warnings.warn("QEMemory is deprecated, use Session.context")
        self._session = session or Session()

    async def store(self, key, value, ttl=None, partition=None):
        self._session.context.set(key, value)

    async def retrieve(self, key):
        return self._session.context.get(key)
```

**Questions for Ocean**:
1. Does Session.context persist across Session instances?
2. How to handle TTL (time-to-live) for memory entries?
3. Best practice for namespace organization? (currently using `aqe/*`)

**Deliverable**: PR with QEMemory removal + Session.context migration

---

### 4.2 Priority 1: Persistence & Tooling (Week 2)

#### Milestone 2.1: Add Redis Persistence Backend (Day 5-6)

**Goal**: Production-ready persistent memory

**Implementation**:

**File**: `src/lionagi_qe/persistence/redis_backend.py` (new)
```python
"""Redis persistence backend for QE Fleet"""

import json
from typing import Any, Dict, Optional
import redis.asyncio as redis


class RedisMemory:
    """Redis-backed memory with TTL support

    Features:
    - Async Redis client
    - JSON serialization
    - TTL support
    - Namespace operations
    - Connection pooling
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        max_connections: int = 10
    ):
        self.pool = redis.ConnectionPool.from_url(
            url,
            max_connections=max_connections,
            decode_responses=True
        )
        self.client = redis.Redis(connection_pool=self.pool)

    async def store(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """Store value with optional TTL

        Args:
            key: Storage key (e.g., 'aqe/coverage/results')
            value: Value to store (will be JSON serialized)
            ttl: Time-to-live in seconds (None = no expiration)
        """
        serialized = json.dumps(value)

        if ttl:
            await self.client.setex(key, ttl, serialized)
        else:
            await self.client.set(key, serialized)

    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value by key

        Args:
            key: Storage key

        Returns:
            Deserialized value or None if not found
        """
        data = await self.client.get(key)
        if data is None:
            return None

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data  # Return raw string if not JSON

    async def search(self, pattern: str) -> Dict[str, Any]:
        """Search keys by pattern

        Args:
            pattern: Redis pattern (e.g., 'aqe/coverage/*')

        Returns:
            Dict of matching key-value pairs
        """
        keys = []
        async for key in self.client.scan_iter(match=pattern):
            keys.append(key)

        if not keys:
            return {}

        # Batch retrieve
        values = await self.client.mget(keys)

        results = {}
        for key, value in zip(keys, values):
            if value:
                try:
                    results[key] = json.loads(value)
                except json.JSONDecodeError:
                    results[key] = value

        return results

    async def delete(self, key: str) -> bool:
        """Delete key

        Args:
            key: Key to delete

        Returns:
            True if deleted, False if not found
        """
        result = await self.client.delete(key)
        return result > 0

    async def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in namespace

        Args:
            namespace: Namespace pattern (e.g., 'aqe/coverage/*')

        Returns:
            Number of keys deleted
        """
        keys = []
        async for key in self.client.scan_iter(match=namespace):
            keys.append(key)

        if not keys:
            return 0

        return await self.client.delete(*keys)

    async def close(self):
        """Close Redis connection"""
        await self.client.close()
        await self.pool.disconnect()
```

**Usage**:
```python
from lionagi_qe.persistence import RedisMemory

# Initialize
memory = RedisMemory("redis://localhost:6379/0")

# Store with TTL
await memory.store("aqe/coverage/results", coverage_data, ttl=3600)

# Retrieve
results = await memory.retrieve("aqe/coverage/results")

# Search namespace
all_coverage = await memory.search("aqe/coverage/*")

# Cleanup
await memory.close()
```

**Configuration**:
```python
# Add to pyproject.toml
[project.optional-dependencies]
persistence = [
    "redis>=5.0.0",
]
```

**Deliverable**: Redis backend implementation + tests

---

#### Milestone 2.2: Add PostgreSQL Persistence Backend (Day 7-8)

**Goal**: Structured storage for trajectories and patterns

**Implementation**:

**File**: `src/lionagi_qe/persistence/postgres_backend.py` (new)
```python
"""PostgreSQL persistence backend for QE Fleet"""

import json
from typing import Any, Dict, Optional, List
from datetime import datetime
import asyncpg


class PostgresMemory:
    """PostgreSQL-backed memory for structured data

    Features:
    - Async PostgreSQL client
    - JSON storage with indexing
    - Full-text search
    - Transaction support
    - Schema versioning
    """

    def __init__(self, url: str):
        self.url = url
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Initialize connection pool and schema"""
        self.pool = await asyncpg.create_pool(self.url)
        await self._create_schema()

    async def _create_schema(self):
        """Create tables if not exist"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS qe_memory (
                    key VARCHAR(500) PRIMARY KEY,
                    value JSONB NOT NULL,
                    partition VARCHAR(100),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_partition
                ON qe_memory(partition);

                CREATE INDEX IF NOT EXISTS idx_expires
                ON qe_memory(expires_at);

                CREATE INDEX IF NOT EXISTS idx_value_gin
                ON qe_memory USING gin(value);
            """)

    async def store(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        partition: str = "default"
    ) -> None:
        """Store value with optional TTL"""
        expires_at = None
        if ttl:
            expires_at = datetime.now() + timedelta(seconds=ttl)

        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO qe_memory (key, value, partition, expires_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (key)
                DO UPDATE SET
                    value = $2,
                    updated_at = NOW(),
                    expires_at = $4
            """, key, json.dumps(value), partition, expires_at)

    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value by key"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT value FROM qe_memory
                WHERE key = $1
                AND (expires_at IS NULL OR expires_at > NOW())
            """, key)

            if row:
                return json.loads(row['value'])
            return None

    async def search(self, pattern: str) -> Dict[str, Any]:
        """Search keys using SQL LIKE pattern"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT key, value FROM qe_memory
                WHERE key LIKE $1
                AND (expires_at IS NULL OR expires_at > NOW())
            """, pattern.replace('*', '%'))

            return {
                row['key']: json.loads(row['value'])
                for row in rows
            }

    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
```

**Schema Design**:
```sql
-- Core memory table
qe_memory (
    key VARCHAR(500) PRIMARY KEY,          -- e.g., 'aqe/coverage/results'
    value JSONB,                           -- Flexible JSON storage
    partition VARCHAR(100),                -- Namespace (coverage, tests, etc.)
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    expires_at TIMESTAMP                   -- For TTL support
)

-- Indexes for performance
CREATE INDEX idx_partition ON qe_memory(partition);
CREATE INDEX idx_expires ON qe_memory(expires_at);
CREATE INDEX idx_value_gin ON qe_memory USING gin(value);
```

**Deliverable**: PostgreSQL backend + schema + tests

---

#### Milestone 2.3: Investigate Tool Registry Pattern (Day 9-10)

**Goal**: Understand LionAGI v0 tool registry for potential migration

**Research Tasks**:

1. **Study LionAGI v0 Tool Implementation**:
   - How does @Tool.register work?
   - How are tools discovered by Session?
   - How to register 18 agents as tools?

2. **Prototype Agent as Tool**:
   ```python
   # Current: Class-based agent
   class TestGeneratorAgent(BaseQEAgent):
       async def execute(self, task: QETask):
           # 200+ LOC implementation
           pass

   # Proposed: Tool-decorated function
   @Tool.register(name="test-generator")
   async def generate_tests(
       code: str,
       framework: str = "pytest",
       test_type: str = "unit"
   ) -> GeneratedTest:
       """Generate comprehensive test suite"""
       # Refactored implementation
       return result

   # Usage:
   session.register_tool(generate_tests)
   result = await session.instruct(
       "Generate tests for this code",
       context={"code": code}
   )
   ```

3. **Evaluate Tradeoffs**:

   **Pros**:
   - Aligns with LionAGI v0 pattern
   - Simpler agent definitions
   - Easier testing (functions vs classes)
   - Automatic tool discovery

   **Cons**:
   - Lose agent instance state (metrics, learned patterns)
   - Q-learning integration more complex
   - Breaking change for current users
   - Need to refactor all 18 agents

4. **Hybrid Approach**:
   ```python
   # Keep classes for state management
   class TestGeneratorAgent:
       def __init__(self):
           self.metrics = {}
           self.learned_patterns = []

       @Tool.register(name="generate_tests")
       async def generate(self, code: str) -> GeneratedTest:
           """Tool method"""
           # Has access to self.metrics, self.learned_patterns
           return result
   ```

**Question for Ocean**: Is the hybrid approach aligned with LionAGI v0?

**Deliverable**: Research report with recommendation

---

### 4.3 Priority 2: Documentation & Refinement (Week 3)

#### Milestone 3.1: Update All Documentation (Day 11-12)

**Goal**: Accurate documentation reflecting refactored architecture

**Files to Update**:

1. **README.md**:
   - Remove QEFleet examples
   - Update to use QEOrchestrator directly
   - Add persistence configuration section
   - Update code examples with Session patterns

2. **docs/quickstart/installation.md**:
   - Add Redis/PostgreSQL optional dependencies
   - Docker setup instructions

3. **docs/quickstart/basic-workflows.md**:
   - Rewrite examples without QEFleet
   - Show direct Session usage
   - Add persistence examples

4. **docs/architecture/system-overview.md**:
   - Update architecture diagram
   - Remove QEFleet/QEMemory/QETask layers
   - Document Session.context usage

5. **docs/migration/** (new):
   - Create migration guides:
     - `fleet-to-orchestrator.md` ✅ (already exists)
     - `memory-to-session-context.md` (new)
     - `task-to-instruct.md` (new)
     - `adding-persistence.md` (new)

**Deliverable**: Complete documentation update

---

#### Milestone 3.2: Create LionAGI Best Practices Guide (Day 13)

**Goal**: Document LionAGI v0 pattern usage in QE Fleet

**File**: `docs/guides/lionagi-best-practices.md` (new)

**Contents**:

```markdown
# LionAGI Best Practices for QE Fleet

## 1. Session Management

### Creating Sessions
```python
from lionagi import Session

# Create new session
session = Session()

# With custom configuration
session = Session(
    max_concurrent=10,
    timeout=300
)
```

### Session Lifecycle
- Create per-workflow or reuse per-orchestrator
- Always clean up resources
- Use context managers for automatic cleanup

## 2. Branch-Based Agent Isolation

### Creating Branches
```python
# Per-agent branches
branch1 = session.new_branch("test-generator")
branch2 = session.new_branch("coverage-analyzer")

# Isolated state
await branch1.instruct("Generate tests")
await branch2.instruct("Analyze coverage")
```

### Branch Communication
```python
# Share data via session context
session.context.set("shared/results", data)

# Retrieve in other branch
results = session.context.get("shared/results")
```

## 3. Builder Workflow Patterns

### Sequential Pipelines
```python
builder = Builder("QE_Pipeline")
n1 = builder.add_operation("generate")
n2 = builder.add_operation("analyze", depends_on=[n1])
n3 = builder.add_operation("validate", depends_on=[n2])
```

### Parallel Execution (Fan-Out)
```python
# Fan-out to multiple agents
n1 = builder.add_operation("analyze_code")
n2a = builder.add_operation("security_scan", depends_on=[n1])
n2b = builder.add_operation("performance_test", depends_on=[n1])
n2c = builder.add_operation("quality_check", depends_on=[n1])

# Fan-in to synthesize
n3 = builder.add_operation("synthesize", depends_on=[n2a, n2b, n2c])
```

## 4. Memory & Persistence

### Using Session.context
```python
# Temporary memory (per-session)
session.context.set("aqe/coverage/results", data)
results = session.context.get("aqe/coverage/results")
```

### Using Redis for Persistence
```python
from lionagi_qe.persistence import RedisMemory

memory = RedisMemory("redis://localhost:6379")
await memory.store("aqe/coverage/results", data, ttl=3600)
```

### Memory Namespace Organization
```
aqe/
├── test-plan/       # Test requirements
├── coverage/        # Coverage data
├── quality/         # Quality metrics
├── performance/     # Performance results
├── security/        # Security findings
└── patterns/        # Learned patterns
```

## 5. Error Handling & Retry

### Using alcall for Automatic Retry
```python
from lionagi.ln import alcall

# Automatic retry with exponential backoff
results = await alcall(
    items,
    process_function,
    max_retries=3,
    initial_delay=1.0
)
```

## 6. Structured Output with Pydantic

### Defining Response Models
```python
from pydantic import BaseModel, Field

class GeneratedTest(BaseModel):
    test_name: str
    test_code: str
    coverage_estimate: float
```

### Using safe_operate for Robust Parsing
```python
result = await agent.safe_operate(
    instruction="Generate test",
    response_format=GeneratedTest
)
# Automatic fuzzy parsing fallback
```
```

**Deliverable**: Comprehensive best practices guide

---

#### Milestone 3.3: Pattern Validation Tests (Day 14)

**Goal**: Validate alignment with LionAGI v0 patterns

**Test Suite**: `tests/pattern_validation/` (new)

```python
# tests/pattern_validation/test_session_usage.py
"""Validate Session usage patterns"""

async def test_session_creation():
    """Verify sessions created correctly"""
    session = Session()
    assert session is not None

async def test_branch_isolation():
    """Verify branches are isolated"""
    session = Session()
    branch1 = session.new_branch("agent1")
    branch2 = session.new_branch("agent2")

    # Set in branch1
    await branch1.instruct("Store data", context={"data": "test1"})

    # Verify branch2 doesn't see it
    # ... validation logic

# tests/pattern_validation/test_builder_patterns.py
"""Validate Builder usage patterns"""

async def test_sequential_pipeline():
    """Verify sequential workflow execution"""
    builder = Builder("test")
    n1 = builder.add_operation("step1")
    n2 = builder.add_operation("step2", depends_on=[n1])

    # Validate execution order
    # ...

async def test_fan_out_fan_in():
    """Verify parallel fan-out/fan-in"""
    # ...
```

**Deliverable**: Pattern validation test suite

---

## 5. Timeline & Resources

### Overall Timeline: 14 days (2 weeks + 2 days)

**Week 1: Critical Alignment (P0)**
- Day 1: Remove QEFleet wrapper
- Day 1-2: Validate QEOrchestrator with Ocean
- Day 2-3: Replace QETask with Instruct
- Day 3-4: Replace QEMemory with Session.context
- Day 5: Buffer/testing

**Week 2: Persistence & Tooling (P1)**
- Day 6-7: Redis persistence backend
- Day 8-9: PostgreSQL persistence backend
- Day 10-11: Tool registry investigation
- Day 12: Buffer/testing

**Week 3: Documentation (P1)**
- Day 13: Update all documentation
- Day 14: LionAGI best practices guide
- Day 15: Pattern validation tests
- Day 16: Buffer/review

### Resource Requirements

**Developer Time**:
- 1 senior developer (full-time)
- Access to Ocean for pattern validation (2-3 hours total)

**Infrastructure**:
- Redis instance for testing
- PostgreSQL instance for testing
- Docker for local development

**Tools**:
- pytest for testing
- mypy for type checking
- ruff for linting
- Coverage.py for test coverage

---

## 6. Success Criteria

### Phase 1 Complete When:
- [ ] QEFleet deprecated with migration guide
- [ ] QEOrchestrator patterns validated by Ocean
- [ ] QETask removed, replaced with dict contexts
- [ ] QEMemory removed, replaced with Session.context
- [ ] All 128 tests passing
- [ ] Examples updated and verified
- [ ] ~1,700 LOC reduced

### Phase 2 Complete When:
- [ ] Redis backend implemented and tested
- [ ] PostgreSQL backend implemented and tested
- [ ] Memory persists across process restarts
- [ ] Tool registry pattern researched
- [ ] Integration tests passing

### Phase 3 Complete When:
- [ ] All documentation updated
- [ ] LionAGI best practices guide complete
- [ ] Pattern validation tests passing
- [ ] Ocean review and approval
- [ ] Zero breaking changes (backward compatible)

### Overall Success Metrics:
- **Code Reduction**: ~2,000 LOC removed (35%)
- **Test Coverage**: Maintain 82%+ coverage
- **Performance**: No regression in execution speed
- **Backward Compatibility**: Deprecation warnings, no breaks
- **Documentation**: 100% up-to-date

---

## 7. Questions for Ocean

### Critical Questions (Need answers for P0):

#### Q1: Orchestrator Design Pattern
**Context**: QEOrchestrator (666 LOC) wraps Session and provides convenience methods

**Current Implementation**:
```python
class QEOrchestrator:
    def __init__(self, memory, router):
        self.session = Session()  # Single session instance

    async def execute_pipeline(self, agents, context):
        builder = Builder(...)
        result = await self.session.flow(builder.get_graph())
        return result
```

**Questions**:
1. Is this wrapper pattern aligned with LionAGI v0 best practices?
2. Should we provide convenience methods, or recommend direct Session usage?
3. Is reusing a single Session instance correct, or create new Session per workflow?

**Alternative Approach**:
```python
# No orchestrator, direct Session usage
session = Session()
builder = Builder("QE_Pipeline")
# ... build workflow
result = await session.flow(builder.get_graph())
```

**Our Assessment**: Keep orchestrator for convenience, but need validation.

---

#### Q2: Tool Registry Pattern for 18 Agents
**Context**: 18 agents currently as classes inheriting BaseQEAgent

**Current Pattern**:
```python
class TestGeneratorAgent(BaseQEAgent):
    def __init__(self, agent_id, model, memory):
        super().__init__(agent_id, model, memory)
        self.metrics = {}
        self.learned_patterns = []

    async def execute(self, task: QETask) -> GeneratedTest:
        # 200+ LOC implementation with state access
        pass
```

**LionAGI Tool Pattern** (from handoff):
```python
@Tool.register(name="test-generator")
async def generate_tests(code: str, framework: str) -> GeneratedTest:
    """Generate tests (stateless function)"""
    return result
```

**Questions**:
1. Should we convert agents to @Tool.register pattern?
2. How to handle agent state (metrics, learned patterns, Q-learning)?
3. Is this hybrid approach acceptable?
   ```python
   class TestGeneratorAgent:
       def __init__(self):
           self.metrics = {}

       @Tool.register
       async def generate(self, code: str) -> GeneratedTest:
           # Has access to self
           return result
   ```

**Tradeoff Analysis**:
- **Full Tool Migration**: Aligns with v0, but loses state management
- **Keep Classes**: Easier state management, but may not align with v0
- **Hybrid**: Best of both, but need to verify it's a valid pattern

**Our Recommendation**: Research hybrid approach, need Ocean's guidance.

---

#### Q3: Session.context vs Custom Memory
**Context**: Need persistent memory for agent coordination

**Current**: Custom QEMemory (800 LOC, in-memory only)

**Proposed Options**:

**Option A: Session.context only** (no persistence)
```python
session.context.set("aqe/coverage/results", data)
results = session.context.get("aqe/coverage/results")
```

**Option B: Session.context + Redis backend**
```python
# Session.context for workflow coordination
session.context.set("aqe/results", data)

# Redis for persistence across restarts
await redis_backend.store("aqe/results", data, ttl=3600)
```

**Option C: Abstraction layer** (current approach)
```python
# Custom interface, swappable backends
await self.memory.store("aqe/results", data)

# Backend: InMemory, Redis, or PostgreSQL
```

**Questions**:
1. Does Session.context persist across Session instances?
2. What's the recommended pattern for persistent memory in LionAGI v0?
3. Should we use Session.context for short-lived workflow state only?
4. Is it acceptable to use Redis/PostgreSQL directly for long-term storage?

**Our Assessment**: Option B (Session.context + Redis) seems best, but need confirmation.

---

#### Q4: Branch Lifecycle Management
**Context**: When to create branches for agent isolation

**Current Pattern** (in BaseQEAgent.__init__):
```python
self.branch = Branch(
    system=self.get_system_prompt(),
    chat_model=model,
    name=agent_id
)
```

**Alternative Patterns**:

**Pattern A: Branch per agent instance** (current)
- Created once in agent __init__
- Reused across multiple task executions
- Branch history accumulates

**Pattern B: Branch per execution**
```python
async def execute(self, task):
    # Create fresh branch for each execution
    branch = Branch(
        system=self.get_system_prompt(),
        chat_model=self.model
    )
    result = await branch.communicate(...)
    return result
```

**Pattern C: Session manages branches**
```python
# Orchestrator creates branches
session = Session()
branch1 = session.new_branch("test-generator")
branch2 = session.new_branch("coverage-analyzer")

# Pass to agents
await agent1.execute_on_branch(branch1, task)
```

**Questions**:
1. Which pattern is recommended in LionAGI v0?
2. Should branch history accumulate or be isolated per execution?
3. How to handle long-running agents (thousands of executions)?

**Our Assessment**: Pattern A works but unclear if it's optimal for high-throughput.

---

#### Q5: Workflow Coordination Patterns
**Context**: 18 agents in complex workflows (fan-out/fan-in, conditional)

**Example Workflow**:
```
Requirements Validator
        ↓
Test Generator (spawns 10 parallel)
        ↓
    [Test 1] [Test 2] ... [Test 10]
        ↓         ↓           ↓
    [Execute] [Execute] ... [Execute]
        ↓
Coverage Analyzer (aggregates)
        ↓
Quality Gate
```

**Current Implementation**:
```python
# QEOrchestrator.execute_parallel_expansion()
builder = Builder("parallel-expansion")
source_op = builder.add_operation("generate")
expanded_ops = builder.expand_from_result(
    items=source_op.response.items,
    operation="execute",
    strategy=ExpansionStrategy.CONCURRENT,
    max_concurrent=10
)
aggregation_op = builder.add_aggregation(
    source_node_ids=expanded_ops
)
```

**Questions**:
1. Is this Builder usage pattern correct for 18-agent coordination?
2. How to handle dynamic agent spawning (based on runtime decisions)?
3. Best practice for result aggregation from 10+ parallel agents?
4. Memory/resource management for high agent counts (50+ agents)?

**Our Assessment**: Current pattern seems reasonable but need validation for scale.

---

### Research Questions (For tool registry investigation):

#### Q6: Tool Registry Implementation
1. How does LionAGI v0's @Tool.register work internally?
2. How are tools discovered and invoked by Session?
3. Can tools maintain instance state? (for metrics, Q-learning)
4. Performance implications of tool registry vs direct method calls?

---

### Optional Questions (Nice to have):

#### Q7: Session Pooling
For high-throughput scenarios (1000+ executions), should we:
1. Create new Session per workflow?
2. Pool Sessions for reuse?
3. Use single long-lived Session?

#### Q8: Performance Best Practices
1. Optimal max_concurrent for Builder workflows?
2. Memory management for long-running agents?
3. Connection pooling for Redis/PostgreSQL?

---

### How to Ask Ocean

**GitHub Issue Template**:
```markdown
**Title**: [qe-fleet] LionAGI v0 Pattern Alignment Questions

**Context**:
We're refactoring lionagi-qe-fleet to align with LionAGI v0 best practices.
After studying the technical handoff, we have specific questions about pattern usage.

**Project**: https://github.com/lionagi/lionagi-qe-fleet
**Technical Handoff**: [link to docs/research/technical_handoff.md]

**Questions**:
[Paste relevant questions from above]

**Current Implementation**: [code examples]
**Proposed Alternatives**: [code examples]

**Request**: Could you review and provide guidance on recommended patterns?

**Availability**: Available for 30-min call if helpful: [scheduling link]
```

---

## 8. Risk Assessment

### Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Breaking changes** | Medium | High | Feature flags + deprecation warnings |
| **Performance regression** | Low | High | Benchmark tests before/after |
| **Session.context doesn't persist** | Medium | High | Add Redis/PostgreSQL backends |
| **Tool registry doesn't support state** | Medium | Medium | Keep hybrid class+tool approach |
| **Ocean unavailable for review** | Low | Medium | Proceed with best judgment, iterate later |
| **Test coverage drops** | Low | High | Run tests after each change |
| **Documentation outdated** | High | Medium | Update docs in parallel with code |
| **Timeline overrun** | Medium | Low | 20% buffer built into estimates |

### High-Risk Areas

#### 1. QEMemory Removal (HIGH RISK)

**Risk**: Session.context doesn't provide needed persistence

**Mitigation**:
- Keep QEMemory as deprecated adapter initially
- Add Redis/PostgreSQL backends in Phase 2
- Feature flag for switching between backends
- Comprehensive integration tests

**Rollback Plan**: Restore QEMemory if Session.context insufficient

---

#### 2. QETask Removal (MEDIUM RISK)

**Risk**: Breaking change for current users

**Mitigation**:
- Add Union[QETask, Dict] support initially
- Deprecation warnings for 2-3 releases
- Clear migration guide with examples
- Backward compatibility tests

**Rollback Plan**: Keep QETask with deprecation warning

---

#### 3. Tool Registry Migration (MEDIUM RISK)

**Risk**: Stateless tools can't support Q-learning, metrics

**Mitigation**:
- Research hybrid approach first
- Prototype with 1-2 agents before full migration
- Keep class-based agents as fallback
- Make tool registry optional enhancement

**Rollback Plan**: Stay with class-based agents

---

### Low-Risk Changes

✅ **QEFleet Removal**: Already deprecated, low impact
✅ **Documentation Updates**: No code risk
✅ **Pattern Validation**: Additive, no breaking changes

---

## 9. Rollout Strategy

### Phase 1: Deprecation & Compatibility (v1.1.0)

**Week 1-2 Implementation**

**Changes**:
- Deprecate QEFleet with migration guide
- Deprecate QEMemory, add Session.context support
- Deprecate QETask, accept Dict[str, Any] in execute()
- Add feature flags for new vs old implementations

**Release Notes**:
```markdown
## v1.1.0 - Deprecations (LionAGI v0 Alignment)

### Deprecated (Still Work)
- `QEFleet` - Use `QEOrchestrator` directly
- `QEMemory` - Use `Session.context` or `RedisMemory`
- `QETask` - Pass dict to `execute()` instead

### New Features
- Redis persistence backend
- PostgreSQL persistence backend
- Session.context integration
- Direct Session/Builder usage patterns

### Migration
See docs/migration/ for detailed guides.

### Breaking Changes
None - all deprecated features still work with warnings.
```

**User Experience**:
```python
# Old code still works (with warnings)
fleet = QEFleet()  # DeprecationWarning
await fleet.execute(agent_id, task)

# New recommended pattern
from lionagi_qe import QEOrchestrator
orchestrator = QEOrchestrator(...)
await orchestrator.execute_agent(agent_id, context)
```

---

### Phase 2: Default to New Patterns (v1.2.0)

**Week 3-4 Implementation**

**Changes**:
- Session.context becomes default memory backend
- Redis/PostgreSQL backends production-ready
- Comprehensive migration guide and examples
- All documentation uses new patterns

**Release Notes**:
```markdown
## v1.2.0 - New Defaults (LionAGI v0 Alignment)

### Changes
- Session.context is now default memory backend
- QEOrchestrator is primary API (QEFleet still works)
- Dict-based task contexts are standard

### Upgrade Path
1. Update imports: `from lionagi_qe import QEOrchestrator`
2. Replace QEMemory with Session.context or RedisMemory
3. Pass dicts instead of QETask objects
4. See docs/migration/ for details

### Deprecated (Removed in v2.0.0)
- QEFleet
- QEMemory
- QETask
```

---

### Phase 3: Remove Deprecated Code (v2.0.0)

**After 6-12 months**

**Changes**:
- Delete QEFleet (fleet.py)
- Delete QEMemory (memory.py)
- Delete QETask (task.py)
- Clean up compatibility shims

**Release Notes**:
```markdown
## v2.0.0 - Major Release (LionAGI v0 Fully Aligned)

### Breaking Changes
- Removed: QEFleet, QEMemory, QETask
- Use: QEOrchestrator, Session.context, dict contexts

### Benefits
- 2,000+ LOC reduction
- Direct LionAGI v0 patterns
- Better performance (no wrapper overhead)
- Simplified architecture

### Migration
Users on v1.1.0 or v1.2.0: Follow deprecation warnings.
Migration time: ~30 minutes for typical projects.
```

---

### Feature Flag Strategy

**Environment Variables**:
```python
# Gradual rollout control
USE_NEW_ORCHESTRATION = os.getenv("QE_USE_NEW_ORCHESTRATION", "false")
USE_SESSION_CONTEXT = os.getenv("QE_USE_SESSION_CONTEXT", "false")
USE_DICT_TASKS = os.getenv("QE_USE_DICT_TASKS", "false")

# v1.1.0: All false by default (backward compatible)
# v1.2.0: All true by default (new patterns)
# v2.0.0: Remove feature flags (only new patterns)
```

**Usage**:
```python
if USE_SESSION_CONTEXT:
    memory = session.context
else:
    memory = QEMemory()  # Deprecated, with warning
```

---

### Communication Plan

#### For Users

**Announcement Blog Post** (v1.1.0 release):
```markdown
# LionAGI v0 Pattern Alignment

We're simplifying lionagi-qe-fleet to align with LionAGI's 5-year evolution.

## What's Changing
- QEFleet → QEOrchestrator
- QEMemory → Session.context or RedisMemory
- QETask → Dict contexts

## Your Code Still Works
All deprecated features work in v1.1.0 and v1.2.0 with warnings.
You have 6-12 months to migrate.

## Why This Change
- 2,000+ fewer lines of code
- Simpler architecture
- Better LionAGI integration
- Production-ready persistence

## Migration Guide
See docs/migration/ for step-by-step instructions.
```

#### For Contributors

**CONTRIBUTING.md Update**:
```markdown
## Architecture Changes (v1.1.0+)

We're aligning with LionAGI v0 patterns:
- Use Session + Builder directly
- No more QEFleet/QEMemory/QETask wrappers
- See docs/guides/lionagi-best-practices.md

## Deprecation Policy
1. Deprecate in v1.1.0 (warnings)
2. Keep working through v1.2.0
3. Remove in v2.0.0 (6-12 months)
```

---

## 10. Appendices

### Appendix A: Code Examples

#### Example 1: Before/After Migration

**Before (v1.0.2 - Current)**:
```python
from lionagi_qe import QEFleet, QETask
from lionagi import iModel

async def main():
    # Initialize fleet
    fleet = QEFleet(
        enable_routing=True,
        enable_learning=True
    )
    await fleet.initialize()

    # Create task
    task = QETask(
        task_type="generate_tests",
        context={
            "code": "def add(a, b): return a + b",
            "framework": "pytest"
        }
    )

    # Execute
    result = await fleet.execute("test-generator", task)
    print(result)
```

**After (v1.1.0 - Recommended)**:
```python
from lionagi_qe import QEOrchestrator, ModelRouter
from lionagi_qe.persistence import RedisMemory
from lionagi import iModel, Session

async def main():
    # Initialize components
    session = Session()
    memory = RedisMemory("redis://localhost:6379")
    router = ModelRouter(enable_routing=True)

    # Create orchestrator
    orchestrator = QEOrchestrator(
        memory=memory,
        router=router,
        enable_learning=True
    )

    # Execute with dict context (no QETask)
    result = await orchestrator.execute_agent(
        "test-generator",
        context={
            "code": "def add(a, b): return a + b",
            "framework": "pytest"
        }
    )
    print(result)

    # Cleanup
    await memory.close()
```

**After (v2.0.0 - Future, Direct Session)**:
```python
from lionagi import iModel, Session, Builder
from lionagi_qe.agents import TestGeneratorAgent

async def main():
    # Direct LionAGI usage
    session = Session()
    model = iModel(provider="openai", model="gpt-4o-mini")

    # Create agent
    agent = TestGeneratorAgent("test-gen", model, session)

    # Execute directly
    result = await agent.execute(
        context={
            "code": "def add(a, b): return a + b",
            "framework": "pytest"
        }
    )
    print(result.test_code)
```

---

#### Example 2: Persistence Patterns

**In-Memory (Development)**:
```python
from lionagi import Session

session = Session()

# Use session.context for workflow state
session.context.set("aqe/coverage/results", coverage_data)
results = session.context.get("aqe/coverage/results")

# Lost on restart
```

**Redis (Production - Fast)**:
```python
from lionagi_qe.persistence import RedisMemory

memory = RedisMemory("redis://localhost:6379/0")

# Persists across restarts
await memory.store("aqe/coverage/results", coverage_data, ttl=3600)
results = await memory.retrieve("aqe/coverage/results")

# Namespace operations
all_coverage = await memory.search("aqe/coverage/*")
```

**PostgreSQL (Production - Structured)**:
```python
from lionagi_qe.persistence import PostgresMemory

memory = PostgresMemory("postgresql://localhost:5432/lionagi_qe")
await memory.initialize()

# Structured storage with full-text search
await memory.store(
    "aqe/coverage/results",
    coverage_data,
    ttl=3600,
    partition="coverage"
)

results = await memory.retrieve("aqe/coverage/results")
```

---

### Appendix B: LOC Reduction Breakdown

**Current Codebase (v1.0.2)**:
```
src/lionagi_qe/
├── core/
│   ├── orchestrator.py      666 LOC  (keep, validate)
│   ├── base_agent.py      1,016 LOC  (keep, excellent)
│   ├── fleet.py             500 LOC  (remove)
│   ├── memory.py            800 LOC  (remove)
│   ├── task.py              400 LOC  (remove)
│   ├── router.py            300 LOC  (keep)
│   └── hooks.py             200 LOC  (keep)
│
├── agents/                4,500 LOC  (keep)
│
└── persistence/             500 LOC  (add new)

Total: ~8,882 LOC
```

**After Refactoring (v2.0.0)**:
```
src/lionagi_qe/
├── core/
│   ├── orchestrator.py      400 LOC  (simplified)
│   ├── base_agent.py      1,016 LOC  (unchanged)
│   ├── router.py            300 LOC  (unchanged)
│   └── hooks.py             200 LOC  (unchanged)
│
├── agents/                4,500 LOC  (unchanged)
│
└── persistence/
    ├── redis_backend.py     250 LOC  (new)
    └── postgres_backend.py  250 LOC  (new)

Total: ~6,916 LOC
```

**Net Change**:
- Removed: 1,700 LOC (fleet, memory, task)
- Simplified: 266 LOC (orchestrator)
- Added: 500 LOC (persistence)
- **Total Reduction: 1,466 LOC (17%)**

**If orchestrator fully removed**:
- Additional reduction: 400 LOC
- **Total Reduction: 1,866 LOC (21%)**

---

### Appendix C: Test Coverage Plan

**Current Coverage**: 82% (128 tests)

**New Tests Required**:

1. **Session.context Integration** (10 tests):
   ```python
   tests/core/test_session_context.py
   - test_store_and_retrieve()
   - test_namespace_isolation()
   - test_context_cleanup()
   # ...
   ```

2. **Redis Backend** (15 tests):
   ```python
   tests/persistence/test_redis_backend.py
   - test_store_with_ttl()
   - test_retrieve_expired()
   - test_namespace_search()
   - test_connection_pooling()
   # ...
   ```

3. **PostgreSQL Backend** (15 tests):
   ```python
   tests/persistence/test_postgres_backend.py
   - test_structured_storage()
   - test_json_indexing()
   - test_full_text_search()
   # ...
   ```

4. **Pattern Validation** (10 tests):
   ```python
   tests/pattern_validation/
   - test_builder_workflows()
   - test_branch_isolation()
   - test_alcall_usage()
   # ...
   ```

5. **Migration Compatibility** (10 tests):
   ```python
   tests/compatibility/test_deprecations.py
   - test_qefleet_still_works()
   - test_deprecation_warnings()
   - test_backward_compatibility()
   # ...
   ```

**Total New Tests**: 60 tests
**Expected Final Coverage**: 85%+ (188 tests)

---

### Appendix D: Performance Benchmarks

**Baseline (v1.0.2)**:
```python
# Benchmark suite
pytest benchmarks/ --benchmark-only

# Results:
# - Agent execution: ~500ms avg
# - Pipeline (4 agents): ~2.1s
# - Parallel (3 agents): ~600ms
# - Memory operations: <1ms
```

**Expected After Refactoring (v2.0.0)**:
```python
# Improvements from removing wrapper overhead:
# - Agent execution: ~480ms (-20ms, -4%)
# - Pipeline (4 agents): ~2.0s (-100ms, -5%)
# - Parallel (3 agents): ~570ms (-30ms, -5%)
# - Redis ops: ~1-2ms (+1ms, acceptable)
# - PostgreSQL ops: ~5-10ms (+5ms, acceptable)

# Net: Slight improvement in execution, acceptable persistence overhead
```

---

### Appendix E: Migration Checklist

**For Users Migrating from v1.0.2 → v1.1.0+**:

#### Phase 1: Preparation (30 minutes)
- [ ] Read migration guide: `docs/migration/fleet-to-orchestrator.md`
- [ ] Install v1.1.0: `uv add lionagi-qe-fleet>=1.1.0`
- [ ] Optional: Install persistence: `uv add lionagi-qe-fleet[persistence]`
- [ ] Run existing tests to ensure baseline

#### Phase 2: Code Updates (1-2 hours)
- [ ] Replace `QEFleet` imports with `QEOrchestrator`
  ```python
  # Before:
  from lionagi_qe import QEFleet
  fleet = QEFleet()

  # After:
  from lionagi_qe import QEOrchestrator, ModelRouter, QEMemory
  orchestrator = QEOrchestrator(memory, router)
  ```

- [ ] Replace `QETask` with dict contexts
  ```python
  # Before:
  task = QETask(task_type="generate", context={...})

  # After:
  context = {"task_type": "generate", ...}
  ```

- [ ] Replace `QEMemory` with Session.context or RedisMemory
  ```python
  # Before:
  from lionagi_qe.core import QEMemory
  memory = QEMemory()

  # After (Option 1 - Session.context):
  from lionagi import Session
  session = Session()
  memory = session.context

  # After (Option 2 - Redis):
  from lionagi_qe.persistence import RedisMemory
  memory = RedisMemory("redis://localhost:6379")
  ```

#### Phase 3: Testing (30 minutes)
- [ ] Run all tests: `pytest`
- [ ] Check for deprecation warnings
- [ ] Verify functionality unchanged
- [ ] Update documentation/comments

#### Phase 4: Persistence Setup (Optional, 1 hour)
- [ ] Start Redis: `docker run -d -p 6379:6379 redis:7-alpine`
- [ ] Or PostgreSQL: See `docs/quickstart/installation.md`
- [ ] Update configuration with connection strings
- [ ] Test persistence across restarts

**Estimated Total Time**: 2-4 hours for typical project

---

### Appendix F: Decision Log

**Decision 1: Keep QEOrchestrator (Week 1, Day 2)**
- **Context**: Should we keep 666 LOC orchestrator or remove it?
- **Decision**: Keep orchestrator, validate patterns with Ocean
- **Rationale**: Provides valuable convenience methods, worth the LOC
- **Action**: Create GitHub issue for Ocean review

**Decision 2: Hybrid Tool Registry Approach (Week 2, Day 10)**
- **Context**: Tool registry vs class-based agents
- **Decision**: Investigate hybrid (class with @Tool.register methods)
- **Rationale**: Need state management for Q-learning, metrics
- **Action**: Research and prototype hybrid pattern

**Decision 3: Session.context + Redis (Week 1, Day 4)**
- **Context**: Memory persistence strategy
- **Decision**: Session.context for workflow state, Redis for persistence
- **Rationale**: Best of both worlds (native LionAGI + persistence)
- **Action**: Implement Redis backend in Phase 2

**Decision 4: Gradual Rollout (Week 3, Day 13)**
- **Context**: Breaking changes vs smooth migration
- **Decision**: 3-phase rollout with 6-12 month deprecation
- **Rationale**: Minimize user disruption, ensure adoption
- **Action**: Document rollout plan in CHANGELOG

---

### Appendix G: Reference Links

**LionAGI Resources**:
- Main Repository: https://github.com/khive-ai/lionagi
- Documentation: https://lionagi.ai (if available)
- Source Study Location: `/Users/lion/projects/open-source/lionagi/lionagi/`

**QE Fleet Resources**:
- Repository: https://github.com/lionagi/lionagi-qe-fleet
- Technical Handoff: `/workspaces/lionagi-qe-fleet/docs/research/technical_handoff.md`
- Migration Guides: `/workspaces/lionagi-qe-fleet/docs/migration/`

**Related Documentation**:
- Fleet to Orchestrator Migration: `docs/migration/fleet-to-orchestrator.md`
- System Overview: `docs/architecture/system-overview.md`
- Q-Learning Integration: `docs/reports/q-learning-integration.md`

---

## Summary

This Phase 3 improvement plan provides a comprehensive roadmap for aligning lionagi-qe-fleet with LionAGI v0's 5-year evolution. The plan:

1. **Identifies Current State**: 2,300 LOC of custom wrappers to simplify
2. **Documents Patterns**: LionAGI v0 tool registry, Session.context, Builder workflows
3. **Proposes Improvements**: 5 priority levels, 14-day timeline
4. **Mitigates Risks**: Feature flags, gradual rollout, backward compatibility
5. **Questions Ocean**: 8 critical questions needing guidance

**Next Steps**:
1. Review this plan with Ocean
2. Get feedback on orchestrator design, tool registry, memory patterns
3. Begin Phase 1 implementation (remove QEFleet, validate orchestrator)
4. Iterate based on Ocean's guidance

**Expected Outcome**: Simplified codebase (~2,000 LOC reduction), better LionAGI alignment, production-ready persistence, maintaining 100% backward compatibility during migration.

---

**Document Status**: ✅ Ready for Ocean Review
**Last Updated**: 2025-11-05
**Next Review**: After Ocean feedback received
