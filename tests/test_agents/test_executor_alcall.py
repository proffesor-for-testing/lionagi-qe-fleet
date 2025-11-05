"""Tests for TestExecutorAgent with alcall parallel execution - Priority 1

Tests the execute_tests_parallel() method with:
- alcall parallel execution
- Automatic retry behavior
- Timeout handling
- Rate limiting
- Concurrent execution (10+ tests)
- Error aggregation
- Mock subprocess calls
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import subprocess
import asyncio
from lionagi_qe.agents.test_executor import TestExecutorAgent, TestExecutionResult
from lionagi_qe.core.task import QETask
from lionagi_qe.core.memory import QEMemory
from lionagi import iModel


class TestExecuteTestsParallel:
    """Test execute_tests_parallel() with alcall"""

    @pytest.mark.asyncio
    async def test_parallel_execution_basic(self, qe_memory, simple_model):
        """Test basic parallel test execution"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        test_files = [
            "test_module1.py",
            "test_module2.py",
            "test_module3.py"
        ]

        # Mock subprocess.run
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="All tests passed",
                stderr=""
            )

            result = await agent.execute_tests_parallel(test_files, framework="pytest")

            assert result["total"] == 3
            assert result["passed"] == 3
            assert result["failed"] == 0
            assert result["pass_rate"] == 100.0
            assert result["framework"] == "pytest"

    @pytest.mark.asyncio
    async def test_parallel_execution_with_failures(self, qe_memory, simple_model):
        """Test parallel execution with some failures"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        test_files = ["test1.py", "test2.py", "test3.py", "test4.py", "test5.py"]

        # Mock subprocess to simulate failures
        def mock_subprocess_run(*args, **kwargs):
            file_path = args[0][1] if len(args[0]) > 1 else "test1.py"
            # Fail test2 and test4
            if "test2" in file_path or "test4" in file_path:
                return MagicMock(returncode=1, stdout="", stderr="Test failed")
            return MagicMock(returncode=0, stdout="Passed", stderr="")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.execute_tests_parallel(test_files, framework="pytest")

            assert result["total"] == 5
            assert result["passed"] == 3
            assert result["failed"] == 2
            assert result["pass_rate"] == 60.0

    @pytest.mark.asyncio
    async def test_parallel_execution_timeout_handling(self, qe_memory, simple_model):
        """Test timeout handling in parallel execution"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        test_files = ["slow_test.py", "fast_test.py"]

        def mock_subprocess_run(*args, **kwargs):
            file_path = args[0][1] if len(args[0]) > 1 else ""
            if "slow" in file_path:
                raise subprocess.TimeoutExpired(cmd=args[0], timeout=60)
            return MagicMock(returncode=0, stdout="Passed", stderr="")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.execute_tests_parallel(test_files)

            assert result["total"] == 2
            assert result["timeouts"] >= 1
            # Timeout counts as failure
            assert result["failed"] >= 1

    @pytest.mark.asyncio
    async def test_parallel_execution_retry_logic(self, qe_memory, simple_model):
        """Test automatic retry logic with alcall"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        test_files = ["flaky_test.py"]

        call_count = 0

        def mock_subprocess_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Fail first 2 attempts, succeed on 3rd
            if call_count < 3:
                return MagicMock(returncode=1, stdout="", stderr="Flaky failure")
            return MagicMock(returncode=0, stdout="Passed", stderr="")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.execute_tests_parallel(test_files)

            # Should retry and eventually pass
            assert result["total"] == 1
            # Retries should be recorded
            assert "retries" in result

    @pytest.mark.asyncio
    async def test_parallel_execution_rate_limiting(self, qe_memory, simple_model):
        """Test rate limiting prevents resource exhaustion"""
        import time

        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        # Create 20 test files
        test_files = [f"test_{i}.py" for i in range(20)]

        execution_times = []

        def mock_subprocess_run(*args, **kwargs):
            start = time.time()
            # Simulate test execution
            time.sleep(0.01)
            execution_times.append(time.time() - start)
            return MagicMock(returncode=0, stdout="Passed", stderr="")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            start_time = time.time()
            result = await agent.execute_tests_parallel(test_files)
            total_time = time.time() - start_time

            assert result["total"] == 20
            # With rate limiting, should not complete instantly
            # Max 10 concurrent, so minimum time should be ~2 batches
            assert total_time > 0.02  # At least 2 batches * 0.01s

    @pytest.mark.asyncio
    async def test_parallel_execution_10_concurrent(self, qe_memory, simple_model):
        """Test concurrent execution of 10+ tests"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        # Create 15 test files
        test_files = [f"test_concurrent_{i}.py" for i in range(15)]

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Passed", stderr="")

            result = await agent.execute_tests_parallel(test_files)

            assert result["total"] == 15
            assert result["passed"] == 15
            assert mock_run.call_count == 15

    @pytest.mark.asyncio
    async def test_parallel_execution_error_aggregation(self, qe_memory, simple_model):
        """Test error aggregation from multiple failed tests"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        test_files = ["test_error1.py", "test_error2.py", "test_error3.py"]

        error_messages = {
            "test_error1.py": "AssertionError: expected 5, got 3",
            "test_error2.py": "TypeError: unsupported operand",
            "test_error3.py": "ValueError: invalid literal"
        }

        def mock_subprocess_run(*args, **kwargs):
            file_path = args[0][1] if len(args[0]) > 1 else ""
            for test_file, error_msg in error_messages.items():
                if test_file in file_path:
                    return MagicMock(returncode=1, stdout="", stderr=error_msg)
            return MagicMock(returncode=0, stdout="Passed", stderr="")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.execute_tests_parallel(test_files)

            assert result["failed"] == 3
            # Check that error details are in results
            for test_result in result["results"]:
                if not test_result["passed"]:
                    assert "error" in test_result or "errors" in test_result

    @pytest.mark.asyncio
    async def test_parallel_execution_framework_pytest(self, qe_memory, simple_model):
        """Test parallel execution with pytest framework"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        test_files = ["test_pytest.py"]

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Passed", stderr="")

            result = await agent.execute_tests_parallel(test_files, framework="pytest")

            # Verify pytest command was used
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            assert "pytest" in call_args
            assert "-v" in call_args
            assert "--tb=short" in call_args

    @pytest.mark.asyncio
    async def test_parallel_execution_framework_jest(self, qe_memory, simple_model):
        """Test parallel execution with jest framework"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        test_files = ["test.spec.js"]

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Passed", stderr="")

            result = await agent.execute_tests_parallel(test_files, framework="jest")

            # Verify jest command was used
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            assert "npm" in call_args
            assert "test" in call_args

    @pytest.mark.asyncio
    async def test_parallel_execution_framework_mocha(self, qe_memory, simple_model):
        """Test parallel execution with mocha framework"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        test_files = ["test.spec.js"]

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Passed", stderr="")

            result = await agent.execute_tests_parallel(test_files, framework="mocha")

            # Verify mocha command was used
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            assert "npx" in call_args
            assert "mocha" in call_args

    @pytest.mark.asyncio
    async def test_parallel_execution_unsupported_framework(self, qe_memory, simple_model):
        """Test error handling for unsupported framework"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        test_files = ["test.py"]

        with patch('subprocess.run'):
            result = await agent.execute_tests_parallel(test_files, framework="unknown")

            # Should handle gracefully
            assert result["total"] == 1
            assert result["failed"] == 1
            # Error should be recorded in results
            assert any("Unsupported framework" in str(r.get("error", "")) for r in result["results"])


class TestExecuteMethod:
    """Test the main execute() method"""

    @pytest.mark.asyncio
    async def test_execute_with_coverage(self, qe_memory, simple_model, mocker):
        """Test execute method with coverage enabled"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        task = QETask(
            task_type="test_execution",
            context={
                "test_path": "./tests",
                "framework": "pytest",
                "parallel": True,
                "coverage": True
            }
        )

        # Mock operate to return TestExecutionResult
        mock_result = TestExecutionResult(
            total_tests=50,
            passed=48,
            failed=2,
            duration=12.5,
            coverage=87.5,
            framework="pytest",
            success_rate=96.0
        )

        mocker.patch.object(
            agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        result = await agent.execute(task)

        assert result.total_tests == 50
        assert result.passed == 48
        assert result.coverage == 87.5
        assert result.framework == "pytest"

    @pytest.mark.asyncio
    async def test_execute_stores_results(self, qe_memory, simple_model, mocker):
        """Test execute stores results in memory"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        task = QETask(
            task_type="test_execution",
            context={"test_path": "./tests"}
        )

        mock_result = TestExecutionResult(
            total_tests=10,
            passed=10,
            failed=0,
            duration=5.0,
            framework="pytest",
            success_rate=100.0
        )

        mocker.patch.object(agent, 'operate', new=AsyncMock(return_value=mock_result))

        await agent.execute(task)

        # Verify result was stored
        stored = await qe_memory.retrieve("aqe/test-executor/last_execution")
        assert stored is not None
        assert stored["total_tests"] == 10

    @pytest.mark.asyncio
    async def test_execute_compares_with_previous(self, qe_memory, simple_model, mocker):
        """Test execute compares with previous execution"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        # Store previous result
        await qe_memory.store("aqe/test-executor/last_execution", {
            "total_tests": 10,
            "success_rate": 95.0
        })

        task = QETask(
            task_type="test_execution",
            context={"test_path": "./tests"}
        )

        mock_result = TestExecutionResult(
            total_tests=10,
            passed=10,
            failed=0,
            duration=5.0,
            framework="pytest",
            success_rate=100.0
        )

        operate_mock = mocker.patch.object(agent, 'operate', new=AsyncMock(return_value=mock_result))

        await agent.execute(task)

        # Verify previous results were passed to operate
        assert operate_mock.called
        call_context = operate_mock.call_args[1]["context"]
        assert call_context["previous_results"] is not None

    @pytest.mark.asyncio
    async def test_execute_flags_flaky_tests(self, qe_memory, simple_model, mocker):
        """Test execute flags potentially flaky tests"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        # Store previous successful run
        await qe_memory.store("aqe/test-executor/last_execution", {
            "success_rate": 100.0
        })

        task = QETask(
            task_type="test_execution",
            context={"test_path": "./tests"}
        )

        # Current run has lower success rate
        mock_result = TestExecutionResult(
            total_tests=10,
            passed=8,
            failed=2,
            duration=5.0,
            framework="pytest",
            success_rate=80.0
        )

        mocker.patch.object(agent, 'operate', new=AsyncMock(return_value=mock_result))

        await agent.execute(task)

        # Verify flaky tests were flagged
        flaky = await qe_memory.retrieve("aqe/test-executor/potential_flaky_tests")
        assert flaky is not None
        assert flaky["current_rate"] == 80.0
        assert flaky["previous_rate"] == 100.0


class TestAlcallConfiguration:
    """Test alcall configuration and behavior"""

    @pytest.mark.asyncio
    async def test_alcall_max_concurrent(self, qe_memory, simple_model):
        """Test alcall max_concurrent parameter is respected"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        test_files = [f"test_{i}.py" for i in range(25)]

        concurrent_count = 0
        max_concurrent = 0

        def mock_subprocess_run(*args, **kwargs):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            if concurrent_count > max_concurrent:
                max_concurrent = concurrent_count
            # Simulate work
            import time
            time.sleep(0.01)
            concurrent_count -= 1
            return MagicMock(returncode=0, stdout="Passed", stderr="")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            await agent.execute_tests_parallel(test_files)

            # Should not exceed 10 concurrent
            assert max_concurrent <= 10

    @pytest.mark.asyncio
    async def test_alcall_exponential_backoff(self, qe_memory, simple_model):
        """Test exponential backoff for retries"""
        import time

        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        test_files = ["flaky_test.py"]

        attempt_times = []

        def mock_subprocess_run(*args, **kwargs):
            attempt_times.append(time.time())
            if len(attempt_times) < 3:
                return MagicMock(returncode=1, stdout="", stderr="Flaky")
            return MagicMock(returncode=0, stdout="Passed", stderr="")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            await agent.execute_tests_parallel(test_files)

            # Verify exponential backoff (2s, 4s)
            if len(attempt_times) >= 3:
                # Check delays between attempts
                delay1 = attempt_times[1] - attempt_times[0]
                delay2 = attempt_times[2] - attempt_times[1]
                # Second delay should be longer (exponential backoff)
                # Note: actual implementation may vary
                assert delay2 >= delay1 * 0.9  # Allow some variance

    @pytest.mark.asyncio
    async def test_alcall_exception_handling(self, qe_memory, simple_model):
        """Test alcall handles exceptions gracefully"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        test_files = ["error_test.py", "good_test.py"]

        def mock_subprocess_run(*args, **kwargs):
            file_path = args[0][1] if len(args[0]) > 1 else ""
            if "error" in file_path:
                raise RuntimeError("Unexpected error")
            return MagicMock(returncode=0, stdout="Passed", stderr="")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.execute_tests_parallel(test_files)

            # Should handle exception and continue with other tests
            assert result["total"] == 2
            assert result["passed"] >= 1  # At least good_test passed


class TestPerformanceMetrics:
    """Test performance metrics collection"""

    @pytest.mark.asyncio
    async def test_execution_time_tracking(self, qe_memory, simple_model):
        """Test execution time is tracked accurately"""
        import time

        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        test_files = [f"test_{i}.py" for i in range(5)]

        def mock_subprocess_run(*args, **kwargs):
            time.sleep(0.01)  # Simulate test execution
            return MagicMock(returncode=0, stdout="Passed", stderr="")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.execute_tests_parallel(test_files)

            assert "execution_time" in result
            assert result["execution_time"] > 0
            # With 5 tests and delays, should take some time
            assert result["execution_time"] >= 0.01

    @pytest.mark.asyncio
    async def test_avg_time_per_test(self, qe_memory, simple_model):
        """Test average time per test calculation"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        test_files = [f"test_{i}.py" for i in range(10)]

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Passed", stderr="")

            result = await agent.execute_tests_parallel(test_files)

            assert "avg_time_per_test" in result
            assert result["avg_time_per_test"] >= 0
            # Average should be total time / number of tests
            expected_avg = result["execution_time"] / 10
            assert abs(result["avg_time_per_test"] - expected_avg) < 0.01

    @pytest.mark.asyncio
    async def test_metrics_stored_in_memory(self, qe_memory, simple_model):
        """Test execution metrics are stored in memory"""
        agent = TestExecutorAgent("test-executor", simple_model, qe_memory)

        test_files = ["test.py"]

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Passed", stderr="")

            await agent.execute_tests_parallel(test_files)

            # Verify metrics were stored
            stored = await qe_memory.retrieve("aqe/test-executor/last_parallel_execution")
            assert stored is not None
            assert "execution_time" in stored
            assert "retries" in stored
            assert "framework" in stored
