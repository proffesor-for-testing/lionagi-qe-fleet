"""Quality Gate Agent - Intelligent quality enforcement with risk assessment"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


class PolicyViolation(BaseModel):
    """Policy violation details"""

    policy_name: str = Field(..., description="Name of violated policy")
    severity: str = Field(..., description="Violation severity (low, medium, high, critical)")
    category: str = Field(..., description="Policy category (security, performance, quality)")
    description: str = Field(..., description="Violation description")
    remediation: str = Field(..., description="Remediation steps")
    can_override: bool = Field(default=False, description="Can be overridden with approval")
    override_authority: Optional[str] = Field(
        None, description="Required approval level for override"
    )


class RiskAssessment(BaseModel):
    """Risk assessment details"""

    risk_level: str = Field(..., description="Overall risk level (low, medium, high, critical)")
    critical_path_impact: float = Field(..., description="Impact on critical paths (0-1)")
    user_impact_scope: float = Field(..., description="Scope of user impact (0-1)")
    recovery_complexity: float = Field(..., description="Recovery complexity (0-1)")
    regulatory_impact: float = Field(..., description="Regulatory impact (0-1)")
    reputation_risk: float = Field(..., description="Reputation risk (0-1)")
    overall_score: float = Field(..., description="Overall risk score (0-100)")
    mitigation_strategies: List[str] = Field(
        default_factory=list, description="Risk mitigation strategies"
    )


class QualityGateDecision(BaseModel):
    """Quality gate decision result"""

    decision: str = Field(..., description="Gate decision (GO, NO-GO, CONDITIONAL_GO)")
    score: float = Field(..., description="Quality score (0-100)")
    risk_assessment: RiskAssessment = Field(..., description="Risk assessment")
    policy_violations: List[PolicyViolation] = Field(
        default_factory=list, description="Policy violations found"
    )
    metrics: Dict[str, float] = Field(..., description="Quality metrics evaluated")
    threshold_results: Dict[str, bool] = Field(
        default_factory=dict, description="Threshold pass/fail results"
    )
    conditions: List[str] = Field(
        default_factory=list, description="Conditions for CONDITIONAL_GO"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations for improvement"
    )
    override_eligible: bool = Field(
        default=False, description="Can decision be overridden"
    )
    justification: str = Field(..., description="Decision justification")
    next_steps: List[str] = Field(..., description="Recommended next steps")


class QualityGateAgent(BaseQEAgent):
    """Intelligent quality gate with risk assessment and policy validation

    Capabilities:
    - Quality enforcement with go/no-go decisions
    - Dynamic threshold management based on risk
    - Policy validation and compliance checking
    - Risk assessment with multi-factor analysis
    - AI-driven decision trees
    - Temporal prediction for quality trends
    - Psycho-symbolic reasoning for complex scenarios
    - Risk-based override mechanisms
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
        """Initialize Quality Gate Agent

        Args:
            agent_id: Unique agent identifier (e.g., "quality-gate")
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
            skills=skills or ["agentic-quality-engineering", "risk-based-testing", "quality-metrics"],
            enable_learning=enable_learning,
            q_learning_service=q_learning_service,
            memory_config=memory_config
        )

    def get_system_prompt(self) -> str:
        return """You are an expert quality gate agent specializing in:

**Core Capabilities:**
- Quality enforcement with intelligent go/no-go decisions
- Threshold management: Dynamically adjust based on context and risk
- Policy validation: Ensure compliance with organizational standards
- Risk assessment: Evaluate quality risks and delivery impact
- Decision orchestration: Coordinate quality decisions across pipeline

**Advanced Capabilities:**
- AI-driven decision trees with machine learning optimization
- Temporal prediction for quality trend analysis
- Psycho-symbolic reasoning for complex quality scenarios
- Risk-based override mechanisms with audit trails
- Real-time policy compliance monitoring

**Decision Workflow:**
Phase 1: Context Assessment
- Analyze test results comprehensively
- Process coverage metrics in detail
- Review performance data in real-time
- Check security scan results
- Verify compliance status

Phase 2: Quality Evaluation
- Metric Analysis: Process all quality indicators using AI
- Threshold Comparison: Compare against dynamic thresholds
- Risk Calculation: Assess potential impact of quality issues
- Trend Analysis: Evaluate quality trajectory using temporal models
- Policy Verification: Validate against compliance requirements

Phase 3: Decision Generation
- GO: All quality gates passed with acceptable risk
- NO-GO: Critical quality issues or unacceptable risk
- CONDITIONAL_GO: Pass with conditions and monitoring requirements
- Override Assessment: Evaluate business justification for exceptions

Phase 4: Action Execution
- Trigger appropriate pipeline actions
- Generate detailed quality reports
- Update quality dashboards
- Notify stakeholders of decisions
- Store decision audit trail

**Risk Assessment Matrix:**
Factor Weights:
- Critical Path Impact: 30%
- User Impact Scope: 25%
- Recovery Complexity: 20%
- Regulatory Impact: 15%
- Reputation Risk: 10%

Risk Levels:
- High Risk: Immediate escalation, additional testing required
- Medium Risk: Enhanced monitoring, conditional approval
- Low Risk: Standard approval with routine monitoring
- Negligible Risk: Automated approval with audit logging

**Threshold Categories:**
- Code Quality: Complexity, maintainability, technical debt
- Test Coverage: Line, branch, functional coverage metrics
- Performance: Response time, throughput, resource utilization
- Security: Vulnerability scanning, compliance verification
- Reliability: Error rates, availability, stability metrics

**Policy Enforcement:**
- Security: Vulnerability scanning required, security review mandatory
- Performance: Load testing required, performance budgets enforced
- Quality: Code review mandatory, min 80% test coverage
- Compliance: Documentation up-to-date, regulatory requirements met

**Override Management:**
- Business Override: Requires C-level approval for production
- Technical Override: Senior architect approval with remediation plan
- Emergency Override: Incident commander authority with immediate review
- Compliance Override: Legal/compliance team approval required"""

    async def execute(self, task: QETask) -> QualityGateDecision:
        """Evaluate quality gate and make go/no-go decision

        Args:
            task: Task containing:
                - test_results: Test execution results
                - coverage_metrics: Coverage analysis results
                - performance_data: Performance test results
                - security_scan: Security scan results
                - context: Deployment context (dev, staging, prod)
                - thresholds: Custom quality thresholds

        Returns:
            QualityGateDecision with decision and justification
        """
        context = task.context
        test_results = context.get("test_results", {})
        coverage_metrics = context.get("coverage_metrics", {})
        performance_data = context.get("performance_data", {})
        security_scan = context.get("security_scan", {})
        deployment_context = context.get("context", "development")
        custom_thresholds = context.get("thresholds", {})

        # Retrieve quality thresholds from memory
        stored_thresholds = await self.get_memory(
            "aqe/quality/thresholds", default={}
        )

        # Retrieve decision context for pattern learning
        decision_context = await self.get_memory(
            "aqe/context", default={}
        )

        # Retrieve historical decisions for trend analysis
        historical_decisions = await self.get_memory(
            "aqe/quality/decisions", default={}
        )

        # Execute quality gate evaluation
        result = await self.operate(
            instruction=f"""Evaluate quality gate and make intelligent go/no-go decision.

Deployment Context: {deployment_context}

Test Results:
```json
{test_results}
```

Coverage Metrics:
```json
{coverage_metrics}
```

Performance Data:
```json
{performance_data}
```

Security Scan:
```json
{security_scan}
```

Quality Thresholds:
```json
{custom_thresholds or stored_thresholds}
```

Historical Context:
```json
{historical_decisions}
```

Evaluation Requirements:
1. Analyze all quality metrics using AI-driven decision trees
2. Compare metrics against dynamic thresholds adjusted for {deployment_context}
3. Perform comprehensive risk assessment:
   - Critical Path Impact (30% weight)
   - User Impact Scope (25% weight)
   - Recovery Complexity (20% weight)
   - Regulatory Impact (15% weight)
   - Reputation Risk (10% weight)
4. Validate against organizational policies:
   - Security: Vulnerability scanning, security review
   - Performance: Load testing, performance budgets
   - Quality: Code review, test coverage (min 80%)
   - Compliance: Documentation, regulatory requirements
5. Use temporal prediction for quality trend analysis
6. Apply psycho-symbolic reasoning for edge cases
7. Calculate overall quality score (0-100)
8. Generate decision with clear justification

Decision Types:
- GO: All gates passed, acceptable risk, proceed with deployment
- NO-GO: Critical issues found, unacceptable risk, block deployment
- CONDITIONAL_GO: Pass with conditions and enhanced monitoring

For NO-GO or CONDITIONAL_GO:
- List all policy violations with severity
- Provide specific remediation steps
- Indicate if override is possible and required authority
- Suggest actionable next steps

Output Format:
- Clear GO/NO-GO/CONDITIONAL_GO decision
- Overall quality score (0-100)
- Comprehensive risk assessment with breakdown
- Policy violations (if any) with remediation
- Threshold comparison results (pass/fail per metric)
- Conditions (if CONDITIONAL_GO)
- Detailed justification with evidence
- Recommended next steps""",
            context={
                "test_results": test_results,
                "coverage_metrics": coverage_metrics,
                "performance_data": performance_data,
                "security_scan": security_scan,
                "deployment_context": deployment_context,
                "thresholds": custom_thresholds or stored_thresholds,
                "historical_decisions": historical_decisions,
            },
            response_format=QualityGateDecision,
        )

        # Store decision for audit trail
        await self.store_memory(
            "aqe/quality/decisions",
            {
                "decision": result.decision,
                "score": result.score,
                "risk_level": result.risk_assessment.risk_level,
                "context": deployment_context,
                "timestamp": task.created_at.isoformat(),
                "violations": [v.model_dump() for v in result.policy_violations],
            },
        )

        # Store metrics for trend analysis
        await self.store_memory(
            "aqe/quality/metrics",
            {
                "timestamp": task.created_at.isoformat(),
                "decision": result.decision,
                "score": result.score,
                "risk_level": result.risk_assessment.risk_level,
                "policy_violations": len(result.policy_violations),
                "metrics": result.metrics,
            },
        )

        # Store learned pattern if decision was made with high confidence
        if result.score >= 80 or result.score <= 40:  # Clear pass or fail
            await self.store_learned_pattern(
                f"quality_gate_{deployment_context}_{result.decision}",
                {
                    "context": deployment_context,
                    "decision": result.decision,
                    "score": result.score,
                    "risk_level": result.risk_assessment.risk_level,
                    "pattern": "high_confidence_decision",
                },
            )

        # Call post execution hook to update metrics
        await self.post_execution_hook(task, result.model_dump())

        return result
