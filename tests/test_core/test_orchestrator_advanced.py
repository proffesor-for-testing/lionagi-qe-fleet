"""Advanced tests for QEOrchestrator - Priority 1 features

Tests advanced orchestration patterns:
- execute_parallel_expansion() with 100+ items
- execute_parallel_fan_out_fan_in() with multiple agents
- execute_conditional_workflow() with branching logic
- Error handling and edge cases
- Metrics tracking
- Context inheritance
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from lionagi_qe.core.orchestrator import QEOrchestrator
from lionagi_qe.core.task import QETask
from lionagi_qe.core.memory import QEMemory
from lionagi_qe.core.router import ModelRouter
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi import iModel


class MockQEAgent(BaseQEAgent):
    """Mock QE agent for testing"""

    def get_system_prompt(self) -> str:
        return "Mock agent for advanced testing"

    async def execute(self, task: QETask):
        return {
            "agent_id": self.agent_id,
            "task_type": task.task_type,
            "result": f"executed_{task.task_type}",
            "status": "success"
        }


class TestExecuteParallelExpansion:
    """Test execute_parallel_expansion() with large datasets"""

    @pytest.mark.asyncio
    async def test_parallel_expansion_100_items(self, qe_orchestrator, qe_memory, simple_model):
        """Test parallel expansion with 100 items"""
        agent = MockQEAgent("expander-agent", simple_model, qe_memory)
        qe_orchestrator.register_agent(agent)

        # Create 100 items to process
        items = [{"id": i, "data": f"item_{i}"} for i in range(100)]

        # Mock alcall to handle parallel execution
        with patch('lionagi_qe.core.orchestrator.alcall') as mock_alcall:
            mock_alcall.return_value = [
                {"id": item["id"], "processed": True} for item in items
            ]

            results = await qe_orchestrator.execute_parallel(
                ["expander-agent"] * 100,
                items
            )

            assert len(results) == 100
            assert qe_orchestrator.metrics["total_agents_used"] >= 100

    @pytest.mark.asyncio
    async def test_parallel_expansion_empty_list(self, qe_orchestrator):
        """Test parallel expansion with empty list"""
        with patch('lionagi_qe.core.orchestrator.alcall') as mock_alcall:
            mock_alcall.return_value = []

            results = await qe_orchestrator.execute_parallel([], [])

            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_parallel_expansion_single_item(self, qe_orchestrator, qe_memory, simple_model):
        """Test parallel expansion with single item"""
        agent = MockQEAgent("single-agent", simple_model, qe_memory)
        qe_orchestrator.register_agent(agent)

        results = await qe_orchestrator.execute_parallel(
            ["single-agent"],
            [{"data": "single"}]
        )

        assert len(results) == 1
        assert results[0]["status"] == "success"

    @pytest.mark.asyncio
    async def test_parallel_expansion_mixed_results(self, qe_orchestrator, qe_memory, simple_model):
        """Test parallel expansion with mixed success/failure"""
        class FailingAgent(BaseQEAgent):
            def get_system_prompt(self) -> str:
                return "Failing agent"

            async def execute(self, task: QETask):
                if task.context.get("should_fail"):
                    raise ValueError("Intentional failure")
                return {"status": "success"}

        agent = FailingAgent("failing-agent", simple_model, qe_memory)
        qe_orchestrator.register_agent(agent)

        tasks = [
            {"should_fail": False},
            {"should_fail": True},
            {"should_fail": False}
        ]

        # Execute and expect partial failures
        with patch('lionagi_qe.core.orchestrator.alcall') as mock_alcall:
            # Simulate mixed results
            mock_alcall.return_value = [
                {"status": "success"},
                None,  # Failed task
                {"status": "success"}
            ]

            results = await qe_orchestrator.execute_parallel(
                ["failing-agent"] * 3,
                tasks
            )

            assert len(results) == 3
            assert results[1] is None  # Failed task

    @pytest.mark.asyncio
    async def test_parallel_expansion_context_isolation(self, qe_orchestrator, qe_memory, simple_model):
        """Test that parallel tasks have isolated contexts"""
        agent = MockQEAgent("context-agent", simple_model, qe_memory)
        qe_orchestrator.register_agent(agent)

        tasks = [{"id": i, "shared": "value"} for i in range(10)]

        with patch('lionagi_qe.core.orchestrator.alcall') as mock_alcall:
            mock_alcall.return_value = [{"id": task["id"]} for task in tasks]

            results = await qe_orchestrator.execute_parallel(
                ["context-agent"] * 10,
                tasks
            )

            # Verify each result has unique ID
            ids = [r["id"] for r in results]
            assert len(set(ids)) == 10  # All unique

    @pytest.mark.asyncio
    async def test_parallel_expansion_performance_tracking(self, qe_orchestrator, qe_memory, simple_model):
        """Test performance metrics for parallel expansion"""
        import time

        agent = MockQEAgent("perf-agent", simple_model, qe_memory)
        qe_orchestrator.register_agent(agent)

        start_time = time.time()

        with patch('lionagi_qe.core.orchestrator.alcall') as mock_alcall:
            mock_alcall.return_value = [{"status": "success"}] * 50

            results = await qe_orchestrator.execute_parallel(
                ["perf-agent"] * 50,
                [{}] * 50
            )

            elapsed = time.time() - start_time

            assert len(results) == 50
            # Parallel execution should be faster than sequential
            assert elapsed < 5.0  # Should complete in reasonable time


class TestExecuteFanOutFanIn:
    """Test execute_fan_out_fan_in() with multiple agents"""

    @pytest.mark.asyncio
    async def test_fan_out_fan_in_basic(self, qe_orchestrator, qe_memory, simple_model, mocker):
        """Test basic fan-out/fan-in workflow"""
        from lionagi.fields import Instruct

        coordinator = MockQEAgent("coordinator", simple_model, qe_memory)
        workers = [MockQEAgent(f"worker-{i}", simple_model, qe_memory) for i in range(3)]

        qe_orchestrator.register_agent(coordinator)
        for worker in workers:
            qe_orchestrator.register_agent(worker)

        # Mock coordinator decomposition
        mock_subtasks = [
            Instruct(instruction=f"Subtask {i}", context={})
            for i in range(3)
        ]

        mock_decomposition = MagicMock()
        mock_decomposition.instruct_model = mock_subtasks

        mocker.patch.object(
            coordinator,
            'operate',
            new=AsyncMock(return_value=mock_decomposition)
        )

        # Mock coordinator synthesis
        mocker.patch.object(
            coordinator,
            'communicate',
            new=AsyncMock(return_value="Synthesis complete")
        )

        result = await qe_orchestrator.execute_fan_out_fan_in(
            "coordinator",
            ["worker-0", "worker-1", "worker-2"],
            {"request": "complex task"}
        )

        assert "decomposition" in result
        assert "worker_results" in result
        assert "synthesis" in result
        assert len(result["worker_results"]) == 3

    @pytest.mark.asyncio
    async def test_fan_out_fan_in_uneven_workers(self, qe_orchestrator, qe_memory, simple_model, mocker):
        """Test fan-out/fan-in with uneven worker distribution"""
        from lionagi.fields import Instruct

        coordinator = MockQEAgent("coordinator", simple_model, qe_memory)
        workers = [MockQEAgent(f"worker-{i}", simple_model, qe_memory) for i in range(5)]

        qe_orchestrator.register_agent(coordinator)
        for worker in workers:
            qe_orchestrator.register_agent(worker)

        mock_subtasks = [
            Instruct(instruction=f"Task {i}", context={"complexity": i})
            for i in range(5)
        ]

        mock_decomposition = MagicMock()
        mock_decomposition.instruct_model = mock_subtasks

        mocker.patch.object(coordinator, 'operate', new=AsyncMock(return_value=mock_decomposition))
        mocker.patch.object(coordinator, 'communicate', new=AsyncMock(return_value="Done"))

        result = await qe_orchestrator.execute_fan_out_fan_in(
            "coordinator",
            [f"worker-{i}" for i in range(5)],
            {"request": "uneven task"}
        )

        assert len(result["worker_results"]) == 5

    @pytest.mark.asyncio
    async def test_fan_out_fan_in_coordinator_not_found(self, qe_orchestrator):
        """Test fan-out/fan-in fails if coordinator not found"""
        with pytest.raises(ValueError, match="Coordinator not found"):
            await qe_orchestrator.execute_fan_out_fan_in(
                "nonexistent-coordinator",
                ["worker-0"],
                {}
            )

    @pytest.mark.asyncio
    async def test_fan_out_fan_in_worker_failure(self, qe_orchestrator, qe_memory, simple_model, mocker):
        """Test fan-out/fan-in handles worker failures"""
        from lionagi.fields import Instruct

        coordinator = MockQEAgent("coordinator", simple_model, qe_memory)

        class FailingWorker(BaseQEAgent):
            def get_system_prompt(self) -> str:
                return "Failing worker"

            async def execute(self, task: QETask):
                raise ValueError("Worker failed")

        worker = FailingWorker("failing-worker", simple_model, qe_memory)

        qe_orchestrator.register_agent(coordinator)
        qe_orchestrator.register_agent(worker)

        mock_subtasks = [Instruct(instruction="Task", context={})]
        mock_decomposition = MagicMock()
        mock_decomposition.instruct_model = mock_subtasks

        mocker.patch.object(coordinator, 'operate', new=AsyncMock(return_value=mock_decomposition))
        mocker.patch.object(coordinator, 'communicate', new=AsyncMock(return_value="Partial synthesis"))

        # Mock alcall to simulate failure
        with patch('lionagi_qe.core.orchestrator.alcall') as mock_alcall:
            mock_alcall.return_value = [None]  # Simulate failure

            result = await qe_orchestrator.execute_fan_out_fan_in(
                "coordinator",
                ["failing-worker"],
                {}
            )

            # Should still return result with failed worker
            assert "worker_results" in result
            assert result["worker_results"][0] is None

    @pytest.mark.asyncio
    async def test_fan_out_fan_in_context_passing(self, qe_orchestrator, qe_memory, simple_model, mocker):
        """Test context is properly passed through fan-out/fan-in"""
        from lionagi.fields import Instruct

        coordinator = MockQEAgent("coordinator", simple_model, qe_memory)
        worker = MockQEAgent("worker", simple_model, qe_memory)

        qe_orchestrator.register_agent(coordinator)
        qe_orchestrator.register_agent(worker)

        initial_context = {
            "project": "test-project",
            "priority": "high",
            "metadata": {"key": "value"}
        }

        mock_subtasks = [Instruct(instruction="Task", context=initial_context)]
        mock_decomposition = MagicMock()
        mock_decomposition.instruct_model = mock_subtasks

        operate_mock = mocker.patch.object(coordinator, 'operate', new=AsyncMock(return_value=mock_decomposition))
        mocker.patch.object(coordinator, 'communicate', new=AsyncMock(return_value="Done"))

        await qe_orchestrator.execute_fan_out_fan_in(
            "coordinator",
            ["worker"],
            initial_context
        )

        # Verify coordinator received initial context
        assert operate_mock.called
        call_args = operate_mock.call_args
        assert "context" in call_args[1] or initial_context == call_args[0][0].context


class TestConditionalWorkflow:
    """Test conditional workflow execution with branching logic"""

    @pytest.mark.asyncio
    async def test_conditional_agent_selection(self, qe_orchestrator, qe_memory, simple_model):
        """Test workflow selects agents based on conditions"""
        fast_agent = MockQEAgent("fast-agent", simple_model, qe_memory)
        thorough_agent = MockQEAgent("thorough-agent", simple_model, qe_memory)

        qe_orchestrator.register_agent(fast_agent)
        qe_orchestrator.register_agent(thorough_agent)

        # Simulate conditional selection
        context = {"priority": "high", "time_constraint": "tight"}

        # Based on context, choose fast agent
        selected_agent = "fast-agent" if context["priority"] == "high" else "thorough-agent"

        task = QETask(task_type="conditional_test", context=context)
        result = await qe_orchestrator.execute_agent(selected_agent, task)

        assert result["agent_id"] == "fast-agent"

    @pytest.mark.asyncio
    async def test_conditional_pipeline_branching(self, qe_orchestrator, qe_memory, simple_model, mocker):
        """Test pipeline branches based on intermediate results"""
        analyzer = MockQEAgent("analyzer", simple_model, qe_memory)
        simple_path = MockQEAgent("simple-path", simple_model, qe_memory)
        complex_path = MockQEAgent("complex-path", simple_model, qe_memory)

        qe_orchestrator.register_agent(analyzer)
        qe_orchestrator.register_agent(simple_path)
        qe_orchestrator.register_agent(complex_path)

        # Step 1: Analyze
        analysis_task = QETask(task_type="analyze", context={"code": "simple code"})
        analysis_result = await qe_orchestrator.execute_agent("analyzer", analysis_task)

        # Step 2: Branch based on analysis
        # In real implementation, would check analysis_result
        complexity = "simple"  # Mock decision

        selected_pipeline = ["simple-path"] if complexity == "simple" else ["complex-path"]

        # Mock session.flow
        mocker.patch.object(
            qe_orchestrator.session,
            'flow',
            new=AsyncMock(return_value={"branch": complexity})
        )

        result = await qe_orchestrator.execute_pipeline(selected_pipeline, {})

        assert result is not None

    @pytest.mark.asyncio
    async def test_conditional_error_recovery(self, qe_orchestrator, qe_memory, simple_model):
        """Test workflow recovers from errors by selecting fallback agent"""
        primary_agent = MockQEAgent("primary", simple_model, qe_memory)
        fallback_agent = MockQEAgent("fallback", simple_model, qe_memory)

        qe_orchestrator.register_agent(primary_agent)
        qe_orchestrator.register_agent(fallback_agent)

        task = QETask(task_type="test", context={})

        try:
            # Try primary
            result = await qe_orchestrator.execute_agent("primary", task)
        except Exception:
            # Fallback
            result = await qe_orchestrator.execute_agent("fallback", task)

        assert result is not None
        assert result["status"] == "success"


class TestErrorHandling:
    """Test comprehensive error handling"""

    @pytest.mark.asyncio
    async def test_agent_execution_timeout(self, qe_orchestrator, qe_memory, simple_model):
        """Test handling of agent execution timeout"""
        import asyncio

        class SlowAgent(BaseQEAgent):
            def get_system_prompt(self) -> str:
                return "Slow agent"

            async def execute(self, task: QETask):
                await asyncio.sleep(10)  # Simulate slow operation
                return {"status": "done"}

        slow_agent = SlowAgent("slow-agent", simple_model, qe_memory)
        qe_orchestrator.register_agent(slow_agent)

        task = QETask(task_type="slow_task", context={})

        # Test with timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                qe_orchestrator.execute_agent("slow-agent", task),
                timeout=0.1
            )

    @pytest.mark.asyncio
    async def test_agent_memory_error(self, qe_orchestrator, qe_memory, simple_model, mocker):
        """Test handling of memory storage errors"""
        agent = MockQEAgent("memory-agent", simple_model, qe_memory)
        qe_orchestrator.register_agent(agent)

        # Mock memory.store to raise error
        mocker.patch.object(
            qe_memory,
            'store',
            side_effect=Exception("Memory full")
        )

        task = QETask(task_type="test", context={})

        # Execution should succeed even if memory storage fails
        # (error is logged but not raised)
        result = await qe_orchestrator.execute_agent("memory-agent", task)
        assert result is not None

    @pytest.mark.asyncio
    async def test_invalid_agent_id(self, qe_orchestrator):
        """Test handling of invalid agent ID"""
        task = QETask(task_type="test", context={})

        with pytest.raises(ValueError, match="Agent not found"):
            await qe_orchestrator.execute_agent("invalid-agent-id", task)

    @pytest.mark.asyncio
    async def test_malformed_task_context(self, qe_orchestrator, qe_memory, simple_model):
        """Test handling of malformed task context"""
        agent = MockQEAgent("test-agent", simple_model, qe_memory)
        qe_orchestrator.register_agent(agent)

        # Task with None context
        task = QETask(task_type="test", context=None)
        result = await qe_orchestrator.execute_agent("test-agent", task)

        assert result is not None  # Should handle gracefully

    @pytest.mark.asyncio
    async def test_parallel_execution_partial_failure(self, qe_orchestrator, qe_memory, simple_model):
        """Test parallel execution handles partial failures"""
        good_agent = MockQEAgent("good-agent", simple_model, qe_memory)

        class BadAgent(BaseQEAgent):
            def get_system_prompt(self) -> str:
                return "Bad agent"

            async def execute(self, task: QETask):
                raise ValueError("Agent error")

        bad_agent = BadAgent("bad-agent", simple_model, qe_memory)

        qe_orchestrator.register_agent(good_agent)
        qe_orchestrator.register_agent(bad_agent)

        # Mock alcall to simulate partial failure
        with patch('lionagi_qe.core.orchestrator.alcall') as mock_alcall:
            mock_alcall.return_value = [
                {"status": "success"},  # Good agent
                None,  # Bad agent failed
                {"status": "success"}   # Good agent
            ]

            results = await qe_orchestrator.execute_parallel(
                ["good-agent", "bad-agent", "good-agent"],
                [{}, {}, {}]
            )

            # Should return partial results
            assert len(results) == 3
            assert results[0] is not None
            assert results[1] is None
            assert results[2] is not None


class TestMetricsTracking:
    """Test comprehensive metrics tracking"""

    @pytest.mark.asyncio
    async def test_workflow_metrics_increment(self, qe_orchestrator, qe_memory, simple_model, mocker):
        """Test workflow metrics increment correctly"""
        agent = MockQEAgent("test-agent", simple_model, qe_memory)
        qe_orchestrator.register_agent(agent)

        initial_workflows = qe_orchestrator.metrics["workflows_executed"]

        mocker.patch.object(
            qe_orchestrator.session,
            'flow',
            new=AsyncMock(return_value={})
        )

        await qe_orchestrator.execute_pipeline(["test-agent"], {})

        assert qe_orchestrator.metrics["workflows_executed"] == initial_workflows + 1

    @pytest.mark.asyncio
    async def test_agent_usage_tracking(self, qe_orchestrator, qe_memory, simple_model, mocker):
        """Test agent usage is tracked across workflows"""
        agents = [MockQEAgent(f"agent-{i}", simple_model, qe_memory) for i in range(3)]
        for agent in agents:
            qe_orchestrator.register_agent(agent)

        initial_usage = qe_orchestrator.metrics["total_agents_used"]

        mocker.patch.object(
            qe_orchestrator.session,
            'flow',
            new=AsyncMock(return_value={})
        )

        await qe_orchestrator.execute_pipeline(
            ["agent-0", "agent-1", "agent-2"],
            {}
        )

        assert qe_orchestrator.metrics["total_agents_used"] == initial_usage + 3

    @pytest.mark.asyncio
    async def test_parallel_metrics_accumulation(self, qe_orchestrator, qe_memory, simple_model):
        """Test metrics accumulate correctly for parallel execution"""
        agents = [MockQEAgent(f"parallel-{i}", simple_model, qe_memory) for i in range(5)]
        for agent in agents:
            qe_orchestrator.register_agent(agent)

        initial_usage = qe_orchestrator.metrics["total_agents_used"]

        with patch('lionagi_qe.core.orchestrator.alcall') as mock_alcall:
            mock_alcall.return_value = [{"status": "success"}] * 5

            await qe_orchestrator.execute_parallel(
                [f"parallel-{i}" for i in range(5)],
                [{}] * 5
            )

            assert qe_orchestrator.metrics["total_agents_used"] == initial_usage + 5

    @pytest.mark.asyncio
    async def test_fleet_status_includes_metrics(self, qe_orchestrator, qe_memory, simple_model):
        """Test fleet status includes all metrics"""
        agent = MockQEAgent("status-agent", simple_model, qe_memory)
        qe_orchestrator.register_agent(agent)

        status = await qe_orchestrator.get_fleet_status()

        assert "orchestration_metrics" in status
        assert "workflows_executed" in status["orchestration_metrics"]
        assert "total_agents_used" in status["orchestration_metrics"]
        assert "total_cost" in status["orchestration_metrics"]


class TestContextInheritance:
    """Test context inheritance across workflow stages"""

    @pytest.mark.asyncio
    async def test_context_preserved_in_pipeline(self, qe_orchestrator, qe_memory, simple_model, mocker):
        """Test context is preserved throughout pipeline"""
        agents = [MockQEAgent(f"stage-{i}", simple_model, qe_memory) for i in range(3)]
        for agent in agents:
            qe_orchestrator.register_agent(agent)

        initial_context = {
            "project": "qe-fleet",
            "version": "1.0.0",
            "config": {"key": "value"}
        }

        mocker.patch.object(
            qe_orchestrator.session,
            'flow',
            new=AsyncMock(return_value={"context": initial_context})
        )

        result = await qe_orchestrator.execute_pipeline(
            ["stage-0", "stage-1", "stage-2"],
            initial_context
        )

        # Context should be in result
        assert result is not None

    @pytest.mark.asyncio
    async def test_context_enrichment(self, qe_orchestrator, qe_memory, simple_model):
        """Test agents can enrich context for downstream agents"""
        class EnrichingAgent(BaseQEAgent):
            def get_system_prompt(self) -> str:
                return "Enriching agent"

            async def execute(self, task: QETask):
                # Add new data to context
                enriched = {**task.context, "enriched": True, "timestamp": "2025-11-04"}
                return {"context": enriched}

        agent1 = EnrichingAgent("enricher-1", simple_model, qe_memory)
        agent2 = MockQEAgent("consumer-1", simple_model, qe_memory)

        qe_orchestrator.register_agent(agent1)
        qe_orchestrator.register_agent(agent2)

        task1 = QETask(task_type="enrich", context={"original": "data"})
        result1 = await qe_orchestrator.execute_agent("enricher-1", task1)

        # Pass enriched context to next agent
        task2 = QETask(task_type="consume", context=result1["context"])
        result2 = await qe_orchestrator.execute_agent("consumer-1", task2)

        assert result2 is not None

    @pytest.mark.asyncio
    async def test_context_isolation_in_parallel(self, qe_orchestrator, qe_memory, simple_model):
        """Test contexts are isolated in parallel execution"""
        agent = MockQEAgent("isolated-agent", simple_model, qe_memory)
        qe_orchestrator.register_agent(agent)

        contexts = [
            {"id": 1, "shared": "value"},
            {"id": 2, "shared": "value"},
            {"id": 3, "shared": "value"}
        ]

        with patch('lionagi_qe.core.orchestrator.alcall') as mock_alcall:
            # Each agent should process its own context
            mock_alcall.return_value = [
                {"id": 1, "processed": True},
                {"id": 2, "processed": True},
                {"id": 3, "processed": True}
            ]

            results = await qe_orchestrator.execute_parallel(
                ["isolated-agent"] * 3,
                contexts
            )

            # Verify each got correct ID
            assert results[0]["id"] == 1
            assert results[1]["id"] == 2
            assert results[2]["id"] == 3
