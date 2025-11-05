# Architecture Comparison: Before & After

## Current Architecture (v1.0.2)

### Component Stack
```
┌─────────────────────────────────────────────────────────┐
│                     User Application                     │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  QEFleet (500 LOC)                      │
│  ❌ Deprecated wrapper                                   │
│  - initialize()                                          │
│  - register_agent()                                      │
│  - execute()                                             │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              QEOrchestrator (666 LOC)                   │
│  ⚠️  Need validation                                     │
│  - execute_pipeline()                                    │
│  - execute_parallel()                                    │
│  - execute_fan_out_fan_in()                             │
└─────────────────────────────────────────────────────────┘
                            ↓
           ┌────────────────┴────────────────┐
           ↓                                  ↓
┌─────────────────────────┐    ┌─────────────────────────┐
│   QEMemory (800 LOC)    │    │   Session (LionAGI)     │
│   ❌ In-memory only      │    │   ✅ Native framework    │
│   - store()             │    │   - flow()              │
│   - retrieve()          │    │   - context             │
│   - search()            │    │   - new_branch()        │
└─────────────────────────┘    └─────────────────────────┘
           ↓                                  ↓
┌─────────────────────────┐    ┌─────────────────────────┐
│  Dict Storage (RAM)     │    │   Builder (LionAGI)     │
│  Lost on restart        │    │   - add_operation()     │
└─────────────────────────┘    │   - expand_from_result()│
                               │   - add_aggregation()    │
                               └─────────────────────────┘
                                          ↓
                               ┌─────────────────────────┐
                               │  Branch (per agent)     │
                               │  - communicate()        │
                               │  - operate()            │
                               └─────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   QETask (400 LOC)                      │
│  ❌ Custom task abstraction                              │
│  - task_type, context, status                           │
│  - mark_in_progress(), mark_completed()                 │
└─────────────────────────────────────────────────────────┘
```

**Total Custom Code**: ~2,366 LOC (QEFleet + QEOrchestrator + QEMemory + QETask)

---

## Proposed Architecture (v2.0.0)

### Option A: Keep QEOrchestrator (If Ocean Validates)

```
┌─────────────────────────────────────────────────────────┐
│                     User Application                     │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│          QEOrchestrator (400 LOC simplified)            │
│  ✅ Validated by Ocean                                   │
│  - execute_pipeline()                                    │
│  - execute_parallel()                                    │
│  - execute_fan_out_fan_in()                             │
└─────────────────────────────────────────────────────────┘
                            ↓
           ┌────────────────┴────────────────┐
           ↓                                  ↓
┌─────────────────────────┐    ┌─────────────────────────┐
│ Session.context + Redis │    │   Session (LionAGI)     │
│ ✅ Persistent memory     │    │   ✅ Native framework    │
│ - context.set/get       │    │   - flow()              │
│ - redis.store()         │    │   - context             │
│ - postgres.store()      │    │   - new_branch()        │
└─────────────────────────┘    └─────────────────────────┘
           ↓                                  ↓
┌─────────────────────────┐    ┌─────────────────────────┐
│  Redis/PostgreSQL       │    │   Builder (LionAGI)     │
│  Persists across        │    │   - add_operation()     │
│  restarts              │    │   - expand_from_result()│
└─────────────────────────┘    │   - add_aggregation()    │
                               └─────────────────────────┘
                                          ↓
                               ┌─────────────────────────┐
                               │  Branch (per agent)     │
                               │  - communicate()        │
                               │  - operate()            │
                               └─────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              Dict Contexts (no class)                    │
│  ✅ Simple dicts                                         │
│  context = {"code": code, "framework": "pytest"}         │
└─────────────────────────────────────────────────────────┘
```

**Total Custom Code**: ~900 LOC (QEOrchestrator + persistence backends)
**Reduction**: ~1,466 LOC (62% reduction)

---

### Option B: Remove QEOrchestrator (If Ocean Recommends)

```
┌─────────────────────────────────────────────────────────┐
│                     User Application                     │
│  ✅ Direct LionAGI usage                                 │
└─────────────────────────────────────────────────────────┘
                            ↓
           ┌────────────────┴────────────────┐
           ↓                                  ↓
┌─────────────────────────┐    ┌─────────────────────────┐
│ Session.context + Redis │    │   Session (LionAGI)     │
│ ✅ Persistent memory     │    │   ✅ Native framework    │
│ - context.set/get       │    │   - flow()              │
│ - redis.store()         │    │   - context             │
│ - postgres.store()      │    │   - new_branch()        │
└─────────────────────────┘    └─────────────────────────┘
           ↓                                  ↓
┌─────────────────────────┐    ┌─────────────────────────┐
│  Redis/PostgreSQL       │    │   Builder (LionAGI)     │
│  Persists across        │    │   ✅ User builds graphs  │
│  restarts              │    │   - add_operation()     │
└─────────────────────────┘    │   - expand_from_result()│
                               │   - add_aggregation()    │
                               └─────────────────────────┘
                                          ↓
                               ┌─────────────────────────┐
                               │  Branch (per agent)     │
                               │  - communicate()        │
                               │  - operate()            │
                               └─────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              Dict Contexts (no class)                    │
│  ✅ Simple dicts                                         │
│  context = {"code": code, "framework": "pytest"}         │
└─────────────────────────────────────────────────────────┘
```

**Total Custom Code**: ~500 LOC (persistence backends only)
**Reduction**: ~1,866 LOC (79% reduction)

---

## Code Examples

### Before (v1.0.2)

```python
from lionagi_qe import QEFleet, QETask
from lionagi import iModel

async def main():
    # 1. Initialize fleet (wrapper)
    fleet = QEFleet(
        enable_routing=True,
        enable_learning=True
    )
    await fleet.initialize()  # Extra initialization step

    # 2. Register agents
    from lionagi_qe.agents import TestGeneratorAgent

    model = iModel(provider="openai", model="gpt-4o-mini")
    agent = TestGeneratorAgent("test-gen", model)
    fleet.register_agent(agent)

    # 3. Create QETask (custom class)
    task = QETask(
        task_type="generate_tests",
        context={
            "code": "def add(a, b): return a + b",
            "framework": "pytest"
        }
    )

    # 4. Execute through fleet wrapper
    result = await fleet.execute("test-gen", task)
    print(result)

# Layers: User → QEFleet → QEOrchestrator → Session
```

---

### After - Option A (v2.0.0 with QEOrchestrator)

```python
from lionagi_qe import QEOrchestrator, ModelRouter
from lionagi_qe.persistence import RedisMemory
from lionagi_qe.agents import TestGeneratorAgent
from lionagi import iModel, Session

async def main():
    # 1. Initialize components explicitly
    session = Session()
    memory = RedisMemory("redis://localhost:6379")
    router = ModelRouter(enable_routing=True)

    # 2. Create orchestrator (validated by Ocean)
    orchestrator = QEOrchestrator(
        memory=memory,
        router=router,
        enable_learning=True
    )

    # 3. Register agent
    model = iModel(provider="openai", model="gpt-4o-mini")
    agent = TestGeneratorAgent("test-gen", model, session)
    orchestrator.register_agent(agent)

    # 4. Execute with simple dict context
    result = await orchestrator.execute_agent(
        "test-gen",
        context={
            "code": "def add(a, b): return a + b",
            "framework": "pytest"
        }
    )
    print(result.test_code)

    # 5. Cleanup
    await memory.close()

# Layers: User → QEOrchestrator → Session
# Benefits: Persistent memory, no QETask, cleaner API
```

---

### After - Option B (v2.0.0 direct Session)

```python
from lionagi import iModel, Session, Builder
from lionagi_qe.agents import TestGeneratorAgent
from lionagi_qe.persistence import RedisMemory

async def main():
    # 1. Direct LionAGI usage
    session = Session()
    model = iModel(provider="openai", model="gpt-4o-mini")

    # 2. Optional: Persistent memory
    memory = RedisMemory("redis://localhost:6379")

    # 3. Create agent directly
    agent = TestGeneratorAgent("test-gen", model, session)

    # 4. Execute directly on agent
    result = await agent.execute(
        context={
            "code": "def add(a, b): return a + b",
            "framework": "pytest"
        }
    )
    print(result.test_code)

    # 5. Store results in memory
    await memory.store("aqe/test-gen/results", result.dict(), ttl=3600)

# Layers: User → Session/Agent (direct)
# Benefits: Maximum simplicity, full LionAGI control
```

---

### Complex Workflow Comparison

#### Before (using QEFleet)

```python
# 4-agent sequential pipeline
result = await fleet.execute_pipeline(
    pipeline=[
        "test-generator",
        "test-executor",
        "coverage-analyzer",
        "quality-gate"
    ],
    context={
        "code_path": "./src",
        "framework": "pytest",
        "coverage_threshold": 80
    }
)

# Abstracts away Builder complexity
```

#### After - Option A (using QEOrchestrator)

```python
# Same API, but validated by Ocean
result = await orchestrator.execute_pipeline(
    pipeline=[
        "test-generator",
        "test-executor",
        "coverage-analyzer",
        "quality-gate"
    ],
    context={
        "code_path": "./src",
        "framework": "pytest",
        "coverage_threshold": 80
    }
)

# Convenience method if Ocean validates it
```

#### After - Option B (direct Builder)

```python
from lionagi import Builder, Session

# More verbose but maximum control
session = Session()
builder = Builder("QE_Pipeline")

# Build graph explicitly
gen_agent = orchestrator.get_agent("test-generator")
exec_agent = orchestrator.get_agent("test-executor")
cov_agent = orchestrator.get_agent("coverage-analyzer")
gate_agent = orchestrator.get_agent("quality-gate")

n1 = builder.add_operation(
    "communicate",
    branch=gen_agent.branch,
    instruction="Generate tests",
    context={"code_path": "./src", "framework": "pytest"}
)

n2 = builder.add_operation(
    "communicate",
    branch=exec_agent.branch,
    instruction="Execute tests",
    depends_on=[n1]
)

n3 = builder.add_operation(
    "communicate",
    branch=cov_agent.branch,
    instruction="Analyze coverage",
    depends_on=[n2]
)

n4 = builder.add_operation(
    "communicate",
    branch=gate_agent.branch,
    instruction="Validate quality gate",
    depends_on=[n3]
)

# Execute
result = await session.flow(builder.get_graph())

# More code but full control
```

---

## Memory Pattern Comparison

### Before (QEMemory - In-Memory)

```python
from lionagi_qe.core import QEMemory

memory = QEMemory()

# Store (lost on restart)
await memory.store(
    "aqe/coverage/results",
    coverage_data,
    ttl=3600,
    partition="coverage"
)

# Retrieve
results = await memory.retrieve("aqe/coverage/results")

# Search
all_coverage = await memory.search("aqe/coverage/.*")

# Problems:
# - Data lost on restart
# - No distributed coordination
# - Memory leaks (unbounded access_log)
```

---

### After (Session.context + Redis)

```python
from lionagi import Session
from lionagi_qe.persistence import RedisMemory

session = Session()
redis_memory = RedisMemory("redis://localhost:6379")

# Short-lived workflow state (in-memory)
session.context.set("aqe/workflow/current_step", "testing")
step = session.context.get("aqe/workflow/current_step")

# Long-lived results (persistent)
await redis_memory.store(
    "aqe/coverage/results",
    coverage_data,
    ttl=3600
)

# Retrieve after restart
results = await redis_memory.retrieve("aqe/coverage/results")

# Search namespace
all_coverage = await redis_memory.search("aqe/coverage/*")

# Benefits:
# - Data persists across restarts
# - Distributed coordination (multiple processes)
# - Production-ready (Redis/PostgreSQL)
```

---

## Agent Pattern Comparison (Tool Registry)

### Current (Class-Based)

```python
class TestGeneratorAgent(BaseQEAgent):
    """Generate comprehensive test suites"""

    def __init__(self, agent_id, model, memory):
        super().__init__(agent_id, model, memory)
        self.metrics = {
            "tasks_completed": 0,
            "total_cost": 0.0
        }
        self.learned_patterns = []

    def get_system_prompt(self) -> str:
        return "You are an expert test generation agent..."

    async def execute(self, task: QETask) -> GeneratedTest:
        # 200+ LOC implementation
        # Uses self.metrics, self.learned_patterns
        result = await self.safe_operate(
            instruction=f"Generate {task.framework} tests",
            response_format=GeneratedTest
        )

        self.metrics["tasks_completed"] += 1
        return result

# Usage:
agent = TestGeneratorAgent("test-gen", model, memory)
result = await agent.execute(task)
```

**Pros**: Easy state management, object-oriented
**Cons**: May not align with LionAGI v0 tool registry

---

### Proposed (Tool Registry - Pure Function)

```python
from lionagi import Tool

@Tool.register(name="test-generator")
async def generate_tests(
    code: str,
    framework: str = "pytest",
    test_type: str = "unit"
) -> GeneratedTest:
    """Generate comprehensive test suite

    This tool analyzes source code and generates
    comprehensive test cases with edge case coverage.
    """
    # Stateless implementation
    result = await llm_call(
        prompt=f"Generate {framework} tests",
        code=code,
        response_format=GeneratedTest
    )
    return result

# Usage with Session:
session = Session()
session.register_tool(generate_tests)

result = await session.instruct(
    "Generate tests for this code",
    context={"code": code}
)
```

**Pros**: Aligns with LionAGI v0, simpler
**Cons**: No instance state (metrics, learned patterns)

---

### Proposed (Hybrid - Class with Tool Methods)

```python
from lionagi import Tool

class TestGeneratorAgent:
    """Stateful agent with tool methods"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.metrics = {
            "tasks_completed": 0,
            "total_cost": 0.0
        }
        self.learned_patterns = []

    @Tool.register(name="generate-tests")
    async def generate(
        self,
        code: str,
        framework: str = "pytest"
    ) -> GeneratedTest:
        """Tool method with access to instance state"""

        # Has access to self.metrics, self.learned_patterns
        result = await llm_call(
            prompt=f"Generate {framework} tests",
            code=code,
            learned_patterns=self.learned_patterns
        )

        # Update instance state
        self.metrics["tasks_completed"] += 1

        # Learn from execution
        if result.coverage_estimate > 80:
            self.learned_patterns.append(result.pattern)

        return result

# Usage:
agent = TestGeneratorAgent("test-gen")
session.register_tool(agent.generate)

result = await session.instruct(
    "Generate tests",
    context={"code": code}
)
```

**Pros**: Best of both worlds (state + tool registry)
**Cons**: Need Ocean to validate this is acceptable pattern

---

## Summary

### Key Questions for Ocean:

1. **QEOrchestrator**: Keep convenience wrapper or remove?
2. **Tool Registry**: Convert agents to @Tool.register? Hybrid approach ok?
3. **Memory**: Session.context + Redis, or different pattern?
4. **Branches**: Per-instance or per-execution?
5. **Workflows**: Is our Builder usage correct for 18+ agents?

### Expected Outcomes:

**Code Reduction**:
- Option A (keep orchestrator): ~1,466 LOC reduction (62%)
- Option B (remove orchestrator): ~1,866 LOC reduction (79%)

**Architecture Simplification**:
- Remove 3 wrapper layers
- Add production persistence
- Align with LionAGI v0

**Timeline**: 14 days implementation after Ocean review

---

**Next Step**: Create GitHub issue with Ocean's questions and await guidance.
