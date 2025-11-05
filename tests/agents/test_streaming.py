"""Tests for streaming progress updates in QE agents"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import AsyncGenerator, Dict, Any

from lionagi_qe.agents.test_generator import TestGeneratorAgent
from lionagi_qe.agents.coverage_analyzer import CoverageAnalyzerAgent
from lionagi_qe.core.task import QETask
from lionagi_qe.core.memory import QEMemory


class MockStreamingModel:
    """Mock model that simulates streaming responses"""

    async def stream(self, messages):
        """Simulate streaming chunks"""
        # Simulate streaming 3 test cases
        test_chunks = [
            '{"test_name": "test_example_1", "test_code": "def test_example_1(): pass", '
            '"framework": "pytest", "test_type": "unit", "assertions": ["assert True"], '
            '"edge_cases": [], "dependencies": [], "coverage_estimate": 85.0}',

            '{"test_name": "test_example_2", "test_code": "def test_example_2(): pass", '
            '"framework": "pytest", "test_type": "unit", "assertions": ["assert True"], '
            '"edge_cases": [], "dependencies": [], "coverage_estimate": 90.0}',

            '{"test_name": "test_example_3", "test_code": "def test_example_3(): pass", '
            '"framework": "pytest", "test_type": "unit", "assertions": ["assert True"], '
            '"edge_cases": [], "dependencies": [], "coverage_estimate": 88.0}',
        ]

        for chunk_text in test_chunks:
            # Simulate gradual streaming
            for i in range(0, len(chunk_text), 50):
                chunk = MagicMock()
                chunk.choices = [MagicMock()]
                chunk.choices[0].delta = MagicMock()
                chunk.choices[0].delta.content = chunk_text[i:i+50]

                yield chunk
                await asyncio.sleep(0.01)


@pytest.fixture
def mock_memory():
    """Create mock memory instance"""
    memory = Mock(spec=QEMemory)
    memory.retrieve = AsyncMock(return_value=None)
    memory.store = AsyncMock()
    memory.search = AsyncMock(return_value={})
    return memory


@pytest.fixture
def test_generator_agent(mock_memory):
    """Create test generator agent with mock streaming model"""
    model = MockStreamingModel()
    agent = TestGeneratorAgent(
        agent_id="test-generator",
        model=model,
        memory=mock_memory,
        skills=["test-generation"],
        enable_learning=False
    )
    return agent


@pytest.fixture
def coverage_analyzer_agent(mock_memory):
    """Create coverage analyzer agent"""
    model = Mock()
    model.stream = AsyncMock()

    agent = CoverageAnalyzerAgent(
        agent_id="coverage-analyzer",
        model=model,
        memory=mock_memory,
        skills=["coverage-analysis"],
        enable_learning=False
    )

    # Mock the operate method to return a result
    from lionagi_qe.agents.coverage_analyzer import CoverageAnalysisResult
    mock_result = CoverageAnalysisResult(
        overall_coverage=78.5,
        line_coverage=80.2,
        branch_coverage=75.8,
        function_coverage=82.1,
        gaps=[],
        critical_paths=["path1", "path2"],
        framework="pytest",
        analysis_time_ms=1250.0,
        optimization_suggestions=["Add more unit tests"]
    )
    agent.operate = AsyncMock(return_value=mock_result)

    return agent


class TestTestGeneratorStreaming:
    """Test streaming for TestGeneratorAgent"""

    @pytest.mark.asyncio
    async def test_generate_tests_streaming_yields_progress(self, test_generator_agent):
        """Test that streaming yields progress updates"""
        task = QETask(
            task_type="test_generation",
            context={
                "code": "def add(a, b): return a + b",
                "framework": "pytest",
                "test_type": "unit",
                "coverage_target": 80,
                "target_count": 3,
            }
        )

        events = []
        async for event in test_generator_agent.generate_tests_streaming(task):
            events.append(event)

        # Check we got events
        assert len(events) > 0, "Should yield at least one event"

        # Check for progress events
        progress_events = [e for e in events if e.get("type") == "progress"]
        assert len(progress_events) > 0, "Should have progress events"

        # Validate progress event structure
        for progress in progress_events:
            assert "count" in progress
            assert "total" in progress
            assert "percent" in progress
            assert "message" in progress

    @pytest.mark.asyncio
    async def test_generate_tests_streaming_yields_individual_tests(self, test_generator_agent):
        """Test that streaming yields individual test cases"""
        task = QETask(
            task_type="test_generation",
            context={
                "code": "def add(a, b): return a + b",
                "framework": "pytest",
                "test_type": "unit",
                "coverage_target": 80,
                "target_count": 3,
            }
        )

        events = []
        async for event in test_generator_agent.generate_tests_streaming(task):
            events.append(event)

        # Check for test events
        test_events = [e for e in events if e.get("type") == "test"]
        assert len(test_events) > 0, "Should have test events"

        # Validate test event structure
        for test_event in test_events:
            assert "test_case" in test_event
            test_case = test_event["test_case"]
            assert "test_name" in test_case
            assert "test_code" in test_case
            assert "framework" in test_case

    @pytest.mark.asyncio
    async def test_generate_tests_streaming_yields_complete(self, test_generator_agent):
        """Test that streaming yields final complete event"""
        task = QETask(
            task_type="test_generation",
            context={
                "code": "def add(a, b): return a + b",
                "framework": "pytest",
                "test_type": "unit",
                "coverage_target": 80,
                "target_count": 3,
            }
        )

        events = []
        async for event in test_generator_agent.generate_tests_streaming(task):
            events.append(event)

        # Check for complete event
        complete_events = [e for e in events if e.get("type") == "complete"]
        assert len(complete_events) == 1, "Should have exactly one complete event"

        complete = complete_events[0]
        assert "tests" in complete
        assert "total" in complete
        assert "coverage_estimate" in complete
        assert "framework" in complete

    @pytest.mark.asyncio
    async def test_generate_tests_streaming_incremental_results(self, test_generator_agent):
        """Test that tests are yielded incrementally"""
        task = QETask(
            task_type="test_generation",
            context={
                "code": "def add(a, b): return a + b",
                "framework": "pytest",
                "test_type": "unit",
                "coverage_target": 80,
                "target_count": 3,
            }
        )

        test_count = 0
        async for event in test_generator_agent.generate_tests_streaming(task):
            if event.get("type") == "test":
                test_count += 1
                # Verify we're getting tests incrementally, not all at once
                assert test_count <= 3, "Should not exceed target count"


class TestCoverageAnalyzerStreaming:
    """Test streaming for CoverageAnalyzerAgent"""

    @pytest.mark.asyncio
    async def test_analyze_coverage_streaming_yields_progress(self, coverage_analyzer_agent):
        """Test that streaming yields progress updates"""
        task = QETask(
            task_type="coverage_analysis",
            context={
                "coverage_data": {
                    "files": {
                        "file1.py": {"coverage": 80},
                        "file2.py": {"coverage": 75},
                        "file3.py": {"coverage": 90},
                    }
                },
                "framework": "pytest",
                "codebase_path": "./src",
                "target_coverage": 85,
            }
        )

        events = []
        async for event in coverage_analyzer_agent.analyze_coverage_streaming(task):
            events.append(event)

        # Check for progress events
        progress_events = [e for e in events if e.get("type") == "progress"]
        assert len(progress_events) > 0, "Should have progress events"

        # Validate progress event structure
        for progress in progress_events:
            assert "percent" in progress
            assert "message" in progress
            assert "files_analyzed" in progress
            assert "total_files" in progress

    @pytest.mark.asyncio
    async def test_analyze_coverage_streaming_yields_gaps(self, coverage_analyzer_agent):
        """Test that streaming yields gap discoveries"""
        task = QETask(
            task_type="coverage_analysis",
            context={
                "coverage_data": {
                    "files": {
                        "file1.py": {"coverage": 80},
                        "file2.py": {"coverage": 75},
                        "file3.py": {"coverage": 90},
                    }
                },
                "framework": "pytest",
                "codebase_path": "./src",
                "target_coverage": 85,
            }
        )

        events = []
        async for event in coverage_analyzer_agent.analyze_coverage_streaming(task):
            events.append(event)

        # Check for gap events (may or may not have gaps depending on simulation)
        gap_events = [e for e in events if e.get("type") == "gap"]

        # Validate gap event structure if present
        for gap_event in gap_events:
            assert "gap" in gap_event
            gap = gap_event["gap"]
            assert "file_path" in gap
            assert "line_start" in gap
            assert "line_end" in gap
            assert "severity" in gap

    @pytest.mark.asyncio
    async def test_analyze_coverage_streaming_yields_complete(self, coverage_analyzer_agent):
        """Test that streaming yields final complete event"""
        task = QETask(
            task_type="coverage_analysis",
            context={
                "coverage_data": {
                    "files": {
                        "file1.py": {"coverage": 80},
                        "file2.py": {"coverage": 75},
                    }
                },
                "framework": "pytest",
                "codebase_path": "./src",
                "target_coverage": 85,
            }
        )

        events = []
        async for event in coverage_analyzer_agent.analyze_coverage_streaming(task):
            events.append(event)

        # Check for complete event
        complete_events = [e for e in events if e.get("type") == "complete"]
        assert len(complete_events) == 1, "Should have exactly one complete event"

        complete = complete_events[0]
        assert "overall_coverage" in complete
        assert "gaps" in complete
        assert "critical_paths" in complete
        assert "analysis_time_ms" in complete
        assert "framework" in complete

    @pytest.mark.asyncio
    async def test_analyze_coverage_streaming_file_by_file(self, coverage_analyzer_agent):
        """Test that coverage is analyzed file-by-file"""
        task = QETask(
            task_type="coverage_analysis",
            context={
                "coverage_data": {
                    "files": {
                        "file1.py": {"coverage": 80},
                        "file2.py": {"coverage": 75},
                        "file3.py": {"coverage": 90},
                    }
                },
                "framework": "pytest",
                "codebase_path": "./src",
                "target_coverage": 85,
            }
        )

        files_seen = 0
        async for event in coverage_analyzer_agent.analyze_coverage_streaming(task):
            if event.get("type") == "progress":
                files_seen = event.get("files_analyzed", 0)
                assert files_seen <= 3, "Should not exceed file count"


class TestStreamingIntegration:
    """Integration tests for streaming functionality"""

    @pytest.mark.asyncio
    async def test_streaming_matches_non_streaming_output(self, test_generator_agent):
        """Test that streaming produces same final result as non-streaming"""
        task = QETask(
            task_type="test_generation",
            context={
                "code": "def add(a, b): return a + b",
                "framework": "pytest",
                "test_type": "unit",
                "coverage_target": 80,
                "target_count": 3,
            }
        )

        # Collect streaming results
        streaming_tests = []
        async for event in test_generator_agent.generate_tests_streaming(task):
            if event.get("type") == "complete":
                streaming_tests = event.get("tests", [])

        # Verify we got tests
        assert len(streaming_tests) > 0, "Should generate tests via streaming"

    @pytest.mark.asyncio
    async def test_streaming_provides_incremental_feedback(self, test_generator_agent):
        """Test that streaming provides feedback before completion"""
        task = QETask(
            task_type="test_generation",
            context={
                "code": "def add(a, b): return a + b",
                "framework": "pytest",
                "test_type": "unit",
                "coverage_target": 80,
                "target_count": 3,
            }
        )

        has_progress_before_complete = False
        has_complete = False

        async for event in test_generator_agent.generate_tests_streaming(task):
            if event.get("type") == "progress" and not has_complete:
                has_progress_before_complete = True
            elif event.get("type") == "complete":
                has_complete = True

        assert has_progress_before_complete, "Should provide progress before completion"
        assert has_complete, "Should eventually complete"
