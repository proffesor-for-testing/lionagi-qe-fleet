# Technical Handoff: LionAGI QE Fleet Refactoring

**From**: Ocean (LionAGI creator)
**To**: Developer's Claude assistant
**Date**: 2025-11-05
**Project**: lionagi-qe-fleet v1.0.2

---

## Context

Ocean reviewed the lionagi-qe-fleet project and identified that while the LionAGI integration is sophisticated, there's significant over-engineering through custom wrapper layers. This handoff provides a technical roadmap for simplifying the codebase while improving alignment with LionAGI's 5-year evolution.

---

## Current Architecture (Identified Issues)

### 1. Custom Wrapper Layers

**Problem**: Three layers of abstraction duplicate LionAGI functionality

```python
# Current flow (3 layers)
QEFleet (~/500 LOC)
  ├─> QEOrchestrator (~/600 LOC) - reimplements workflow logic
  │     └─> Session (LionAGI native)
  │
  ├─> QEMemory (~/800 LOC) - custom dict storage
  │     vs Session.context (LionAGI native)
  │
  └─> QETask (~/400 LOC) - custom message abstraction
        vs Instruct pattern (LionAGI native)
```

**Impact**: ~2000-2300 LOC that could be removed

### 2. Memory System (In-Memory)

**Problem**: `QEMemory` stores everything in Python dicts - no persistence

```python
# src/lionagi_qe/core/memory.py
class QEMemory:
    def __init__(self):
        self._storage: Dict[str, Any] = {}  # Lost on restart
        self._access_log: List[...] = []    # Unbounded (memory leak)
```

**Impact**: Cannot scale horizontally, state lost on crashes

### 3. LionAGI Integration Points

**What's Working Well**:
- `Branch` usage for agent state ✅
- `Session` for lifecycle ✅
- `Builder` for workflows ✅
- `ReAct` reasoning ✅
- `alcall` parallel async ✅

**What's Over-Engineered**:
- `QEOrchestrator` reimplements `Builder` workflows ❌
- `QEMemory` reimplements `Session.context` ❌
- `QETask` reimplements `Instruct` pattern ❌

---

## Refactoring Roadmap

### Phase 1: Remove Custom Wrappers (High Priority)

**Effort**: 2-3 days
**Benefit**: 2000-2300 fewer LOC, better LionAGI alignment

#### Step 1.1: Replace `QEFleet` with Direct Session Usage

**Before** (src/lionagi_qe/core/fleet.py):
```python
class QEFleet:
    def __init__(self):
        self.orchestrator = QEOrchestrator()  # Wrapper
        self.agents = {}

    async def execute(self, agent_id, task):
        return await self.orchestrator.execute(agent_id, task)
```

**After** (use LionAGI Session directly):
```python
from lionagi import Session

# Initialize session per-request (or reuse)
session = Session()
await session.initiate()

# Register agents as tools
session.register_tool(test_generator_tool)
session.register_tool(coverage_analyzer_tool)

# Execute directly
result = await session.instruct(
    instruction="Generate pytest tests for function: add(a, b)",
    context={"code": "def add(a, b): return a + b"},
    model="gpt-4o-mini"
)
```

**Files to modify**:
- Delete: `src/lionagi_qe/core/fleet.py` (~500 LOC)
- Update: All agent imports to use `Session` directly
- Update: Examples in `examples/*.py`

#### Step 1.2: Replace `QEMemory` with Session.context

**Before** (src/lionagi_qe/core/memory.py):
```python
class QEMemory:
    def store(self, key, value, partition=None):
        self._storage[key] = value  # In-memory only

    def retrieve(self, key):
        return self._storage.get(key)
```

**After** (use Session.context):
```python
# LionAGI provides this natively
session.context.set("aqe/coverage/results", coverage_data)
results = session.context.get("aqe/coverage/results")

# For persistence, use Redis/PostgreSQL
import redis
r = redis.Redis()
r.setex("aqe/coverage/results", 3600, json.dumps(coverage_data))
```

**Files to modify**:
- Delete: `src/lionagi_qe/core/memory.py` (~800 LOC)
- Update: All `QEMemory()` usage → `session.context`
- Add: Redis/PostgreSQL adapter for persistence

#### Step 1.3: Replace `QETask` with Instruct Pattern

**Before** (src/lionagi_qe/core/task.py):
```python
class QETask:
    def __init__(self, task_type, context, priority=None):
        self.task_type = task_type
        self.context = context
        # Custom message abstraction
```

**After** (use LionAGI Instruct):
```python
# LionAGI's native instruction pattern
result = await session.instruct(
    instruction=f"Perform {task_type} analysis",
    context=context,
    model="gpt-4o-mini",
    response_format=TestGenerationOutput  # Pydantic model
)
```

**Files to modify**:
- Delete: `src/lionagi_qe/core/task.py` (~400 LOC)
- Update: All agent execute methods to accept instructions directly
- Update: Examples to use `instruct` pattern

#### Step 1.4: Remove `QEOrchestrator` (Use Builder)

**Before** (src/lionagi_qe/core/orchestrator.py):
```python
class QEOrchestrator:
    async def execute_pipeline(self, agents, context):
        # Custom workflow logic
        for agent in agents:
            result = await self.execute_agent(agent, context)
            context.update(result)
        return context
```

**After** (use LionAGI Builder):
```python
from lionagi import Builder

# Define workflow
builder = Builder("QE_Pipeline")
node1 = builder.add_operation("generate_tests", context=ctx)
node2 = builder.add_operation("analyze_coverage", depends_on=[node1])
node3 = builder.add_operation("quality_gate", depends_on=[node1, node2])

# Execute
result = await session.execute_workflow(builder.get_graph())
```

**Files to modify**:
- Delete: `src/lionagi_qe/core/orchestrator.py` (~600 LOC)
- Update: Pipeline examples to use `Builder`
- Add: Workflow definition helpers

### Phase 2: Add Persistence Layer (Medium Priority)

**Effort**: 3-5 days
**Benefit**: Production-ready state management

#### Step 2.1: Redis Backend for Memory

**Add** (src/lionagi_qe/persistence/redis_memory.py):
```python
import redis
from typing import Any, Dict

class RedisMemory:
    def __init__(self, host="localhost", port=6379):
        self.client = redis.Redis(host=host, port=port, decode_responses=True)

    def store(self, key: str, value: Any, ttl: int = 3600):
        """Store with TTL (time-to-live)"""
        self.client.setex(key, ttl, json.dumps(value))

    def retrieve(self, key: str) -> Any:
        data = self.client.get(key)
        return json.loads(data) if data else None

    def namespace(self, pattern: str) -> Dict[str, Any]:
        """Get all keys matching pattern (e.g., 'aqe/coverage/*')"""
        keys = self.client.keys(pattern)
        return {k: self.retrieve(k) for k in keys}
```

**Usage**:
```python
# In agent initialization
from lionagi_qe.persistence import RedisMemory

memory = RedisMemory()

# Store results
memory.store("aqe/coverage/results", coverage_data, ttl=3600)

# Retrieve later
results = memory.retrieve("aqe/coverage/results")
```

**Files to create**:
- `src/lionagi_qe/persistence/__init__.py`
- `src/lionagi_qe/persistence/redis_memory.py`
- `src/lionagi_qe/persistence/postgres_memory.py` (optional)

**Configuration** (add to pyproject.toml):
```toml
[project.optional-dependencies]
persistence = [
    "redis>=5.0.0",
    "psycopg2-binary>=2.9.0",  # PostgreSQL
]
```

#### Step 2.2: Update Base Agent to Use Persistent Memory

**Modify** (src/lionagi_qe/core/base_agent.py):
```python
class BaseQEAgent:
    def __init__(self, agent_id, model, memory=None):
        self.agent_id = agent_id
        self.model = model

        # Support both in-memory (dev) and Redis (prod)
        if memory is None:
            from lionagi import Session
            self.memory = Session().context  # In-memory
        else:
            self.memory = memory  # Redis/PostgreSQL
```

### Phase 3: Study LionAGI v0 Patterns (High Priority)

**Effort**: 1 week (learning + alignment)
**Benefit**: Learn 5-year evolution of multi-agent patterns

#### Resources

**Location**: `/Users/lion/projects/open-source/lionagi/lionagi/`

**Key Files to Study**:
1. `operations/` - How Ocean implements agent operations
2. `session/` - Session lifecycle and context management
3. `branch/` - Agent state isolation patterns
4. `tool_manager/` - Native tool registry
5. `protocols/` - Message passing patterns

#### Specific Patterns to Learn

**Pattern 1: Native Tool Registry**
```python
# Study: lionagi/session/branch.py
# How LionAGI registers and invokes tools natively

from lionagi import Tool

@Tool.register
def analyze_coverage(coverage_data: dict) -> CoverageReport:
    """Tool decorator registers function as agent capability"""
    # Implementation
    return report

# Session automatically discovers and uses registered tools
session.register_tool(analyze_coverage)
```

**Pattern 2: Branch-Based Agent Isolation**
```python
# Study: lionagi/session/branch.py
# How to create independent agent contexts

branch1 = session.new_branch("test-generator")
branch2 = session.new_branch("coverage-analyzer")

# Each branch has isolated state
await branch1.instruct("Generate tests")
await branch2.instruct("Analyze coverage")

# Branches can communicate via session context
session.context.set("shared/data", results)
```

**Pattern 3: Builder Workflow Patterns**
```python
# Study: lionagi/protocols/graph.py
# How to build complex multi-agent workflows

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

### Phase 4: Documentation Updates (Low Priority)

**Effort**: 1-2 days
**Benefit**: Accurate documentation for refactored architecture

#### Updates Needed

1. **README.md**:
   - Update code examples to use Session/Builder directly
   - Remove QEFleet/QEOrchestrator references
   - Add persistence configuration section

2. **USAGE_GUIDE.md**:
   - Rewrite examples with LionAGI native patterns
   - Add Redis/PostgreSQL setup instructions
   - Document Builder workflow patterns

3. **API Reference** (docs/reference/):
   - Generate autodocs with Sphinx
   - Document Session usage patterns
   - Add workflow examples

---

## Testing Strategy

### Phase 1 Testing (Wrapper Removal)

```bash
# After each refactoring step:
pytest tests/ -v --cov=src/lionagi_qe

# Specific regression tests:
pytest tests/test_agents/ -k "test_generator or coverage_analyzer"
pytest tests/core/ -k "orchestration"
```

### Phase 2 Testing (Persistence)

```bash
# Start Redis for tests
docker run -d -p 6379:6379 redis:latest

# Run persistence tests
pytest tests/persistence/ -v

# Integration tests with Redis
pytest tests/integration/ --redis-enabled
```

### Phase 3 Validation (Pattern Alignment)

```bash
# Compare with LionAGI v0 patterns
cd /Users/lion/projects/open-source/lionagi/
pytest tests/unit/test_branch.py  # Study test patterns
pytest tests/integration/test_session.py  # Study integration tests

# Apply learned patterns to lionagi-qe-fleet
cd /path/to/lionagi-qe-fleet/
pytest tests/ --pattern-validation
```

---

## Success Criteria

### Phase 1 Complete When:
- [ ] QEFleet, QEOrchestrator, QEMemory, QETask classes deleted
- [ ] All agents use Session + Builder directly
- [ ] All tests passing (581 tests)
- [ ] Examples updated and verified working
- [ ] LOC reduced by ~2000-2300 lines

### Phase 2 Complete When:
- [ ] Redis backend implemented and tested
- [ ] Memory persistence working (survives process restart)
- [ ] Configuration documented
- [ ] Integration tests with Redis passing

### Phase 3 Complete When:
- [ ] Native tool registry pattern implemented
- [ ] Branch-based agent isolation used
- [ ] Builder workflow patterns aligned with v0
- [ ] Codebase follows LionAGI best practices

---

## Rollback Plan

If refactoring causes issues:

1. **Git branches**: Create branch per phase (`refactor/phase-1`, etc.)
2. **Feature flags**: Add environment variable to toggle old/new implementations
3. **Parallel implementations**: Keep old code temporarily with deprecation warnings

```python
# Example feature flag
import os
USE_NEW_ORCHESTRATION = os.getenv("QE_USE_NEW_ORCHESTRATION", "false") == "true"

if USE_NEW_ORCHESTRATION:
    from lionagi import Builder, Session
    # New implementation
else:
    from lionagi_qe.core import QEOrchestrator  # Old (deprecated)
    warnings.warn("QEOrchestrator is deprecated, use Session + Builder")
```

---

## Questions for Ocean (If Needed)

1. **Tool Registry**: Best practice for registering 18 agents as tools?
2. **Branch Isolation**: Should each agent get its own Branch or share Branches?
3. **Memory Namespace**: Is `aqe/*` convention aligned with LionAGI patterns?
4. **Workflow Coordination**: How to handle 18-agent fan-out/fan-in with Builder?

**Contact**: Open GitHub issue at `khive-ai/lionagi` with `[qe-fleet]` prefix

---

## Estimated Timeline

- **Phase 1**: 2-3 days (wrapper removal)
- **Phase 2**: 3-5 days (persistence layer)
- **Phase 3**: 5-7 days (pattern study + alignment)
- **Phase 4**: 1-2 days (documentation)

**Total**: 11-17 days (single developer, focused effort)

---

## Deliverables

**Code**:
- Simplified codebase (~2000 fewer LOC)
- Redis persistence backend
- LionAGI v0 pattern alignment

**Documentation**:
- Updated README with refactored examples
- Redis setup guide
- LionAGI pattern usage guide

**Testing**:
- All 581 tests passing
- New persistence integration tests
- Pattern validation tests

---

**Next Steps**: Start with Phase 1 (wrapper removal) - highest impact, lowest risk.

---

**Ocean's Note**: This is about **simplifying**, not rewriting. You built something solid - we're just removing unnecessary complexity to align with how LionAGI was designed to be used. The agents themselves are great - keep those!

🦁 Good luck!
