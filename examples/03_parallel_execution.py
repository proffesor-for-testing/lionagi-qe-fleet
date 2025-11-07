"""Example 3: Parallel Multi-Agent Execution

This example demonstrates parallel agent execution using QEOrchestrator directly
instead of the deprecated QEFleet wrapper.
"""

import asyncio
from lionagi import iModel
from lionagi_qe import QEOrchestrator, ModelRouter
from lionagi_qe.core.memory import QEMemory
from lionagi_qe.agents import TestGeneratorAgent, CoverageAnalyzerAgent


async def main():
    """Execute multiple agents in parallel for different tasks"""

    # Initialize components directly
    memory = QEMemory()
    router = ModelRouter(enable_routing=True)
    orchestrator = QEOrchestrator(
        memory=memory,
        router=router,
        enable_learning=True  # Enable Q-Learning for continuous improvement
    )

    # Create agents
    model = iModel(provider="openai", model="gpt-4o-mini")

    agents_to_register = [
        TestGeneratorAgent(
            agent_id="test-generator-unit",
            model=model,
            memory=memory
        ),
        TestGeneratorAgent(
            agent_id="test-generator-integration",
            model=model,
            memory=memory
        ),
        CoverageAnalyzerAgent(
            agent_id="coverage-analyzer",
            model=model,
            memory=memory
        ),
    ]

    for agent in agents_to_register:
        orchestrator.register_agent(agent)

    # Define parallel tasks
    agent_ids = [
        "test-generator-unit",
        "test-generator-integration",
        "coverage-analyzer"
    ]

    tasks = [
        # Unit test generation
        {
            "task_type": "generate_tests",
            "code": "def multiply(a, b): return a * b",
            "framework": "pytest",
            "test_type": "unit"
        },
        # Integration test generation
        {
            "task_type": "generate_tests",
            "code": "def api_call(url): return requests.get(url).json()",
            "framework": "pytest",
            "test_type": "integration"
        },
        # Coverage analysis
        {
            "task_type": "analyze_coverage",
            "coverage_data": {},  # Would contain actual coverage data
            "framework": "pytest",
            "codebase_path": "./src",
            "target_coverage": 80.0
        }
    ]

    # Execute in parallel using orchestrator
    print("🚀 Executing 3 Agents in Parallel...\n")

    results = await orchestrator.execute_parallel(agent_ids, tasks)

    print("\n✅ Parallel Execution Complete!")
    print(f"\n📊 Results:\n")

    for i, (agent_id, result) in enumerate(zip(agent_ids, results)):
        print(f"{i+1}. {agent_id}:")
        print(f"   Task Type: {tasks[i]['task_type']}")
        print(f"   Result: {type(result).__name__}")
        if hasattr(result, 'test_name'):
            print(f"   Generated: {result.test_name}")
        if hasattr(result, 'overall_coverage'):
            print(f"   Coverage: {result.overall_coverage:.1f}%")
            print(f"   Gaps Found: {len(result.gaps)}")
        print()

    # Orchestrator status
    status = await orchestrator.get_fleet_status()
    print(f"Total Agents Used: {status['orchestration_metrics']['total_agents_used']}")


if __name__ == "__main__":
    asyncio.run(main())
