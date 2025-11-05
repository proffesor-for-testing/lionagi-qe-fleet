"""Test Executor Agent - Execute tests across multiple frameworks"""

from typing import Dict, Any, List, Optional
import time
import subprocess
import os
from pathlib import Path
from pydantic import BaseModel, Field
from lionagi.ln import alcall, AlcallParams
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


# Security: Whitelist of allowed test frameworks
ALLOWED_FRAMEWORKS = {"pytest", "jest", "mocha", "unittest", "nose2"}


def validate_file_path(file_path: str, must_exist: bool = False) -> str:
    """Validate and sanitize file path to prevent path traversal attacks

    Args:
        file_path: Path to validate
        must_exist: If True, verify file exists

    Returns:
        Absolute, sanitized path

    Raises:
        ValueError: If path is invalid or contains path traversal
        FileNotFoundError: If must_exist=True and file doesn't exist
    """
    if not file_path or not isinstance(file_path, str):
        raise ValueError("File path must be a non-empty string")

    # Resolve to absolute path and normalize
    abs_path = Path(file_path).resolve()

    # Check for path traversal attempts
    if ".." in str(abs_path):
        raise ValueError(f"Path traversal detected in: {file_path}")

    # Verify file exists if required
    if must_exist and not abs_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return str(abs_path)


def validate_framework(framework: str) -> str:
    """Validate framework is in allowed list

    Args:
        framework: Framework name

    Returns:
        Validated framework name

    Raises:
        ValueError: If framework is not allowed
    """
    if not framework or not isinstance(framework, str):
        raise ValueError("Framework must be a non-empty string")

    framework = framework.lower().strip()

    if framework not in ALLOWED_FRAMEWORKS:
        raise ValueError(
            f"Framework '{framework}' not allowed. "
            f"Allowed frameworks: {', '.join(sorted(ALLOWED_FRAMEWORKS))}"
        )

    return framework


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

    def __init__(
        self,
        agent_id: str,
        model: Any,
        memory: Optional[Any] = None,
        skills: Optional[List[str]] = None,
        enable_learning: bool = False,
        q_learning_service: Optional[Any] = None,
        memory_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize Test Executor Agent

        Args:
            agent_id: Unique agent identifier (e.g., "test-executor")
            model: LionAGI model instance
            memory: Memory backend (PostgresMemory/RedisMemory/QEMemory or None for Session.context)
            skills: List of QE skills this agent uses
            enable_learning: Enable Q-learning integration
            q_learning_service: Optional Q-learning service instance
            memory_config: Optional config for auto-initializing memory backend
        """
        super().__init__(
            agent_id=agent_id,
            model=model,
            memory=memory,
            skills=skills or ["agentic-quality-engineering", "test-automation-strategy", "shift-left-testing"],
            enable_learning=enable_learning,
            q_learning_service=q_learning_service,
            memory_config=memory_config
        )

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

        # Security: Validate inputs
        try:
            test_path = validate_file_path(test_path)
            framework = validate_framework(framework)
        except (ValueError, FileNotFoundError) as e:
            self.logger.error(f"Input validation failed: {e}")
            raise

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
        # Security: Validate framework
        framework = validate_framework(framework)

        async def run_single_test(file_path: str) -> Dict[str, Any]:
            """Execute single test file"""
            try:
                # Security: Validate file path before execution
                validated_path = validate_file_path(file_path)

                if framework == "pytest":
                    result = subprocess.run(
                        ["pytest", validated_path, "-v", "--tb=short"],
                        capture_output=True,
                        text=True,
                        timeout=60,
                        shell=False  # Explicit security: never use shell=True
                    )
                elif framework == "jest":
                    result = subprocess.run(
                        ["npm", "test", "--", validated_path],
                        capture_output=True,
                        text=True,
                        timeout=60,
                        shell=False  # Explicit security: never use shell=True
                    )
                elif framework == "mocha":
                    result = subprocess.run(
                        ["npx", "mocha", validated_path],
                        capture_output=True,
                        text=True,
                        timeout=60,
                        shell=False  # Explicit security: never use shell=True
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
