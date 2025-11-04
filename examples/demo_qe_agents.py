"""
LionAGI QE Fleet - Complete Agent Demonstration

This script demonstrates all QE agents in action:
1. Coverage Analyzer - Find gaps in test coverage
2. Quality Gate - Make GO/NO-GO deployment decisions
3. Quality Analyzer - Comprehensive quality metrics
4. Chaos Engineer - Test system resilience
5. API Contract Validator - Detect breaking changes
6. Flaky Test Hunter - Stabilize unreliable tests
7. Test Data Architect - Generate realistic test data
8. Regression Risk Analyzer - Smart test selection
"""

import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv
from lionagi import iModel

from lionagi_qe.core.memory import QEMemory
from lionagi_qe.core.task import QETask
from lionagi_qe.agents import (
    CoverageAnalyzerAgent,
    QualityGateAgent,
    QualityAnalyzerAgent,
    ChaosEngineerAgent,
    APIContractValidatorAgent,
    FlakyTestHunterAgent,
    TestDataArchitectAgent,
    RegressionRiskAnalyzerAgent,
)

# Load environment variables
load_dotenv()


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_result(result, title: str = "Result"):
    """Pretty print a result"""
    print(f"\n{title}:")
    print("-" * 60)
    if hasattr(result, 'model_dump'):
        print(json.dumps(result.model_dump(), indent=2, default=str))
    else:
        print(json.dumps(result, indent=2, default=str))
    print("-" * 60)


async def demo_coverage_analyzer():
    """Demo: Coverage Analyzer - Find gaps in test coverage"""
    print_section("1. Coverage Analyzer - Finding Test Coverage Gaps")

    # Initialize
    model = iModel(provider="openai", model="gpt-4o-mini")
    memory = QEMemory()
    agent = CoverageAnalyzerAgent(
        agent_id="coverage-analyzer",
        model=model,
        memory=memory
    )

    print("🔍 Analyzing test coverage with O(log n) gap detection...")

    # Sample coverage data
    coverage_data = {
        "overall": 78.5,
        "files": {
            "src/auth/user_service.py": {
                "lines": {"covered": 85, "total": 100},
                "branches": {"covered": 20, "total": 30}
            },
            "src/payment/processor.py": {
                "lines": {"covered": 45, "total": 80},
                "branches": {"covered": 10, "total": 25}
            }
        }
    }

    task = QETask(
        task_type="analyze_coverage",
        context={
            "coverage_data": coverage_data,
            "framework": "pytest",
            "codebase_path": "/src",
            "target_coverage": 85
        }
    )

    result = await agent.execute(task)

    print(f"✅ Overall Coverage: {result.overall_coverage}%")
    print(f"📊 Gaps Found: {len(result.gaps)}")
    print(f"🎯 Critical Paths: {len(result.critical_paths)}")
    print(f"⚡ Analysis Time: {result.analysis_time_ms}ms")

    if result.gaps:
        print("\n📍 Top Coverage Gaps:")
        for i, gap in enumerate(result.gaps[:3], 1):
            print(f"  {i}. {gap.file_path} (lines {gap.line_start}-{gap.line_end}) - Severity: {gap.severity}")

    if result.optimization_suggestions:
        print("\n💡 Optimization Suggestions:")
        for i, suggestion in enumerate(result.optimization_suggestions[:3], 1):
            print(f"  {i}. {suggestion}")

    return result


async def demo_quality_gate():
    """Demo: Quality Gate - Make GO/NO-GO deployment decisions"""
    print_section("2. Quality Gate - GO/NO-GO Deployment Decision")

    model = iModel(provider="openai", model="gpt-4o-mini")
    memory = QEMemory()
    agent = QualityGateAgent(
        agent_id="quality-gate",
        model=model,
        memory=memory
    )

    print("🚦 Evaluating deployment readiness...")

    task = QETask(
        task_type="evaluate_quality",
        context={
            "test_results": {
                "total": 450,
                "passed": 445,
                "failed": 5,
                "skipped": 0
            },
            "coverage": {"overall": 92.5, "critical": 98.0},
            "code_quality": {"maintainability": 85, "complexity": 12},
            "security_scan": {"critical": 0, "high": 1, "medium": 3},
            "context": "production",
            "thresholds": {
                "min_coverage": 85,
                "max_failures": 10,
                "max_critical_security": 0
            }
        }
    )

    result = await agent.execute(task)

    print(f"\n🎯 Decision: {result.decision}")
    print(f"📊 Quality Score: {result.quality_score}/100")
    print(f"⚠️  Policy Violations: {len(result.policy_violations)}")

    if result.policy_violations:
        print("\n❌ Policy Violations:")
        for violation in result.policy_violations:
            print(f"  • {violation}")

    if result.recommendations:
        print("\n💡 Recommendations:")
        for i, rec in enumerate(result.recommendations[:3], 1):
            print(f"  {i}. {rec}")

    return result


async def demo_api_contract_validator():
    """Demo: API Contract Validator - Detect breaking changes"""
    print_section("3. API Contract Validator - Breaking Change Detection")

    model = iModel(provider="openai", model="gpt-4o-mini")
    memory = QEMemory()
    agent = APIContractValidatorAgent(
        agent_id="api-validator",
        model=model,
        memory=memory
    )

    print("🔍 Validating API contract changes...")

    baseline_schema = {
        "openapi": "3.0.0",
        "paths": {
            "/users": {
                "get": {
                    "parameters": [
                        {"name": "limit", "required": False}
                    ],
                    "responses": {
                        "200": {"description": "List of users"}
                    }
                }
            }
        }
    }

    candidate_schema = {
        "openapi": "3.0.0",
        "paths": {
            "/users": {
                "get": {
                    "parameters": [
                        {"name": "limit", "required": True},  # Breaking: now required
                        {"name": "page", "required": True}    # Breaking: new required param
                    ],
                    "responses": {
                        "200": {"description": "List of users"}
                    }
                }
            }
        }
    }

    task = QETask(
        task_type="api_contract_validation",
        context={
            "baseline_schema": baseline_schema,
            "candidate_schema": candidate_schema,
            "current_version": "1.5.0",
            "proposed_version": "2.0.0",
            "consumers": ["mobile-app", "web-dashboard"]
        }
    )

    result = await agent.execute(task)

    print(f"\n✅ Validation: {'PASSED' if result.validation.valid else 'FAILED'}")
    print(f"⚠️  Breaking Changes: {len(result.breaking_changes.breaking_changes)}")
    print(f"📊 Version Bump: {result.version_recommendation.recommended_bump}")
    print(f"🎯 Recommendation: {result.recommendation}")

    if result.breaking_changes.breaking_changes:
        print("\n💥 Breaking Changes Detected:")
        for i, change in enumerate(result.breaking_changes.breaking_changes[:3], 1):
            print(f"  {i}. {change.type} at {change.path} - Severity: {change.severity}")

    return result


async def demo_flaky_test_hunter():
    """Demo: Flaky Test Hunter - Stabilize unreliable tests"""
    print_section("4. Flaky Test Hunter - Detecting Unreliable Tests")

    model = iModel(provider="openai", model="gpt-4o-mini")
    memory = QEMemory()
    agent = FlakyTestHunterAgent(
        agent_id="flaky-hunter",
        model=model,
        memory=memory
    )

    print("🔍 Analyzing test stability patterns...")

    # Simulate test results over 20 runs
    test_results = {
        "test_user_login": [True] * 20,  # Always passes
        "test_payment_processing": [True, False, True, True, False] + [True] * 15,  # Flaky!
        "test_api_timeout": [True] * 18 + [False, True],  # Slightly flaky
    }

    task = QETask(
        task_type="detect_flaky_tests",
        context={
            "test_results": test_results,
            "min_runs": 10,
            "auto_fix": False,
            "target_reliability": 0.95
        }
    )

    result = await agent.execute(task)

    print(f"\n🎯 Flaky Tests Found: {len(result.flaky_tests)}")
    print(f"✅ Stable Tests: {len(result.stable_tests)}")
    print(f"📊 Overall Reliability: {result.overall_reliability:.2%}")

    if result.flaky_tests:
        print("\n⚠️  Flaky Tests:")
        for flaky in result.flaky_tests[:3]:
            print(f"  • {flaky.test_name} - Reliability: {flaky.reliability_score:.2%}")
            if flaky.root_causes:
                print(f"    Root Cause: {flaky.root_causes[0]}")

    return result


async def demo_test_data_architect():
    """Demo: Test Data Architect - Generate realistic test data"""
    print_section("5. Test Data Architect - Generating Test Data")

    model = iModel(provider="openai", model="gpt-4o-mini")
    memory = QEMemory()
    agent = TestDataArchitectAgent(
        agent_id="test-data",
        model=model,
        memory=memory
    )

    print("🏗️  Generating realistic test data at scale...")

    schema = {
        "User": {
            "fields": {
                "id": "uuid",
                "email": "email",
                "age": "integer[18:100]",
                "created_at": "datetime"
            },
            "relationships": {
                "orders": "hasMany:Order"
            }
        },
        "Order": {
            "fields": {
                "id": "uuid",
                "user_id": "uuid",
                "amount": "decimal[10:10000]",
                "status": "enum[pending,completed,cancelled]"
            }
        }
    }

    task = QETask(
        task_type="generate_test_data",
        context={
            "schema_source": schema,
            "record_count": 100,
            "include_edge_cases": True,
            "anonymize": True
        }
    )

    result = await agent.execute(task)

    print(f"\n✅ Records Generated: {result.generation_summary.total_records}")
    print(f"⚡ Generation Speed: {result.generation_summary.records_per_second:.0f} records/sec")
    print(f"📊 Quality Score: {result.quality_metrics.quality_score}/100")
    print(f"🎯 Edge Cases: {result.quality_metrics.edge_case_coverage}%")

    print("\n📦 Datasets Created:")
    for entity, count in result.generation_summary.entities.items():
        print(f"  • {entity}: {count} records")

    return result


async def demo_regression_risk_analyzer():
    """Demo: Regression Risk Analyzer - Smart test selection"""
    print_section("6. Regression Risk Analyzer - Smart Test Selection")

    model = iModel(provider="openai", model="gpt-4o-mini")
    memory = QEMemory()
    agent = RegressionRiskAnalyzerAgent(
        agent_id="regression-risk",
        model=model,
        memory=memory
    )

    print("🤖 Analyzing code changes for regression risk...")

    code_changes = """
    diff --git a/src/payment/processor.py b/src/payment/processor.py
    @@ -45,7 +45,10 @@ def process_payment(amount, currency):
         if amount <= 0:
             raise ValueError("Amount must be positive")
    -    return charge_card(amount, currency)
    +    # New feature: multi-currency support
    +    converted_amount = convert_currency(amount, currency, "USD")
    +    result = charge_card(converted_amount, "USD")
    +    return result
    """

    task = QETask(
        task_type="analyze_regression_risk",
        context={
            "code_changes": code_changes,
            "baseline_version": "v1.5.0",
            "confidence_threshold": 0.95
        }
    )

    result = await agent.execute(task)

    print(f"\n⚠️  Overall Risk: {result.overall_risk}")
    print(f"📊 Confidence: {result.confidence:.2%}")
    print(f"🎯 Recommended Tests: {len(result.recommended_tests)}")
    print(f"⏱️  Estimated Time Savings: {result.optimization.time_savings_percentage:.0f}%")

    print("\n🔍 High-Risk Areas:")
    for area in result.risk_by_area[:3]:
        print(f"  • {area.area} - Risk: {area.risk_level} (Score: {area.risk_score})")

    if result.recommended_tests:
        print("\n✅ Recommended Tests to Run:")
        for i, test in enumerate(result.recommended_tests[:5], 1):
            print(f"  {i}. {test}")

    return result


async def demo_chaos_engineer():
    """Demo: Chaos Engineer - Test system resilience"""
    print_section("7. Chaos Engineer - Resilience Testing")

    model = iModel(provider="openai", model="gpt-4o-mini")
    memory = QEMemory()
    agent = ChaosEngineerAgent(
        agent_id="chaos-engineer",
        model=model,
        memory=memory
    )

    print("💥 Running chaos experiment to test resilience...")

    task = QETask(
        task_type="chaos_experiment",
        context={
            "experiment_type": "network_latency",
            "target_service": "payment-api",
            "fault_config": {
                "type": "latency",
                "parameters": {
                    "latency_ms": 2000,
                    "variance_ms": 500
                }
            },
            "blast_radius": {
                "max_affected_percentage": 10,
                "max_downtime_seconds": 30
            },
            "steady_state_hypothesis": {
                "metrics": {
                    "response_time_p95_ms": 200,
                    "error_rate_percentage": 1.0,
                    "availability_percentage": 99.9
                }
            }
        }
    )

    result = await agent.execute(task)

    print(f"\n🎯 Experiment Result: {result.result}")
    print(f"📊 Resilience Score: {result.resilience_score}/100")
    print(f"⚡ Recovery Time: {result.recovery_time_seconds}s")
    print(f"🎭 Blast Radius: {result.blast_radius.affected_percentage:.1f}%")

    if result.failures_detected:
        print(f"\n⚠️  Failures Detected: {len(result.failures_detected)}")
        for failure in result.failures_detected[:2]:
            print(f"  • {failure}")

    if result.recommendations:
        print("\n💡 Recommendations:")
        for i, rec in enumerate(result.recommendations[:3], 1):
            print(f"  {i}. {rec}")

    return result


async def demo_quality_analyzer():
    """Demo: Quality Analyzer - Comprehensive quality metrics"""
    print_section("8. Quality Analyzer - Comprehensive Quality Analysis")

    model = iModel(provider="openai", model="gpt-4o-mini")
    memory = QEMemory()
    agent = QualityAnalyzerAgent(
        agent_id="quality-analyzer",
        model=model,
        memory=memory
    )

    print("📊 Analyzing comprehensive quality metrics...")

    task = QETask(
        task_type="analyze_quality",
        context={
            "codebase_path": "/src",
            "static_analysis": {
                "complexity": 12,
                "duplication": 5.2,
                "maintainability": 78
            },
            "test_results": {
                "coverage": 85.5,
                "test_count": 450,
                "execution_time": 120
            },
            "security_scan": {
                "vulnerabilities": 3,
                "severity_distribution": {"high": 1, "medium": 2}
            }
        }
    )

    result = await agent.execute(task)

    print(f"\n🎯 Overall Quality Score: {result.overall_quality_score}/100")
    print(f"📈 Trend: {result.trend.direction}")

    print("\n📊 Code Quality:")
    print(f"  • Maintainability: {result.code_quality.maintainability_index}/100")
    print(f"  • Complexity: {result.code_quality.complexity_score}")
    print(f"  • Duplication: {result.code_quality.duplication_percentage}%")

    print("\n🧪 Test Quality:")
    print(f"  • Coverage: {result.test_quality.coverage_percentage}%")
    print(f"  • Effectiveness: {result.test_quality.test_effectiveness_score}/100")

    if result.recommendations:
        print("\n💡 Top Recommendations:")
        for i, rec in enumerate(result.recommendations[:3], 1):
            print(f"  {i}. {rec}")

    return result


async def main():
    """Run all agent demonstrations"""
    print("\n" + "="*80)
    print("  🤖 LionAGI QE Fleet - Complete Agent Demonstration")
    print("="*80)
    print("\nThis demo showcases 8 specialized QE agents working together")
    print("to provide comprehensive quality engineering capabilities.\n")

    try:
        # Run demonstrations
        await demo_coverage_analyzer()
        await demo_quality_gate()
        await demo_api_contract_validator()
        await demo_flaky_test_hunter()
        await demo_test_data_architect()
        await demo_regression_risk_analyzer()
        await demo_chaos_engineer()
        await demo_quality_analyzer()

        print_section("✅ Demo Complete!")
        print("All 8 QE agents successfully demonstrated their capabilities.")
        print("\nKey Takeaways:")
        print("  • Each agent specializes in a specific quality engineering task")
        print("  • Agents share memory through the aqe/* namespace")
        print("  • Results are structured using Pydantic models")
        print("  • All agents support async/await for efficient execution")
        print("  • Agents can be composed into pipelines for complex workflows")

        print("\n📚 Next Steps:")
        print("  1. Check examples/01_basic_usage.py for simple use cases")
        print("  2. Check examples/02_sequential_pipeline.py for workflows")
        print("  3. Check examples/03_parallel_execution.py for concurrent agents")
        print("  4. Read CLAUDE.md for complete documentation")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
