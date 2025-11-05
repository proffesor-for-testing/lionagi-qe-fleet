"""Example 4: Fan-Out/Fan-In Pattern with Fleet Commander

This example demonstrates fan-out/fan-in orchestration using QEOrchestrator directly
instead of the deprecated QEFleet wrapper.
"""

import asyncio
from lionagi import iModel
from lionagi_qe import QEOrchestrator, ModelRouter
from lionagi_qe.core.memory import QEMemory
from lionagi_qe.agents import (
    FleetCommanderAgent,
    TestGeneratorAgent,
    TestExecutorAgent
)


async def main():
    """Fan-out/fan-in: Commander decomposes, workers execute, commander synthesizes"""

    # Initialize components directly
    memory = QEMemory()
    router = ModelRouter(enable_routing=True)
    orchestrator = QEOrchestrator(
        memory=memory,
        router=router,
        enable_learning=True
    )

    # Create models
    commander_model = iModel(provider="openai", model="gpt-4")  # More powerful
    worker_model = iModel(provider="openai", model="gpt-4o-mini")  # Cost-effective

    # Create fleet commander
    commander = FleetCommanderAgent(
        agent_id="fleet-commander",
        model=commander_model,
        memory=memory
    )

    # Create worker agents
    workers = [
        TestGeneratorAgent(
            agent_id="test-generator",
            model=worker_model,
            memory=memory
        ),
        TestExecutorAgent(
            agent_id="test-executor",
            model=worker_model,
            memory=memory
        ),
    ]

    # Register all agents with orchestrator
    orchestrator.register_agent(commander)
    for worker in workers:
        orchestrator.register_agent(worker)

    # Execute fan-out/fan-in
    context = {
        "request": """
Perform comprehensive quality assurance for a new API endpoint:

Endpoint: POST /api/users
Functionality: Create new user accounts
Requirements:
- Email validation
- Password strength checking
- Duplicate email detection
- Return 201 on success
- Return 400 on validation errors

Tasks:
1. Generate comprehensive test suite
2. Execute tests with coverage analysis
3. Provide quality assessment
""",
        "project_path": "./api",
        "coverage_target": 90
    }

    print("🚀 Executing Fan-Out/Fan-In Pattern...")
    print("Commander → Workers → Synthesis\n")

    result = await orchestrator.execute_fan_out_fan_in(
        coordinator="fleet-commander",
        workers=["test-generator", "test-executor"],
        context=context
    )

    print("\n✅ Workflow Complete!")
    print(f"\n📋 Decomposition:")
    for i, subtask in enumerate(result['decomposition'], 1):
        print(f"  {i}. {subtask.get('instruction', 'Subtask')}")

    print(f"\n🔧 Worker Results:")
    for i, worker_result in enumerate(result['worker_results'], 1):
        print(f"  Worker {i}: {type(worker_result).__name__}")

    print(f"\n📊 Final Synthesis:")
    print(result['synthesis'][:500] + "..." if len(result['synthesis']) > 500 else result['synthesis'])

    # Get comprehensive status from orchestrator
    status = await orchestrator.get_fleet_status()
    print(f"\n💰 Cost Analysis:")
    routing_stats = status['routing_stats']
    print(f"  Total Cost: ${routing_stats['total_cost']:.4f}")
    print(f"  Estimated Savings: {routing_stats.get('savings_percentage', 0):.1f}%")
    print(f"  Model Distribution:")
    for level, percentage in routing_stats.get('distribution', {}).items():
        print(f"    {level}: {percentage:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
