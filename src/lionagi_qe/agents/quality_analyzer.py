"""Quality Analyzer Agent - Comprehensive quality metrics analysis"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


class CodeQualityMetrics(BaseModel):
    """Code quality metrics"""

    maintainability_index: float = Field(..., description="Maintainability index (0-100)")
    complexity_score: float = Field(..., description="Complexity score (0-100)")
    duplication_score: float = Field(..., description="Duplication score (0-100)")
    code_smell_score: float = Field(..., description="Code smell score (0-100)")
    documentation_score: float = Field(..., description="Documentation score (0-100)")
    overall_score: float = Field(..., description="Overall code quality (0-100)")


class TestQualityMetrics(BaseModel):
    """Test quality metrics"""

    coverage_score: float = Field(..., description="Overall coverage score (0-100)")
    test_effectiveness: float = Field(..., description="Test effectiveness (0-100)")
    test_maintainability: float = Field(..., description="Test maintainability (0-100)")
    test_performance: float = Field(..., description="Test performance (0-100)")
    mutation_score: Optional[float] = Field(
        None, description="Mutation testing score (0-100)"
    )
    assertion_density: float = Field(
        default=0.0, description="Assertions per test"
    )


class TechnicalDebt(BaseModel):
    """Technical debt analysis"""

    debt_ratio: float = Field(..., description="Technical debt ratio (%)")
    remediation_days: float = Field(..., description="Estimated remediation time (days)")
    categories: Dict[str, float] = Field(
        default_factory=dict, description="Debt by category with weights"
    )
    priority_items: List[Dict[str, Any]] = Field(
        default_factory=list, description="Prioritized debt items"
    )
    estimated_cost: float = Field(
        default=0.0, description="Estimated cost in developer-days"
    )


class QualityTrend(BaseModel):
    """Quality trend information"""

    direction: str = Field(..., description="Trend direction (improving, declining, stable)")
    change_rate: float = Field(..., description="Rate of change per week (%)")
    predictions: Dict[str, Any] = Field(
        default_factory=dict, description="Future quality predictions"
    )
    anomalies: List[str] = Field(
        default_factory=list, description="Detected anomalies"
    )


class QualityAnalysisResult(BaseModel):
    """Comprehensive quality analysis result"""

    overall_score: float = Field(..., description="Overall quality score (0-100)")
    code_quality: CodeQualityMetrics = Field(..., description="Code quality metrics")
    test_quality: TestQualityMetrics = Field(..., description="Test quality metrics")
    technical_debt: TechnicalDebt = Field(..., description="Technical debt analysis")
    trends: QualityTrend = Field(..., description="Quality trends")
    recommendations: List[str] = Field(
        default_factory=list, description="Actionable recommendations"
    )
    risk_areas: List[str] = Field(
        default_factory=list, description="High-risk areas identified"
    )
    strengths: List[str] = Field(
        default_factory=list, description="Quality strengths"
    )
    comparative_analysis: Dict[str, Any] = Field(
        default_factory=dict, description="Comparison with baselines"
    )
    analysis_timestamp: str = Field(..., description="Analysis timestamp")


class QualityAnalyzerAgent(BaseQEAgent):
    """Comprehensive quality metrics analysis with predictive analytics

    Capabilities:
    - Quality metrics collection from multiple sources
    - Trend analysis and pattern detection
    - Predictive analytics for quality forecasting
    - Code quality assessment (complexity, maintainability, debt)
    - Test quality evaluation (effectiveness, coverage)
    - Actionable insights generation
    - ML-powered quality prediction
    - Technical debt quantification
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
        """Initialize QualityAnalyzer Agent

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
            skills=skills or ['agentic-quality-engineering', 'quality-metrics', 'code-review-quality'],
            enable_learning=enable_learning,
            q_learning_service=q_learning_service,
            memory_config=memory_config
        )

    def get_system_prompt(self) -> str:
        return """You are an expert quality analysis agent specializing in:

**Core Capabilities:**
- Quality Metrics Collection: Gather comprehensive quality indicators from multiple sources
- Trend Analysis: Identify quality trends and patterns over time
- Predictive Analytics: Forecast quality trajectories and potential issues
- Code Quality Assessment: Evaluate maintainability, complexity, and technical debt
- Test Quality Evaluation: Analyze test effectiveness, coverage, and performance
- Actionable Insights: Generate prioritized recommendations for improvement

**Advanced Capabilities:**
- ML-powered quality prediction and anomaly detection
- Temporal analysis for quality trend forecasting
- Psycho-symbolic reasoning for complex quality scenarios
- Technical debt quantification and prioritization
- Real-time quality dashboard updates
- Comparative analysis against industry baselines

**Analysis Workflow:**
Phase 1: Data Collection
- Static analysis: ESLint, SonarQube, Code Climate
- Test results: Unit, integration, e2e coverage
- Code metrics: Complexity, duplication, maintainability
- Dependency analysis: Outdated, vulnerable, deprecated packages
- Documentation: Completeness, accuracy, coverage

Phase 2: Metric Calculation
- Code Quality Metrics: Calculate complexity, maintainability, code smell indices
- Test Quality Metrics: Analyze test coverage, quality, and effectiveness
- Technical Debt: Quantify technical debt and prioritize remediation
- Security Metrics: Assess vulnerability count, severity, fix urgency
- Performance Metrics: Evaluate performance characteristics and bottlenecks

Phase 3: Trend Analysis
- Historical Comparison: Compare current metrics against historical baselines
- Trajectory Prediction: Forecast future quality based on current trends
- Anomaly Detection: Identify unusual patterns or sudden quality changes
- Seasonal Adjustment: Account for cyclical patterns in quality metrics

Phase 4: Insight Generation
- Generate actionable recommendations with priority
- Prioritize quality improvements by ROI
- Estimate effort for remediation
- Create quality improvement roadmap
- Update quality dashboards

**Quality Metrics:**
Code Quality Score (0-100):
- Maintainability Index: 30% weight
- Complexity Score: 25% weight
- Duplication Score: 20% weight
- Code Smell Score: 15% weight
- Documentation Score: 10% weight

Test Quality Score (0-100):
- Coverage: Line, branch, function coverage
- Test Effectiveness: Mutation score, assertion density
- Test Maintainability: Test complexity, duplication
- Test Performance: Execution time, flakiness rate

Technical Debt Ratio:
- Remediation Effort / Development Time * 100
- Categories: Code smells (25%), Security (30%), Performance (20%), Documentation (15%), Test gaps (10%)
- Prioritization by: Severity, ROI, Business Impact

**Predictive Analytics:**
- Quality trend forecasting using time-series models
- Anomaly detection (statistical outliers, ML-based, pattern deviation)
- Early warning system for quality degradation
- Confidence intervals for predictions

**Integration Points:**
- SonarQube: Comprehensive code quality analysis
- ESLint: JavaScript/TypeScript linting
- Code Climate: Maintainability and test coverage
- Custom metrics: Complexity, coupling, cohesion analysis"""

    async def execute(self, task: QETask) -> QualityAnalysisResult:
        """Analyze comprehensive quality metrics

        Args:
            task: Task containing:
                - static_analysis: Results from linters and analyzers
                - test_results: Test execution and coverage data
                - code_metrics: Complexity and maintainability metrics
                - dependency_data: Dependency analysis results
                - codebase_path: Path to source code
                - historical_baseline: Historical quality data

        Returns:
            QualityAnalysisResult with metrics and recommendations
        """
        context = task.context
        static_analysis = context.get("static_analysis", {})
        test_results = context.get("test_results", {})
        code_metrics = context.get("code_metrics", {})
        dependency_data = context.get("dependency_data", {})
        codebase_path = context.get("codebase_path", "")
        historical_baseline = context.get("historical_baseline", {})

        # Retrieve quality configuration
        quality_config = await self.get_memory(
            "aqe/quality/config", default={}
        )

        # Retrieve historical quality data for trend analysis
        quality_history = await self.get_memory(
            "aqe/quality/history", default=[]
        )

        # Execute quality analysis using safe_operate for robust parsing
        # This handles malformed LLM outputs with automatic fuzzy parsing fallback
        result = await self.safe_operate(
            instruction=f"""Perform comprehensive quality analysis with predictive analytics.

Codebase: {codebase_path}

Static Analysis Results:
```json
{static_analysis}
```

Test Results:
```json
{test_results}
```

Code Metrics:
```json
{code_metrics}
```

Dependency Analysis:
```json
{dependency_data}
```

Historical Baseline:
```json
{historical_baseline}
```

Quality History (for trend analysis):
```json
{quality_history[-10:] if quality_history else []}
```

Analysis Requirements:
1. Calculate Code Quality Score (0-100):
   - Maintainability Index (30%)
   - Complexity Score (25%)
   - Duplication Score (20%)
   - Code Smell Score (15%)
   - Documentation Score (10%)

2. Calculate Test Quality Score (0-100):
   - Coverage metrics (line, branch, function)
   - Test effectiveness (mutation score if available)
   - Test maintainability (complexity, duplication)
   - Test performance (execution time, flakiness)

3. Quantify Technical Debt:
   - Calculate debt ratio (remediation time / development time * 100)
   - Categorize debt: Code smells (25%), Security (30%), Performance (20%), Docs (15%), Tests (10%)
   - Prioritize remediation items by severity and ROI
   - Estimate remediation effort in developer-days

4. Perform Trend Analysis:
   - Compare current metrics against historical data
   - Identify direction (improving, declining, stable)
   - Calculate rate of change per week
   - Predict future quality using time-series forecasting
   - Detect anomalies and unusual patterns

5. Generate Actionable Insights:
   - Create prioritized recommendations for improvement
   - Identify high-risk areas requiring immediate attention
   - Highlight quality strengths to maintain
   - Provide comparative analysis against baselines
   - Estimate effort and ROI for each recommendation

6. Risk Assessment:
   - Identify areas with high complexity + low coverage
   - Flag security vulnerabilities by severity
   - Highlight performance bottlenecks
   - Note documentation gaps in critical areas

Output Format:
- Overall quality score (0-100) with breakdown
- Detailed code and test quality metrics
- Comprehensive technical debt analysis with priorities
- Trend analysis with predictions and anomalies
- Actionable recommendations ranked by priority
- Risk areas and quality strengths
- Comparative analysis against historical baseline
- Timestamp for tracking""",
            context={
                "static_analysis": static_analysis,
                "test_results": test_results,
                "code_metrics": code_metrics,
                "dependency_data": dependency_data,
                "quality_config": quality_config,
                "quality_history": quality_history,
                "historical_baseline": historical_baseline,
            },
            response_format=QualityAnalysisResult,
        )

        # Store analysis results
        await self.store_memory(
            "aqe/quality/analysis",
            {
                "overall_score": result.overall_score,
                "code_quality": result.code_quality.model_dump(),
                "test_quality": result.test_quality.model_dump(),
                "technical_debt": result.technical_debt.model_dump(),
                "timestamp": task.created_at.isoformat(),
            },
        )

        # Store metrics for trend analysis (append to history)
        current_history = await self.get_memory("aqe/quality/history", default=[])
        current_history.append({
            "timestamp": task.created_at.isoformat(),
            "overall_score": result.overall_score,
            "code_quality": result.code_quality.overall_score,
            "test_quality": result.test_quality.coverage_score,
            "debt_ratio": result.technical_debt.debt_ratio,
        })
        # Keep last 100 entries
        await self.store_memory(
            "aqe/quality/history",
            current_history[-100:]
        )

        # Store learned pattern if quality is exceptional or concerning
        if result.overall_score >= 90:
            await self.store_learned_pattern(
                "quality_analysis_excellence",
                {
                    "overall_score": result.overall_score,
                    "code_quality": result.code_quality.overall_score,
                    "test_quality": result.test_quality.coverage_score,
                    "pattern": "high_quality_achieved",
                    "strengths": result.strengths,
                },
            )
        elif result.overall_score <= 50:
            await self.store_learned_pattern(
                "quality_analysis_concern",
                {
                    "overall_score": result.overall_score,
                    "risk_areas": result.risk_areas,
                    "debt_ratio": result.technical_debt.debt_ratio,
                    "pattern": "quality_degradation_detected",
                },
            )

        # Call post execution hook to update metrics
        await self.post_execution_hook(task, result.model_dump())

        return result
