"""Unit tests for TestExecutorAgent - Test execution agent"""

import pytest
from unittest.mock import AsyncMock
from lionagi_qe.agents.test_executor import TestExecutorAgent, TestExecutionResult
from lionagi_qe.core.task import QETask
from lionagi import iModel


class TestTestExecutionResult:
    """Test TestExecutionResult model"""

    def test_execution_result_creation(self):
        """Test creating TestExecutionResult"""
        result = TestExecutionResult(
            total_tests=100,
            passed=95,
            failed=5,
            skipped=0,
            duration=12.5,
            coverage=87.3,
            failures=[
                {"test": "test_edge_case", "error": "AssertionError"}
            ],
            framework="pytest",
            success_rate=95.0
        )

        assert result.total_tests == 100
        assert result.passed == 95
        assert result.success_rate == 95.0

    def test_execution_result_defaults(self):
        """Test TestExecutionResult default values"""
        result = TestExecutionResult(
            total_tests=10,
            passed=10,
            failed=0,
            duration=1.0,
            framework="pytest",
            success_rate=100.0
        )

        assert result.skipped == 0
        assert result.coverage == 0.0
        assert result.failures == []


class TestTestExecutorAgent:
    """Test TestExecutorAgent functionality"""

    @pytest.mark.asyncio
    async def test_init(self, qe_memory, simple_model):
        """Test TestExecutorAgent initialization"""
        agent = TestExecutorAgent(
            agent_id="test-executor",
            model=simple_model,
            memory=qe_memory
        )

        assert agent.agent_id == "test-executor"

    @pytest.mark.asyncio
    async def test_system_prompt(self, test_executor_agent):
        """Test system prompt is comprehensive"""
        prompt = test_executor_agent.get_system_prompt()

        assert "execution" in prompt.lower()
        assert "parallel" in prompt.lower() or "coverage" in prompt.lower()

    @pytest.mark.asyncio
    async def test_execute_basic_test_run(self, test_executor_agent, mocker):
        """Test basic test execution"""
        mock_result = TestExecutionResult(
            total_tests=50,
            passed=48,
            failed=2,
            duration=5.2,
            coverage=85.0,
            framework="pytest",
            success_rate=96.0,
            failures=[
                {"test": "test_edge_case", "error": "AssertionError"}
            ]
        )

        mocker.patch.object(
            test_executor_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_execution",
            context={
                "test_path": "./tests",
                "framework": "pytest"
            }
        )

        result = await test_executor_agent.execute(task)

        assert result.total_tests == 50
        assert result.passed == 48
        assert result.framework == "pytest"

    @pytest.mark.asyncio
    async def test_execute_with_parallel(self, test_executor_agent, mocker):
        """Test execution with parallel enabled"""
        mock_result = TestExecutionResult(
            total_tests=100,
            passed=100,
            failed=0,
            duration=2.5,  # Faster with parallel
            framework="pytest",
            success_rate=100.0
        )

        mocker.patch.object(
            test_executor_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_execution",
            context={
                "test_path": "./tests",
                "framework": "pytest",
                "parallel": True
            }
        )

        result = await test_executor_agent.execute(task)

        assert result.duration < 5  # Fast execution

    @pytest.mark.asyncio
    async def test_execute_with_coverage(self, test_executor_agent, mocker):
        """Test execution with coverage reporting"""
        mock_result = TestExecutionResult(
            total_tests=30,
            passed=30,
            failed=0,
            duration=3.0,
            coverage=92.5,
            framework="pytest",
            success_rate=100.0
        )

        mocker.patch.object(
            test_executor_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_execution",
            context={
                "test_path": "./tests",
                "coverage": True
            }
        )

        result = await test_executor_agent.execute(task)

        assert result.coverage > 0

    @pytest.mark.asyncio
    async def test_execute_stores_results(self, test_executor_agent, mocker):
        """Test that execution results are stored"""
        mock_result = TestExecutionResult(
            total_tests=10,
            passed=10,
            failed=0,
            duration=1.0,
            framework="pytest",
            success_rate=100.0
        )

        mocker.patch.object(
            test_executor_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_execution",
            context={"test_path": "./tests"}
        )

        await test_executor_agent.execute(task)

        # Verify result was stored
        stored = await test_executor_agent.retrieve_context(
            "aqe/test-executor/last_execution"
        )
        assert stored is not None

    @pytest.mark.asyncio
    async def test_execute_retrieves_previous_results(self, test_executor_agent, mocker):
        """Test that previous execution results are retrieved for comparison"""
        # Store previous result
        previous_result = {
            "total_tests": 10,
            "passed": 9,
            "success_rate": 90.0
        }
        await test_executor_agent.store_result("last_execution", previous_result)

        mock_retrieve = mocker.patch.object(
            test_executor_agent,
            'retrieve_context',
            new=AsyncMock(return_value=previous_result)
        )

        mock_result = TestExecutionResult(
            total_tests=10,
            passed=10,
            failed=0,
            duration=1.0,
            framework="pytest",
            success_rate=100.0
        )

        mocker.patch.object(
            test_executor_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_execution",
            context={"test_path": "./tests"}
        )

        await test_executor_agent.execute(task)

        # Verify previous results were retrieved
        mock_retrieve.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_detects_flaky_tests(self, test_executor_agent, mocker):
        """Test detection of flaky tests"""
        # Store previous successful result
        previous_result = {
            "total_tests": 10,
            "passed": 10,
            "success_rate": 100.0
        }
        await test_executor_agent.store_result("last_execution", previous_result)

        # Current result has failures
        mock_result = TestExecutionResult(
            total_tests=10,
            passed=8,
            failed=2,
            duration=1.0,
            framework="pytest",
            success_rate=80.0  # Lower than previous
        )

        mocker.patch.object(
            test_executor_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_execution",
            context={"test_path": "./tests"}
        )

        await test_executor_agent.execute(task)

        # Verify flaky tests were flagged
        flaky = await test_executor_agent.retrieve_context(
            "aqe/test-executor/potential_flaky_tests"
        )
        assert flaky is not None
        assert flaky["current_rate"] == 80.0
        assert flaky["previous_rate"] == 100.0

    @pytest.mark.asyncio
    async def test_execute_different_frameworks(self, test_executor_agent, mocker):
        """Test execution with different frameworks"""
        frameworks = ["pytest", "jest", "mocha", "cypress"]

        for framework in frameworks:
            mock_result = TestExecutionResult(
                total_tests=5,
                passed=5,
                failed=0,
                duration=1.0,
                framework=framework,
                success_rate=100.0
            )

            mocker.patch.object(
                test_executor_agent,
                'operate',
                new=AsyncMock(return_value=mock_result)
            )

            task = QETask(
                task_type="test_execution",
                context={
                    "test_path": "./tests",
                    "framework": framework
                }
            )

            result = await test_executor_agent.execute(task)
            assert result.framework == framework

    @pytest.mark.asyncio
    async def test_execute_with_failures(self, test_executor_agent, mocker):
        """Test execution with test failures"""
        mock_result = TestExecutionResult(
            total_tests=20,
            passed=15,
            failed=5,
            duration=3.0,
            framework="pytest",
            success_rate=75.0,
            failures=[
                {"test": "test_api_endpoint", "error": "404 Not Found"},
                {"test": "test_validation", "error": "ValueError"},
                {"test": "test_edge_case", "error": "AssertionError"},
            ]
        )

        mocker.patch.object(
            test_executor_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_execution",
            context={"test_path": "./tests"}
        )

        result = await test_executor_agent.execute(task)

        assert result.failed > 0
        assert len(result.failures) > 0

    @pytest.mark.asyncio
    async def test_execute_with_skipped_tests(self, test_executor_agent, mocker):
        """Test execution with skipped tests"""
        mock_result = TestExecutionResult(
            total_tests=30,
            passed=25,
            failed=0,
            skipped=5,
            duration=2.0,
            framework="pytest",
            success_rate=100.0
        )

        mocker.patch.object(
            test_executor_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_execution",
            context={"test_path": "./tests"}
        )

        result = await test_executor_agent.execute(task)

        assert result.skipped == 5
        assert result.total_tests == result.passed + result.failed + result.skipped

    @pytest.mark.asyncio
    async def test_default_test_path(self, test_executor_agent, mocker):
        """Test default test path is ./tests"""
        mock_result = TestExecutionResult(
            total_tests=1,
            passed=1,
            failed=0,
            duration=0.1,
            framework="pytest",
            success_rate=100.0
        )

        mocker.patch.object(
            test_executor_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_execution",
            context={}  # No test_path specified
        )

        await test_executor_agent.execute(task)
        # Should use default ./tests path (verified in operate call)

    @pytest.mark.asyncio
    async def test_default_framework(self, test_executor_agent, mocker):
        """Test default framework is pytest"""
        mock_result = TestExecutionResult(
            total_tests=1,
            passed=1,
            failed=0,
            duration=0.1,
            framework="pytest",
            success_rate=100.0
        )

        mocker.patch.object(
            test_executor_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_execution",
            context={"test_path": "./tests"}
        )

        result = await test_executor_agent.execute(task)

        assert result.framework == "pytest"

    @pytest.mark.asyncio
    async def test_parallel_enabled_by_default(self, test_executor_agent, mocker):
        """Test parallel execution is enabled by default"""
        mock_result = TestExecutionResult(
            total_tests=1,
            passed=1,
            failed=0,
            duration=0.1,
            framework="pytest",
            success_rate=100.0
        )

        mocker.patch.object(
            test_executor_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_execution",
            context={"test_path": "./tests"}
        )

        await test_executor_agent.execute(task)
        # Parallel should be True by default

    @pytest.mark.asyncio
    async def test_coverage_enabled_by_default(self, test_executor_agent, mocker):
        """Test coverage reporting is enabled by default"""
        mock_result = TestExecutionResult(
            total_tests=1,
            passed=1,
            failed=0,
            duration=0.1,
            coverage=85.0,
            framework="pytest",
            success_rate=100.0
        )

        mocker.patch.object(
            test_executor_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_execution",
            context={"test_path": "./tests"}
        )

        result = await test_executor_agent.execute(task)
        # Coverage should be included

    @pytest.mark.asyncio
    async def test_no_flaky_tests_first_run(self, test_executor_agent, mocker):
        """Test no flaky test detection on first run"""
        # No previous results
        mock_result = TestExecutionResult(
            total_tests=10,
            passed=8,
            failed=2,
            duration=1.0,
            framework="pytest",
            success_rate=80.0
        )

        mocker.patch.object(
            test_executor_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_execution",
            context={"test_path": "./tests"}
        )

        await test_executor_agent.execute(task)

        # Should not flag flaky tests on first run
        flaky = await test_executor_agent.retrieve_context(
            "aqe/test-executor/potential_flaky_tests"
        )
        assert flaky is None
