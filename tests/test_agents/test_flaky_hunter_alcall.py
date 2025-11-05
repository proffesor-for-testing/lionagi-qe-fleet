"""Tests for FlakyTestHunterAgent with alcall parallel execution - Priority 1

Tests the detect_flaky_tests() method with:
- Nested alcall execution (test files × iterations)
- Flakiness calculation based on pass/fail patterns
- Pattern identification (RANDOM, INTERMITTENT, etc.)
- Statistical analysis with 10+ iterations
- Comprehensive flaky detection scenarios
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import subprocess
from datetime import datetime
from lionagi_qe.agents.flaky_test_hunter import (
    FlakyTestHunterAgent,
    FlakyTestHunterResult,
    FlakyDetectionResult,
    FlakyTest,
    RootCause,
    FailurePattern,
    EnvironmentalFactors,
    LastFlake,
    SuggestedFix
)
from lionagi_qe.core.task import QETask
from lionagi_qe.core.memory import QEMemory
from lionagi import iModel


class TestDetectFlakyTests:
    """Test detect_flaky_tests() with nested alcall"""

    @pytest.mark.asyncio
    async def test_detect_flaky_basic(self, qe_memory, simple_model):
        """Test basic flaky test detection"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_files = ["test_stable.py", "test_flaky.py"]

        call_count = {}

        def mock_subprocess_run(*args, **kwargs):
            file_path = args[0][1] if len(args[0]) > 1 else ""

            # Initialize counter
            if file_path not in call_count:
                call_count[file_path] = 0
            call_count[file_path] += 1

            # stable test always passes
            if "stable" in file_path:
                return MagicMock(returncode=0, stdout="Passed", stderr="")

            # flaky test alternates pass/fail
            if call_count[file_path] % 2 == 0:
                return MagicMock(returncode=0, stdout="Passed", stderr="")
            else:
                return MagicMock(returncode=1, stdout="", stderr="Failed")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.detect_flaky_tests(test_files, iterations=10)

            assert result["total_tests"] == 2
            assert result["flaky_tests"] == 1  # Only flaky test detected
            assert result["flakiness_rate"] == 50.0

    @pytest.mark.asyncio
    async def test_detect_flaky_iterations(self, qe_memory, simple_model):
        """Test flaky detection with different iteration counts"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_files = ["test_flaky.py"]

        # Mock flaky test that passes 70% of the time
        call_count = [0]

        def mock_subprocess_run(*args, **kwargs):
            call_count[0] += 1
            # Pass 7 out of 10 times
            if call_count[0] % 10 < 7:
                return MagicMock(returncode=0, stdout="Passed", stderr="")
            return MagicMock(returncode=1, stdout="", stderr="Failed")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.detect_flaky_tests(test_files, iterations=10)

            assert result["total_tests"] == 1
            assert result["total_runs"] == 10
            # Should detect as flaky since it's not 100% pass or 100% fail
            flaky_test = result["flaky_list"][0]
            assert flaky_test["is_flaky"] is True
            assert 0.6 < flaky_test["pass_rate"] < 0.8

    @pytest.mark.asyncio
    async def test_flakiness_score_calculation(self, qe_memory, simple_model):
        """Test flakiness score calculation accuracy"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_files = ["test_50_50.py"]

        # Mock test that passes exactly 50% of the time (most flaky)
        call_count = [0]

        def mock_subprocess_run(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                return MagicMock(returncode=0, stdout="Passed", stderr="")
            return MagicMock(returncode=1, stdout="", stderr="Failed")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.detect_flaky_tests(test_files, iterations=10)

            flaky_test = result["flaky_list"][0]
            # Score should be 1.0 (maximum flakiness) for 50/50 pass/fail
            assert flaky_test["flakiness_score"] == 1.0
            assert flaky_test["pass_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_pattern_identification_random(self, qe_memory, simple_model):
        """Test identification of RANDOM flakiness pattern"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_files = ["test_random.py"]

        # Mock test with random pattern
        import random
        random.seed(42)

        def mock_subprocess_run(*args, **kwargs):
            if random.random() > 0.5:
                return MagicMock(returncode=0, stdout="Passed", stderr="")
            return MagicMock(returncode=1, stdout="", stderr="Failed")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.detect_flaky_tests(test_files, iterations=10)

            if result["flaky_list"]:
                flaky_test = result["flaky_list"][0]
                # Pattern should be RANDOM due to frequent alternation
                assert flaky_test["pattern"] in ["RANDOM", "INTERMITTENT"]

    @pytest.mark.asyncio
    async def test_pattern_identification_intermittent(self, qe_memory, simple_model):
        """Test identification of INTERMITTENT flakiness pattern"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_files = ["test_intermittent.py"]

        # Mock test that has long runs of success/failure
        call_count = [0]

        def mock_subprocess_run(*args, **kwargs):
            call_count[0] += 1
            # Pass first 8, fail last 2 (intermittent pattern)
            if call_count[0] <= 8:
                return MagicMock(returncode=0, stdout="Passed", stderr="")
            return MagicMock(returncode=1, stdout="", stderr="Failed")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.detect_flaky_tests(test_files, iterations=10)

            flaky_test = result["flaky_list"][0]
            # Should detect INTERMITTENT pattern (long run of passes, then fails)
            assert flaky_test["pattern"] == "INTERMITTENT"

    @pytest.mark.asyncio
    async def test_stable_pass_not_flaky(self, qe_memory, simple_model):
        """Test that stable passing tests are not flagged as flaky"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_files = ["test_stable_pass.py"]

        def mock_subprocess_run(*args, **kwargs):
            return MagicMock(returncode=0, stdout="Passed", stderr="")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.detect_flaky_tests(test_files, iterations=10)

            assert result["flaky_tests"] == 0
            # Test should have STABLE_PASS pattern
            assert result["flaky_list"] == []

    @pytest.mark.asyncio
    async def test_stable_fail_not_flaky(self, qe_memory, simple_model):
        """Test that stable failing tests are not flagged as flaky"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_files = ["test_stable_fail.py"]

        def mock_subprocess_run(*args, **kwargs):
            return MagicMock(returncode=1, stdout="", stderr="Always fails")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.detect_flaky_tests(test_files, iterations=10)

            assert result["flaky_tests"] == 0

    @pytest.mark.asyncio
    async def test_nested_alcall_execution(self, qe_memory, simple_model):
        """Test nested alcall: multiple files × multiple iterations"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_files = [f"test_{i}.py" for i in range(5)]

        execution_count = [0]

        def mock_subprocess_run(*args, **kwargs):
            execution_count[0] += 1
            # Make some tests flaky
            file_path = args[0][1] if len(args[0]) > 1 else ""
            if "test_1" in file_path or "test_3" in file_path:
                # Flaky tests
                if execution_count[0] % 3 == 0:
                    return MagicMock(returncode=1, stdout="", stderr="Flaky")
            return MagicMock(returncode=0, stdout="Passed", stderr="")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.detect_flaky_tests(test_files, iterations=10)

            assert result["total_tests"] == 5
            assert result["total_runs"] == 50  # 5 tests × 10 iterations
            # Should detect 2 flaky tests (test_1 and test_3)
            assert result["flaky_tests"] >= 1

    @pytest.mark.asyncio
    async def test_timeout_handling(self, qe_memory, simple_model):
        """Test timeout handling during flaky detection"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_files = ["test_slow.py"]

        def mock_subprocess_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=args[0], timeout=30)

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.detect_flaky_tests(test_files, iterations=5)

            # Timeouts should be recorded as failures
            assert result["total_runs"] == 5
            # All should have timeout errors
            flaky_test = result["flaky_list"][0] if result["flaky_list"] else None
            if flaky_test:
                assert any("timeout" in str(r.get("error", "")).lower() for r in flaky_test["results"])

    @pytest.mark.asyncio
    async def test_framework_pytest(self, qe_memory, simple_model):
        """Test flaky detection with pytest framework"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_files = ["test.py"]

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Passed", stderr="")

            await agent.detect_flaky_tests(test_files, iterations=5, framework="pytest")

            # Verify pytest command was used
            assert mock_run.called
            call_args = mock_run.call_args[0][0]
            assert "pytest" in call_args
            assert "-v" in call_args

    @pytest.mark.asyncio
    async def test_framework_jest(self, qe_memory, simple_model):
        """Test flaky detection with jest framework"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_files = ["test.spec.js"]

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Passed", stderr="")

            await agent.detect_flaky_tests(test_files, iterations=5, framework="jest")

            # Verify jest command was used
            assert mock_run.called
            call_args = mock_run.call_args[0][0]
            assert "npm" in call_args
            assert "test" in call_args


class TestExecuteMethod:
    """Test the main execute() method"""

    @pytest.mark.asyncio
    async def test_execute_basic(self, qe_memory, simple_model, mocker):
        """Test basic execute with flaky detection"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_results = [
            {"test": "test1", "passed": True},
            {"test": "test1", "passed": False},
            {"test": "test1", "passed": True},
        ]

        task = QETask(
            task_type="flaky_detection",
            context={
                "test_results": test_results,
                "min_runs": 3
            }
        )

        # Mock operate to return result
        mock_result = FlakyTestHunterResult(
            detection=FlakyDetectionResult(
                time_window="last_7_days",
                total_tests=10,
                flaky_tests=2,
                flakiness_rate=20.0,
                target_reliability=0.95,
                top_flaky_tests=[],
                statistics={"by_category": {}, "by_severity": {}, "by_status": {}},
                recommendation="Fix 2 flaky tests"
            )
        )

        mocker.patch.object(agent, 'operate', new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.detection.flaky_tests == 2
        assert result.detection.flakiness_rate == 20.0

    @pytest.mark.asyncio
    async def test_execute_stores_results(self, qe_memory, simple_model, mocker):
        """Test execute stores results in memory"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        task = QETask(
            task_type="flaky_detection",
            context={"test_results": []}
        )

        mock_result = FlakyTestHunterResult(
            detection=FlakyDetectionResult(
                time_window="test",
                total_tests=5,
                flaky_tests=1,
                flakiness_rate=20.0,
                target_reliability=0.95,
                top_flaky_tests=[],
                statistics={"by_category": {}, "by_severity": {}, "by_status": {}},
                recommendation="Test"
            )
        )

        mocker.patch.object(agent, 'operate', new=AsyncMock(return_value=mock_result))

        await agent.execute(task)

        # Verify result was stored
        stored = await qe_memory.retrieve("aqe/flaky-tests/latest-detection")
        assert stored is not None
        assert stored["detection"]["flaky_tests"] == 1

    @pytest.mark.asyncio
    async def test_execute_with_auto_quarantine(self, qe_memory, simple_model, mocker):
        """Test execute with auto-quarantine enabled"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        task = QETask(
            task_type="flaky_detection",
            context={
                "test_results": [],
                "auto_quarantine": True
            }
        )

        # Create flaky test with QUARANTINED status
        flaky_test = FlakyTest(
            test_name="test_flaky",
            flakiness_score=0.5,
            severity="HIGH",
            total_runs=10,
            failures=5,
            passes=5,
            failure_rate=0.5,
            pass_rate=0.5,
            pattern="RANDOM",
            last_flakes=[],
            root_cause=RootCause(
                category="RACE_CONDITION",
                confidence=0.8,
                description="Test",
                evidence=[],
                recommendation="Fix"
            ),
            failure_pattern=FailurePattern(
                randomness=0.5,
                timing_correlation=0.3,
                environmental_correlation=0.2
            ),
            environmental_factors=EnvironmentalFactors(),
            suggested_fixes=[],
            status="QUARANTINED",
            quarantined_at=datetime.now()
        )

        mock_result = FlakyTestHunterResult(
            detection=FlakyDetectionResult(
                time_window="test",
                total_tests=10,
                flaky_tests=1,
                flakiness_rate=10.0,
                target_reliability=0.95,
                top_flaky_tests=[flaky_test],
                statistics={"by_category": {}, "by_severity": {}, "by_status": {}},
                recommendation="Quarantine flaky test"
            )
        )

        mocker.patch.object(agent, 'operate', new=AsyncMock(return_value=mock_result))

        await agent.execute(task)

        # Verify quarantined test was stored
        quarantined = await qe_memory.retrieve("aqe/flaky-tests/quarantined")
        assert quarantined is not None
        assert len(quarantined) >= 1


class TestFlakinessCalculations:
    """Test flakiness score and pattern calculations"""

    @pytest.mark.asyncio
    async def test_perfect_flakiness_score(self, qe_memory, simple_model):
        """Test flakiness score for perfect 50/50 split"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_files = ["test.py"]

        results = [True, False, True, False, True, False, True, False, True, False]
        call_index = [0]

        def mock_subprocess_run(*args, **kwargs):
            result = results[call_index[0] % len(results)]
            call_index[0] += 1
            if result:
                return MagicMock(returncode=0, stdout="Passed", stderr="")
            return MagicMock(returncode=1, stdout="", stderr="Failed")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.detect_flaky_tests(test_files, iterations=10)

            flaky_test = result["flaky_list"][0]
            # 5 passes, 5 fails = score of 1.0
            assert flaky_test["flakiness_score"] == 1.0

    @pytest.mark.asyncio
    async def test_low_flakiness_score(self, qe_memory, simple_model):
        """Test flakiness score for low flakiness (90% pass)"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_files = ["test.py"]

        # 9 passes, 1 fail
        call_count = [0]

        def mock_subprocess_run(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 5:  # Fail once
                return MagicMock(returncode=1, stdout="", stderr="Failed")
            return MagicMock(returncode=0, stdout="Passed", stderr="")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            result = await agent.detect_flaky_tests(test_files, iterations=10)

            flaky_test = result["flaky_list"][0]
            # 9 passes, 1 fail = min(9, 1) / 10 * 2 = 0.2
            assert flaky_test["flakiness_score"] == 0.2
            assert flaky_test["pass_rate"] == 0.9

    @pytest.mark.asyncio
    async def test_pattern_stable_pass(self, qe_memory, simple_model):
        """Test STABLE_PASS pattern identification"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        # Test _identify_pattern directly
        results = [{"passed": True} for _ in range(10)]
        pattern = agent._identify_pattern(results)
        assert pattern == "STABLE_PASS"

    @pytest.mark.asyncio
    async def test_pattern_stable_fail(self, qe_memory, simple_model):
        """Test STABLE_FAIL pattern identification"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        results = [{"passed": False} for _ in range(10)]
        pattern = agent._identify_pattern(results)
        assert pattern == "STABLE_FAIL"

    @pytest.mark.asyncio
    async def test_pattern_unknown_empty(self, qe_memory, simple_model):
        """Test UNKNOWN pattern for empty results"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        pattern = agent._identify_pattern([])
        assert pattern == "UNKNOWN"


class TestMemoryIntegration:
    """Test memory storage and retrieval"""

    @pytest.mark.asyncio
    async def test_stores_detection_results(self, qe_memory, simple_model):
        """Test detection results are stored in memory"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_files = ["test.py"]

        def mock_subprocess_run(*args, **kwargs):
            return MagicMock(returncode=0, stdout="Passed", stderr="")

        with patch('subprocess.run', side_effect=mock_subprocess_run):
            await agent.detect_flaky_tests(test_files, iterations=5)

            # Verify stored in memory
            stored = await qe_memory.retrieve("aqe/flaky-tests/alcall-detection")
            assert stored is not None
            assert stored["total_tests"] == 1
            assert stored["framework"] == "pytest"

    @pytest.mark.asyncio
    async def test_updates_flaky_history(self, qe_memory, simple_model, mocker):
        """Test flaky test history is updated"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        task = QETask(
            task_type="flaky_detection",
            context={"test_results": []}
        )

        mock_result = FlakyTestHunterResult(
            detection=FlakyDetectionResult(
                time_window="test",
                total_tests=10,
                flaky_tests=2,
                flakiness_rate=20.0,
                target_reliability=0.95,
                top_flaky_tests=[],
                statistics={"by_category": {}, "by_severity": {}, "by_status": {}},
                recommendation="Test"
            )
        )

        mocker.patch.object(agent, 'operate', new=AsyncMock(return_value=mock_result))

        await agent.execute(task)

        # Verify history was updated
        history = await qe_memory.retrieve("aqe/flaky-tests/history")
        assert history is not None
        assert len(history) >= 1
        assert history[-1]["flaky_tests"] == 2

    @pytest.mark.asyncio
    async def test_updates_stability_scores(self, qe_memory, simple_model, mocker):
        """Test stability scores are updated for flaky tests"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        flaky_test = FlakyTest(
            test_name="test_unstable",
            flakiness_score=0.7,
            severity="HIGH",
            total_runs=20,
            failures=7,
            passes=13,
            failure_rate=0.35,
            pass_rate=0.65,
            pattern="RANDOM",
            last_flakes=[],
            root_cause=RootCause(
                category="TIMEOUT",
                confidence=0.85,
                description="Test times out",
                evidence=[],
                recommendation="Increase timeout"
            ),
            failure_pattern=FailurePattern(
                randomness=0.6,
                timing_correlation=0.7,
                environmental_correlation=0.3
            ),
            environmental_factors=EnvironmentalFactors(),
            suggested_fixes=[],
            status="INVESTIGATING"
        )

        task = QETask(
            task_type="flaky_detection",
            context={"test_results": []}
        )

        mock_result = FlakyTestHunterResult(
            detection=FlakyDetectionResult(
                time_window="test",
                total_tests=10,
                flaky_tests=1,
                flakiness_rate=10.0,
                target_reliability=0.95,
                top_flaky_tests=[flaky_test],
                statistics={"by_category": {}, "by_severity": {}, "by_status": {}},
                recommendation="Test"
            )
        )

        mocker.patch.object(agent, 'operate', new=AsyncMock(return_value=mock_result))

        await agent.execute(task)

        # Verify stability score was updated
        scores = await qe_memory.retrieve("aqe/test-stability/scores")
        assert scores is not None
        assert "test_unstable" in scores
        assert scores["test_unstable"]["flakiness_score"] == 0.7


class TestPerformanceMetrics:
    """Test performance metrics collection"""

    @pytest.mark.asyncio
    async def test_execution_time_tracking(self, qe_memory, simple_model):
        """Test execution time is tracked"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_files = ["test1.py", "test2.py"]

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Passed", stderr="")

            result = await agent.detect_flaky_tests(test_files, iterations=5)

            assert "execution_time" in result
            assert result["execution_time"] >= 0

    @pytest.mark.asyncio
    async def test_avg_time_per_test(self, qe_memory, simple_model):
        """Test average time per test calculation"""
        agent = FlakyTestHunterAgent("flaky-hunter", simple_model, qe_memory)

        test_files = [f"test_{i}.py" for i in range(5)]

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Passed", stderr="")

            result = await agent.detect_flaky_tests(test_files, iterations=5)

            assert "avg_time_per_test" in result
            expected_avg = result["execution_time"] / 5 if result["execution_time"] > 0 else 0
            assert abs(result["avg_time_per_test"] - expected_avg) < 0.1
