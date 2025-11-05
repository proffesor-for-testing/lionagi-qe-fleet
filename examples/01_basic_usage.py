"""Example 1: Basic QE Orchestrator Usage

This example demonstrates the updated API using QEOrchestrator directly
instead of the deprecated QEFleet wrapper.
"""

import asyncio
from lionagi import iModel, Session
from lionagi_qe import QEOrchestrator, QETask, ModelRouter
from lionagi_qe.core.memory import QEMemory
from lionagi_qe.agents import TestGeneratorAgent


async def main():
    """Basic usage: Generate tests for a simple function"""

    # Initialize components directly (no QEFleet wrapper)
    memory = QEMemory()  # For simple examples; use Session().context or persistence in production
    router = ModelRouter(enable_routing=True)
    orchestrator = QEOrchestrator(
        memory=memory,
        router=router,
        enable_learning=False
    )

    # Create a test generator agent
    model = iModel(provider="openai", model="gpt-4o-mini")
    test_gen = TestGeneratorAgent(
        agent_id="test-generator",
        model=model,
        memory=memory,
        skills=["tdd", "property-based-testing"]
    )

    # Register the agent with orchestrator
    orchestrator.register_agent(test_gen)

    # Create a test generation task
    code_to_test = """
def add(a: int, b: int) -> int:
    \"\"\"Add two numbers\"\"\"
    return a + b

def divide(a: float, b: float) -> float:
    \"\"\"Divide a by b\"\"\"
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
"""

    task = QETask(
        task_type="generate_tests",
        context={
            "code": code_to_test,
            "framework": "pytest",
            "test_type": "unit",
            "coverage_target": 90
        }
    )

    # Execute the task using orchestrator
    print("🚀 Generating tests...")
    result = await orchestrator.execute_agent("test-generator", task)

    print("\n✅ Test Generation Complete!")
    print(f"\nTest Name: {result.test_name}")
    print(f"Framework: {result.framework}")
    print(f"Test Type: {result.test_type}")
    print(f"Edge Cases Covered: {len(result.edge_cases)}")
    print(f"Estimated Coverage: {result.coverage_estimate}%")
    print(f"\n📝 Generated Test Code:\n")
    print(result.test_code)

    # Get orchestrator status
    status = await orchestrator.get_fleet_status()
    print(f"\n📊 Orchestrator Status:")
    print(f"Total Agents: {status['total_agents']}")
    print(f"Routing Stats: {status['routing_stats']}")


if __name__ == "__main__":
    asyncio.run(main())
