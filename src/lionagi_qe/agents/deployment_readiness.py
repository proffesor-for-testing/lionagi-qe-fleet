"""Deployment Readiness Agent - Multi-factor deployment risk assessment"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


class RiskScore(BaseModel):
    """Risk assessment score"""

    dimension: str = Field(..., description="Risk dimension (code_quality, security, etc.)")
    score: float = Field(..., description="Risk score (0-100)")
    weight: float = Field(..., description="Dimension weight in overall risk")
    status: str = Field(..., description="Status (PASS, WARNING, FAIL)")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed metrics")


class DeploymentDecision(BaseModel):
    """Deployment readiness decision"""

    decision: str = Field(..., description="GO, NO-GO, CONDITIONAL")
    overall_risk_score: float = Field(..., description="Overall risk score (0-100)")
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    confidence_score: float = Field(..., description="Release confidence (0-100)")
    risk_dimensions: List[RiskScore] = Field(..., description="Individual risk dimensions")
    blockers: List[str] = Field(default_factory=list, description="Deployment blockers")
    warnings: List[str] = Field(default_factory=list, description="Warnings to monitor")
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations for deployment"
    )
    rollback_plan: Dict[str, Any] = Field(
        default_factory=dict, description="Automated rollback plan"
    )
    checklist: Dict[str, Any] = Field(
        default_factory=dict, description="Deployment checklist results"
    )


class DeploymentReadinessAgent(BaseQEAgent):
    """Aggregates quality signals to provide deployment risk assessment

    Capabilities:
    - Multi-dimensional risk scoring (code quality, tests, security, performance)
    - Release confidence calculation using Bayesian inference
    - Automated deployment checklist validation
    - Rollback risk prediction and planning
    - Stakeholder reporting with executive summaries
    - Deployment gate enforcement
    - Post-deployment monitoring setup

    Skills:
    - agentic-quality-engineering: AI agents as force multipliers
    - risk-based-testing: Focus testing on highest-risk areas
    - shift-right-testing: Testing in production with feature flags
    - compliance-testing: Regulatory compliance validation
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
        """Initialize DeploymentReadiness Agent

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
            skills=skills or ['agentic-quality-engineering', 'risk-based-testing', 'quality-metrics'],
            enable_learning=enable_learning,
            q_learning_service=q_learning_service,
            memory_config=memory_config
        )

    def get_system_prompt(self) -> str:
        return """You are a deployment readiness expert specializing in:

**Core Capabilities:**
- Multi-dimensional risk scoring across 6 dimensions:
  * Code Quality (20% weight): complexity, duplication, maintainability
  * Test Coverage (25% weight): line/branch coverage, mutation score, reliability
  * Performance (15% weight): latency, throughput, scalability
  * Security (20% weight): vulnerabilities, compliance status
  * Change Risk (10% weight): change size, affected modules, blast radius
  * Historical Stability (10% weight): failure rate, MTTR, rollback frequency
- Bayesian release confidence calculation
- Automated deployment checklist validation
- Rollback risk prediction using ML models
- Deployment gate enforcement

**Risk Assessment:**
- Aggregate quality signals from all testing stages
- Calculate weighted risk scores with configurable thresholds
- Provide data-driven go/no-go decisions
- Generate rollback probability and automated rollback plans
- Track blast radius and impact assessment

**Quality Gates:**
- Code quality: Min grade B, 0 critical issues
- Test coverage: ≥85% line, ≥80% branch, ≥75% mutation
- Security: 0 critical/high vulnerabilities
- Performance: p95 <500ms, error rate <0.1%
- Compliance: GDPR, CCPA, HIPAA validation

**Deployment Strategies:**
- Blue-Green deployment with automatic cutover
- Canary rollout with gradual traffic shifting
- Feature flags for safe rollback
- A/B testing integration
- Multi-region orchestration

**Output Format:**
- Executive-friendly deployment reports
- Risk score breakdown with actionable recommendations
- Confidence interval with historical comparison
- Automated checklist with real-time validation
- Rollback plan with time estimates

**Decision Making:**
- Risk Score 0-20: ✅ LOW - Deploy with confidence
- Risk Score 21-40: ⚠️ MEDIUM - Deploy with monitoring
- Risk Score 41-60: 🚨 HIGH - Manual approval required
- Risk Score 61-100: 🛑 CRITICAL - DO NOT DEPLOY

Use Bayesian inference to calculate release confidence from historical data.
Prevent 90% of production incidents through pre-deployment validation.
Reduce MTTR by 65% through automated rollback procedures."""

    async def execute(self, task: QETask) -> DeploymentDecision:
        """Assess deployment readiness

        Args:
            task: Task containing:
                - version: Release version (e.g., "v2.5.0")
                - quality_signals: Aggregated quality metrics from all agents
                - deployment_config: Deployment configuration and gates
                - historical_data: Historical deployment outcomes

        Returns:
            DeploymentDecision with risk score and go/no-go decision
        """
        await self.pre_execution_hook(task)

        try:
            context = task.context
            version = context.get("version", "unknown")
            quality_signals = context.get("quality_signals", {})
            deployment_config = context.get("deployment_config", {})
            historical_data = context.get("historical_data", {})

            # Retrieve learned patterns and historical metrics
            learned_patterns = await self.get_learned_patterns()
            deployment_history = await self.retrieve_context("aqe/deployment/history")

            # Generate deployment assessment
            result = await self.operate(
                instruction=f"""Assess deployment readiness for version {version}.

**Quality Signals Available:**
{self._format_quality_signals(quality_signals)}

**Deployment Configuration:**
{self._format_deployment_config(deployment_config)}

**Historical Deployment Data:**
- Total Deployments: {historical_data.get('total_deployments', 0)}
- Success Rate: {historical_data.get('success_rate', 0)}%
- Average Rollback Rate: {historical_data.get('rollback_rate', 0)}%

**Assessment Requirements:**
1. Calculate risk scores for all 6 dimensions (code_quality, test_coverage, performance, security, change_risk, historical_stability)
2. Apply dimension weights: code_quality=0.20, test_coverage=0.25, performance=0.15, security=0.20, change_risk=0.10, historical_stability=0.10
3. Calculate overall risk score (0-100) and risk level (LOW/MEDIUM/HIGH/CRITICAL)
4. Calculate release confidence using Bayesian inference based on historical success rate
5. Identify blockers (critical issues that prevent deployment)
6. Identify warnings (issues requiring monitoring)
7. Generate actionable recommendations
8. Create automated rollback plan with triggers and procedures
9. Validate deployment checklist items

**Deployment Decision Criteria:**
- Risk Score 0-20: GO (Low risk, deploy with confidence)
- Risk Score 21-40: GO (Medium risk, deploy with enhanced monitoring)
- Risk Score 41-60: CONDITIONAL (High risk, manual approval required)
- Risk Score 61-100: NO-GO (Critical risk, do not deploy)

**Quality Gate Thresholds:**
- Code Quality: Min grade B, max 0 critical issues
- Test Coverage: ≥85% line, ≥80% branch, ≥75% mutation
- Security: 0 critical/high vulnerabilities
- Performance: p95 ≤500ms, error rate ≤0.1%

Provide comprehensive risk assessment with specific evidence and recommendations.""",
                response_format=DeploymentDecision,
            )

            # Store deployment decision in memory
            await self.store_result(
                f"deployment/{version}/decision",
                result.model_dump(),
                ttl=2592000,  # 30 days
            )

            # Store risk score for historical tracking
            await self.store_result(
                f"deployment/{version}/risk_score",
                {
                    "overall_risk": result.overall_risk_score,
                    "risk_level": result.risk_level,
                    "confidence": result.confidence_score,
                    "dimensions": [dim.model_dump() for dim in result.risk_dimensions],
                },
                ttl=2592000,
            )

            # Store rollback plan
            await self.store_result(
                f"deployment/{version}/rollback_plan",
                result.rollback_plan,
                ttl=2592000,
            )

            await self.post_execution_hook(task, result.model_dump())
            return result

        except Exception as e:
            await self.error_handler(task, e)
            raise

    def _format_quality_signals(self, signals: Dict[str, Any]) -> str:
        """Format quality signals for prompt"""
        if not signals:
            return "No quality signals available"

        formatted = []
        for category, metrics in signals.items():
            formatted.append(f"\n{category.upper()}:")
            if isinstance(metrics, dict):
                for key, value in metrics.items():
                    formatted.append(f"  - {key}: {value}")
            else:
                formatted.append(f"  {metrics}")

        return "\n".join(formatted)

    def _format_deployment_config(self, config: Dict[str, Any]) -> str:
        """Format deployment configuration for prompt"""
        if not config:
            return "No deployment configuration specified"

        formatted = []
        for key, value in config.items():
            formatted.append(f"  - {key}: {value}")

        return "\n".join(formatted)

    async def calculate_risk_score(
        self, quality_signals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate multi-dimensional risk score

        Args:
            quality_signals: Aggregated quality metrics

        Returns:
            Risk score breakdown
        """
        # This would contain the actual risk calculation logic
        # For now, it's a placeholder showing the structure
        pass

    async def generate_rollback_plan(
        self, deployment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate automated rollback plan

        Args:
            deployment_config: Deployment configuration

        Returns:
            Rollback plan with triggers and procedures
        """
        # This would contain rollback plan generation logic
        pass

    async def validate_deployment_gates(
        self, quality_signals: Dict[str, Any], gates_config: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Validate deployment gates

        Args:
            quality_signals: Quality metrics
            gates_config: Gate configuration

        Returns:
            Dict of gate results (passed/failed)
        """
        # This would contain gate validation logic
        pass
