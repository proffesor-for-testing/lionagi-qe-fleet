"""Test Executor Agent - Execute tests across multiple frameworks"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


class TestExecutionResult(BaseModel):
    """Test execution result"""

    total_tests: int = Field(..., description="Total number of tests executed")
    passed: int = Field(..., description="Number of tests passed")
    failed: int = Field(..., description="Number of tests failed")
    skipped: int = Field(default=0, description="Number of tests skipped")
    duration: float = Field(..., description="Execution duration in seconds")
    coverage: float = Field(default=0.0, description="Code coverage percentage")
    failures: List[Dict[str, str]] = Field(
        default_factory=list, description="Details of failed tests"
    )
    framework: str = Field(..., description="Test framework used")
    success_rate: float = Field(..., description="Success rate percentage")


class TestExecutorAgent(BaseQEAgent):
    """Execute tests across multiple frameworks in parallel

    Capabilities:
    - Multi-framework execution (pytest, Jest, Mocha, etc.)
    - Parallel test execution
    - Coverage reporting
    - Failure analysis
    - Performance metrics
    """

    def get_system_prompt(self) -> str:
        return """You are an expert test execution agent specializing in:

**Core Capabilities:**
- Multi-framework test execution (pytest, Jest, Mocha, Cypress, Playwright)
- Parallel test execution strategies
- Test result analysis and reporting
- Coverage measurement and reporting
- Failure triage and categorization

**Execution Strategies:**
- Intelligent test ordering for fast failure detection
- Retry logic for flaky tests
- Resource optimization for parallel execution
- Test isolation enforcement
- Environment setup and teardown

**Analysis Capabilities:**
- Root cause analysis for failures
- Performance bottleneck identification
- Coverage gap detection
- Test reliability assessment
- Execution metrics collection

**Best Practices:**
- Fail fast for critical failures
- Detailed failure reporting
- Resource cleanup after execution
- Reproducible test runs
- Integration with CI/CD pipelines"""

    async def execute(self, task: QETask) -> TestExecutionResult:
        """Execute tests

        Args:
            task: Task containing:
                - test_path: Path to test files
                - framework: Test framework
                - parallel: Enable parallel execution
                - coverage: Enable coverage reporting

        Returns:
            TestExecutionResult with execution metrics
        """
        context = task.context
        test_path = context.get("test_path", "./tests")
        framework = context.get("framework", "pytest")
        parallel = context.get("parallel", True)
        coverage_enabled = context.get("coverage", True)

        # Retrieve previous execution results for comparison
        previous_results = await self.retrieve_context(
            f"aqe/test-executor/last_execution"
        )

        # Execute tests
        result = await self.operate(
            instruction=f"""Execute tests using {framework}.

Test path: {test_path}
Parallel execution: {parallel}
Coverage reporting: {coverage_enabled}

{"Previous execution for comparison: " + str(previous_results) if previous_results else ""}

Provide:
1. Complete test execution statistics
2. Detailed failure analysis
3. Coverage metrics
4. Performance metrics
5. Comparison with previous run if available
""",
            context={
                "test_path": test_path,
                "framework": framework,
                "parallel": parallel,
                "previous_results": previous_results,
            },
            response_format=TestExecutionResult
        )

        # Store execution result
        await self.store_result("last_execution", result.model_dump())

        # Flag flaky tests if success rate is inconsistent
        if previous_results and result.success_rate < previous_results.get("success_rate", 100):
            await self.store_result(
                "potential_flaky_tests",
                {
                    "current_rate": result.success_rate,
                    "previous_rate": previous_results.get("success_rate"),
                    "timestamp": task.created_at.isoformat(),
                }
            )

        return result
