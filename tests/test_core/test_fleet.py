"""Unit tests for QEFleet - Main fleet interface"""

import pytest
from unittest.mock import AsyncMock, Mock
from lionagi_qe.core.fleet import QEFleet
from lionagi_qe.core.task import QETask
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi import iModel


class MockAgent(BaseQEAgent):
    """Mock agent for testing"""

    def get_system_prompt(self) -> str:
        return "Mock agent"

    async def execute(self, task: QETask):
        return {"result": "mock"}


class TestQEFleet:
    """Test QEFleet initialization and configuration"""

    def test_init_default(self):
        """Test fleet initialization with defaults"""
        fleet = QEFleet()

        assert fleet.enable_routing is True
        assert fleet.enable_learning is False
        assert fleet.initialized is False
        assert fleet.memory is not None
        assert fleet.router is not None
        assert fleet.orchestrator is not None

    def test_init_with_routing_disabled(self):
        """Test fleet with routing disabled"""
        fleet = QEFleet(enable_routing=False)

        assert fleet.enable_routing is False
        assert fleet.router.enable_routing is False

    def test_init_with_learning_enabled(self):
        """Test fleet with learning enabled"""
        fleet = QEFleet(enable_learning=True)

        assert fleet.enable_learning is True
        assert fleet.orchestrator.enable_learning is True

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test fleet initialization"""
        fleet = QEFleet()

        assert not fleet.initialized

        await fleet.initialize()

        assert fleet.initialized

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, qe_fleet, caplog):
        """Test initialization can be called multiple times safely"""
        # Already initialized from fixture
        assert qe_fleet.initialized

        await qe_fleet.initialize()

        # Should log warning but not fail
        assert qe_fleet.initialized

    @pytest.mark.asyncio
    async def test_register_agent(self, qe_fleet):
        """Test registering an agent"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")
        agent = MockAgent(
            agent_id="test-agent",
            model=model,
            memory=qe_fleet.memory
        )

        qe_fleet.register_agent(agent)

        registered = qe_fleet.get_agent("test-agent")
        assert registered == agent

    @pytest.mark.asyncio
    async def test_execute_single_agent(self, qe_fleet):
        """Test executing a single agent task"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")
        agent = MockAgent("test-agent", model, qe_fleet.memory)
        qe_fleet.register_agent(agent)

        task = QETask(
            task_type="test_task",
            context={"data": "test"}
        )

        result = await qe_fleet.execute("test-agent", task)

        assert result == {"result": "mock"}
        assert task.status == "completed"

    @pytest.mark.asyncio
    async def test_execute_initializes_fleet(self):
        """Test execute initializes fleet if not initialized"""
        fleet = QEFleet()
        model = iModel(provider="openai", model="gpt-3.5-turbo")
        agent = MockAgent("auto-init-agent", model, fleet.memory)
        fleet.register_agent(agent)

        assert not fleet.initialized

        task = QETask(task_type="test")
        await fleet.execute("auto-init-agent", task)

        assert fleet.initialized

    @pytest.mark.asyncio
    async def test_execute_pipeline(self, qe_fleet, mocker):
        """Test executing a pipeline"""
        # Create agents
        model = iModel(provider="openai", model="gpt-3.5-turbo")
        for i in range(3):
            agent = MockAgent(f"pipeline-agent-{i}", model, qe_fleet.memory)
            qe_fleet.register_agent(agent)

        # Mock orchestrator pipeline
        mock_result = {"pipeline": "complete"}
        mocker.patch.object(
            qe_fleet.orchestrator,
            'execute_pipeline',
            new=AsyncMock(return_value=mock_result)
        )

        pipeline = ["pipeline-agent-0", "pipeline-agent-1", "pipeline-agent-2"]
        context = {"task": "test"}

        result = await qe_fleet.execute_pipeline(pipeline, context)

        assert result == mock_result

    @pytest.mark.asyncio
    async def test_execute_parallel(self, qe_fleet, mocker):
        """Test executing agents in parallel"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")
        for i in range(3):
            agent = MockAgent(f"parallel-agent-{i}", model, qe_fleet.memory)
            qe_fleet.register_agent(agent)

        mock_results = [{"agent": i} for i in range(3)]
        mocker.patch.object(
            qe_fleet.orchestrator,
            'execute_parallel',
            new=AsyncMock(return_value=mock_results)
        )

        agents = ["parallel-agent-0", "parallel-agent-1", "parallel-agent-2"]
        tasks = [{"task": i} for i in range(3)]

        results = await qe_fleet.execute_parallel(agents, tasks)

        assert results == mock_results

    @pytest.mark.asyncio
    async def test_execute_fan_out_fan_in(self, qe_fleet, mocker):
        """Test fan-out/fan-in workflow"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")

        # Register coordinator and workers
        coordinator = MockAgent("coordinator", model, qe_fleet.memory)
        qe_fleet.register_agent(coordinator)

        for i in range(3):
            worker = MockAgent(f"worker-{i}", model, qe_fleet.memory)
            qe_fleet.register_agent(worker)

        mock_result = {
            "decomposition": [],
            "worker_results": [],
            "synthesis": "complete"
        }

        mocker.patch.object(
            qe_fleet.orchestrator,
            'execute_fan_out_fan_in',
            new=AsyncMock(return_value=mock_result)
        )

        result = await qe_fleet.execute_fan_out_fan_in(
            "coordinator",
            ["worker-0", "worker-1", "worker-2"],
            {"task": "complex"}
        )

        assert result == mock_result

    @pytest.mark.asyncio
    async def test_execute_workflow(self, qe_fleet, mocker):
        """Test executing custom workflow graph"""
        mock_graph = Mock()
        mock_result = {"workflow": "executed"}

        mocker.patch.object(
            qe_fleet.orchestrator.session,
            'flow',
            new=AsyncMock(return_value=mock_result)
        )

        result = await qe_fleet.execute_workflow(mock_graph)

        assert result == mock_result

    @pytest.mark.asyncio
    async def test_get_status(self, qe_fleet, mocker):
        """Test getting fleet status"""
        mock_status = {
            "total_agents": 3,
            "agent_statuses": {},
            "orchestration_metrics": {},
            "routing_stats": {},
            "memory_stats": {}
        }

        mocker.patch.object(
            qe_fleet.orchestrator,
            'get_fleet_status',
            new=AsyncMock(return_value=mock_status)
        )

        status = await qe_fleet.get_status()

        assert status == mock_status

    @pytest.mark.asyncio
    async def test_get_status_not_initialized(self):
        """Test getting status when not initialized"""
        fleet = QEFleet()

        status = await fleet.get_status()

        assert status == {"status": "not_initialized"}

    @pytest.mark.asyncio
    async def test_get_agent(self, qe_fleet):
        """Test getting registered agent"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")
        agent = MockAgent("lookup-agent", model, qe_fleet.memory)
        qe_fleet.register_agent(agent)

        retrieved = qe_fleet.get_agent("lookup-agent")

        assert retrieved == agent

    @pytest.mark.asyncio
    async def test_get_nonexistent_agent(self, qe_fleet):
        """Test getting non-existent agent returns None"""
        agent = qe_fleet.get_agent("nonexistent")

        assert agent is None

    @pytest.mark.asyncio
    async def test_export_state(self, qe_fleet):
        """Test exporting fleet state"""
        # Store some data in memory
        await qe_fleet.memory.store("test_key", "test_value")

        state = await qe_fleet.export_state()

        assert "memory" in state
        assert "router_stats" in state
        assert "orchestrator_metrics" in state

    @pytest.mark.asyncio
    async def test_import_state(self, qe_fleet):
        """Test importing fleet state"""
        # Create state
        state = {
            "memory": {
                "store": {
                    "imported_key": {
                        "value": "imported_value",
                        "timestamp": 0,
                        "ttl": None,
                        "partition": "default"
                    }
                }
            },
            "router_stats": {},
            "orchestrator_metrics": {}
        }

        await qe_fleet.import_state(state)

        # Verify memory was imported
        value = await qe_fleet.memory.retrieve("imported_key")
        assert value == "imported_value"

    @pytest.mark.asyncio
    async def test_fleet_component_integration(self, qe_fleet):
        """Test all fleet components are properly integrated"""
        # Verify memory is shared
        assert qe_fleet.orchestrator.memory == qe_fleet.memory

        # Verify router is shared
        assert qe_fleet.orchestrator.router == qe_fleet.router

        # Verify configuration is propagated
        assert qe_fleet.orchestrator.enable_learning == qe_fleet.enable_learning

    @pytest.mark.asyncio
    async def test_multiple_agent_registration(self, qe_fleet):
        """Test registering multiple agents"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")

        agents = [
            MockAgent(f"multi-agent-{i}", model, qe_fleet.memory)
            for i in range(5)
        ]

        for agent in agents:
            qe_fleet.register_agent(agent)

        # Verify all registered
        for i in range(5):
            retrieved = qe_fleet.get_agent(f"multi-agent-{i}")
            assert retrieved is not None

    @pytest.mark.asyncio
    async def test_fleet_lifecycle(self):
        """Test complete fleet lifecycle"""
        # Create fleet
        fleet = QEFleet(enable_routing=False, enable_learning=False)
        assert not fleet.initialized

        # Initialize
        await fleet.initialize()
        assert fleet.initialized

        # Register agent
        model = iModel(provider="openai", model="gpt-3.5-turbo")
        agent = MockAgent("lifecycle-agent", model, fleet.memory)
        fleet.register_agent(agent)

        # Execute task
        task = QETask(task_type="test")
        result = await fleet.execute("lifecycle-agent", task)
        assert result is not None

        # Export state
        state = await fleet.export_state()
        assert state is not None

        # Get status
        status = await fleet.get_status()
        assert "total_agents" in status

    @pytest.mark.asyncio
    async def test_fleet_configuration_variations(self):
        """Test different fleet configurations"""
        configs = [
            {"enable_routing": True, "enable_learning": False},
            {"enable_routing": False, "enable_learning": True},
            {"enable_routing": True, "enable_learning": True},
            {"enable_routing": False, "enable_learning": False},
        ]

        for config in configs:
            fleet = QEFleet(**config)
            await fleet.initialize()

            assert fleet.enable_routing == config["enable_routing"]
            assert fleet.enable_learning == config["enable_learning"]
            assert fleet.initialized

    @pytest.mark.asyncio
    async def test_pipeline_auto_initialization(self):
        """Test pipeline execution auto-initializes fleet"""
        fleet = QEFleet()
        model = iModel(provider="openai", model="gpt-3.5-turbo")
        agent = MockAgent("auto-agent", model, fleet.memory)
        fleet.register_agent(agent)

        assert not fleet.initialized

        # Pipeline should auto-initialize
        result = await fleet.execute_pipeline(
            ["auto-agent"],
            {"test": "data"}
        )

        assert fleet.initialized

    @pytest.mark.asyncio
    async def test_parallel_auto_initialization(self):
        """Test parallel execution auto-initializes fleet"""
        fleet = QEFleet()
        model = iModel(provider="openai", model="gpt-3.5-turbo")
        agent = MockAgent("parallel-auto", model, fleet.memory)
        fleet.register_agent(agent)

        assert not fleet.initialized

        result = await fleet.execute_parallel(
            ["parallel-auto"],
            [{"test": "data"}]
        )

        assert fleet.initialized

    @pytest.mark.asyncio
    async def test_workflow_auto_initialization(self):
        """Test workflow execution auto-initializes fleet"""
        fleet = QEFleet()

        assert not fleet.initialized

        mock_graph = Mock()
        await fleet.execute_workflow(mock_graph)

        assert fleet.initialized
