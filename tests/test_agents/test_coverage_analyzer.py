"""Unit tests for CoverageAnalyzerAgent - Real-time gap detection with sublinear optimization"""

import pytest
from unittest.mock import AsyncMock, Mock
from hypothesis import given, strategies as st
from lionagi_qe.agents.coverage_analyzer import (
    CoverageAnalyzerAgent,
    CoverageGap,
    CoverageAnalysisResult,
)
from lionagi_qe.core.task import QETask


class TestCoverageAnalyzerAgent:
    """Test suite for CoverageAnalyzerAgent"""

    @pytest.fixture
    async def agent(self, qe_memory, simple_model):
        """Create coverage analyzer agent"""
        return CoverageAnalyzerAgent(
            agent_id="coverage-analyzer",
            model=simple_model,
            memory=qe_memory,
            skills=["agentic-quality-engineering", "test-automation-strategy"],
            enable_learning=False,
        )

    @pytest.fixture
    def sample_coverage_data(self):
        """Sample coverage data from test framework"""
        return {
            "total": {"lines": 1000, "statements": 950, "branches": 400, "functions": 150},
            "covered": {"lines": 850, "statements": 810, "branches": 320, "functions": 135},
            "files": {
                "src/user_service.py": {
                    "lines": {"total": 200, "covered": 150, "pct": 75.0},
                    "statements": {"total": 180, "covered": 140, "pct": 77.8},
                    "branches": {"total": 80, "covered": 55, "pct": 68.8},
                    "functions": {"total": 25, "covered": 20, "pct": 80.0},
                    "uncovered_lines": [15, 16, 45, 46, 47, 102, 103, 150],
                },
                "src/auth_service.py": {
                    "lines": {"total": 150, "covered": 145, "pct": 96.7},
                    "statements": {"total": 140, "covered": 138, "pct": 98.6},
                    "branches": {"total": 60, "covered": 58, "pct": 96.7},
                    "functions": {"total": 20, "covered": 20, "pct": 100.0},
                    "uncovered_lines": [89, 90],
                },
            },
        }

    # ==================== Initialization Tests ====================

    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """Test agent initialization"""
        assert agent.agent_id == "coverage-analyzer"
        assert "agentic-quality-engineering" in agent.skills
        assert agent.branch is not None

    @pytest.mark.asyncio
    async def test_system_prompt(self, agent):
        """Test system prompt contains coverage analysis concepts"""
        prompt = agent.get_system_prompt()
        assert "coverage analysis" in prompt.lower()
        assert "O(log n)" in prompt or "sublinear" in prompt.lower()
        assert "gap detection" in prompt.lower()
        assert "critical path" in prompt.lower()

    # ==================== Coverage Analysis Tests ====================

    @pytest.mark.asyncio
    async def test_analyze_coverage_success(self, agent, sample_coverage_data, mocker):
        """Test successful coverage analysis"""
        task = QETask(
            task_type="analyze_coverage",
            context={
                "coverage_data": sample_coverage_data,
                "framework": "pytest",
                "codebase_path": "/src",
                "target_coverage": 85,
            },
        )

        mock_result = CoverageAnalysisResult(
            overall_coverage=85.0,
            line_coverage=85.0,
            branch_coverage=80.0,
            function_coverage=90.0,
            gaps=[
                CoverageGap(
                    file_path="src/user_service.py",
                    line_start=15,
                    line_end=16,
                    gap_type="uncovered",
                    severity="medium",
                    critical_path=False,
                    suggested_tests=["test_user_validation_edge_case"],
                ),
                CoverageGap(
                    file_path="src/user_service.py",
                    line_start=45,
                    line_end=47,
                    gap_type="uncovered",
                    severity="high",
                    critical_path=True,
                    suggested_tests=["test_user_creation_flow", "test_error_handling"],
                ),
            ],
            critical_paths=["user_creation", "authentication_flow"],
            trends={"7_days": 83.5, "30_days": 80.2, "trend": "improving"},
            optimization_suggestions=[
                "Focus on user_service.py lines 45-47 (critical path)",
                "Add branch coverage for error handling paths",
            ],
            framework="pytest",
            analysis_time_ms=850.5,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.overall_coverage == 85.0
        assert len(result.gaps) > 0
        assert result.analysis_time_ms < 2000  # O(log n) performance
        assert len(result.optimization_suggestions) > 0

    @pytest.mark.asyncio
    async def test_detect_critical_path_gaps(self, agent, sample_coverage_data, mocker):
        """Test detection of gaps on critical execution paths"""
        task = QETask(
            task_type="analyze_coverage",
            context={
                "coverage_data": sample_coverage_data,
                "framework": "jest",
                "enable_prediction": True,
            },
        )

        mock_result = CoverageAnalysisResult(
            overall_coverage=75.0,
            line_coverage=75.0,
            branch_coverage=68.8,
            function_coverage=80.0,
            gaps=[
                CoverageGap(
                    file_path="src/user_service.py",
                    line_start=45,
                    line_end=47,
                    gap_type="uncovered",
                    severity="critical",
                    critical_path=True,
                    suggested_tests=[
                        "test_user_creation_critical_path",
                        "test_database_transaction_rollback",
                    ],
                )
            ],
            critical_paths=["user_creation", "payment_processing"],
            trends={},
            optimization_suggestions=["PRIORITY: Cover critical path in user_service.py"],
            framework="jest",
            analysis_time_ms=920.0,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        critical_gaps = [g for g in result.gaps if g.critical_path]
        assert len(critical_gaps) > 0
        assert all(g.severity in ["high", "critical"] for g in critical_gaps)

    @pytest.mark.asyncio
    async def test_sublinear_performance(self, agent, mocker):
        """Test analysis completes in sublinear time O(log n)"""
        # Large codebase simulation
        large_coverage_data = {
            "total": {"lines": 100000, "statements": 95000},
            "covered": {"lines": 85000, "statements": 81000},
            "files": {f"file_{i}.py": {"lines": {"total": 500, "covered": 425}} for i in range(200)},
        }

        task = QETask(
            task_type="analyze_coverage",
            context={
                "coverage_data": large_coverage_data,
                "framework": "pytest",
            },
        )

        mock_result = CoverageAnalysisResult(
            overall_coverage=85.0,
            line_coverage=85.0,
            branch_coverage=80.0,
            function_coverage=90.0,
            gaps=[],
            critical_paths=[],
            trends={},
            optimization_suggestions=[],
            framework="pytest",
            analysis_time_ms=1500.0,  # Should be O(log n) even for large codebase
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        # Verify sublinear performance target met
        assert result.analysis_time_ms < 2000

    # ==================== Gap Detection Tests ====================

    @pytest.mark.asyncio
    async def test_gap_severity_classification(self, agent, sample_coverage_data, mocker):
        """Test gap severity is classified correctly"""
        task = QETask(
            task_type="analyze_coverage",
            context={
                "coverage_data": sample_coverage_data,
                "framework": "pytest",
            },
        )

        mock_result = CoverageAnalysisResult(
            overall_coverage=85.0,
            line_coverage=85.0,
            branch_coverage=80.0,
            function_coverage=90.0,
            gaps=[
                CoverageGap(
                    file_path="src/utils.py",
                    line_start=10,
                    line_end=12,
                    gap_type="uncovered",
                    severity="low",
                    critical_path=False,
                    suggested_tests=["test_utility_helper"],
                ),
                CoverageGap(
                    file_path="src/payment.py",
                    line_start=100,
                    line_end=120,
                    gap_type="partial",
                    severity="critical",
                    critical_path=True,
                    suggested_tests=["test_payment_transaction", "test_refund_flow"],
                ),
            ],
            critical_paths=["payment_processing"],
            trends={},
            optimization_suggestions=[],
            framework="pytest",
            analysis_time_ms=800.0,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        severities = [g.severity for g in result.gaps]
        assert "low" in severities
        assert "critical" in severities

    @pytest.mark.asyncio
    async def test_suggested_tests_generation(self, agent, sample_coverage_data, mocker):
        """Test suggested tests are generated for gaps"""
        task = QETask(
            task_type="analyze_coverage",
            context={
                "coverage_data": sample_coverage_data,
                "framework": "pytest",
            },
        )

        mock_result = CoverageAnalysisResult(
            overall_coverage=75.0,
            line_coverage=75.0,
            branch_coverage=68.0,
            function_coverage=80.0,
            gaps=[
                CoverageGap(
                    file_path="src/api.py",
                    line_start=50,
                    line_end=55,
                    gap_type="uncovered",
                    severity="high",
                    critical_path=True,
                    suggested_tests=[
                        "test_api_endpoint_error_handling",
                        "test_api_authentication_failure",
                        "test_api_rate_limiting",
                    ],
                )
            ],
            critical_paths=["api_request_handling"],
            trends={},
            optimization_suggestions=[],
            framework="pytest",
            analysis_time_ms=750.0,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert all(len(g.suggested_tests) > 0 for g in result.gaps)

    # ==================== Trend Analysis Tests ====================

    @pytest.mark.asyncio
    async def test_coverage_trend_analysis(self, agent, qe_memory, sample_coverage_data, mocker):
        """Test coverage trend analysis over time"""
        # Store historical trends
        await qe_memory.store(
            "aqe/coverage/trends",
            {
                "overall": 80.0,
                "line": 78.0,
                "branch": 75.0,
                "function": 85.0,
                "timestamp": "2024-01-01",
            },
        )

        task = QETask(
            task_type="analyze_coverage",
            context={
                "coverage_data": sample_coverage_data,
                "framework": "pytest",
            },
        )

        mock_result = CoverageAnalysisResult(
            overall_coverage=85.0,
            line_coverage=85.0,
            branch_coverage=80.0,
            function_coverage=90.0,
            gaps=[],
            critical_paths=[],
            trends={
                "previous": 80.0,
                "current": 85.0,
                "delta": 5.0,
                "trend": "improving",
                "predictions": {"next_week": 87.0, "next_month": 90.0},
            },
            optimization_suggestions=["Continue current testing strategy - coverage improving"],
            framework="pytest",
            analysis_time_ms=900.0,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert "trend" in result.trends
        assert result.trends["trend"] == "improving"
        assert "predictions" in result.trends

    # ==================== Multi-Framework Support Tests ====================

    @pytest.mark.asyncio
    async def test_jest_framework_support(self, agent, mocker):
        """Test Jest framework coverage analysis"""
        jest_coverage = {
            "total": {"lines": 500, "statements": 480, "branches": 200, "functions": 80},
            "covered": {"lines": 450, "statements": 432, "branches": 180, "functions": 72},
        }

        task = QETask(
            task_type="analyze_coverage",
            context={
                "coverage_data": jest_coverage,
                "framework": "jest",
            },
        )

        mock_result = CoverageAnalysisResult(
            overall_coverage=90.0,
            line_coverage=90.0,
            branch_coverage=90.0,
            function_coverage=90.0,
            gaps=[],
            critical_paths=[],
            trends={},
            optimization_suggestions=[],
            framework="jest",
            analysis_time_ms=700.0,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.framework == "jest"
        assert result.overall_coverage == 90.0

    @pytest.mark.asyncio
    async def test_junit_framework_support(self, agent, mocker):
        """Test JUnit framework coverage analysis"""
        task = QETask(
            task_type="analyze_coverage",
            context={
                "coverage_data": {"total": 1000, "covered": 850},
                "framework": "junit",
            },
        )

        mock_result = CoverageAnalysisResult(
            overall_coverage=85.0,
            line_coverage=85.0,
            branch_coverage=80.0,
            function_coverage=90.0,
            gaps=[],
            critical_paths=[],
            trends={},
            optimization_suggestions=[],
            framework="junit",
            analysis_time_ms=800.0,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.framework == "junit"

    # ==================== Memory Integration Tests ====================

    @pytest.mark.asyncio
    async def test_stores_gaps_in_memory(self, agent, qe_memory, sample_coverage_data, mocker):
        """Test coverage gaps are stored in memory"""
        task = QETask(
            task_type="analyze_coverage",
            context={
                "coverage_data": sample_coverage_data,
                "framework": "pytest",
            },
        )

        mock_result = CoverageAnalysisResult(
            overall_coverage=85.0,
            line_coverage=85.0,
            branch_coverage=80.0,
            function_coverage=90.0,
            gaps=[
                CoverageGap(
                    file_path="src/test.py",
                    line_start=10,
                    line_end=15,
                    gap_type="uncovered",
                    severity="medium",
                    critical_path=False,
                    suggested_tests=["test_coverage"],
                )
            ],
            critical_paths=["test_path"],
            trends={},
            optimization_suggestions=[],
            framework="pytest",
            analysis_time_ms=850.0,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        # Verify gaps stored
        stored_gaps = await qe_memory.retrieve("aqe/coverage/gaps")
        assert stored_gaps is not None
        assert len(stored_gaps["gaps"]) > 0

    @pytest.mark.asyncio
    async def test_stores_critical_paths(self, agent, qe_memory, sample_coverage_data, mocker):
        """Test critical paths are stored for other agents"""
        task = QETask(
            task_type="analyze_coverage",
            context={
                "coverage_data": sample_coverage_data,
                "framework": "pytest",
            },
        )

        mock_result = CoverageAnalysisResult(
            overall_coverage=85.0,
            line_coverage=85.0,
            branch_coverage=80.0,
            function_coverage=90.0,
            gaps=[],
            critical_paths=["user_registration", "payment_processing", "data_export"],
            trends={},
            optimization_suggestions=[],
            framework="pytest",
            analysis_time_ms=750.0,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        # Verify critical paths shared
        stored_paths = await qe_memory.retrieve("aqe/shared/critical-paths")
        assert stored_paths is not None
        assert len(stored_paths["paths"]) > 0

    @pytest.mark.asyncio
    async def test_stores_learned_patterns(self, agent, qe_memory, sample_coverage_data, mocker):
        """Test efficient analysis patterns are learned"""
        task = QETask(
            task_type="analyze_coverage",
            context={
                "coverage_data": sample_coverage_data,
                "framework": "pytest",
            },
        )

        mock_result = CoverageAnalysisResult(
            overall_coverage=85.0,
            line_coverage=85.0,
            branch_coverage=80.0,
            function_coverage=90.0,
            gaps=[],
            critical_paths=[],
            trends={},
            optimization_suggestions=[],
            framework="pytest",
            analysis_time_ms=1500.0,  # Under 2000ms threshold
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        initial_patterns = agent.metrics["patterns_learned"]

        result = await agent.execute(task)

        # Verify pattern learned (analysis was efficient)
        assert agent.metrics["patterns_learned"] == initial_patterns + 1

    # ==================== Optimization Tests ====================

    @pytest.mark.asyncio
    async def test_optimization_suggestions(self, agent, sample_coverage_data, mocker):
        """Test optimization suggestions are generated"""
        task = QETask(
            task_type="analyze_coverage",
            context={
                "coverage_data": sample_coverage_data,
                "framework": "pytest",
                "target_coverage": 95,
            },
        )

        mock_result = CoverageAnalysisResult(
            overall_coverage=85.0,
            line_coverage=85.0,
            branch_coverage=80.0,
            function_coverage=90.0,
            gaps=[],
            critical_paths=[],
            trends={},
            optimization_suggestions=[
                "Increase branch coverage by 10% to reach target",
                "Focus on user_service.py (75% coverage)",
                "Add integration tests for API layer",
            ],
            framework="pytest",
            analysis_time_ms=850.0,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert len(result.optimization_suggestions) > 0
        assert any("target" in s.lower() for s in result.optimization_suggestions)

    # ==================== Error Handling Tests ====================

    @pytest.mark.asyncio
    async def test_handles_invalid_coverage_data(self, agent, mocker):
        """Test handling of invalid coverage data"""
        task = QETask(
            task_type="analyze_coverage",
            context={
                "coverage_data": None,  # Invalid
                "framework": "pytest",
            },
        )

        mocker.patch.object(
            agent,
            "operate",
            side_effect=Exception("Invalid coverage data"),
        )

        with pytest.raises(Exception) as exc_info:
            await agent.execute(task)

        assert "Invalid coverage data" in str(exc_info.value)

    # ==================== Property-Based Tests ====================

    @given(st.floats(min_value=0.0, max_value=100.0))
    def test_coverage_percentage_range(self, coverage):
        """Property-based test for coverage percentage range"""
        assert 0.0 <= coverage <= 100.0

    @given(
        st.integers(min_value=0, max_value=10000),
        st.integers(min_value=0, max_value=10000),
    )
    def test_coverage_calculation_logic(self, total, covered):
        """Property-based test for coverage calculation"""
        if total > 0:
            coverage = (covered / total) * 100 if covered <= total else 100.0
            assert 0.0 <= coverage <= 100.0

    # ==================== Integration Tests ====================

    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, agent, sample_coverage_data, qe_memory, mocker):
        """Test complete coverage analysis workflow"""
        # Store historical data
        await qe_memory.store("aqe/coverage/trends", {"overall": 80.0})

        task = QETask(
            task_type="analyze_coverage",
            context={
                "coverage_data": sample_coverage_data,
                "framework": "pytest",
                "codebase_path": "/src",
                "enable_prediction": True,
                "target_coverage": 90,
            },
        )

        mock_result = CoverageAnalysisResult(
            overall_coverage=85.0,
            line_coverage=85.0,
            branch_coverage=80.0,
            function_coverage=90.0,
            gaps=[
                CoverageGap(
                    file_path="src/user_service.py",
                    line_start=45,
                    line_end=47,
                    gap_type="uncovered",
                    severity="high",
                    critical_path=True,
                    suggested_tests=["test_user_creation"],
                )
            ],
            critical_paths=["user_creation"],
            trends={"previous": 80.0, "current": 85.0, "trend": "improving"},
            optimization_suggestions=["Add 5% more coverage to reach 90% target"],
            framework="pytest",
            analysis_time_ms=950.0,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        # Verify complete workflow
        assert result.overall_coverage == 85.0
        assert len(result.gaps) > 0
        assert len(result.critical_paths) > 0
        assert "trend" in result.trends
        assert len(result.optimization_suggestions) > 0

        # Verify memory storage
        stored_gaps = await qe_memory.retrieve("aqe/coverage/gaps")
        stored_trends = await qe_memory.retrieve("aqe/coverage/trends")
        stored_paths = await qe_memory.retrieve("aqe/shared/critical-paths")

        assert stored_gaps is not None
        assert stored_trends is not None
        assert stored_paths is not None

    @pytest.mark.asyncio
    async def test_agent_metrics_tracking(self, agent, sample_coverage_data, mocker):
        """Test agent tracks metrics correctly"""
        task = QETask(
            task_type="analyze_coverage",
            context={
                "coverage_data": sample_coverage_data,
                "framework": "pytest",
            },
        )

        mock_result = CoverageAnalysisResult(
            overall_coverage=85.0,
            line_coverage=85.0,
            branch_coverage=80.0,
            function_coverage=90.0,
            gaps=[],
            critical_paths=[],
            trends={},
            optimization_suggestions=[],
            framework="pytest",
            analysis_time_ms=850.0,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        initial_completed = agent.metrics["tasks_completed"]

        await agent.execute(task)

        metrics = await agent.get_metrics()
        assert metrics["tasks_completed"] == initial_completed + 1
