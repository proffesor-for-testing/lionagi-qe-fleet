"""Unit tests for QualityAnalyzerAgent - Comprehensive quality metrics analysis"""

import pytest
from unittest.mock import AsyncMock
from hypothesis import given, strategies as st
from lionagi_qe.agents.quality_analyzer import (
    QualityAnalyzerAgent,
    CodeQualityMetrics,
    TestQualityMetrics,
    TechnicalDebt,
    QualityTrend,
    QualityAnalysisResult,
)
from lionagi_qe.core.task import QETask


class TestQualityAnalyzerAgent:
    """Test suite for QualityAnalyzerAgent"""

    @pytest.fixture
    async def agent(self, qe_memory, simple_model):
        """Create quality analyzer agent"""
        return QualityAnalyzerAgent(
            agent_id="quality-analyzer",
            model=simple_model,
            memory=qe_memory,
            skills=["agentic-quality-engineering", "quality-metrics"],
            enable_learning=False,
        )

    # ==================== Initialization Tests ====================

    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """Test agent initialization"""
        assert agent.agent_id == "quality-analyzer"
        assert agent.branch is not None

    @pytest.mark.asyncio
    async def test_system_prompt(self, agent):
        """Test system prompt"""
        prompt = agent.get_system_prompt()
        assert "quality" in prompt.lower()
        assert "metrics" in prompt.lower()

    # ==================== Quality Analysis Tests ====================

    @pytest.mark.asyncio
    async def test_comprehensive_quality_analysis(self, agent, mocker):
        """Test comprehensive quality analysis"""
        task = QETask(
            task_type="analyze_quality",
            context={
                "static_analysis": {"issues": 10, "warnings": 25},
                "test_results": {"coverage": 85.0, "tests_passed": 95},
                "code_metrics": {"complexity": 15, "maintainability": 75},
            },
        )

        mock_result = QualityAnalysisResult(
            overall_score=82.0,
            code_quality=CodeQualityMetrics(
                maintainability_index=75.0,
                complexity_score=80.0,
                duplication_score=90.0,
                code_smell_score=85.0,
                documentation_score=70.0,
                overall_score=80.0,
            ),
            test_quality=TestQualityMetrics(
                coverage_score=85.0,
                test_effectiveness=80.0,
                test_maintainability=75.0,
                test_performance=90.0,
                mutation_score=78.0,
                assertion_density=2.5,
            ),
            technical_debt=TechnicalDebt(
                debt_ratio=15.0,
                remediation_days=12.5,
                categories={"code_smells": 5.0, "security": 3.0, "performance": 2.0},
                priority_items=[{"item": "Refactor UserService", "priority": "high"}],
                estimated_cost=10.0,
            ),
            trends=QualityTrend(
                direction="improving",
                change_rate=2.5,
                predictions={"next_week": 84.0, "next_month": 88.0},
                anomalies=[],
            ),
            recommendations=["Focus on documentation", "Reduce complexity in UserService"],
            risk_areas=["Low test coverage in PaymentService"],
            strengths=["Good test quality", "Low duplication"],
            comparative_analysis={"baseline": 75.0, "current": 82.0, "improvement": 7.0},
            analysis_timestamp="2024-01-01T00:00:00",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.overall_score > 0
        assert result.code_quality is not None
        assert result.test_quality is not None
        assert result.technical_debt is not None
        assert result.trends is not None

    @pytest.mark.asyncio
    async def test_excellent_quality_pattern_learning(self, agent, qe_memory, mocker):
        """Test learning pattern for excellent quality"""
        task = QETask(task_type="analyze_quality", context={})

        mock_result = QualityAnalysisResult(
            overall_score=95.0,
            code_quality=CodeQualityMetrics(
                maintainability_index=95.0,
                complexity_score=90.0,
                duplication_score=95.0,
                code_smell_score=98.0,
                documentation_score=92.0,
                overall_score=94.0,
            ),
            test_quality=TestQualityMetrics(
                coverage_score=98.0,
                test_effectiveness=95.0,
                test_maintainability=90.0,
                test_performance=95.0,
            ),
            technical_debt=TechnicalDebt(
                debt_ratio=5.0, remediation_days=2.0, categories={}, priority_items=[]
            ),
            trends=QualityTrend(
                direction="improving", change_rate=1.0, predictions={}, anomalies=[]
            ),
            recommendations=[],
            risk_areas=[],
            strengths=["Excellent overall quality"],
            comparative_analysis={},
            analysis_timestamp="2024-01-01",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        initial_patterns = agent.metrics["patterns_learned"]
        await agent.execute(task)

        assert agent.metrics["patterns_learned"] == initial_patterns + 1

    # ==================== Memory Integration Tests ====================

    @pytest.mark.asyncio
    async def test_stores_analysis_results(self, agent, qe_memory, mocker):
        """Test analysis results stored in memory"""
        task = QETask(task_type="analyze_quality", context={})

        mock_result = QualityAnalysisResult(
            overall_score=80.0,
            code_quality=CodeQualityMetrics(
                maintainability_index=75.0,
                complexity_score=80.0,
                duplication_score=85.0,
                code_smell_score=80.0,
                documentation_score=70.0,
                overall_score=78.0,
            ),
            test_quality=TestQualityMetrics(
                coverage_score=82.0,
                test_effectiveness=78.0,
                test_maintainability=75.0,
                test_performance=85.0,
            ),
            technical_debt=TechnicalDebt(
                debt_ratio=12.0, remediation_days=8.0, categories={}, priority_items=[]
            ),
            trends=QualityTrend(direction="stable", change_rate=0.5, predictions={}, anomalies=[]),
            recommendations=[],
            risk_areas=[],
            strengths=[],
            comparative_analysis={},
            analysis_timestamp="2024-01-01",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        await agent.execute(task)

        stored = await qe_memory.retrieve("aqe/quality/analysis")
        assert stored is not None
        assert stored["overall_score"] == 80.0

    @pytest.mark.asyncio
    async def test_stores_quality_history(self, agent, qe_memory, mocker):
        """Test quality history is maintained"""
        task = QETask(task_type="analyze_quality", context={})

        mock_result = QualityAnalysisResult(
            overall_score=80.0,
            code_quality=CodeQualityMetrics(
                maintainability_index=75.0,
                complexity_score=80.0,
                duplication_score=85.0,
                code_smell_score=80.0,
                documentation_score=70.0,
                overall_score=78.0,
            ),
            test_quality=TestQualityMetrics(
                coverage_score=82.0,
                test_effectiveness=78.0,
                test_maintainability=75.0,
                test_performance=85.0,
            ),
            technical_debt=TechnicalDebt(
                debt_ratio=12.0, remediation_days=8.0, categories={}, priority_items=[]
            ),
            trends=QualityTrend(direction="stable", change_rate=0.5, predictions={}, anomalies=[]),
            recommendations=[],
            risk_areas=[],
            strengths=[],
            comparative_analysis={},
            analysis_timestamp="2024-01-01",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        await agent.execute(task)

        history = await qe_memory.retrieve("aqe/quality/history")
        assert history is not None
        assert len(history) > 0

    # ==================== Property-Based Tests ====================

    @given(st.floats(min_value=0.0, max_value=100.0))
    def test_score_range(self, score):
        """Property-based test for score range"""
        assert 0.0 <= score <= 100.0

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, agent, mocker):
        """Test metrics tracking"""
        task = QETask(task_type="analyze_quality", context={})

        mock_result = QualityAnalysisResult(
            overall_score=80.0,
            code_quality=CodeQualityMetrics(
                maintainability_index=75.0,
                complexity_score=80.0,
                duplication_score=85.0,
                code_smell_score=80.0,
                documentation_score=70.0,
                overall_score=78.0,
            ),
            test_quality=TestQualityMetrics(
                coverage_score=82.0,
                test_effectiveness=78.0,
                test_maintainability=75.0,
                test_performance=85.0,
            ),
            technical_debt=TechnicalDebt(
                debt_ratio=12.0, remediation_days=8.0, categories={}, priority_items=[]
            ),
            trends=QualityTrend(direction="stable", change_rate=0.5, predictions={}, anomalies=[]),
            recommendations=[],
            risk_areas=[],
            strengths=[],
            comparative_analysis={},
            analysis_timestamp="2024-01-01",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        initial = agent.metrics["tasks_completed"]
        await agent.execute(task)
        assert agent.metrics["tasks_completed"] == initial + 1
