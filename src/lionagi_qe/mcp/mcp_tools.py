"""MCP tool definitions for all QE agents

Each tool corresponds to a specialized QE agent and exposes its functionality
via the Model Context Protocol for Claude Code integration.
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
from enum import Enum
import asyncio
import json


class TestFramework(str, Enum):
    """Supported test frameworks"""
    PYTEST = "pytest"
    JEST = "jest"
    MOCHA = "mocha"
    CYPRESS = "cypress"
    PLAYWRIGHT = "playwright"
    JUNIT = "junit"


class TestType(str, Enum):
    """Test types"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    API = "api"


class ScanType(str, Enum):
    """Security scan types"""
    SAST = "sast"
    DAST = "dast"
    DEPENDENCY = "dependency"
    SECRETS = "secrets"
    COMPREHENSIVE = "comprehensive"


# Global fleet instance (initialized by server)
_fleet_instance = None


def set_fleet_instance(fleet):
    """Set the global fleet instance for tools to use"""
    global _fleet_instance
    _fleet_instance = fleet


def get_fleet_instance():
    """Get the global fleet instance"""
    if _fleet_instance is None:
        raise RuntimeError("Fleet not initialized. Call set_fleet_instance first.")
    return _fleet_instance


# ============================================================================
# Core Testing Tools
# ============================================================================

async def test_generate(
    code: str,
    framework: TestFramework = TestFramework.PYTEST,
    test_type: TestType = TestType.UNIT,
    coverage_target: float = 80.0,
    include_edge_cases: bool = True,
) -> Dict[str, Any]:
    """Generate comprehensive test suites with AI-powered edge case detection

    Args:
        code: Source code to generate tests for
        framework: Test framework to use (pytest, jest, etc.)
        test_type: Type of tests to generate (unit, integration, e2e)
        coverage_target: Target code coverage percentage (0-100)
        include_edge_cases: Include edge case and boundary testing

    Returns:
        Dict containing:
            - test_code: Generated test code
            - test_name: Name of the generated test
            - assertions: List of assertions included
            - edge_cases: Edge cases covered
            - coverage_estimate: Estimated coverage percentage
            - framework: Framework used
    """
    from lionagi_qe.core.task import QETask
    from lionagi_qe.agents import TestGeneratorAgent

    fleet = get_fleet_instance()

    # Create task
    task = QETask(
        task_type="test_generation",
        context={
            "code": code,
            "framework": framework.value,
            "test_type": test_type.value,
            "coverage_target": coverage_target,
            "include_edge_cases": include_edge_cases,
        }
    )

    # Execute via fleet
    result = await fleet.execute("test-generator", task)

    return {
        "test_code": result.test_code,
        "test_name": result.test_name,
        "assertions": result.assertions,
        "edge_cases": result.edge_cases,
        "coverage_estimate": result.coverage_estimate,
        "framework": result.framework,
        "test_type": result.test_type,
        "dependencies": result.dependencies,
    }


async def test_execute(
    test_path: str,
    framework: TestFramework = TestFramework.PYTEST,
    parallel: bool = True,
    coverage: bool = True,
    timeout: int = 300,
) -> Dict[str, Any]:
    """Execute test suites with parallel processing and real-time coverage

    Args:
        test_path: Path to test files or directory
        framework: Test framework to use
        parallel: Run tests in parallel
        coverage: Collect coverage metrics
        timeout: Test execution timeout in seconds

    Returns:
        Dict containing:
            - passed: Number of tests passed
            - failed: Number of tests failed
            - skipped: Number of tests skipped
            - coverage: Coverage percentage (if enabled)
            - duration: Execution duration in seconds
            - failures: List of failure details
    """
    from lionagi_qe.core.task import QETask

    fleet = get_fleet_instance()

    task = QETask(
        task_type="test_execution",
        context={
            "test_path": test_path,
            "framework": framework.value,
            "parallel": parallel,
            "coverage": coverage,
            "timeout": timeout,
        }
    )

    result = await fleet.execute("test-executor", task)

    return {
        "passed": result.get("passed", 0),
        "failed": result.get("failed", 0),
        "skipped": result.get("skipped", 0),
        "coverage": result.get("coverage", 0.0),
        "duration": result.get("duration", 0.0),
        "failures": result.get("failures", []),
        "success": result.get("failed", 0) == 0,
    }


async def coverage_analyze(
    source_path: str,
    test_path: str,
    threshold: float = 80.0,
    algorithm: str = "sublinear",
) -> Dict[str, Any]:
    """Analyze test coverage with O(log n) gap detection algorithms

    Args:
        source_path: Path to source code
        test_path: Path to test files
        threshold: Minimum acceptable coverage threshold
        algorithm: Algorithm to use (sublinear, linear, comprehensive)

    Returns:
        Dict containing:
            - overall_coverage: Overall coverage percentage
            - file_coverage: Per-file coverage breakdown
            - gaps: List of coverage gaps with priorities
            - recommendations: AI-generated recommendations
            - meets_threshold: Whether threshold is met
    """
    from lionagi_qe.core.task import QETask

    fleet = get_fleet_instance()

    task = QETask(
        task_type="coverage_analysis",
        context={
            "source_path": source_path,
            "test_path": test_path,
            "threshold": threshold,
            "algorithm": algorithm,
        }
    )

    result = await fleet.execute("coverage-analyzer", task)

    return result


async def quality_gate(
    metrics: Dict[str, Any],
    thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Intelligent quality gate with risk assessment

    Args:
        metrics: Quality metrics to evaluate
        thresholds: Custom thresholds (defaults applied if not provided)

    Returns:
        Dict containing:
            - passed: Whether quality gate passed
            - score: Overall quality score (0-100)
            - violations: List of threshold violations
            - risks: Identified risks with severity
            - recommendations: Improvement recommendations
    """
    from lionagi_qe.core.task import QETask

    fleet = get_fleet_instance()

    default_thresholds = {
        "coverage": 80.0,
        "complexity": 10.0,
        "duplication": 5.0,
        "security_score": 90.0,
    }

    task = QETask(
        task_type="quality_gate",
        context={
            "metrics": metrics,
            "thresholds": thresholds or default_thresholds,
        }
    )

    result = await fleet.execute("quality-gate", task)

    return result


# ============================================================================
# Performance & Security Tools
# ============================================================================

async def performance_test(
    endpoint: str,
    duration: int = 60,
    users: int = 10,
    ramp_up: int = 5,
    tool: str = "locust",
) -> Dict[str, Any]:
    """Run performance and load tests

    Args:
        endpoint: API endpoint or URL to test
        duration: Test duration in seconds
        users: Number of concurrent users
        ramp_up: Ramp-up time in seconds
        tool: Performance testing tool (locust, k6, jmeter)

    Returns:
        Dict containing:
            - requests_per_second: Average RPS
            - response_time_p50: 50th percentile response time
            - response_time_p95: 95th percentile response time
            - response_time_p99: 99th percentile response time
            - error_rate: Percentage of failed requests
            - total_requests: Total requests made
    """
    from lionagi_qe.core.task import QETask

    fleet = get_fleet_instance()

    task = QETask(
        task_type="performance_test",
        context={
            "endpoint": endpoint,
            "duration": duration,
            "users": users,
            "ramp_up": ramp_up,
            "tool": tool,
        }
    )

    result = await fleet.execute("performance-tester", task)

    return result


async def security_scan(
    path: str,
    scan_type: ScanType = ScanType.COMPREHENSIVE,
    severity_threshold: str = "medium",
) -> Dict[str, Any]:
    """Multi-layer security scanning (SAST, DAST, dependency scanning)

    Args:
        path: Path to code or application to scan
        scan_type: Type of security scan to perform
        severity_threshold: Minimum severity to report (low, medium, high, critical)

    Returns:
        Dict containing:
            - vulnerabilities: List of vulnerabilities found
            - severity_counts: Count by severity level
            - risk_score: Overall security risk score (0-100)
            - recommendations: Security improvement recommendations
            - compliance_status: Compliance check results
    """
    from lionagi_qe.core.task import QETask

    fleet = get_fleet_instance()

    task = QETask(
        task_type="security_scan",
        context={
            "path": path,
            "scan_type": scan_type.value,
            "severity_threshold": severity_threshold,
        }
    )

    result = await fleet.execute("security-scanner", task)

    return result


# ============================================================================
# Fleet Orchestration Tools
# ============================================================================

async def fleet_orchestrate(
    workflow: str,
    context: Dict[str, Any],
    agents: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Orchestrate complex multi-agent workflows

    Args:
        workflow: Workflow type (pipeline, parallel, fan-out-fan-in)
        context: Workflow context and parameters
        agents: List of agent IDs to use (auto-selected if None)

    Returns:
        Dict containing:
            - results: Workflow execution results
            - agents_used: List of agents that participated
            - duration: Total execution time
            - success: Whether workflow succeeded
    """
    from lionagi_qe.core.task import QETask

    fleet = get_fleet_instance()

    if workflow == "pipeline":
        result = await fleet.execute_pipeline(
            pipeline=agents or [],
            context=context
        )
    elif workflow == "parallel":
        tasks = context.get("tasks", [])
        result = await fleet.execute_parallel(
            agents=agents or [],
            tasks=tasks
        )
    elif workflow == "fan-out-fan-in":
        result = await fleet.execute_fan_out_fan_in(
            coordinator=context.get("coordinator", "fleet-commander"),
            workers=agents or [],
            context=context
        )
    else:
        raise ValueError(f"Unknown workflow type: {workflow}")

    return result


async def get_fleet_status() -> Dict[str, Any]:
    """Get comprehensive fleet status and metrics

    Returns:
        Dict containing:
            - initialized: Whether fleet is initialized
            - agents: List of registered agents
            - memory_stats: Memory usage statistics
            - routing_stats: Model routing statistics (if enabled)
            - performance_metrics: Performance metrics
    """
    fleet = get_fleet_instance()
    return await fleet.get_status()


# ============================================================================
# Advanced Tools
# ============================================================================

async def requirements_validate(
    requirements: List[str],
    format: str = "user_story",
) -> Dict[str, Any]:
    """Validate requirements using INVEST criteria and BDD generation

    Args:
        requirements: List of requirements to validate
        format: Format of requirements (user_story, use_case, acceptance_criteria)

    Returns:
        Dict containing:
            - valid_requirements: List of valid requirements
            - invalid_requirements: List with validation issues
            - bdd_scenarios: Generated BDD scenarios
            - invest_scores: INVEST criteria scores per requirement
    """
    from lionagi_qe.core.task import QETask

    fleet = get_fleet_instance()

    task = QETask(
        task_type="requirements_validation",
        context={
            "requirements": requirements,
            "format": format,
        }
    )

    result = await fleet.execute("requirements-validator", task)

    return result


async def flaky_test_hunt(
    test_path: str,
    iterations: int = 10,
    detect_threshold: float = 0.1,
) -> Dict[str, Any]:
    """Detect and stabilize flaky tests using statistical analysis

    Args:
        test_path: Path to tests to analyze
        iterations: Number of iterations to run
        detect_threshold: Flakiness detection threshold (0-1)

    Returns:
        Dict containing:
            - flaky_tests: List of detected flaky tests
            - stability_scores: Stability score per test
            - root_causes: Identified root causes
            - fixes: Suggested stabilization fixes
    """
    from lionagi_qe.core.task import QETask

    fleet = get_fleet_instance()

    task = QETask(
        task_type="flaky_test_detection",
        context={
            "test_path": test_path,
            "iterations": iterations,
            "detect_threshold": detect_threshold,
        }
    )

    result = await fleet.execute("flaky-test-hunter", task)

    return result


async def api_contract_validate(
    spec_path: str,
    version_a: str,
    version_b: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate API contracts and detect breaking changes

    Args:
        spec_path: Path to API specification (OpenAPI, GraphQL schema, etc.)
        version_a: First version to compare
        version_b: Second version to compare (if checking for breaking changes)

    Returns:
        Dict containing:
            - valid: Whether contract is valid
            - breaking_changes: List of breaking changes (if comparing versions)
            - warnings: Non-breaking warnings
            - recommendations: Contract improvement recommendations
    """
    from lionagi_qe.core.task import QETask

    fleet = get_fleet_instance()

    task = QETask(
        task_type="api_contract_validation",
        context={
            "spec_path": spec_path,
            "version_a": version_a,
            "version_b": version_b,
        }
    )

    result = await fleet.execute("api-contract-validator", task)

    return result


async def regression_risk_analyze(
    changes: List[str],
    test_suite: str,
    ml_enabled: bool = True,
) -> Dict[str, Any]:
    """Smart test selection with ML-based risk analysis

    Args:
        changes: List of changed files or modules
        test_suite: Path to test suite
        ml_enabled: Use ML patterns for risk prediction

    Returns:
        Dict containing:
            - high_risk_tests: Tests that should run (high risk)
            - medium_risk_tests: Tests that could run
            - low_risk_tests: Tests that can be skipped
            - risk_scores: Risk score per test
            - estimated_time_saved: Time saved by smart selection
    """
    from lionagi_qe.core.task import QETask

    fleet = get_fleet_instance()

    task = QETask(
        task_type="regression_risk_analysis",
        context={
            "changes": changes,
            "test_suite": test_suite,
            "ml_enabled": ml_enabled,
        }
    )

    result = await fleet.execute("regression-risk-analyzer", task)

    return result


async def test_data_generate(
    schema: Dict[str, Any],
    count: int = 1000,
    realistic: bool = True,
) -> Dict[str, Any]:
    """Generate realistic test data at high speed (10k+ records/sec)

    Args:
        schema: Data schema definition
        count: Number of records to generate
        realistic: Use realistic data patterns vs random

    Returns:
        Dict containing:
            - data: Generated test data
            - record_count: Number of records generated
            - generation_time: Time taken to generate
            - records_per_second: Generation throughput
    """
    from lionagi_qe.core.task import QETask

    fleet = get_fleet_instance()

    task = QETask(
        task_type="test_data_generation",
        context={
            "schema": schema,
            "count": count,
            "realistic": realistic,
        }
    )

    result = await fleet.execute("test-data-architect", task)

    return result


async def visual_test(
    baseline_path: str,
    current_path: str,
    threshold: float = 0.95,
) -> Dict[str, Any]:
    """Visual regression testing with AI-powered comparison

    Args:
        baseline_path: Path to baseline screenshots
        current_path: Path to current screenshots
        threshold: Similarity threshold (0-1)

    Returns:
        Dict containing:
            - matches: Number of matching screenshots
            - differences: Number of different screenshots
            - diff_details: Detailed diff information
            - similarity_scores: Similarity score per screenshot
    """
    from lionagi_qe.core.task import QETask

    fleet = get_fleet_instance()

    task = QETask(
        task_type="visual_testing",
        context={
            "baseline_path": baseline_path,
            "current_path": current_path,
            "threshold": threshold,
        }
    )

    result = await fleet.execute("visual-tester", task)

    return result


async def chaos_test(
    target: str,
    fault_types: List[str],
    duration: int = 300,
) -> Dict[str, Any]:
    """Resilience testing with controlled fault injection

    Args:
        target: Target system or service
        fault_types: Types of faults to inject (latency, errors, resource_exhaustion)
        duration: Test duration in seconds

    Returns:
        Dict containing:
            - resilience_score: Overall resilience score (0-100)
            - fault_results: Results per fault type
            - recovery_times: Time to recover from each fault
            - recommendations: Resilience improvement recommendations
    """
    from lionagi_qe.core.task import QETask

    fleet = get_fleet_instance()

    task = QETask(
        task_type="chaos_engineering",
        context={
            "target": target,
            "fault_types": fault_types,
            "duration": duration,
        }
    )

    result = await fleet.execute("chaos-engineer", task)

    return result


async def deployment_readiness(
    version: str,
    environment: str = "production",
) -> Dict[str, Any]:
    """Multi-factor deployment readiness assessment

    Args:
        version: Version to deploy
        environment: Target environment

    Returns:
        Dict containing:
            - ready: Whether deployment is recommended
            - risk_level: Overall risk level (low, medium, high, critical)
            - factors: Assessment of individual factors
            - blockers: List of blocking issues
            - recommendations: Pre-deployment recommendations
    """
    from lionagi_qe.core.task import QETask

    fleet = get_fleet_instance()

    task = QETask(
        task_type="deployment_readiness",
        context={
            "version": version,
            "environment": environment,
        }
    )

    result = await fleet.execute("deployment-readiness", task)

    return result


# ============================================================================
# Streaming Tools (for long-running operations)
# ============================================================================

async def test_execute_stream(
    test_path: str,
    framework: TestFramework = TestFramework.PYTEST,
    parallel: bool = True,
    coverage: bool = True,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Execute tests with real-time progress streaming

    Args:
        test_path: Path to test files
        framework: Test framework to use
        parallel: Run tests in parallel
        coverage: Collect coverage

    Yields:
        Progress events with type, percent, and message
    """
    # Simulate streaming progress (real implementation would integrate with test runner)
    total_steps = 10

    for i in range(total_steps):
        await asyncio.sleep(0.5)
        yield {
            "type": "progress",
            "percent": (i + 1) / total_steps * 100,
            "message": f"Running tests... {i + 1}/{total_steps}",
            "current_test": f"test_example_{i + 1}",
        }

    # Final result
    result = await test_execute(test_path, framework, parallel, coverage)
    yield {
        "type": "result",
        "data": result,
    }


async def test_generate_stream(
    code: str,
    framework: TestFramework = TestFramework.PYTEST,
    test_type: TestType = TestType.UNIT,
    coverage_target: float = 80.0,
    target_count: int = 10,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Generate tests with real-time streaming progress

    This tool provides incremental test generation with real-time progress updates.
    Each test is yielded as soon as it's generated, allowing for immediate feedback
    during long-running test generation operations.

    Args:
        code: Source code to generate tests for
        framework: Test framework to use (pytest, jest, etc.)
        test_type: Type of tests to generate (unit, integration, e2e)
        coverage_target: Target code coverage percentage (0-100)
        target_count: Number of tests to generate

    Yields:
        Progress events in the following formats:

        Progress update:
        {
            "type": "progress",
            "count": 5,
            "total": 10,
            "percent": 50.0,
            "message": "Generated test 5 of 10..."
        }

        Individual test generated:
        {
            "type": "test",
            "test_case": {
                "test_name": "test_user_creation",
                "test_code": "def test_user_creation(): ...",
                "framework": "pytest",
                "assertions": [...],
                "edge_cases": [...]
            }
        }

        Final completion:
        {
            "type": "complete",
            "tests": [...],
            "total": 10,
            "coverage_estimate": 85.0,
            "framework": "pytest"
        }

    Example Usage:
        ```python
        # Stream test generation
        async for event in test_generate_stream(code, target_count=20):
            if event["type"] == "progress":
                print(f"Progress: {event['percent']}%")
            elif event["type"] == "test":
                print(f"Generated: {event['test_case']['test_name']}")
            elif event["type"] == "complete":
                print(f"Complete! Generated {event['total']} tests")
        ```

    Benefits:
        - Real-time feedback during generation
        - Immediate access to generated tests
        - No need to wait for entire batch
        - Better UX for long-running operations
    """
    from lionagi_qe.core.task import QETask

    fleet = get_fleet_instance()

    # Get the test generator agent
    agent = fleet.agents.get("test-generator")
    if not agent:
        yield {
            "type": "error",
            "message": "Test generator agent not found"
        }
        return

    # Create task
    task = QETask(
        task_type="test_generation_streaming",
        context={
            "code": code,
            "framework": framework.value,
            "test_type": test_type.value,
            "coverage_target": coverage_target,
            "target_count": target_count,
        }
    )

    # Stream test generation
    async for event in agent.generate_tests_streaming(task):
        yield event


async def coverage_analyze_stream(
    source_path: str,
    coverage_data: Dict[str, Any],
    framework: str = "pytest",
    target_coverage: float = 85.0,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Analyze coverage with real-time streaming progress

    This tool provides file-by-file coverage analysis with real-time progress updates.
    Gaps and critical paths are yielded as they're discovered, enabling immediate
    action on coverage issues.

    Args:
        source_path: Path to source code
        coverage_data: Raw coverage data from test framework
        framework: Test framework used (pytest, jest, junit, mocha)
        target_coverage: Target coverage threshold (0-100)

    Yields:
        Progress events in the following formats:

        Progress update:
        {
            "type": "progress",
            "percent": 45.0,
            "message": "Analyzing file src/utils.py...",
            "files_analyzed": 5,
            "total_files": 10
        }

        Gap discovered:
        {
            "type": "gap",
            "gap": {
                "file_path": "src/utils.py",
                "line_start": 42,
                "line_end": 58,
                "gap_type": "uncovered",
                "severity": "high",
                "suggested_tests": [...]
            }
        }

        Critical path identified:
        {
            "type": "critical_path",
            "path": "src/payment/processor.py::charge_card",
            "impact": "high"
        }

        Final result:
        {
            "type": "complete",
            "overall_coverage": 78.5,
            "line_coverage": 80.2,
            "branch_coverage": 75.8,
            "gaps": [...],
            "critical_paths": [...],
            "meets_threshold": false,
            "analysis_time_ms": 1250
        }

    Example Usage:
        ```python
        # Stream coverage analysis
        async for event in coverage_analyze_stream(
            source_path="./src",
            coverage_data=coverage_json,
            framework="pytest",
            target_coverage=85.0
        ):
            if event["type"] == "progress":
                print(f"Progress: {event['percent']}%")
            elif event["type"] == "gap":
                gap = event["gap"]
                print(f"Gap: {gap['file_path']} lines {gap['line_start']}-{gap['line_end']}")
            elif event["type"] == "critical_path":
                print(f"Critical: {event['path']}")
            elif event["type"] == "complete":
                print(f"Coverage: {event['overall_coverage']}%")
        ```

    Benefits:
        - Real-time gap discovery
        - Immediate action on critical issues
        - Progressive analysis feedback
        - Better UX for large codebases
    """
    from lionagi_qe.core.task import QETask

    fleet = get_fleet_instance()

    # Get the coverage analyzer agent
    agent = fleet.agents.get("coverage-analyzer")
    if not agent:
        yield {
            "type": "error",
            "message": "Coverage analyzer agent not found"
        }
        return

    # Create task
    task = QETask(
        task_type="coverage_analysis_streaming",
        context={
            "coverage_data": coverage_data,
            "framework": framework,
            "codebase_path": source_path,
            "target_coverage": target_coverage,
        }
    )

    # Stream coverage analysis
    async for event in agent.analyze_coverage_streaming(task):
        yield event
