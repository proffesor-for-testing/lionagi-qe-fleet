## 🚀 Quick Start Guide: LionAGI QE Fleet

Get up and running with the LionAGI QE Fleet in 5 minutes!

## Installation

### Using pip
```bash
pip install lionagi-qe-fleet
```

### From source
```bash
git clone <repository-url>
cd lionagi-qe-fleet
pip install -e ".[dev]"
```

## Setup API Keys

Create a `.env` file:

```bash
# Required for OpenAI models
OPENAI_API_KEY=your_openai_key_here

# Optional for Anthropic models
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional configuration
ENABLE_ROUTING=true
ENABLE_LEARNING=true
```

## Your First QE Agent

Create `my_first_test.py`:

```python
import asyncio
from lionagi import iModel
from lionagi_qe import QEFleet, QETask
from lionagi_qe.agents import TestGeneratorAgent


async def main():
    # 1. Initialize fleet
    fleet = QEFleet(enable_routing=True)
    await fleet.initialize()

    # 2. Create agent
    model = iModel(provider="openai", model="gpt-4o-mini")
    test_gen = TestGeneratorAgent(
        agent_id="test-generator",
        model=model,
        memory=fleet.memory
    )

    # 3. Register agent
    fleet.register_agent(test_gen)

    # 4. Create task
    task = QETask(
        task_type="generate_tests",
        context={
            "code": """
def add(a: int, b: int) -> int:
    return a + b
""",
            "framework": "pytest"
        }
    )

    # 5. Execute
    result = await fleet.execute("test-generator", task)

    # 6. Print results
    print(f"Test Name: {result.test_name}")
    print(f"\nGenerated Test:\n{result.test_code}")


if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python my_first_test.py
```

## Next Steps

### Example 1: Sequential Pipeline
```bash
python examples/02_sequential_pipeline.py
```

### Example 2: Parallel Execution
```bash
python examples/03_parallel_execution.py
```

### Example 3: Fan-Out/Fan-In
```bash
python examples/04_fan_out_fan_in.py
```

## Common Patterns

### Generate and Execute Tests
```python
# Sequential pipeline
result = await fleet.execute_pipeline(
    pipeline=["test-generator", "test-executor"],
    context={"code": code, "framework": "pytest"}
)
```

### Multi-Agent Parallel
```python
# Run multiple agents simultaneously
results = await fleet.execute_parallel(
    agents=["test-gen", "security", "performance"],
    tasks=[task1, task2, task3]
)
```

### Fleet Commander
```python
# Hierarchical coordination
result = await fleet.execute_fan_out_fan_in(
    coordinator="fleet-commander",
    workers=["agent1", "agent2", "agent3"],
    context={"request": "Comprehensive QA"}
)
```

## Available Agents

- **test-generator**: Generate comprehensive test suites
- **test-executor**: Execute tests with coverage
- **fleet-commander**: Coordinate multi-agent workflows
- ... (19 total agents)

See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for complete agent list.

## Documentation

- [Architecture](./LIONAGI_QE_FLEET_ARCHITECTURE.md)
- [Migration Guide](./MIGRATION_GUIDE.md)
- [Examples](../examples/)

## Getting Help

- 📖 Read the [documentation](./LIONAGI_QE_FLEET_ARCHITECTURE.md)
- 💬 Open an [issue](https://github.com/your-repo/issues)
- 🦁 Learn about [LionAGI](https://khive-ai.github.io/lionagi/)
