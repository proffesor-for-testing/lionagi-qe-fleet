"""Unit tests for QEOrchestrator - Pipeline and parallel execution"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from lionagi_qe.core.orchestrator import QEOrchestrator
from lionagi_qe.core.task import QETask
from lionagi_qe.core.memory import QEMemory
from lionagi_qe.core.router import ModelRouter
from lionagi_qe.core.base_agent import BaseQEAgent


class MockQEAgent(BaseQEAgent):
    """Mock QE agent for testing"""

    def get_system_prompt(self) -> str:
        return "Mock agent for testing"

    async def execute(self, task: QETask):
        return {
            "agent_id": self.agent_id,
            "task_type": task.task_type,
            "result": "mock_result"
        }


class TestQEOrchestrator:
    """Test QEOrchestrator initialization and basic operations"""

    @pytest.mark.asyncio
    async def test_init(self, qe_memory, model_router):
        """Test orchestrator initialization"""
        orchestrator = QEOrchestrator(
            memory=qe_memory,
            router=model_router,
            enable_learning=False
        )

        assert orchestrator.memory == qe_memory
        assert orchestrator.router == model_router
        assert orchestrator.enable_learning is False
        assert len(orchestrator.agents) == 0
        assert orchestrator.metrics["workflows_executed"] == 0

    @pytest.mark.asyncio
    async def test_register_agent(self, qe_orchestrator, qe_memory, simple_model):
        """Test registering an agent"""
        agent = MockQEAgent(
            agent_id="test-agent",
            model=simple_model,
            memory=qe_memory
        )

        qe_orchestrator.register_agent(agent)

        assert "test-agent" in qe_orchestrator.agents
        assert qe_orchestrator.get_agent("test-agent") == agent

    @pytest.mark.asyncio
    async def test_get_nonexistent_agent(self, qe_orchestrator):
        """Test getting non-existent agent returns None"""
        agent = qe_orchestrator.get_agent("nonexistent")
        assert agent is None

    @pytest.mark.asyncio
    async def test_execute_agent(self, qe_orchestrator, qe_memory, simple_model):
        """Test executing a single agent"""
        agent = MockQEAgent(
            agent_id="test-agent",
            model=simple_model,
            memory=qe_memory
        )
        qe_orchestrator.register_agent(agent)

        task = QETask(
            task_type="test_task",
            context={"data": "test"}
        )

        result = await qe_orchestrator.execute_agent("test-agent", task)

        assert result["agent_id"] == "test-agent"
        assert task.status == "completed"
        assert task.agent_id == "test-agent"

    @pytest.mark.asyncio
    async def test_execute_agent_not_found(self, qe_orchestrator):
        """Test executing non-existent agent raises error"""
        task = QETask(task_type="test")

        with pytest.raises(ValueError, match="Agent not found"):
            await qe_orchestrator.execute_agent("nonexistent", task)

    @pytest.mark.asyncio
    async def test_execute_agent_with_hooks(self, qe_orchestrator, qe_memory, simple_model, mocker):
        """Test agent execution calls hooks"""
        agent = MockQEAgent(
            agent_id="test-agent",
            model=simple_model,
            memory=qe_memory
        )

        # Mock hook methods
        pre_hook = mocker.patch.object(agent, 'pre_execution_hook', new=AsyncMock())
        post_hook = mocker.patch.object(agent, 'post_execution_hook', new=AsyncMock())

        qe_orchestrator.register_agent(agent)

        task = QETask(task_type="test")
        await qe_orchestrator.execute_agent("test-agent", task)

        # Verify hooks were called
        pre_hook.assert_called_once()
        post_hook.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_agent_error_handling(self, qe_orchestrator, qe_memory, simple_model, mocker):
        """Test agent execution error handling"""
        agent = MockQEAgent(
            agent_id="failing-agent",
            model=simple_model,
            memory=qe_memory
        )

        # Mock execute to raise error
        error_msg = "Execution failed"
        mocker.patch.object(
            agent,
            'execute',
            side_effect=Exception(error_msg)
        )

        error_handler = mocker.patch.object(agent, 'error_handler', new=AsyncMock())

        qe_orchestrator.register_agent(agent)

        task = QETask(task_type="test")

        with pytest.raises(Exception):
            await qe_orchestrator.execute_agent("failing-agent", task)

        # Verify error handler was called
        error_handler.assert_called_once()
        assert task.status == "failed"
        assert error_msg in task.error

    @pytest.mark.asyncio
    async def test_execute_pipeline(self, qe_orchestrator, qe_memory, simple_model, mocker):
        """Test executing sequential pipeline"""
        # Create multiple agents
        agents = [
            MockQEAgent(f"agent-{i}", simple_model, qe_memory)
            for i in range(3)
        ]

        for agent in agents:
            qe_orchestrator.register_agent(agent)

        # Mock Session.flow
        mock_flow = mocker.patch.object(
            qe_orchestrator.session,
            'flow',
            new=AsyncMock(return_value={"pipeline": "result"})
        )

        pipeline = ["agent-0", "agent-1", "agent-2"]
        context = {"task": "sequential_test"}

        result = await qe_orchestrator.execute_pipeline(pipeline, context)

        assert result == {"pipeline": "result"}
        assert qe_orchestrator.metrics["workflows_executed"] == 1
        assert qe_orchestrator.metrics["total_agents_used"] == 3

    @pytest.mark.asyncio
    async def test_execute_pipeline_agent_not_found(self, qe_orchestrator):
        """Test pipeline execution fails if agent not found"""
        pipeline = ["nonexistent-agent"]
        context = {}

        with pytest.raises(ValueError, match="Agent not found in pipeline"):
            await qe_orchestrator.execute_pipeline(pipeline, context)

    @pytest.mark.asyncio
    async def test_execute_parallel(self, qe_orchestrator, qe_memory, simple_model):
        """Test executing agents in parallel"""
        # Create agents
        agents = [
            MockQEAgent(f"agent-{i}", simple_model, qe_memory)
            for i in range(3)
        ]

        for agent in agents:
            qe_orchestrator.register_agent(agent)

        agent_ids = ["agent-0", "agent-1", "agent-2"]
        tasks = [
            {"task_type": f"task_{i}", "data": f"data_{i}"}
            for i in range(3)
        ]

        results = await qe_orchestrator.execute_parallel(agent_ids, tasks)

        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["agent_id"] == f"agent-{i}"

    @pytest.mark.asyncio
    async def test_execute_parallel_single_agent(self, qe_orchestrator, qe_memory, simple_model):
        """Test parallel execution with single agent"""
        agent = MockQEAgent("solo-agent", simple_model, qe_memory)
        qe_orchestrator.register_agent(agent)

        results = await qe_orchestrator.execute_parallel(
            ["solo-agent"],
            [{"task_type": "solo_task"}]
        )

        assert len(results) == 1
        assert results[0]["agent_id"] == "solo-agent"

    @pytest.mark.asyncio
    async def test_execute_fan_out_fan_in(self, qe_orchestrator, qe_memory, simple_model, mocker):
        """Test fan-out/fan-in workflow pattern"""
        # Create coordinator and workers
        coordinator = MockQEAgent("coordinator", simple_model, qe_memory)
        workers = [
            MockQEAgent(f"worker-{i}", simple_model, qe_memory)
            for i in range(3)
        ]

        qe_orchestrator.register_agent(coordinator)
        for worker in workers:
            qe_orchestrator.register_agent(worker)

        # Mock coordinator operate to return subtasks
        from lionagi.fields import Instruct
        mock_subtasks = [
            Instruct(
                instruction=f"Subtask {i}",
                context={"agent_id": f"worker-{i}"}
            )
            for i in range(3)
        ]

        mock_decomposition = MagicMock()
        mock_decomposition.instruct_model = mock_subtasks

        mocker.patch.object(
            coordinator,
            'operate',
            new=AsyncMock(return_value=mock_decomposition)
        )

        # Mock coordinator communicate for synthesis
        mocker.patch.object(
            coordinator,
            'communicate',
            new=AsyncMock(return_value="Synthesis complete")
        )

        context = {"request": "complex task"}

        result = await qe_orchestrator.execute_fan_out_fan_in(
            "coordinator",
            ["worker-0", "worker-1", "worker-2"],
            context
        )

        assert "decomposition" in result
        assert "worker_results" in result
        assert "synthesis" in result
        assert len(result["worker_results"]) == 3

    @pytest.mark.asyncio
    async def test_execute_hierarchical(self, qe_orchestrator, qe_memory, simple_model):
        """Test hierarchical coordination"""
        commander = MockQEAgent("fleet-commander", simple_model, qe_memory)
        qe_orchestrator.register_agent(commander)

        context = {"request": "Hierarchical task"}

        result = await qe_orchestrator.execute_hierarchical(
            "fleet-commander",
            context
        )

        assert result is not None
        assert result["task_type"] == "hierarchical_coordination"

    @pytest.mark.asyncio
    async def test_execute_hierarchical_commander_not_found(self, qe_orchestrator):
        """Test hierarchical execution fails if commander not found"""
        with pytest.raises(ValueError, match="Fleet commander not found"):
            await qe_orchestrator.execute_hierarchical(
                "nonexistent-commander",
                {}
            )

    @pytest.mark.asyncio
    async def test_get_fleet_status(self, qe_orchestrator, qe_memory, simple_model):
        """Test getting fleet status"""
        # Register agents
        for i in range(3):
            agent = MockQEAgent(f"agent-{i}", simple_model, qe_memory)
            qe_orchestrator.register_agent(agent)

        status = await qe_orchestrator.get_fleet_status()

        assert status["total_agents"] == 3
        assert "agent_statuses" in status
        assert "orchestration_metrics" in status
        assert "routing_stats" in status
        assert "memory_stats" in status

    @pytest.mark.asyncio
    async def test_orchestration_metrics_tracking(self, qe_orchestrator, qe_memory, simple_model, mocker):
        """Test orchestration metrics are tracked correctly"""
        agent = MockQEAgent("test-agent", simple_model, qe_memory)
        qe_orchestrator.register_agent(agent)

        # Mock session.flow
        mocker.patch.object(
            qe_orchestrator.session,
            'flow',
            new=AsyncMock(return_value={})
        )

        # Execute pipeline
        await qe_orchestrator.execute_pipeline(["test-agent"], {})

        assert qe_orchestrator.metrics["workflows_executed"] == 1
        assert qe_orchestrator.metrics["total_agents_used"] == 1

        # Execute parallel
        await qe_orchestrator.execute_parallel(["test-agent"], [{}])

        assert qe_orchestrator.metrics["total_agents_used"] == 2

    @pytest.mark.asyncio
    async def test_concurrent_agent_execution(self, qe_orchestrator, qe_memory, simple_model):
        """Test multiple agents can execute concurrently"""
        agents = [
            MockQEAgent(f"concurrent-{i}", simple_model, qe_memory)
            for i in range(5)
        ]

        for agent in agents:
            qe_orchestrator.register_agent(agent)

        agent_ids = [f"concurrent-{i}" for i in range(5)]
        tasks = [{"task_type": f"task_{i}"} for i in range(5)]

        results = await qe_orchestrator.execute_parallel(agent_ids, tasks)

        assert len(results) == 5
        # All results should be from different agents
        agent_ids_in_results = [r["agent_id"] for r in results]
        assert len(set(agent_ids_in_results)) == 5

    @pytest.mark.asyncio
    async def test_empty_pipeline(self, qe_orchestrator, mocker):
        """Test executing empty pipeline"""
        mocker.patch.object(
            qe_orchestrator.session,
            'flow',
            new=AsyncMock(return_value={})
        )

        result = await qe_orchestrator.execute_pipeline([], {})

        assert qe_orchestrator.metrics["total_agents_used"] == 0

    @pytest.mark.asyncio
    async def test_learning_enabled(self, qe_memory, model_router):
        """Test orchestrator with learning enabled"""
        orchestrator = QEOrchestrator(
            memory=qe_memory,
            router=model_router,
            enable_learning=True
        )

        assert orchestrator.enable_learning is True
