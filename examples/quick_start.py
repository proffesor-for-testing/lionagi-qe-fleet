"""
LionAGI QE Fleet - Quick Start Example

A simple example showing how to use QE agents.
This demonstrates the basic usage pattern for all agents.
"""

import asyncio
from dotenv import load_dotenv
from lionagi import iModel

from lionagi_qe.core.memory import QEMemory
from lionagi_qe.core.task import QETask
from lionagi_qe.agents import CoverageAnalyzerAgent, QualityGateAgent

load_dotenv()


async def example_coverage_analysis():
    """Simple coverage analysis example"""
    print("\n" + "="*70)
    print("  Example 1: Coverage Analyzer - Finding Test Coverage Gaps")
    print("="*70 + "\n")

    # Step 1: Initialize the agent
    model = iModel(provider="openai", model="gpt-4o-mini")
    memory = QEMemory()

    agent = CoverageAnalyzerAgent(
        agent_id="coverage-analyzer",
        model=model,
        memory=memory
    )

    # Step 2: Prepare sample data
    coverage_data = {
        "overall": 78.5,
        "files": {
            "src/user_service.py": {
                "lines": {"covered": 85, "total": 100},
                "branches": {"covered": 20, "total": 30}
            },
            "src/payment_processor.py": {
                "lines": {"covered": 45, "total": 80},
                "branches": {"covered": 10, "total": 25}
            }
        }
    }

    # Step 3: Create a task
    task = QETask(
        task_type="analyze_coverage",
        context={
            "coverage_data": coverage_data,
            "framework": "pytest",
            "codebase_path": "/src",
            "target_coverage": 85
        }
    )

    # Step 4: Execute the agent
    print("🔍 Analyzing coverage...")
    result = await agent.execute(task)

    # Step 5: Use the results
    print(f"\n✅ Analysis Complete!")
    print(f"   Overall Coverage: {result.overall_coverage}%")
    print(f"   Line Coverage: {result.line_coverage}%")
    print(f"   Branch Coverage: {result.branch_coverage}%")
    print(f"   Gaps Found: {len(result.gaps)}")
    print(f"   Critical Paths: {len(result.critical_paths)}")
    print(f"   Analysis Time: {result.analysis_time_ms}ms")

    if result.gaps:
        print(f"\n📍 Coverage Gaps:")
        for gap in result.gaps[:3]:
            print(f"   • {gap.file_path} (lines {gap.line_start}-{gap.line_end})")
            print(f"     Severity: {gap.severity}, Critical Path: {gap.critical_path}")

    if result.optimization_suggestions:
        print(f"\n💡 Suggestions:")
        for suggestion in result.optimization_suggestions[:3]:
            print(f"   • {suggestion}")

    return result


async def example_quality_gate():
    """Simple quality gate example"""
    print("\n" + "="*70)
    print("  Example 2: Quality Gate - Deployment Decision")
    print("="*70 + "\n")

    # Initialize
    model = iModel(provider="openai", model="gpt-4o-mini")
    memory = QEMemory()

    agent = QualityGateAgent(
        agent_id="quality-gate",
        model=model,
        memory=memory
    )

    # Prepare data
    task = QETask(
        task_type="evaluate_quality",
        context={
            "test_results": {
                "total": 450,
                "passed": 445,
                "failed": 5,
                "skipped": 0
            },
            "coverage": {
                "overall": 92.5,
                "critical": 98.0
            },
            "code_quality": {
                "maintainability": 85,
                "complexity": 12
            },
            "security_scan": {
                "critical": 0,
                "high": 1,
                "medium": 3
            },
            "context": "production"
        }
    )

    # Execute
    print("🚦 Evaluating deployment readiness...")
    result = await agent.execute(task)

    # Display results
    print(f"\n✅ Evaluation Complete!")
    print(f"   Decision: {result.decision}")
    print(f"   Quality Score: {result.quality_score}/100")
    print(f"   Risk Level: {result.risk_level}")

    if result.decision == "GO":
        print(f"\n🟢 APPROVED for deployment!")
    elif result.decision == "NO_GO":
        print(f"\n🔴 BLOCKED - Issues must be resolved!")
    else:
        print(f"\n🟡 CONDITIONAL - Review recommendations!")

    if result.policy_violations:
        print(f"\n❌ Policy Violations:")
        for violation in result.policy_violations:
            print(f"   • {violation}")

    if result.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in result.recommendations[:3]:
            print(f"   • {rec}")

    return result


async def main():
    """Run quick start examples"""
    print("\n" + "="*70)
    print("  🤖 LionAGI QE Fleet - Quick Start Guide")
    print("="*70)
    print("\n  This demo shows the basic pattern for using QE agents:\n")
    print("  1. Initialize agent with model and memory")
    print("  2. Create a QETask with context data")
    print("  3. Execute the agent")
    print("  4. Process the structured results")
    print()

    try:
        # Run examples
        await example_coverage_analysis()
        await example_quality_gate()

        # Summary
        print("\n" + "="*70)
        print("  ✅ Quick Start Complete!")
        print("="*70)
        print("\n  All agents follow this same pattern:")
        print("     agent = AgentClass(agent_id, model, memory)")
        print("     task = QETask(task_type, context)")
        print("     result = await agent.execute(task)")
        print("\n  Next: Try examples/demo_qe_agents.py for all 8 agents!")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
