"""Test Executor Agent - Execute tests across multiple frameworks"""

from typing import Dict, Any, List
import time
import subprocess
from pydantic import BaseModel, Field
from lionagi.ln import alcall, AlcallParams
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

    async def execute_tests_parallel(
        self,
        test_files: List[str],
        framework: str = "pytest"
    ) -> Dict[str, Any]:
        """
        Execute tests in parallel with automatic retry and timeout

        Uses LionAGI's alcall for parallel execution with:
        - Automatic retry logic (3 attempts)
        - Timeout handling (60s per test)
        - Rate limiting (prevent resource exhaustion)
        - Exponential backoff for retries

        Args:
            test_files: List of test file paths
            framework: Test framework (pytest, jest, mocha, etc.)

        Returns:
            {
                "total": 150,
                "passed": 145,
                "failed": 5,
                "pass_rate": 96.67,
                "results": [...],
                "execution_time": 45.3,
                "retries": 8,
                "framework": "pytest"
            }
        """

        async def run_single_test(file_path: str) -> Dict[str, Any]:
            """Execute single test file"""
            try:
                if framework == "pytest":
                    result = subprocess.run(
                        ["pytest", file_path, "-v", "--tb=short"],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                elif framework == "jest":
                    result = subprocess.run(
                        ["npm", "test", "--", file_path],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                elif framework == "mocha":
                    result = subprocess.run(
                        ["npx", "mocha", file_path],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                else:
                    raise ValueError(f"Unsupported framework: {framework}")

                return {
                    "file": file_path,
                    "passed": result.returncode == 0,
                    "output": result.stdout,
                    "errors": result.stderr,
                    "exit_code": result.returncode,
                    "timeout": False
                }
            except subprocess.TimeoutExpired:
                return {
                    "file": file_path,
                    "passed": False,
                    "error": "Test execution timeout (60s)",
                    "timeout": True
                }
            except Exception as e:
                return {
                    "file": file_path,
                    "passed": False,
                    "error": str(e),
                    "timeout": False
                }

        # Configure alcall parameters for optimal parallel execution
        params = AlcallParams(
            max_concurrent=10,        # Run 10 tests at a time
            retry_attempts=3,         # Retry failed tests 3 times
            retry_timeout=60.0,       # 60s timeout per attempt
            retry_backoff=2.0,        # Exponential backoff: 2s, 4s, 8s
            throttle_period=0.1       # 100ms between test starts (rate limit)
        )

        start_time = time.time()

        # Execute all tests with retry logic using alcall
        self.logger.info(f"Executing {len(test_files)} tests in parallel with alcall")
        results = await params(test_files, run_single_test)

        execution_time = time.time() - start_time

        # Aggregate results
        passed = sum(1 for r in results if r.get("passed"))
        failed = len(results) - passed
        retries = sum(r.get("_retry_count", 0) for r in results)
        timeouts = sum(1 for r in results if r.get("timeout"))

        # Store in memory
        await self.store_result("last_parallel_execution", {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "results": results,
            "execution_time": execution_time,
            "retries": retries,
            "timeouts": timeouts,
            "framework": framework
        })

        self.logger.info(
            f"Parallel execution complete: {passed}/{len(results)} passed, "
            f"{retries} retries, {execution_time:.2f}s"
        )

        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / len(results)) * 100 if results else 0,
            "results": results,
            "execution_time": execution_time,
            "retries": retries,
            "timeouts": timeouts,
            "framework": framework,
            "avg_time_per_test": execution_time / len(results) if results else 0
        }
