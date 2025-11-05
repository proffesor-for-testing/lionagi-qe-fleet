# Your First Agent

This tutorial walks you through creating and executing your first QE agent step by step.

## What You'll Build

A test generator agent that:
1. Analyzes Python code
2. Generates comprehensive pytest tests
3. Includes edge cases and assertions
4. Explains the reasoning behind each test

**Time to complete**: 5-10 minutes

## Prerequisites

- Completed [Installation](installation.md)
- Python 3.10+ installed
- OpenAI API key configured

## Step 1: Create Your Project

Create a new directory for your project:

```bash
mkdir my-qe-fleet
cd my-qe-fleet
```

Create a `.env` file with your API key:

```bash
echo "OPENAI_API_KEY=your-key-here" > .env
```

## Step 2: Write the Code

Create `my_first_agent.py`:

```python
import asyncio
from lionagi import iModel
from lionagi_qe import QETask
from lionagi_qe.agents import TestGeneratorAgent


async def main():
    # Step 1: Create a model
    # Using GPT-4o-mini for cost-effective test generation
    model = iModel(provider="openai", model="gpt-4o-mini")

    # Step 2: Create a test generator agent
    # No fleet or shared memory needed for single agent
    test_gen = TestGeneratorAgent(
        agent_id="test-generator",
        model=model
    )

    # Step 3: Define code to test
    code_to_test = """
def add(a: int, b: int) -> int:
    '''Add two numbers and return the result.'''
    return a + b

def divide(a: float, b: float) -> float:
    '''Divide a by b. Raises ZeroDivisionError if b is zero.'''
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b
"""

    # Step 4: Create a task
    task = QETask(
        task_type="generate_tests",
        context={
            "code": code_to_test,
            "framework": "pytest"
        }
    )

    # Step 5: Execute the agent
    print("Generating tests...")
    result = await test_gen.execute(task)

    # Step 6: Display results
    print("\n" + "=" * 60)
    print(f"Test Name: {result.test_name}")
    print("=" * 60)
    print(f"\nGenerated Test Code:\n{result.test_code}")
    print(f"\nFramework: {result.framework}")
    print(f"\nAssertions: {len(result.assertions)}")
    for i, assertion in enumerate(result.assertions, 1):
        print(f"  {i}. {assertion}")
    print(f"\nEdge Cases Covered: {len(result.edge_cases)}")
    for i, edge_case in enumerate(result.edge_cases, 1):
        print(f"  {i}. {edge_case}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Step 3: Run Your Agent

Execute the script:

```bash
python my_first_agent.py
```

Expected output:

```
Generating tests...
============================================================
Test Name: test_add_and_divide
============================================================

Generated Test Code:
import pytest

def test_add_positive_numbers():
    assert add(2, 3) == 5

def test_add_negative_numbers():
    assert add(-2, -3) == -5

def test_add_zero():
    assert add(0, 5) == 5
    assert add(5, 0) == 5

def test_divide_positive_numbers():
    assert divide(10, 2) == 5.0

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_divide_negative_numbers():
    assert divide(-10, 2) == -5.0

Framework: pytest

Assertions: 6
  1. add(2, 3) == 5
  2. add(-2, -3) == -5
  3. add(0, 5) == 5
  4. divide(10, 2) == 5.0
  5. divide(10, 0) raises ZeroDivisionError
  6. divide(-10, 2) == -5.0

Edge Cases Covered: 4
  1. Adding zero
  2. Adding negative numbers
  3. Division by zero
  4. Negative number division
```

## Step 4: Understanding the Code

Let's break down what happened:

### Model Creation
```python
model = iModel(provider="openai", model="gpt-4o-mini")
```
- Specifies which AI model to use
- GPT-4o-mini is cost-effective for test generation
- Can use other models: `gpt-4`, `claude-3-5-sonnet-20241022`, etc.

### Agent Creation
```python
test_gen = TestGeneratorAgent(
    agent_id="test-generator",
    model=model
)
```
- Creates a specialized test generation agent
- `agent_id` uniquely identifies this agent
- No shared memory needed for single agent usage
- Simple and direct - no orchestration overhead

### Task Execution
```python
task = QETask(
    task_type="generate_tests",
    context={"code": code_to_test, "framework": "pytest"}
)
result = await test_gen.execute(task)
```
- Creates a task with context (code + framework)
- Executes asynchronously (use `await`)
- Returns structured results (Pydantic model)
- Direct agent execution - no fleet wrapper needed

### When to Use QEOrchestrator?

For **multi-agent workflows** or **persistent memory**, use QEOrchestrator:

```python
from lionagi_qe import QEOrchestrator

orchestrator = QEOrchestrator(
    memory_backend="postgres",  # Persistent storage
    enable_routing=True  # Intelligent model selection
)
await orchestrator.initialize()

# Register and execute
orchestrator.register_agent(test_gen)
result = await orchestrator.execute_agent("test-generator", task)
```

## Step 5: Experiment

Try modifying the code:

### Change the Model
```python
# Use GPT-4 for more sophisticated tests
model = iModel(provider="openai", model="gpt-4")

# Or use Claude for different reasoning
model = iModel(provider="anthropic", model="claude-3-5-sonnet-20241022")
```

### Test Different Code
```python
code_to_test = """
def calculate_discount(price: float, discount_percent: float) -> float:
    '''Calculate final price after discount.'''
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")
    return price * (1 - discount_percent / 100)
"""
```

### Change Framework
```python
task = QETask(
    task_type="generate_tests",
    context={
        "code": code_to_test,
        "framework": "unittest"  # Or "jest", "mocha"
    }
)
```

## Common Issues

### Issue: "OPENAI_API_KEY not found"

**Solution**: Load environment variables:
```python
from dotenv import load_dotenv
load_dotenv()  # Add at the top of your script
```

### Issue: "Model not available"

**Solution**: Check supported models:
```python
from lionagi import iModel
print(iModel.list_providers())  # See available providers
```

### Issue: Async errors

**Solution**: Always use `await` inside `async def`:
```python
# Wrong
result = fleet.execute("test-generator", task)  # Missing await

# Correct
result = await fleet.execute("test-generator", task)
```

## What's Next?

Now that you've created your first agent, explore:

1. **Multiple agents** → [Basic Workflows](basic-workflows.md)
2. **Sequential pipelines** → [Patterns: Sequential](../patterns/sequential-pipeline.md)
3. **All available agents** → [Agent Catalog](../agents/index.md)

## Key Takeaways

- **QEFleet** manages agents and provides coordination
- **Agents** are specialists (test generation, execution, analysis)
- **Tasks** define what agents should do
- **Results** are structured Pydantic models
- **Everything is async** - use `await` for operations

---

**Next**: [Basic Workflows](basic-workflows.md) - Coordinate multiple agents →
