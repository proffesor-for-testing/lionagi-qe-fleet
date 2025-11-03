"""Example usage of LionAGI QE Fleet via MCP

This example demonstrates how to use the MCP server to interact
with the QE Fleet programmatically.
"""

import asyncio
from lionagi_qe.mcp.mcp_server import create_mcp_server
from lionagi_qe.mcp import mcp_tools


async def example_test_generation():
    """Example: Generate tests using MCP tools"""
    print("\n=== Test Generation Example ===\n")

    # Sample code to test
    code = """
class UserService:
    def __init__(self, db):
        self.db = db

    async def get_user(self, user_id: int):
        if user_id <= 0:
            raise ValueError("Invalid user ID")
        return await self.db.users.find_one({"id": user_id})

    async def create_user(self, name: str, email: str):
        if not name or not email:
            raise ValueError("Name and email required")

        user = {
            "name": name,
            "email": email,
            "created_at": datetime.now()
        }
        return await self.db.users.insert_one(user)
"""

    # Generate tests
    result = await mcp_tools.test_generate(
        code=code,
        framework=mcp_tools.TestFramework.PYTEST,
        test_type=mcp_tools.TestType.UNIT,
        coverage_target=90.0,
        include_edge_cases=True
    )

    print(f"Test Name: {result['test_name']}")
    print(f"Framework: {result['framework']}")
    print(f"Coverage Estimate: {result['coverage_estimate']}%")
    print(f"\nEdge Cases Covered:")
    for edge_case in result['edge_cases']:
        print(f"  - {edge_case}")

    print(f"\nGenerated Test Code:")
    print("=" * 60)
    print(result['test_code'])
    print("=" * 60)


async def example_pipeline_workflow():
    """Example: Sequential pipeline workflow"""
    print("\n=== Pipeline Workflow Example ===\n")

    # Execute sequential pipeline
    result = await mcp_tools.fleet_orchestrate(
        workflow="pipeline",
        agents=[
            "test-generator",
            "test-executor",
            "coverage-analyzer",
            "quality-gate"
        ],
        context={
            "code_path": "./src/user_service.py",
            "framework": "pytest",
            "coverage_threshold": 80.0
        }
    )

    print("Pipeline completed successfully!")
    print(f"Agents used: {result.get('agents_used', [])}")
    print(f"Duration: {result.get('duration', 0):.2f}s")
    print(f"Success: {result.get('success', False)}")


async def example_parallel_execution():
    """Example: Parallel execution of independent tasks"""
    print("\n=== Parallel Execution Example ===\n")

    # Execute multiple agents in parallel
    result = await mcp_tools.fleet_orchestrate(
        workflow="parallel",
        agents=[
            "test-generator",
            "security-scanner",
            "performance-tester"
        ],
        context={
            "code_path": "./src",
            "framework": "pytest"
        }
    )

    print("Parallel execution completed!")
    print(f"Results: {len(result.get('results', []))} agents")


async def example_streaming_execution():
    """Example: Streaming test execution with progress"""
    print("\n=== Streaming Execution Example ===\n")

    # Execute tests with real-time progress
    async for event in mcp_tools.test_execute_stream(
        test_path="./tests",
        framework=mcp_tools.TestFramework.PYTEST,
        parallel=True,
        coverage=True
    ):
        if event["type"] == "progress":
            percent = event["percent"]
            message = event["message"]
            print(f"[{percent:5.1f}%] {message}")
        elif event["type"] == "result":
            result = event["data"]
            print(f"\n✓ Tests completed:")
            print(f"  Passed: {result['passed']}")
            print(f"  Failed: {result['failed']}")
            print(f"  Coverage: {result['coverage']:.1f}%")


async def example_quality_gate():
    """Example: Quality gate validation"""
    print("\n=== Quality Gate Example ===\n")

    # Define metrics
    metrics = {
        "coverage": 85.0,
        "complexity": 8.5,
        "duplication": 3.2,
        "security_score": 95.0,
        "test_pass_rate": 98.5
    }

    # Define thresholds
    thresholds = {
        "coverage": 80.0,
        "complexity": 10.0,
        "duplication": 5.0,
        "security_score": 90.0,
        "test_pass_rate": 95.0
    }

    # Run quality gate
    result = await mcp_tools.quality_gate(
        metrics=metrics,
        thresholds=thresholds
    )

    print(f"Quality Gate: {'PASSED ✓' if result['passed'] else 'FAILED ✗'}")
    print(f"Quality Score: {result['score']}/100")

    if result['violations']:
        print("\nViolations:")
        for violation in result['violations']:
            print(f"  ✗ {violation}")

    if result['recommendations']:
        print("\nRecommendations:")
        for rec in result['recommendations']:
            print(f"  → {rec}")


async def example_security_scan():
    """Example: Security scanning"""
    print("\n=== Security Scan Example ===\n")

    result = await mcp_tools.security_scan(
        path="./src",
        scan_type=mcp_tools.ScanType.COMPREHENSIVE,
        severity_threshold="medium"
    )

    print(f"Security Risk Score: {result['risk_score']}/100")
    print(f"\nVulnerabilities by Severity:")
    for severity, count in result['severity_counts'].items():
        print(f"  {severity}: {count}")

    if result['vulnerabilities']:
        print(f"\nTop Vulnerabilities:")
        for vuln in result['vulnerabilities'][:5]:
            print(f"  [{vuln['severity']}] {vuln['title']}")


async def example_fleet_status():
    """Example: Get fleet status and metrics"""
    print("\n=== Fleet Status Example ===\n")

    status = await mcp_tools.get_fleet_status()

    print(f"Fleet Initialized: {status.get('initialized', False)}")

    if status.get('agents'):
        print(f"\nRegistered Agents: {len(status['agents'])}")
        for agent in status['agents'][:5]:
            print(f"  - {agent.get('agent_id', 'unknown')}")

    if status.get('memory_stats'):
        print(f"\nMemory Statistics:")
        mem = status['memory_stats']
        print(f"  Keys: {mem.get('total_keys', 0)}")
        print(f"  Partitions: {mem.get('partitions', 0)}")

    if status.get('routing_stats'):
        print(f"\nRouting Statistics:")
        routing = status['routing_stats']
        print(f"  Total Requests: {routing.get('total_requests', 0)}")
        print(f"  Cost Savings: {routing.get('cost_savings', 0):.2f}%")


async def main():
    """Main function to run all examples"""
    print("\n" + "=" * 70)
    print("LionAGI QE Fleet - MCP Usage Examples")
    print("=" * 70)

    # Create and start MCP server
    print("\nInitializing MCP server...")
    server = create_mcp_server(
        enable_routing=True,
        enable_learning=False
    )
    await server.start()

    try:
        # Run examples (comment out as needed)

        # Basic examples
        await example_fleet_status()
        # await example_test_generation()

        # Workflow examples
        # await example_pipeline_workflow()
        # await example_parallel_execution()
        # await example_streaming_execution()

        # Quality examples
        # await example_quality_gate()
        # await example_security_scan()

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Stop server
        print("\nStopping MCP server...")
        await server.stop()

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    """
    Run examples:

    python examples/mcp_usage.py
    """
    asyncio.run(main())
