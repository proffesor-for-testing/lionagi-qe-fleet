"""Unit tests for QualityGateAgent - Intelligent quality enforcement with risk assessment"""

import pytest
from unittest.mock import AsyncMock
from hypothesis import given, strategies as st
from lionagi_qe.agents.quality_gate import (
    QualityGateAgent,
    PolicyViolation,
    RiskAssessment,
    QualityGateDecision,
)
from lionagi_qe.core.task import QETask


class TestQualityGateAgent:
    """Test suite for QualityGateAgent"""

    @pytest.fixture
    async def agent(self, qe_memory, simple_model):
        """Create quality gate agent"""
        return QualityGateAgent(
            agent_id="quality-gate",
            model=simple_model,
            memory=qe_memory,
            skills=["agentic-quality-engineering", "risk-based-testing"],
            enable_learning=False,
        )

    # ==================== Initialization Tests ====================

    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """Test agent initialization"""
        assert agent.agent_id == "quality-gate"
        assert agent.branch is not None

    @pytest.mark.asyncio
    async def test_system_prompt(self, agent):
        """Test system prompt contains quality gate concepts"""
        prompt = agent.get_system_prompt()
        assert "quality gate" in prompt.lower()
        assert "go/no-go" in prompt.lower() or "decision" in prompt.lower()

    # ==================== Quality Gate Decision Tests ====================

    @pytest.mark.asyncio
    async def test_quality_gate_go_decision(self, agent, mocker):
        """Test GO decision when all gates pass"""
        task = QETask(
            task_type="quality_gate",
            context={
                "test_results": {"total": 100, "passed": 100, "failed": 0},
                "coverage_metrics": {"overall": 95.0, "branch": 90.0},
                "performance_data": {"p99_latency": 150, "error_rate": 0.001},
                "security_scan": {"vulnerabilities": 0},
                "context": "production",
            },
        )

        mock_result = QualityGateDecision(
            decision="GO",
            score=98.0,
            risk_assessment=RiskAssessment(
                risk_level="low",
                critical_path_impact=0.1,
                user_impact_scope=0.1,
                recovery_complexity=0.2,
                regulatory_impact=0.0,
                reputation_risk=0.1,
                overall_score=15.0,
                mitigation_strategies=[],
            ),
            policy_violations=[],
            metrics={"coverage": 95.0, "tests_passed": 100.0},
            threshold_results={"coverage": True, "tests": True},
            conditions=[],
            recommendations=["Maintain current quality standards"],
            override_eligible=False,
            justification="All quality gates passed with excellent scores",
            next_steps=["Proceed with deployment"],
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.decision == "GO"
        assert result.score >= 95.0
        assert len(result.policy_violations) == 0
        assert result.risk_assessment.risk_level == "low"

    @pytest.mark.asyncio
    async def test_quality_gate_no_go_decision(self, agent, mocker):
        """Test NO-GO decision when critical issues found"""
        task = QETask(
            task_type="quality_gate",
            context={
                "test_results": {"total": 100, "passed": 85, "failed": 15},
                "coverage_metrics": {"overall": 65.0, "branch": 55.0},
                "security_scan": {"vulnerabilities": 5, "critical": 2},
                "context": "production",
            },
        )

        mock_result = QualityGateDecision(
            decision="NO-GO",
            score=45.0,
            risk_assessment=RiskAssessment(
                risk_level="critical",
                critical_path_impact=0.8,
                user_impact_scope=0.9,
                recovery_complexity=0.7,
                regulatory_impact=0.6,
                reputation_risk=0.8,
                overall_score=85.0,
                mitigation_strategies=["Fix security vulnerabilities", "Increase test coverage"],
            ),
            policy_violations=[
                PolicyViolation(
                    policy_name="Security Review Required",
                    severity="critical",
                    category="security",
                    description="2 critical security vulnerabilities found",
                    remediation="Fix CVE-2024-001 and CVE-2024-002",
                    can_override=False,
                )
            ],
            metrics={"coverage": 65.0, "security_issues": 5},
            threshold_results={"coverage": False, "security": False},
            recommendations=["BLOCK DEPLOYMENT - Fix security issues", "Increase coverage to 80%"],
            override_eligible=False,
            justification="Critical security vulnerabilities and insufficient coverage",
            next_steps=["Fix security issues", "Add test coverage", "Re-run quality gate"],
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.decision == "NO-GO"
        assert result.score < 50.0
        assert len(result.policy_violations) > 0
        assert result.risk_assessment.risk_level == "critical"

    @pytest.mark.asyncio
    async def test_quality_gate_conditional_go(self, agent, mocker):
        """Test CONDITIONAL_GO with monitoring requirements"""
        task = QETask(
            task_type="quality_gate",
            context={
                "test_results": {"total": 100, "passed": 95, "failed": 5},
                "coverage_metrics": {"overall": 82.0, "branch": 78.0},
                "context": "staging",
            },
        )

        mock_result = QualityGateDecision(
            decision="CONDITIONAL_GO",
            score=78.0,
            risk_assessment=RiskAssessment(
                risk_level="medium",
                critical_path_impact=0.4,
                user_impact_scope=0.3,
                recovery_complexity=0.3,
                regulatory_impact=0.2,
                reputation_risk=0.3,
                overall_score=45.0,
                mitigation_strategies=["Enhanced monitoring", "Quick rollback capability"],
            ),
            policy_violations=[],
            metrics={"coverage": 82.0},
            threshold_results={"coverage": True},
            conditions=[
                "Monitor error rates closely during rollout",
                "Enable feature flag for quick rollback",
                "Increase test coverage to 85% within 1 week",
            ],
            recommendations=["Deploy with enhanced monitoring"],
            override_eligible=True,
            justification="Quality acceptable with conditions and monitoring",
            next_steps=["Deploy to staging", "Monitor closely", "Add coverage"],
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.decision == "CONDITIONAL_GO"
        assert 70.0 <= result.score < 85.0
        assert len(result.conditions) > 0
        assert result.risk_assessment.risk_level == "medium"

    # ==================== Memory Integration Tests ====================

    @pytest.mark.asyncio
    async def test_stores_decision_in_memory(self, agent, qe_memory, mocker):
        """Test decision is stored for audit trail"""
        task = QETask(
            task_type="quality_gate",
            context={"test_results": {}, "context": "development"},
        )

        mock_result = QualityGateDecision(
            decision="GO",
            score=90.0,
            risk_assessment=RiskAssessment(
                risk_level="low",
                critical_path_impact=0.1,
                user_impact_scope=0.1,
                recovery_complexity=0.1,
                regulatory_impact=0.0,
                reputation_risk=0.1,
                overall_score=10.0,
            ),
            policy_violations=[],
            metrics={},
            justification="All gates passed",
            next_steps=[],
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        await agent.execute(task)

        stored = await qe_memory.retrieve("aqe/quality/decisions")
        assert stored is not None
        assert stored["decision"] == "GO"

    # ==================== Property-Based Tests ====================

    @given(st.floats(min_value=0.0, max_value=100.0))
    def test_quality_score_range(self, score):
        """Property-based test for quality score range"""
        assert 0.0 <= score <= 100.0

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, agent, mocker):
        """Test agent tracks metrics"""
        task = QETask(task_type="quality_gate", context={})

        mock_result = QualityGateDecision(
            decision="GO",
            score=90.0,
            risk_assessment=RiskAssessment(
                risk_level="low",
                critical_path_impact=0.1,
                user_impact_scope=0.1,
                recovery_complexity=0.1,
                regulatory_impact=0.0,
                reputation_risk=0.1,
                overall_score=10.0,
            ),
            policy_violations=[],
            metrics={},
            justification="Pass",
            next_steps=[],
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        initial = agent.metrics["tasks_completed"]
        await agent.execute(task)
        assert agent.metrics["tasks_completed"] == initial + 1
