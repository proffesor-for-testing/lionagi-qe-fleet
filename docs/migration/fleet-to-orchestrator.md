# Migration Guide: QEFleet to QEOrchestrator

## Overview

As of **v1.1.0**, `QEFleet` is deprecated and will be removed in **v2.0.0**. This guide helps you migrate to the recommended approach using `QEOrchestrator` directly.

## Why Migrate?

1. **Reduced Complexity**: `QEFleet` was a 541 LOC wrapper that simply delegated to `QEOrchestrator`
2. **Better LionAGI Integration**: Direct use of `QEOrchestrator` aligns with LionAGI's architecture
3. **Clearer API**: Explicit component initialization makes dependencies visible
4. **Future-Proof**: `QEOrchestrator` is the maintained interface going forward

## Deprecation Timeline

- **v1.1.0** (Current): `QEFleet` deprecated with warnings
- **v1.5.0** (Planned): Warnings become errors in strict mode
- **v2.0.0** (Future): `QEFleet` removed entirely

## Quick Migration

### Before (QEFleet)

```python
from lionagi_qe import QEFleet, QETask
from lionagi_qe.agents import TestGeneratorAgent

fleet = QEFleet(enable_routing=True)
await fleet.initialize()

agent = TestGeneratorAgent(
    agent_id="test-generator",
    model=model,
    memory=fleet.memory
)

fleet.register_agent(agent)
result = await fleet.execute("test-generator", task)
```

### After (QEOrchestrator)

```python
from lionagi_qe import QEOrchestrator, QETask, ModelRouter
from lionagi_qe.core.memory import QEMemory
from lionagi_qe.agents import TestGeneratorAgent

# Initialize components explicitly
memory = QEMemory()  # or use Session().context
router = ModelRouter(enable_routing=True)
orchestrator = QEOrchestrator(
    memory=memory,
    router=router,
    enable_learning=False
)

agent = TestGeneratorAgent(
    agent_id="test-generator",
    model=model,
    memory=memory
)

orchestrator.register_agent(agent)
result = await orchestrator.execute_agent("test-generator", task)
```

## API Changes

### Initialization

**Before:**
```python
fleet = QEFleet(
    enable_routing=True,
    enable_learning=False,
    enable_hooks=True,
    fleet_id="qe-fleet"
)
await fleet.initialize()
```

**After:**
```python
memory = QEMemory()
router = ModelRouter(enable_routing=True)
orchestrator = QEOrchestrator(
    memory=memory,
    router=router,
    enable_learning=False
)
# No initialize() needed!
```

### Agent Registration

**Before:**
```python
fleet.register_agent(agent)
```

**After:**
```python
orchestrator.register_agent(agent)
```

### Task Execution

**Before:**
```python
result = await fleet.execute("agent-id", task)
```

**After:**
```python
result = await orchestrator.execute_agent("agent-id", task)
```

### Pipeline Execution

**Before:**
```python
result = await fleet.execute_pipeline(
    pipeline=["agent-1", "agent-2"],
    context={"key": "value"}
)
```

**After:**
```python
result = await orchestrator.execute_pipeline(
    pipeline=["agent-1", "agent-2"],
    context={"key": "value"}
)
```

### Parallel Execution

**Before:**
```python
results = await fleet.execute_parallel(
    agents=["agent-1", "agent-2"],
    tasks=[task1, task2]
)
```

**After:**
```python
results = await orchestrator.execute_parallel(
    agents=["agent-1", "agent-2"],
    tasks=[task1, task2]
)
```

### Fan-Out/Fan-In

**Before:**
```python
result = await fleet.execute_fan_out_fan_in(
    coordinator="commander",
    workers=["worker-1", "worker-2"],
    context={"key": "value"}
)
```

**After:**
```python
result = await orchestrator.execute_fan_out_fan_in(
    coordinator="commander",
    workers=["worker-1", "worker-2"],
    context={"key": "value"}
)
```

### Status and Metrics

**Before:**
```python
status = await fleet.get_status()
metrics = fleet.get_metrics()
```

**After:**
```python
status = await orchestrator.get_fleet_status()
metrics = orchestrator.metrics  # Direct access
```

## Memory Migration

`QEMemory` is also deprecated in favor of LionAGI's native memory or persistence backends.

### Option 1: In-Memory (Development)

```python
from lionagi.core import Session

memory = Session().context
```

### Option 2: Keep QEMemory (Temporary)

```python
from lionagi_qe.core.memory import QEMemory

memory = QEMemory()  # Will show deprecation warning
```

### Option 3: Persistence (Production) - Coming Soon

```python
# Future release will support:
from lionagi_qe.persistence import RedisMemory, PostgresMemory

# Redis
memory = RedisMemory(host="localhost", port=6379)

# PostgreSQL
memory = PostgresMemory(
    connection_string="postgresql://user:pass@localhost/db"
)
```

## Complete Examples

### Example 1: Basic Test Generation

**Before:**
```python
import asyncio
from lionagi import iModel
from lionagi_qe import QEFleet, QETask
from lionagi_qe.agents import TestGeneratorAgent

async def main():
    fleet = QEFleet(enable_routing=True)
    await fleet.initialize()

    model = iModel(provider="openai", model="gpt-4o-mini")
    agent = TestGeneratorAgent(
        agent_id="test-gen",
        model=model,
        memory=fleet.memory
    )

    fleet.register_agent(agent)

    task = QETask(
        task_type="generate_tests",
        context={"code": "def add(a, b): return a + b"}
    )

    result = await fleet.execute("test-gen", task)
    print(result)

asyncio.run(main())
```

**After:**
```python
import asyncio
from lionagi import iModel
from lionagi_qe import QEOrchestrator, QETask, ModelRouter
from lionagi_qe.core.memory import QEMemory
from lionagi_qe.agents import TestGeneratorAgent

async def main():
    # Explicit initialization
    memory = QEMemory()
    router = ModelRouter(enable_routing=True)
    orchestrator = QEOrchestrator(
        memory=memory,
        router=router,
        enable_learning=False
    )

    model = iModel(provider="openai", model="gpt-4o-mini")
    agent = TestGeneratorAgent(
        agent_id="test-gen",
        model=model,
        memory=memory
    )

    orchestrator.register_agent(agent)

    task = QETask(
        task_type="generate_tests",
        context={"code": "def add(a, b): return a + b"}
    )

    result = await orchestrator.execute_agent("test-gen", task)
    print(result)

asyncio.run(main())
```

### Example 2: Sequential Pipeline

See [examples/02_sequential_pipeline.py](/workspaces/lionagi-qe-fleet/examples/02_sequential_pipeline.py) for updated pipeline example.

### Example 3: Parallel Execution

See [examples/03_parallel_execution.py](/workspaces/lionagi-qe-fleet/examples/03_parallel_execution.py) for updated parallel execution example.

### Example 4: Fan-Out/Fan-In

See [examples/04_fan_out_fan_in.py](/workspaces/lionagi-qe-fleet/examples/04_fan_out_fan_in.py) for updated fan-out/fan-in example.

## Testing Migration

### Update Test Fixtures

**Before:**
```python
@pytest.fixture
async def qe_fleet():
    fleet = QEFleet(enable_routing=False)
    await fleet.initialize()
    return fleet
```

**After:**
```python
@pytest.fixture
async def qe_orchestrator(qe_memory, model_router):
    return QEOrchestrator(
        memory=qe_memory,
        router=model_router,
        enable_learning=False
    )
```

### Update Test Cases

**Before:**
```python
async def test_agent_execution(qe_fleet, test_agent):
    qe_fleet.register_agent(test_agent)
    result = await qe_fleet.execute("test-agent", task)
    assert result is not None
```

**After:**
```python
async def test_agent_execution(qe_orchestrator, test_agent):
    qe_orchestrator.register_agent(test_agent)
    result = await qe_orchestrator.execute_agent("test-agent", task)
    assert result is not None
```

## Common Pitfalls

### 1. Forgetting to Rename Methods

**Wrong:**
```python
result = await orchestrator.execute("agent-id", task)  # Old API
```

**Correct:**
```python
result = await orchestrator.execute_agent("agent-id", task)  # New API
```

### 2. Using fleet.initialize()

`QEOrchestrator` doesn't need initialization - remove `await fleet.initialize()` calls.

### 3. Status Method Name

**Wrong:**
```python
status = await orchestrator.get_status()  # Old method
```

**Correct:**
```python
status = await orchestrator.get_fleet_status()  # Correct method
```

## Hooks and Metrics

If you were using QEFleet's hooks feature:

**Before:**
```python
fleet = QEFleet(enable_hooks=True, cost_alert_threshold=10.0)
metrics = fleet.get_metrics()
dashboard = fleet.get_dashboard()
```

**After:**
```python
from lionagi_qe.core.hooks import QEHooks

# Create hooks separately
hooks = QEHooks(
    fleet_id="my-fleet",
    cost_alert_threshold=10.0
)

# Pass to router
router = ModelRouter(enable_routing=True, hooks=hooks)
orchestrator = QEOrchestrator(memory=memory, router=router)

# Access metrics
metrics = hooks.get_metrics()
dashboard = hooks.dashboard_ascii()
```

## FAQ

### Q: Can I still use QEFleet during migration?

Yes! QEFleet will continue to work with deprecation warnings until v2.0.0. This gives you time to migrate gradually.

### Q: Will my existing tests break?

No. We've updated the test fixtures to return `QEOrchestrator` when `qe_fleet` is used, maintaining backward compatibility.

### Q: What about QEMemory?

QEMemory is also deprecated but still usable. For production, plan to migrate to LionAGI's Session.context or future persistence backends.

### Q: Do I need to update all files at once?

No. You can migrate incrementally. Start with new code using `QEOrchestrator`, then update existing code module by module.

### Q: Where can I get help?

1. Check updated examples in `examples/` directory
2. Review `tests/` for test patterns
3. Open an issue on GitHub for specific questions

## Checklist

Use this checklist to track your migration:

- [ ] Update imports: `QEFleet` → `QEOrchestrator`
- [ ] Initialize components explicitly (memory, router, orchestrator)
- [ ] Remove `await fleet.initialize()` calls
- [ ] Update method calls: `execute()` → `execute_agent()`
- [ ] Update status calls: `get_status()` → `get_fleet_status()`
- [ ] Update test fixtures to use `qe_orchestrator`
- [ ] Update test cases to use new API
- [ ] Run tests to verify changes
- [ ] Update documentation and comments
- [ ] Remove QEFleet import statements

## Support

For migration assistance:
- GitHub Issues: [lionagi-qe-fleet/issues](https://github.com/your-org/lionagi-qe-fleet/issues)
- Documentation: [Full API Reference](../reference/orchestrator.md)
- Examples: [examples/](../../examples/)

---

**Last Updated**: 2025-11-05
**Migration Guide Version**: 1.0.0
