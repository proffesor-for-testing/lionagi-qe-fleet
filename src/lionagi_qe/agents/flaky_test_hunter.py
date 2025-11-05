"""
QE Flaky Test Hunter Agent

Mission: Detects, analyzes, and stabilizes flaky tests through pattern recognition
and auto-remediation, achieving 95%+ test reliability.

Capabilities:
- Flaky detection using statistical analysis
- Root cause analysis with ML-powered diagnosis
- Auto-stabilization applying common fixes
- Quarantine management for flaky tests
- Trend tracking over time
- Reliability scoring for all tests
- Predictive flakiness detection
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Any
from datetime import datetime
import time
import subprocess
from pathlib import Path
from lionagi.ln import alcall, AlcallParams


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


# ============================================================================
# Pydantic Result Models
# ============================================================================

class FailurePattern(BaseModel):
    """Detected failure pattern"""
    randomness: float
    timing_correlation: float
    environmental_correlation: float


class EnvironmentalFactors(BaseModel):
    """Environmental factors affecting test"""
    time_of_day: Optional[str] = None
    ci_agent: Optional[str] = None
    parallelization: Optional[str] = None


class RootCause(BaseModel):
    """Root cause analysis result"""
    category: Literal[
        "RACE_CONDITION", "TIMEOUT", "NETWORK_FLAKE",
        "DATA_DEPENDENCY", "ORDER_DEPENDENCY", "MEMORY_LEAK"
    ]
    confidence: float
    description: str
    evidence: List[str]
    recommendation: str


class LastFlake(BaseModel):
    """Information about a recent flake"""
    timestamp: datetime
    result: Literal["pass", "fail"]
    duration: int  # milliseconds
    error: Optional[str] = None
    agent: Optional[str] = None


class SuggestedFix(BaseModel):
    """A suggested fix for flaky test"""
    priority: Literal["LOW", "MEDIUM", "HIGH"]
    approach: str
    code: str
    estimated_effectiveness: float


class FlakyTest(BaseModel):
    """Information about a flaky test"""
    test_name: str
    flakiness_score: float
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    total_runs: int
    failures: int
    passes: int
    failure_rate: float
    pass_rate: float
    pattern: str
    last_flakes: List[LastFlake]
    root_cause: RootCause
    failure_pattern: FailurePattern
    environmental_factors: EnvironmentalFactors
    suggested_fixes: List[SuggestedFix]
    status: Literal["ACTIVE", "QUARANTINED", "FIXED", "INVESTIGATING"]
    quarantined_at: Optional[datetime] = None
    assigned_to: Optional[str] = None


class FlakyTestStatistics(BaseModel):
    """Statistics about flaky tests"""
    by_category: Dict[str, int]
    by_severity: Dict[str, int]
    by_status: Dict[str, int]


class FlakyDetectionResult(BaseModel):
    """Complete flaky detection result"""
    time_window: str
    total_tests: int
    flaky_tests: int
    flakiness_rate: float
    target_reliability: float
    top_flaky_tests: List[FlakyTest]
    statistics: FlakyTestStatistics
    recommendation: str


class StabilizationResult(BaseModel):
    """Result of test stabilization"""
    success: bool
    original_pass_rate: float
    new_pass_rate: float
    modifications: List[str]
    validation_runs: int
    reason: Optional[str] = None


class Quarantine(BaseModel):
    """Quarantine information"""
    test_name: str
    reason: str
    quarantined_at: datetime
    assigned_to: str
    estimated_fix_time: str
    max_quarantine_days: int
    status: Literal["QUARANTINED", "FIXED", "REINSTATED", "ESCALATED", "DELETED"]
    jira_issue: Optional[str] = None


class QuarantineReviewResult(BaseModel):
    """Result of quarantine review"""
    reviewed: List[Quarantine]
    reinstated: List[Quarantine]
    escalated: List[Quarantine]
    deleted: List[Quarantine]


class WeeklyTrend(BaseModel):
    """Weekly flakiness trend data"""
    week: int
    flaky_tests: int
    total_tests: int
    flakiness_rate: float


class TrendAnalysis(BaseModel):
    """Flakiness trend analysis"""
    current: float
    trend: Literal["IMPROVING", "STABLE", "DEGRADING"]
    weekly_data: List[WeeklyTrend]
    target_reliability: float
    days_to_target: Optional[int] = None


class ReliabilityScoreComponents(BaseModel):
    """Components of reliability score"""
    recent_pass_rate: float
    overall_pass_rate: float
    consistency: float
    environmental_stability: float
    execution_speed: float


class ReliabilityScore(BaseModel):
    """Test reliability score"""
    score: float
    grade: Literal["A", "B", "C", "D", "F"]
    components: ReliabilityScoreComponents


class FlakinessPrediction(BaseModel):
    """Prediction of future flakiness"""
    probability: float
    confidence: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    recommendation: Dict[str, Any]


class FlakyTestHunterResult(BaseModel):
    """Complete flaky test hunter result"""
    detection: FlakyDetectionResult
    stabilization: Optional[StabilizationResult] = None
    quarantine: Optional[Quarantine] = None
    trend_analysis: Optional[TrendAnalysis] = None
    reliability_scores: Optional[Dict[str, ReliabilityScore]] = None
    predictions: Optional[Dict[str, FlakinessPrediction]] = None


# ============================================================================
# System Prompt
# ============================================================================

FLAKY_TEST_HUNTER_PROMPT = """You are the QE Flaky Test Hunter, an expert at eliminating test flakiness through intelligent detection, root cause analysis, and automated stabilization.

## Your Mission

**Eliminate test flakiness** through intelligent detection, root cause analysis, and automated stabilization. Using statistical analysis, pattern recognition, and ML-powered prediction, identify flaky tests with 98% accuracy, diagnose root causes, and auto-remediate common flakiness patterns. Transform unreliable test suites into rock-solid confidence builders, achieving 95%+ test reliability.

## Core Capabilities

### 1. Flaky Detection
- Analyze historical test results statistically
- Calculate flakiness scores from multiple factors:
  - **Inconsistency**: How often results change
  - **Volatility**: Neither always passing nor failing
  - **Recency**: Weight recent flakes more heavily
  - **Environmental sensitivity**: Fails under specific conditions
- Detect patterns: random, timing, environmental, data, order
- Require minimum runs (default: 10) for statistical validity

### 2. Root Cause Analysis
- Analyze error messages and patterns
- Examine timing patterns and correlations
- Inspect test code for common issues:
  - Missing `await` statements
  - Unawaited promises
  - Hardcoded sleeps
  - Shared state between tests
  - External dependencies
- Correlate failures with environmental factors:
  - Time of day
  - Day of week
  - CI agent
  - Parallelization level
  - System load
- Provide confidence scores for diagnoses

### 3. Auto-Stabilization
Apply fixes for common patterns:

**Race Conditions**:
- Add explicit waits for conditions
- Fix unawaited promises
- Add retry logic with idempotency checks
- Replace hardcoded sleeps with condition waits

**Timeouts**:
- Increase timeout thresholds (2x recommended)
- Replace generic timeouts with explicit waits
- Add timeout buffer for CI environments

**Network Flakes**:
- Add retry with exponential backoff
- Implement circuit breakers
- Increase network request timeouts
- Add fallback mechanisms

**Data Dependencies**:
- Isolate test data
- Reset shared state
- Use test-specific fixtures
- Clear caches between tests

**Order Dependencies**:
- Make tests independent
- Remove global state
- Run in random order
- Add cleanup hooks

### 4. Quarantine Management
- Automatically quarantine flaky tests (>10% flakiness)
- Add skip annotations to prevent CI blocks
- Create tracking issues (Jira, GitHub)
- Notify responsible teams
- Schedule regular reviews
- Auto-reinstate when fixed (>95% pass rate)
- Escalate overdue tests (>30 days)
- Delete irrelevant tests

### 5. Trend Tracking
- Track flakiness trends over time (weekly, monthly)
- Calculate trend direction (improving/stable/degrading)
- Identify systemic issues
- Predict future trends
- Estimate time to reliability targets
- Generate visualizations and reports

### 6. Reliability Scoring
Assign reliability scores (0-1) based on:
- Recent pass rate (40% weight)
- Overall pass rate (20% weight)
- Consistency (20% weight)
- Environmental stability (10% weight)
- Execution speed stability (10% weight)

Grades:
- **A**: ≥0.95 (Excellent)
- **B**: 0.90-0.94 (Good)
- **C**: 0.80-0.89 (Fair)
- **D**: 0.70-0.79 (Poor)
- **F**: <0.70 (Failing)

### 7. Predictive Flakiness
Predict which tests will become flaky based on:
- Test complexity
- Async operations
- Network calls
- Shared state
- Recent code changes
- Author's historical flakiness rate
- Module's historical flakiness

Risk levels:
- **HIGH** (>70%): Review before merge, run 20+ times
- **MEDIUM** (40-70%): Monitor closely, run 10+ times
- **LOW** (<40%): Standard process

## Root Cause Categories

### RACE_CONDITION
**Indicators**:
- Error messages: "race", "not found", "undefined"
- Faster executions fail more often
- Missing `await` in code
- Unawaited promises

**Fix**:
- Add explicit waits: `await waitForCondition(...)`
- Fix unawaited promises: `await promise`
- Add retry with idempotency

### TIMEOUT
**Indicators**:
- Error messages: "timeout", "timed out", "exceeded"
- Failures take longer than successes
- Failures near timeout threshold

**Fix**:
- Increase timeout: 2x current value
- Replace sleep with explicit wait
- Optimize slow operations

### NETWORK_FLAKE
**Indicators**:
- Error messages: "network", "connection", "ECONNREFUSED", "502/503/504"
- Specific CI agents fail more
- Fails during peak hours

**Fix**:
- Add retry with exponential backoff
- Implement circuit breaker
- Increase network timeouts

### DATA_DEPENDENCY
**Indicators**:
- Shared state between tests
- Test order affects outcomes
- Data cleanup missing

**Fix**:
- Isolate test data
- Reset state before/after tests
- Use unique test fixtures

### ORDER_DEPENDENCY
**Indicators**:
- Failures correlate with test order
- Passes when run alone, fails in suite
- Global state mutations

**Fix**:
- Make tests independent
- Remove global state
- Add proper cleanup

## Quarantine Strategy

**When to Quarantine**:
- Flakiness score >0.1 (>10% flakiness)
- High severity (blocking critical tests)
- Repeated failures without fix

**Quarantine Process**:
1. Add `test.skip()` annotation with metadata
2. Create tracking issue (Jira/GitHub)
3. Assign to responsible team
4. Set max quarantine period (default: 30 days)
5. Schedule weekly reviews

**Review Process**:
- Run test 20 times to validate fix
- Reinstate if pass rate ≥95%
- Escalate if overdue (>30 days)
- Delete if no longer relevant

**Success Metrics**:
- Average quarantine duration: <8 days
- Auto-fix success rate: 65%
- Fix rate within 7 days: 80%

## Output Requirements

Provide comprehensive reports including:
1. **Flaky Tests**: List sorted by severity
2. **Root Causes**: Category, confidence, evidence
3. **Suggested Fixes**: Code changes with effectiveness estimates
4. **Quarantine Status**: Currently quarantined tests
5. **Trends**: Historical flakiness over time
6. **Reliability Scores**: All tests graded A-F
7. **Predictions**: Tests likely to become flaky

## Performance Targets

Achieve:
- **95%+ test reliability** (consistent results)
- **98% detection accuracy** (correct flaky identification)
- **<2% false negative rate** (missed flaky tests)
- **<3% false positive rate** (stable tests flagged)
- **65% auto-fix success rate** (automated stabilization)
- **80% fixed within 7 days** (quick resolution)

Focus on building developer trust through reliable, consistent test results."""


# ============================================================================
# Agent Implementation
# ============================================================================

from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


class FlakyTestHunterAgent(BaseQEAgent):
    """Flaky Test Hunter Agent

    Detects, analyzes, and stabilizes flaky tests through pattern recognition
    and auto-remediation, achieving 95%+ test reliability.

    Capabilities:
    - Flaky detection using statistical analysis
    - Root cause analysis with ML-powered diagnosis
    - Auto-stabilization applying common fixes
    - Quarantine management for flaky tests
    - Trend tracking over time
    - Reliability scoring for all tests
    - Predictive flakiness detection
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
        """Initialize FlakyTestHunter Agent

        Args:
            agent_id: Unique agent identifier
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
            skills=skills or ['agentic-quality-engineering', 'exploratory-testing-advanced', 'regression-testing'],
            enable_learning=enable_learning,
            q_learning_service=q_learning_service,
            memory_config=memory_config
        )

    def get_system_prompt(self) -> str:
        """Define agent expertise"""
        return FLAKY_TEST_HUNTER_PROMPT

    async def execute(self, task: QETask) -> FlakyTestHunterResult:
        """Execute flaky test detection and analysis

        Args:
            task: Task containing:
                - test_results: Historical test execution results
                - min_runs: Minimum runs required for detection (default: 10)
                - auto_fix: Whether to attempt auto-stabilization (default: False)
                - auto_quarantine: Whether to auto-quarantine flaky tests (default: True)
                - target_reliability: Target reliability percentage (default: 0.95)

        Returns:
            FlakyTestHunterResult with detection and analysis
        """
        # Extract context
        context = task.context
        test_results = context.get("test_results", [])
        min_runs = context.get("min_runs", 10)
        auto_fix = context.get("auto_fix", False)
        auto_quarantine = context.get("auto_quarantine", True)
        target_reliability = context.get("target_reliability", 0.95)

        # Retrieve flaky test history from memory
        flaky_history = await self.get_memory(
            "aqe/flaky-tests/history",
            default=[]
        )

        # Retrieve test stability data
        stability_data = await self.get_memory(
            "aqe/test-stability/scores",
            default={}
        )

        # Retrieve quarantined tests
        quarantined = await self.get_memory(
            "aqe/flaky-tests/quarantined",
            default=[]
        )

        # Use LionAGI to perform flaky test detection
        result = await self.operate(
            instruction=f"""Detect and analyze flaky tests using statistical analysis and pattern recognition.

            Test Results (Last {len(test_results)} runs):
            ```json
            {str(test_results)[:2000]}
            ```

            Configuration:
            - Minimum Runs: {min_runs} (for statistical validity)
            - Auto-Fix: {auto_fix}
            - Auto-Quarantine: {auto_quarantine}
            - Target Reliability: {target_reliability * 100}%

            Requirements:
            1. Calculate flakiness scores for all tests using:
               - Inconsistency rate (result changes)
               - Volatility (neither always passing nor failing)
               - Recency weighting (recent flakes weighted more)
               - Environmental sensitivity
            2. Detect flakiness patterns: random, timing, environmental, data, order
            3. Perform root cause analysis:
               - RACE_CONDITION: Missing await, unawaited promises
               - TIMEOUT: Insufficient timeouts
               - NETWORK_FLAKE: Network instability
               - DATA_DEPENDENCY: Shared state issues
               - ORDER_DEPENDENCY: Test ordering problems
            4. Suggest fixes with effectiveness estimates
            5. Calculate reliability scores (A-F grades)
            6. Predict future flakiness risk
            7. Generate quarantine recommendations

            Historical Data (for pattern learning):
            {flaky_history[:10] if flaky_history else "No history available"}

            Stability Scores:
            {str(stability_data)[:500] if stability_data else "No stability data"}

            Currently Quarantined ({len(quarantined)} tests):
            {[q.get("test_name") for q in quarantined[:5]] if quarantined else "None"}

            Performance Targets:
            - 95%+ test reliability
            - 98% detection accuracy
            - <2% false negative rate
            - 65% auto-fix success rate
            """,
            response_format=FlakyTestHunterResult,
        )

        # Store detection result in memory
        await self.store_memory(
            "aqe/flaky-tests/latest-detection",
            result.model_dump(),
        )

        # Update flaky test history
        flaky_history.append({
            "timestamp": datetime.now().isoformat(),
            "flaky_tests": result.detection.flaky_tests,
            "flakiness_rate": result.detection.flakiness_rate,
            "target_reliability": target_reliability,
        })
        await self.store_memory(
            "aqe/flaky-tests/history",
            flaky_history[-100:],  # Keep last 100 detections
        )

        # Update stability scores for all tests
        for flaky_test in result.detection.top_flaky_tests:
            stability_data[flaky_test.test_name] = {
                "flakiness_score": flaky_test.flakiness_score,
                "severity": flaky_test.severity,
                "failure_rate": flaky_test.failure_rate,
                "last_updated": datetime.now().isoformat(),
            }
        await self.store_memory(
            "aqe/test-stability/scores",
            stability_data,
        )

        # Update quarantined tests list
        if auto_quarantine:
            for flaky_test in result.detection.top_flaky_tests:
                if flaky_test.status == "QUARANTINED":
                    quarantined.append({
                        "test_name": flaky_test.test_name,
                        "quarantined_at": flaky_test.quarantined_at.isoformat() if flaky_test.quarantined_at else datetime.now().isoformat(),
                        "severity": flaky_test.severity,
                        "flakiness_score": flaky_test.flakiness_score,
                        "assigned_to": flaky_test.assigned_to,
                    })
            await self.store_memory(
                "aqe/flaky-tests/quarantined",
                quarantined,
            )

        return result

    async def detect_flaky_tests(
        self,
        test_files: List[str],
        iterations: int = 10,
        framework: str = "pytest"
    ) -> Dict[str, Any]:
        """
        Run tests multiple times to detect flakiness

        Uses nested alcall to:
        1. Run each test N times in parallel
        2. Analyze results for inconsistency patterns
        3. Calculate flakiness scores
        4. Identify root causes

        Args:
            test_files: List of test file paths to check
            iterations: Number of times to run each test (default: 10)
            framework: Test framework (pytest, jest, mocha)

        Returns:
            {
                "total_tests": 50,
                "flaky_tests": 8,
                "flaky_list": [...],
                "flakiness_rate": 16.0,
                "execution_time": 120.5,
                "total_runs": 500
            }
        """
        # Validate inputs (CC=2)
        framework = self._validate_detection_inputs(iterations, framework)

        start_time = time.time()

        # Log detection start (CC=1)
        self._log_detection_start(test_files, iterations)

        # Create test execution function (CC=1)
        run_test_multiple_times = self._create_test_runner(iterations, framework)

        # Execute flaky detection with alcall (CC=1)
        flaky_results = await self._execute_parallel_detection(
            test_files, run_test_multiple_times
        )

        # Calculate execution metrics (CC=1)
        execution_time = time.time() - start_time
        flaky_tests = [r for r in flaky_results if r.get("is_flaky")]

        # Store results in memory (CC=1)
        await self._store_detection_results(
            test_files, flaky_tests, execution_time, iterations, framework
        )

        # Log completion (CC=1)
        self._log_detection_complete(test_files, flaky_tests, execution_time)

        # Build final result dictionary (CC=1)
        return self._build_detection_result(
            test_files, flaky_tests, execution_time, iterations, framework
        )

    def _validate_detection_inputs(self, iterations: int, framework: str) -> str:
        """Validate detection inputs for security and correctness

        Args:
            iterations: Number of iterations per test
            framework: Test framework name

        Returns:
            Validated framework name

        Raises:
            ValueError: If inputs are invalid
        """
        # Security: Validate framework and iteration count
        framework = validate_framework(framework)
        if not isinstance(iterations, int) or iterations < 1 or iterations > 100:
            raise ValueError("Iterations must be an integer between 1 and 100")

        return framework

    def _log_detection_start(self, test_files: List[str], iterations: int) -> None:
        """Log detection start message

        Args:
            test_files: List of test files
            iterations: Number of iterations per test
        """
        self.logger.info(
            f"Running flaky detection on {len(test_files)} tests "
            f"({iterations} iterations each)"
        )

    def _create_test_runner(self, iterations: int, framework: str):
        """Create test runner function for parallel execution

        Args:
            iterations: Number of times to run each test
            framework: Test framework to use

        Returns:
            Async function that runs a test multiple times
        """
        async def run_test_multiple_times(file_path: str) -> Dict[str, Any]:
            """Run single test N times to detect flakiness"""
            # Create single test execution function (CC=1)
            execute_test_once = self._create_single_test_executor(file_path, framework)

            # Execute test multiple times in parallel (CC=1)
            results = await self._run_test_iterations(execute_test_once, iterations)

            # Analyze results for flakiness (CC=1)
            return self._analyze_test_results(file_path, results, iterations)

        return run_test_multiple_times

    def _create_single_test_executor(self, file_path: str, framework: str):
        """Create function to execute a single test run

        Args:
            file_path: Path to test file
            framework: Test framework to use

        Returns:
            Async function that executes one test run
        """
        async def execute_test_once(run_number: int) -> Dict[str, Any]:
            """Execute test once"""
            try:
                # Security: Validate file path before execution
                validated_path = validate_file_path(file_path)

                # Run test with appropriate framework (CC=1)
                result = self._run_framework_test(validated_path, framework)

                return {
                    "run": run_number,
                    "passed": result.returncode == 0,
                    "exit_code": result.returncode,
                    "error": result.stderr if result.returncode != 0 else None,
                    "duration": 0  # Could parse from output
                }
            except subprocess.TimeoutExpired:
                return {
                    "run": run_number,
                    "passed": False,
                    "error": "Timeout",
                    "timeout": True
                }
            except Exception as e:
                return {
                    "run": run_number,
                    "passed": False,
                    "error": str(e)
                }

        return execute_test_once

    def _run_framework_test(self, file_path: str, framework: str):
        """Run test using specified framework with security

        Args:
            file_path: Validated path to test file
            framework: Test framework (pytest, jest, mocha)

        Returns:
            subprocess.CompletedProcess result

        Raises:
            ValueError: If framework is unsupported
        """
        if framework == "pytest":
            return subprocess.run(
                ["pytest", file_path, "-v", "-x"],
                capture_output=True,
                text=True,
                timeout=30,
                shell=False  # Explicit security: never use shell=True
            )
        elif framework == "jest":
            return subprocess.run(
                ["npm", "test", "--", file_path, "--no-coverage"],
                capture_output=True,
                text=True,
                timeout=30,
                shell=False  # Explicit security: never use shell=True
            )
        elif framework == "mocha":
            return subprocess.run(
                ["npx", "mocha", file_path],
                capture_output=True,
                text=True,
                timeout=30,
                shell=False  # Explicit security: never use shell=True
            )
        else:
            raise ValueError(f"Unsupported framework: {framework}")

    async def _run_test_iterations(self, execute_test_once, iterations: int) -> List[Dict[str, Any]]:
        """Run test multiple times using alcall

        Args:
            execute_test_once: Function to execute single test
            iterations: Number of iterations

        Returns:
            List of test results
        """
        # Use nested alcall for parallel execution of multiple runs
        # Run with minimal concurrency to avoid interfering with test results
        run_params = AlcallParams(
            max_concurrent=3,         # Run 3 iterations at a time
            retry_attempts=1,         # Don't retry for flaky detection
            retry_timeout=30.0,       # 30s timeout per run
            throttle_period=0.2       # 200ms between runs
        )

        results = await run_params(
            range(iterations),
            execute_test_once
        )

        return results

    def _analyze_test_results(
        self, file_path: str, results: List[Dict[str, Any]], iterations: int
    ) -> Dict[str, Any]:
        """Analyze test results to determine flakiness

        Args:
            file_path: Path to test file
            results: List of test execution results
            iterations: Total iterations run

        Returns:
            Dictionary with flakiness analysis
        """
        # Count passes and failures (CC=1)
        passed_count = sum(1 for r in results if r.get("passed"))
        failed_count = iterations - passed_count

        # Determine if test is flaky (CC=1)
        is_flaky = 0 < passed_count < iterations

        # Calculate flakiness score (0-1) (CC=1)
        # Higher score = more flaky (closer to 50/50 pass/fail ratio)
        flakiness_score = (min(passed_count, failed_count) / iterations) * 2

        return {
            "file": file_path,
            "iterations": iterations,
            "passed": passed_count,
            "failed": failed_count,
            "is_flaky": is_flaky,
            "flakiness_score": flakiness_score,
            "pass_rate": passed_count / iterations,
            "results": results,
            "pattern": self._identify_pattern(results)
        }

    async def _execute_parallel_detection(
        self, test_files: List[str], run_test_multiple_times
    ) -> List[Dict[str, Any]]:
        """Execute flaky detection for all tests in parallel

        Args:
            test_files: List of test file paths
            run_test_multiple_times: Function to run a test multiple times

        Returns:
            List of flaky test detection results
        """
        detection_params = AlcallParams(
            max_concurrent=2,        # Don't overwhelm system
            retry_attempts=1,        # No retry for detection
            retry_timeout=300.0,     # 5 min timeout per test
            throttle_period=0.5      # 500ms between test starts
        )

        flaky_results = await detection_params(
            test_files,
            run_test_multiple_times
        )

        return flaky_results

    async def _store_detection_results(
        self, test_files: List[str], flaky_tests: List[Dict[str, Any]],
        execution_time: float, iterations: int, framework: str
    ) -> None:
        """Store detection results in memory

        Args:
            test_files: List of test files
            flaky_tests: List of flaky tests found
            execution_time: Total execution time
            iterations: Iterations per test
            framework: Test framework used
        """
        await self.store_memory(
            "aqe/flaky-tests/alcall-detection",
            {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(test_files),
                "flaky_tests": len(flaky_tests),
                "flakiness_rate": (len(flaky_tests) / len(test_files)) * 100,
                "flaky_list": flaky_tests,
                "execution_time": execution_time,
                "total_runs": len(test_files) * iterations,
                "framework": framework
            }
        )

    def _log_detection_complete(
        self, test_files: List[str], flaky_tests: List[Dict[str, Any]], execution_time: float
    ) -> None:
        """Log detection completion message

        Args:
            test_files: List of test files
            flaky_tests: List of flaky tests found
            execution_time: Total execution time
        """
        self.logger.info(
            f"Flaky detection complete: {len(flaky_tests)}/{len(test_files)} flaky, "
            f"{execution_time:.2f}s"
        )

    def _build_detection_result(
        self, test_files: List[str], flaky_tests: List[Dict[str, Any]],
        execution_time: float, iterations: int, framework: str
    ) -> Dict[str, Any]:
        """Build final detection result dictionary

        Args:
            test_files: List of test files
            flaky_tests: List of flaky tests found
            execution_time: Total execution time
            iterations: Iterations per test
            framework: Test framework used

        Returns:
            Complete detection result dictionary
        """
        return {
            "total_tests": len(test_files),
            "flaky_tests": len(flaky_tests),
            "flaky_list": flaky_tests,
            "flakiness_rate": (len(flaky_tests) / len(test_files)) * 100 if test_files else 0,
            "execution_time": execution_time,
            "total_runs": len(test_files) * iterations,
            "avg_time_per_test": execution_time / len(test_files) if test_files else 0,
            "framework": framework
        }

    def _identify_pattern(self, results: List[Dict[str, Any]]) -> str:
        """
        Identify flakiness pattern from test results

        Args:
            results: List of test execution results

        Returns:
            Pattern description (e.g., "TIMING", "RANDOM", "ENVIRONMENTAL")
        """
        if not results:
            return "UNKNOWN"

        # Count consecutive passes and fails
        consecutive_passes = 0
        consecutive_fails = 0
        max_consecutive_passes = 0
        max_consecutive_fails = 0

        for result in results:
            if result.get("passed"):
                consecutive_passes += 1
                consecutive_fails = 0
                max_consecutive_passes = max(max_consecutive_passes, consecutive_passes)
            else:
                consecutive_fails += 1
                consecutive_passes = 0
                max_consecutive_fails = max(max_consecutive_fails, consecutive_fails)

        # Analyze pattern
        total_results = len(results)
        if max_consecutive_passes == total_results:
            return "STABLE_PASS"
        elif max_consecutive_fails == total_results:
            return "STABLE_FAIL"
        elif max_consecutive_passes > total_results * 0.7 or max_consecutive_fails > total_results * 0.7:
            return "INTERMITTENT"  # Long runs of same result
        else:
            return "RANDOM"  # Frequent alternation


# ============================================================================
# Placeholder Function (For Backward Compatibility)
# ============================================================================

def execute(
    test_results: List[Dict],
    min_runs: int = 10,
    auto_fix: bool = False,
    auto_quarantine: bool = True
) -> FlakyTestHunterResult:
    """
    Execute flaky test detection and analysis.

    Args:
        test_results: Historical test execution results
        min_runs: Minimum runs required for detection
        auto_fix: Whether to attempt auto-stabilization
        auto_quarantine: Whether to auto-quarantine flaky tests

    Returns:
        FlakyTestHunterResult with detection and analysis

    Note:
        This is a placeholder implementation. In production, this would:
        1. Aggregate test statistics from historical results
        2. Calculate flakiness scores
        3. Detect patterns and root causes
        4. Attempt auto-stabilization if enabled
        5. Quarantine flaky tests if enabled
        6. Track trends over time
        7. Generate reliability scores
        8. Predict future flakiness
    """
    # Placeholder implementation
    # In production, integrate with:
    # - CI/CD systems for test results
    # - Test runners (Jest, Pytest, JUnit)
    # - Issue tracking (Jira, GitHub)
    # - Version control for code analysis

    # Example result structure
    return FlakyTestHunterResult(
        detection=FlakyDetectionResult(
            time_window="last_30_days",
            total_tests=1287,
            flaky_tests=47,
            flakiness_rate=0.0365,
            target_reliability=0.95,
            top_flaky_tests=[
                FlakyTest(
                    test_name="test/integration/checkout.integration.test.ts::Checkout Flow::processes payment successfully",
                    flakiness_score=0.68,
                    severity="HIGH",
                    total_runs=156,
                    failures=42,
                    passes=114,
                    failure_rate=0.269,
                    pass_rate=0.731,
                    pattern="Timing-related (race conditions, timeouts)",
                    last_flakes=[
                        LastFlake(
                            timestamp=datetime.now(),
                            result="fail",
                            duration=1234,
                            error="TimeoutError: Waiting for element timed out after 5000ms",
                            agent="ci-agent-3"
                        )
                    ],
                    root_cause=RootCause(
                        category="RACE_CONDITION",
                        confidence=0.89,
                        description="Payment API responds before order state is persisted",
                        evidence=[
                            "Failures occur when test runs <50ms",
                            "Success rate increases with explicit wait",
                            "Logs show 'order not found' errors"
                        ],
                        recommendation="Add explicit wait for order persistence before payment call"
                    ),
                    failure_pattern=FailurePattern(
                        randomness=0.42,
                        timing_correlation=0.89,
                        environmental_correlation=0.31
                    ),
                    environmental_factors=EnvironmentalFactors(
                        time_of_day="Fails more during peak hours (12pm-2pm)",
                        ci_agent="Fails 80% on agent-3 vs 20% on others",
                        parallelization="Fails when >4 tests run in parallel"
                    ),
                    suggested_fixes=[
                        SuggestedFix(
                            priority="HIGH",
                            approach="Add explicit wait",
                            code="await waitForCondition(() => orderService.exists(orderId), { timeout: 5000 });",
                            estimated_effectiveness=0.85
                        )
                    ],
                    status="QUARANTINED",
                    quarantined_at=datetime.now(),
                    assigned_to="backend-team@company.com"
                )
            ],
            statistics=FlakyTestStatistics(
                by_category={
                    "RACE_CONDITION": 23,
                    "TIMEOUT": 12,
                    "NETWORK_FLAKE": 7,
                    "DATA_DEPENDENCY": 3,
                    "ORDER_DEPENDENCY": 2
                },
                by_severity={
                    "HIGH": 14,
                    "MEDIUM": 21,
                    "LOW": 12
                },
                by_status={
                    "QUARANTINED": 27,
                    "FIXED": 15,
                    "INVESTIGATING": 5
                }
            ),
            recommendation="Focus on 14 HIGH severity flaky tests first. Estimated fix time: 2-3 weeks to reach 95% reliability."
        )
    )
