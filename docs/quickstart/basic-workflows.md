# Basic Workflows

Learn common patterns for coordinating multiple QE agents.

## Overview

The QE Fleet supports three fundamental workflow patterns:
1. **Sequential Pipeline** - Agents execute in order, passing results
2. **Parallel Execution** - Multiple agents work simultaneously
3. **Fan-Out/Fan-In** - Coordinator distributes work, then synthesizes

## Pattern 1: Sequential Pipeline

Execute agents in sequence, where each agent builds on the previous agent's work.

### When to Use
- Test generation → execution → coverage analysis
- Step-by-step workflows where order matters
- Results from one agent feed the next

### Example: Generate and Execute Tests

```python
import asyncio
from lionagi import iModel
from lionagi_qe import QEOrchestrator
from lionagi_qe.agents import TestGeneratorAgent, TestExecutorAgent

async def main():
    # Initialize orchestrator (with optional persistence)
    orchestrator = QEOrchestrator(
        memory_backend="postgres",  # or "memory" for dev
        enable_routing=True
    )
    await orchestrator.initialize()

    # Create model
    model = iModel(provider="openai", model="gpt-4o-mini")

    # Register agents (they share orchestrator's memory)
    test_gen = TestGeneratorAgent(
        agent_id="test-generator",
        model=model,
        memory=orchestrator.memory
    )
    test_exec = TestExecutorAgent(
        agent_id="test-executor",
        model=model,
        memory=orchestrator.memory
    )

    orchestrator.register_agent(test_gen)
    orchestrator.register_agent(test_exec)

    # Define pipeline (order matters!)
    pipeline = ["test-generator", "test-executor"]

    # Shared context flows through pipeline
    context = {
        "instruction": "Generate and execute comprehensive tests",
        "code": """
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
""",
        "framework": "pytest",
        "test_path": "./tests/test_fibonacci.py"
    }

    # Execute pipeline (results persist if using postgres backend)
    result = await orchestrator.execute_pipeline(pipeline, context)

    print("Pipeline complete!")
    print(f"Results: {result}")

asyncio.run(main())
```

**Key Points**:
- Agents execute in the order specified in `pipeline`
- Each agent can access results from previous agents via `memory`
- Context is shared and accumulated through the pipeline

## Pattern 2: Parallel Execution

Execute multiple agents simultaneously for independent tasks.

### When to Use
- Multiple test types (unit, integration, E2E)
- Independent quality checks (security, performance, visual)
- Need to minimize total execution time

### Example: Multiple Test Generators

```python
import asyncio
from lionagi import iModel
from lionagi_qe import QEOrchestrator, QETask
from lionagi_qe.agents import TestGeneratorAgent

async def main():
    # Initialize orchestrator
    orchestrator = QEOrchestrator(enable_routing=True)
    await orchestrator.initialize()

    model = iModel(provider="openai", model="gpt-4o-mini")

    # Create three generators for different test types
    agents = [
        TestGeneratorAgent(
            agent_id="test-generator-unit",
            model=model,
            memory=orchestrator.memory
        ),
        TestGeneratorAgent(
            agent_id="test-generator-integration",
            model=model,
            memory=orchestrator.memory
        ),
        TestGeneratorAgent(
            agent_id="test-generator-e2e",
            model=model,
            memory=orchestrator.memory
        ),
    ]

    for agent in agents:
        orchestrator.register_agent(agent)

    # Three independent tasks
    agent_ids = [
        "test-generator-unit",
        "test-generator-integration",
        "test-generator-e2e"
    ]

    tasks = [
        {
            "task_type": "generate_tests",
            "code": "def add(a, b): return a + b",
            "framework": "pytest",
            "test_type": "unit"
        },
        {
            "task_type": "generate_tests",
            "code": "def api_call(url): return requests.get(url).json()",
            "framework": "pytest",
            "test_type": "integration"
        },
        {
            "task_type": "generate_tests",
            "code": "def login_flow(): ...",
            "framework": "playwright",
            "test_type": "e2e"
        }
    ]

    # Execute all three simultaneously
    results = await orchestrator.execute_parallel(agent_ids, tasks)

    print(f"Generated {len(results)} test suites in parallel")
    for agent_id, result in zip(agent_ids, results):
        print(f"\n{agent_id}:")
        print(f"  Test: {result.test_name}")

asyncio.run(main())
```

**Key Points**:
- All agents execute concurrently (using `asyncio`)
- Tasks are independent - no dependencies between them
- Results come back in the same order as agent_ids
- Much faster than sequential execution

## Pattern 3: Fan-Out/Fan-In

Coordinator agent distributes work to workers, then synthesizes results.

### When to Use
- Complex requests requiring multiple perspectives
- Need intelligent task decomposition
- Want a single synthesized result from multiple agents

### Example: Fleet Commander Coordination

```python
import asyncio
from lionagi import iModel
from lionagi_qe import QEFleet
from lionagi_qe.agents import (
    FleetCommanderAgent,
    TestGeneratorAgent,
    SecurityScannerAgent,
    PerformanceTesterAgent
)

async def main():
    # Initialize fleet
    fleet = QEFleet(enable_routing=True)
    await fleet.initialize()

    model = iModel(provider="openai", model="gpt-4")

    # Create coordinator
    commander = FleetCommanderAgent(
        agent_id="fleet-commander",
        model=model,
        memory=fleet.memory
    )

    # Create workers
    test_gen = TestGeneratorAgent(
        agent_id="test-generator",
        model=iModel(provider="openai", model="gpt-4o-mini"),
        memory=fleet.memory
    )
    security = SecurityScannerAgent(
        agent_id="security-scanner",
        model=iModel(provider="openai", model="gpt-4o-mini"),
        memory=fleet.memory
    )
    performance = PerformanceTesterAgent(
        agent_id="performance-tester",
        model=iModel(provider="openai", model="gpt-4o-mini"),
        memory=fleet.memory
    )

    # Register all agents
    for agent in [commander, test_gen, security, performance]:
        fleet.register_agent(agent)

    # High-level request
    context = {
        "request": "Comprehensive QA for UserService API",
        "service": "UserService",
        "endpoints": ["/login", "/register", "/profile"],
        "requirements": [
            "Unit and integration tests",
            "Security scan (OWASP Top 10)",
            "Performance test (1000 RPS)"
        ]
    }

    # Fan-out: Commander decomposes and distributes
    # Workers execute in parallel
    # Fan-in: Commander synthesizes results
    result = await fleet.execute_fan_out_fan_in(
        coordinator="fleet-commander",
        workers=["test-generator", "security-scanner", "performance-tester"],
        context=context
    )

    print("QA Complete!")
    print(f"\nSynthesized Report:\n{result['synthesis']}")

asyncio.run(main())
```

**Key Points**:
- Coordinator (Fleet Commander) uses GPT-4 for intelligent decomposition
- Workers use GPT-4o-mini for cost-effective execution
- Commander synthesizes worker results into coherent report
- Best for complex, multi-faceted quality requests

## Combining Patterns

Real-world QE workflows often combine these patterns:

```python
# Example: Hybrid workflow
async def comprehensive_qa_workflow():
    fleet = QEFleet(enable_routing=True)
    await fleet.initialize()

    # Step 1: Parallel test generation (Pattern 2)
    test_results = await fleet.execute_parallel(
        agents=["test-gen-unit", "test-gen-integration"],
        tasks=[unit_task, integration_task]
    )

    # Step 2: Sequential execution and analysis (Pattern 1)
    qa_results = await fleet.execute_pipeline(
        pipeline=["test-executor", "coverage-analyzer", "quality-gate"],
        context={"generated_tests": test_results}
    )

    # Step 3: Fan-out for specialized checks (Pattern 3)
    final_report = await fleet.execute_fan_out_fan_in(
        coordinator="fleet-commander",
        workers=["security-scanner", "performance-tester"],
        context={"qa_results": qa_results}
    )

    return final_report
```

## Workflow Comparison

| Pattern | Use Case | Execution Time | Complexity |
|---------|----------|----------------|------------|
| **Sequential** | Dependent tasks | Sum of agents | Low |
| **Parallel** | Independent tasks | Max of agents | Low |
| **Fan-Out/Fan-In** | Complex coordination | Max of workers + coordination | Medium |

## Best Practices

### 1. Use Parallel When Possible
```python
# ❌ Slow: Sequential when tasks are independent
await fleet.execute_pipeline(
    ["security", "performance", "visual"],  # These could run in parallel!
    context
)

# ✅ Fast: Parallel for independent tasks
await fleet.execute_parallel(
    ["security", "performance", "visual"],
    [security_task, perf_task, visual_task]
)
```

### 2. Share Context via Memory
```python
# Store results for other agents
await fleet.memory.store("aqe/test-gen/results", test_results)

# Retrieve in another agent
previous_results = await fleet.memory.retrieve("aqe/test-gen/results")
```

### 3. Use Routing for Cost Optimization
```python
# Enable routing to use cheaper models for simple tasks
fleet = QEFleet(enable_routing=True)  # up to 80% theoretical cost savings
```

### 4. Monitor Fleet Status
```python
status = await fleet.get_status()
print(f"Workflows executed: {status['orchestration_metrics']['workflows_executed']}")
print(f"Total cost: ${status['routing_stats']['total_cost']:.4f}")
```

## Next Steps

Now that you understand basic workflows:

1. **Explore agents** → [Agent Catalog](../agents/index.md)
2. **Advanced patterns** → [Patterns: Sequential](../patterns/sequential-pipeline.md)
3. **System architecture** → [System Overview](../architecture/system-overview.md)

## Examples to Try

Run these examples from the repository:

```bash
# Sequential pipeline
python examples/02_sequential_pipeline.py

# Parallel execution
python examples/03_parallel_execution.py

# Fan-out/fan-in (if available)
python examples/04_fan_out_fan_in.py
```

---

**Next**: [Agent Catalog](../agents/index.md) - Explore all 18 specialized agents →
