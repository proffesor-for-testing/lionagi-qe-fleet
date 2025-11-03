"""Example 3: Parallel Multi-Agent Execution"""

import asyncio
from lionagi import iModel
from lionagi_qe import QEFleet
from lionagi_qe.agents import TestGeneratorAgent, TestExecutorAgent


async def main():
    """Execute multiple agents in parallel for different tasks"""

    # Initialize fleet
    fleet = QEFleet(enable_routing=True)
    await fleet.initialize()

    # Create agents
    model = iModel(provider="openai", model="gpt-4o-mini")

    agents_to_register = [
        TestGeneratorAgent(
            agent_id="test-generator-unit",
            model=model,
            memory=fleet.memory
        ),
        TestGeneratorAgent(
            agent_id="test-generator-integration",
            model=model,
            memory=fleet.memory
        ),
        TestExecutorAgent(
            agent_id="test-executor-fast",
            model=model,
            memory=fleet.memory
        ),
    ]

    for agent in agents_to_register:
        fleet.register_agent(agent)

    # Define parallel tasks
    agent_ids = [
        "test-generator-unit",
        "test-generator-integration",
        "test-executor-fast"
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
        # Test execution
        {
            "task_type": "execute_tests",
            "test_path": "./tests",
            "framework": "pytest",
            "parallel": True
        }
    ]

    # Execute in parallel
    print("🚀 Executing 3 Agents in Parallel...\n")

    results = await fleet.execute_parallel(agent_ids, tasks)

    print("\n✅ Parallel Execution Complete!")
    print(f"\n📊 Results:\n")

    for i, (agent_id, result) in enumerate(zip(agent_ids, results)):
        print(f"{i+1}. {agent_id}:")
        print(f"   Task Type: {tasks[i]['task_type']}")
        print(f"   Result: {type(result).__name__}")
        if hasattr(result, 'test_name'):
            print(f"   Generated: {result.test_name}")
        if hasattr(result, 'total_tests'):
            print(f"   Tests Executed: {result.total_tests}")
        print()

    # Fleet status
    status = await fleet.get_status()
    print(f"Total Agents Used: {status['orchestration_metrics']['total_agents_used']}")


if __name__ == "__main__":
    asyncio.run(main())
