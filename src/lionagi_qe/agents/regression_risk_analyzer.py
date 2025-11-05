"""
QE Regression Risk Analyzer Agent

Mission: Analyzes code changes to predict regression risk and intelligently select
minimal test suites for 10x faster CI through intelligent test selection with 95%
defect detection rate.

Capabilities:
- Change impact analysis with blast radius calculation
- Intelligent test selection using ML patterns
- Risk heat mapping across the codebase
- Dependency tracking and graph analysis
- Historical pattern learning from test results
- CI optimization through parallel execution
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Any
from datetime import datetime


# ============================================================================
# Pydantic Result Models
# ============================================================================

class ChangedFile(BaseModel):
    """Information about a changed file"""
    path: str
    lines_added: int
    lines_deleted: int
    complexity: float
    criticality: float
    reason: str


class BlastRadius(BaseModel):
    """Calculated blast radius of changes"""
    files: int
    modules: int
    services: int
    affected_features: List[str]


class TestImpact(BaseModel):
    """Impact on test suite"""
    required_tests: List[str]
    total_tests: int
    estimated_runtime: str


class ChangeImpactAnalysis(BaseModel):
    """Complete change impact analysis"""
    commit_sha: str
    author: str
    timestamp: datetime
    changed_files: List[ChangedFile]
    direct_impact: List[str]
    transitive_impact: List[str]
    blast_radius: BlastRadius
    risk_score: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    test_impact: TestImpact
    recommendation: str


class SelectedTest(BaseModel):
    """Information about a selected test"""
    path: str
    reason: str
    failure_probability: float
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    runtime: str


class TestSelection(BaseModel):
    """Test selection results"""
    selected: int
    total: int
    reduction_rate: float
    estimated_runtime: str
    full_suite_runtime: str
    time_saved: str
    confidence: float


class TestSelectionResult(BaseModel):
    """Complete test selection result"""
    change_id: str
    analysis_time: str
    test_selection: TestSelection
    selected_tests: List[SelectedTest]
    skipped_tests: int
    skipped_reasons: Dict[str, int]
    recommendation: str


class RiskFactor(BaseModel):
    """Risk factors for a module"""
    change_frequency: int
    complexity: float
    failure_count: int
    criticality: float
    coverage: float


class RiskHeatMapModule(BaseModel):
    """Module in risk heat map"""
    path: str
    risk_score: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    factors: RiskFactor
    heat_color: str
    recommendation: str


class RiskHeatMap(BaseModel):
    """Risk heat map across codebase"""
    time_window: str
    modules: List[RiskHeatMapModule]


class HistoricalPattern(BaseModel):
    """Learned pattern from history"""
    pattern: str
    historical_occurrences: int
    failure_rate: float
    common_failures: List[str]
    recommendation: str


class ModelMetrics(BaseModel):
    """ML model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_size: int
    false_positive_rate: float
    false_negative_rate: float


class HistoricalPatternLearning(BaseModel):
    """Historical pattern learning results"""
    learned_patterns: List[HistoricalPattern]
    model_metrics: ModelMetrics


class RegressionRiskAnalyzerResult(BaseModel):
    """Complete regression risk analyzer result"""
    change_impact: ChangeImpactAnalysis
    test_selection: TestSelectionResult
    risk_heat_map: Optional[RiskHeatMap] = None
    historical_patterns: Optional[HistoricalPatternLearning] = None
    ci_optimization_recommendations: Dict[str, str]


# ============================================================================
# System Prompt
# ============================================================================

REGRESSION_RISK_ANALYZER_PROMPT = """You are the QE Regression Risk Analyzer, an expert at analyzing code changes to predict regression risk and intelligently select minimal test suites.

## Your Mission

Revolutionize CI/CD efficiency by **intelligently selecting the minimal set of tests** required to validate code changes. Using static analysis, dynamic dependency tracking, and ML-powered historical pattern learning, you reduce CI execution time by 90% while maintaining 95% defect detection rate.

## Core Capabilities

### 1. Change Impact Analysis
- Analyze git diffs to determine affected modules and features
- Calculate blast radius (direct + transitive impact)
- Assign risk scores based on complexity, criticality, and history
- Identify critical paths and dependencies

### 2. Intelligent Test Selection
- Select minimal test set using coverage mapping
- Apply ML predictions for likely-to-fail tests
- Use historical patterns to identify similar past changes
- Prioritize tests by failure probability

### 3. Risk Heat Mapping
- Create visual heat maps of codebase risk
- Track change frequency, complexity, and failure history
- Identify high-risk modules requiring attention
- Generate actionable recommendations

### 4. Dependency Tracking
- Build and maintain dependency graphs
- Analyze transitive dependencies
- Detect circular dependencies
- Calculate centrality scores for critical modules

### 5. Historical Pattern Learning
- Train ML models on historical test results
- Detect patterns in failures (time, author, complexity)
- Predict which tests will fail for new changes
- Continuously improve accuracy from feedback

### 6. CI Optimization
- Parallelize test execution across workers
- Implement intelligent caching strategies
- Skip redundant tests safely
- Balance test distribution for optimal runtime

## Input Analysis

When analyzing code changes, extract:
1. **Changed files**: paths, lines added/deleted, complexity
2. **Dependencies**: imports, exports, call graphs
3. **Risk factors**: criticality, historical failures, coverage
4. **Test coverage**: which tests cover changed code
5. **Historical data**: similar past changes and outcomes

## Test Selection Strategy

Prioritize tests based on:
1. **Coverage-based**: Must cover changed code directly
2. **Dependency-based**: Cover transitive dependencies
3. **Historical-based**: Failed for similar changes in past
4. **ML-predicted**: High failure probability
5. **Critical-path**: Cover business-critical flows

Aim for:
- **95%+ defect detection** (minimize false negatives)
- **90%+ test reduction** (maximize CI speed)
- **<5% false positive** rate (minimize unnecessary test runs)

## Risk Scoring Formula

Risk Score = (
    (lines_changed / 1000) * 0.2 +
    (complexity / 20) * 0.25 +
    criticality * 0.3 +
    (dependencies / 50) * 0.15 +
    historical_failure_rate * 0.1
) * 100

Risk Levels:
- **CRITICAL**: >80 (run full test suite + manual review)
- **HIGH**: 60-80 (run comprehensive test selection)
- **MEDIUM**: 40-60 (run targeted test selection)
- **LOW**: <40 (run minimal test selection)

## Output Format

Provide comprehensive analysis including:
1. **Change Impact Analysis**: Affected files, modules, blast radius
2. **Test Selection**: Minimal test set with justification
3. **Risk Assessment**: Risk score and level with recommendations
4. **CI Optimization**: Parallelization strategy and estimated runtime
5. **Recommendations**: Actions to take based on risk level

## Example Analysis

For a change to `payment.service.ts`:
- **Risk Score**: 78.3 (HIGH)
- **Blast Radius**: 9 files, 7 modules, 3 services
- **Test Selection**: 47 of 1,287 tests (96.3% reduction)
- **Estimated Runtime**: 4m 23s (vs 47m 12s full suite)
- **Recommendation**: Run selected tests + integration suite

## Success Metrics

Track and report:
- CI time reduction (target: 90%)
- Defect detection rate (target: 95%)
- False negative rate (target: <5%)
- False positive rate (target: <3%)

Focus on maximizing speed while maintaining confidence in test results."""


# ============================================================================
# Agent Implementation
# ============================================================================

from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


class RegressionRiskAnalyzerAgent(BaseQEAgent):
    """Regression Risk Analyzer Agent

    Analyzes code changes to predict regression risk and intelligently select
    minimal test suites for 10x faster CI through intelligent test selection
    with 95% defect detection rate.

    Capabilities:
    - Change impact analysis with blast radius calculation
    - Intelligent test selection using ML patterns
    - Risk heat mapping across the codebase
    - Dependency tracking and graph analysis
    - Historical pattern learning from test results
    - CI optimization through parallel execution
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
        """Initialize RegressionRiskAnalyzer Agent

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
            skills=skills or ['agentic-quality-engineering', 'regression-testing', 'risk-based-testing'],
            enable_learning=enable_learning,
            q_learning_service=q_learning_service,
            memory_config=memory_config
        )

    def get_system_prompt(self) -> str:
        """Define agent expertise"""
        return REGRESSION_RISK_ANALYZER_PROMPT

    async def execute(self, task: QETask) -> RegressionRiskAnalyzerResult:
        """Execute regression risk analysis on code changes

        Args:
            task: Task containing:
                - code_changes: Git diff or description of code changes
                - baseline_version: Baseline version for comparison (optional)
                - confidence_threshold: Minimum confidence for test selection (default: 0.95)
                - commit_sha: Git commit SHA (optional)
                - author: Code change author (optional)

        Returns:
            RegressionRiskAnalyzerResult with complete analysis
        """
        # Extract context
        context = task.context
        code_changes = context.get("code_changes", "")
        baseline_version = context.get("baseline_version")
        confidence_threshold = context.get("confidence_threshold", 0.95)
        commit_sha = context.get("commit_sha", "unknown")
        author = context.get("author", "unknown")

        # Retrieve historical patterns from memory
        historical_patterns = await self.get_memory(
            "aqe/regression/patterns",
            default=[]
        )

        # Retrieve risk heat map data
        risk_heat_map = await self.get_memory(
            "aqe/regression/risk-heat-map",
            default={}
        )

        # Use LionAGI to perform regression risk analysis
        result = await self.operate(
            instruction=f"""Analyze code changes to predict regression risk and select minimal test suite.

            Code Changes:
            ```
            {code_changes}
            ```

            {f'Baseline Version: {baseline_version}' if baseline_version else ''}
            {f'Commit SHA: {commit_sha}'}
            {f'Author: {author}'}
            Confidence Threshold: {confidence_threshold}

            Requirements:
            1. Analyze changed files with complexity and criticality scores
            2. Calculate blast radius (direct + transitive impact)
            3. Assign risk score (0-100) and level (LOW/MEDIUM/HIGH/CRITICAL)
            4. Select minimal test set using coverage mapping and ML predictions
            5. Prioritize tests by failure probability
            6. Estimate runtime and time savings vs full suite
            7. Provide CI optimization recommendations

            Historical Patterns (for ML prediction):
            {historical_patterns[:10] if historical_patterns else "No patterns available"}

            Risk Heat Map (for risk scoring):
            {str(risk_heat_map)[:500] if risk_heat_map else "No heat map available"}

            Selection Strategy:
            - Coverage-based: Must cover changed code directly
            - Dependency-based: Cover transitive dependencies
            - Historical-based: Failed for similar changes in past
            - ML-predicted: High failure probability
            - Critical-path: Cover business-critical flows

            Target: 95%+ defect detection, 90%+ test reduction
            """,
            response_format=RegressionRiskAnalyzerResult,
        )

        # Store analysis result in memory
        await self.store_memory(
            "aqe/regression/latest-analysis",
            result.model_dump(),
        )

        # Update historical patterns
        historical_patterns.append({
            "timestamp": datetime.now().isoformat(),
            "commit_sha": commit_sha,
            "risk_score": result.change_impact.risk_score,
            "risk_level": result.change_impact.risk_level,
            "selected_tests": result.test_selection.test_selection.selected,
            "reduction_rate": result.test_selection.test_selection.reduction_rate,
        })
        await self.store_memory(
            "aqe/regression/patterns",
            historical_patterns[-100:],  # Keep last 100 analyses
        )

        # Update risk heat map with new data
        for changed_file in result.change_impact.changed_files:
            risk_heat_map[changed_file.path] = {
                "risk_score": changed_file.complexity * changed_file.criticality,
                "last_modified": datetime.now().isoformat(),
                "change_frequency": risk_heat_map.get(changed_file.path, {}).get("change_frequency", 0) + 1,
            }
        await self.store_memory(
            "aqe/regression/risk-heat-map",
            risk_heat_map,
        )

        return result


# ============================================================================
# Placeholder Function (For Backward Compatibility)
# ============================================================================

def execute(
    code_changes: str,
    baseline_version: Optional[str] = None,
    confidence_threshold: float = 0.95
) -> RegressionRiskAnalyzerResult:
    """
    Execute regression risk analysis on code changes.

    Args:
        code_changes: Git diff or description of code changes
        baseline_version: Baseline version for comparison
        confidence_threshold: Minimum confidence for test selection

    Returns:
        RegressionRiskAnalyzerResult with complete analysis

    Note:
        This is a placeholder implementation. In production, this would:
        1. Parse git diff and analyze changed files
        2. Build dependency graph and calculate blast radius
        3. Query historical test results for pattern learning
        4. Apply ML model to predict test failures
        5. Select minimal test set meeting confidence threshold
        6. Generate risk heat map and recommendations
    """
    # Placeholder implementation
    # In production, integrate with:
    # - Git for diff analysis
    # - Coverage tools (Istanbul, Jest) for code-to-test mapping
    # - CI/CD for historical test results
    # - ML models for failure prediction

    # Example result structure
    return RegressionRiskAnalyzerResult(
        change_impact=ChangeImpactAnalysis(
            commit_sha="abc123def456",
            author="developer@example.com",
            timestamp=datetime.now(),
            changed_files=[
                ChangedFile(
                    path="src/services/payment.service.ts",
                    lines_added=47,
                    lines_deleted=23,
                    complexity=12.4,
                    criticality=0.95,
                    reason="Handles financial transactions"
                )
            ],
            direct_impact=[
                "src/controllers/checkout.controller.ts",
                "src/services/order.service.ts"
            ],
            transitive_impact=[
                "src/controllers/cart.controller.ts",
                "src/services/inventory.service.ts"
            ],
            blast_radius=BlastRadius(
                files=9,
                modules=7,
                services=6,
                affected_features=["checkout", "payment", "order-management"]
            ),
            risk_score=78.3,
            risk_level="HIGH",
            test_impact=TestImpact(
                required_tests=[
                    "tests/services/payment.service.test.ts",
                    "tests/integration/checkout.integration.test.ts"
                ],
                total_tests=47,
                estimated_runtime="4m 23s"
            ),
            recommendation="HIGH RISK - Run full payment test suite + integration tests"
        ),
        test_selection=TestSelectionResult(
            change_id="PR-1234",
            analysis_time="2.3s",
            test_selection=TestSelection(
                selected=47,
                total=1287,
                reduction_rate=0.963,
                estimated_runtime="4m 23s",
                full_suite_runtime="47m 12s",
                time_saved="42m 49s",
                confidence=0.95
            ),
            selected_tests=[
                SelectedTest(
                    path="tests/services/payment.service.test.ts",
                    reason="Direct coverage of changed file",
                    failure_probability=0.87,
                    priority="CRITICAL",
                    runtime="23s"
                )
            ],
            skipped_tests=1240,
            skipped_reasons={
                "no_coverage_overlap": 894,
                "low_failure_probability": 312,
                "unrelated_modules": 34
            },
            recommendation="Run 47 selected tests (96.3% reduction) with 95% confidence"
        ),
        ci_optimization_recommendations={
            "parallelization": "Use 8 workers with balanced runtime distribution",
            "caching": "Enable test result and dependency caching",
            "incremental": "Run only affected tests on feature branches"
        }
    )
