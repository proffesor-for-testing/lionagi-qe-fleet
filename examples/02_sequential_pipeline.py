"""Example 2: Sequential QE Pipeline

This example demonstrates pipeline orchestration using QEOrchestrator directly
instead of the deprecated QEFleet wrapper.
"""

import asyncio
from lionagi import iModel
from lionagi_qe import QEOrchestrator, ModelRouter
from lionagi_qe.core.memory import QEMemory
from lionagi_qe.agents import TestGeneratorAgent, TestExecutorAgent


async def main():
    """Execute a sequential QE pipeline: generate → execute → analyze"""

    # Initialize components directly
    memory = QEMemory()
    router = ModelRouter(enable_routing=True)
    orchestrator = QEOrchestrator(
        memory=memory,
        router=router,
        enable_learning=True
    )

    # Create model (or use router)
    model = iModel(provider="openai", model="gpt-4o-mini")

    # Register agents
    test_gen = TestGeneratorAgent(
        agent_id="test-generator",
        model=model,
        memory=memory
    )
    test_exec = TestExecutorAgent(
        agent_id="test-executor",
        model=model,
        memory=memory
    )

    orchestrator.register_agent(test_gen)
    orchestrator.register_agent(test_exec)

    # Define pipeline
    pipeline = [
        "test-generator",
        "test-executor",
    ]

    # Shared context for the pipeline
    context = {
        "instruction": "Generate and execute comprehensive tests",
        "code": """
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
""",
        "framework": "pytest",
        "test_path": "./tests/test_fibonacci.py",
        "coverage_target": 85,
        "parallel": True
    }

    # Execute pipeline using orchestrator
    print("🚀 Executing QE Pipeline...")
    print(f"Pipeline: {' → '.join(pipeline)}\n")

    result = await orchestrator.execute_pipeline(pipeline, context)

    print("\n✅ Pipeline Complete!")
    print(f"\n📊 Results:")
    for operation_id, operation_result in result.get("operation_results", {}).items():
        print(f"\nOperation {operation_id}:")
        print(f"Result: {operation_result}")

    # Get orchestrator metrics
    status = await orchestrator.get_fleet_status()
    print(f"\n📈 Orchestrator Metrics:")
    print(f"Workflows Executed: {status['orchestration_metrics']['workflows_executed']}")
    print(f"Total Agents Used: {status['orchestration_metrics']['total_agents_used']}")

    # Routing statistics
    routing_stats = status['routing_stats']
    print(f"\n💰 Cost Optimization:")
    print(f"Total Requests: {routing_stats['total_requests']}")
    print(f"Average Cost: ${routing_stats.get('average_cost', 0):.4f}")
    print(f"Estimated Savings: {routing_stats.get('savings_percentage', 0):.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
