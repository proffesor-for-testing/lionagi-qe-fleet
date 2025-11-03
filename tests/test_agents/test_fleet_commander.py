"""Unit tests for FleetCommanderAgent - Hierarchical coordination agent"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from lionagi_qe.agents.fleet_commander import FleetCommanderAgent, TaskDecomposition
from lionagi_qe.core.task import QETask
from lionagi.fields import Instruct


class TestTaskDecomposition:
    """Test TaskDecomposition model"""

    def test_task_decomposition_creation(self):
        """Test creating TaskDecomposition"""
        decomposition = TaskDecomposition(
            subtasks=[
                {"task": "generate_tests", "agent": "test-generator"},
                {"task": "run_tests", "agent": "test-executor"}
            ],
            agent_assignments={
                "subtask_0": "test-generator",
                "subtask_1": "test-executor"
            },
            execution_strategy="sequential",
            estimated_duration=30.0
        )

        assert len(decomposition.subtasks) == 2
        assert decomposition.execution_strategy == "sequential"
        assert decomposition.estimated_duration == 30.0


class TestFleetCommanderAgent:
    """Test FleetCommanderAgent functionality"""

    @pytest.mark.asyncio
    async def test_init(self, qe_memory, simple_model):
        """Test FleetCommanderAgent initialization"""
        agent = FleetCommanderAgent(
            agent_id="fleet-commander",
            model=simple_model,
            memory=qe_memory
        )

        assert agent.agent_id == "fleet-commander"

    @pytest.mark.asyncio
    async def test_system_prompt(self, fleet_commander_agent):
        """Test system prompt is comprehensive"""
        prompt = fleet_commander_agent.get_system_prompt()

        # Check for key coordination concepts
        assert "coordinator" in prompt.lower() or "fleet" in prompt.lower()
        assert "decompose" in prompt.lower() or "subtask" in prompt.lower()
        assert "agent" in prompt.lower()

    @pytest.mark.asyncio
    async def test_execute_task_decomposition(self, fleet_commander_agent, mocker):
        """Test task decomposition"""
        # Mock operate to return decomposition
        mock_subtasks = [
            Instruct(
                instruction="Generate comprehensive test suite",
                context={"agent_id": "test-generator"}
            ),
            Instruct(
                instruction="Execute tests with coverage",
                context={"agent_id": "test-executor"}
            ),
            Instruct(
                instruction="Analyze coverage gaps",
                context={"agent_id": "coverage-analyzer"}
            )
        ]

        mock_decomposition = MagicMock()
        mock_decomposition.instruct_model = mock_subtasks

        mocker.patch.object(
            fleet_commander_agent,
            'operate',
            new=AsyncMock(return_value=mock_decomposition)
        )

        # Mock communicate for synthesis
        mocker.patch.object(
            fleet_commander_agent,
            'communicate',
            new=AsyncMock(return_value="Synthesis complete")
        )

        task = QETask(
            task_type="hierarchical_coordination",
            context={
                "request": "Run complete QE workflow",
                "orchestrator": None,  # No orchestrator for simple test
                "available_agents": ["test-generator", "test-executor"]
            }
        )

        result = await fleet_commander_agent.execute(task)

        assert "decomposition" in result
        assert "synthesis" in result
        assert len(result["decomposition"]) == 3

    @pytest.mark.asyncio
    async def test_execute_with_orchestrator(self, fleet_commander_agent, qe_orchestrator, mocker):
        """Test execution with orchestrator for agent coordination"""
        # Mock decomposition
        mock_subtasks = [
            Instruct(
                instruction="Subtask 1",
                context={"agent_id": "agent-1"}
            ),
            Instruct(
                instruction="Subtask 2",
                context={"agent_id": "agent-2"}
            )
        ]

        mock_decomposition = MagicMock()
        mock_decomposition.instruct_model = mock_subtasks

        mocker.patch.object(
            fleet_commander_agent,
            'operate',
            new=AsyncMock(return_value=mock_decomposition)
        )

        # Mock orchestrator execute_parallel
        mocker.patch.object(
            qe_orchestrator,
            'execute_parallel',
            new=AsyncMock(return_value=[
                {"result": "agent-1 complete"},
                {"result": "agent-2 complete"}
            ])
        )

        # Mock synthesis
        mocker.patch.object(
            fleet_commander_agent,
            'communicate',
            new=AsyncMock(return_value="Final synthesis")
        )

        task = QETask(
            task_type="hierarchical_coordination",
            context={
                "request": "Complex QE request",
                "orchestrator": qe_orchestrator,
                "available_agents": ["agent-1", "agent-2"]
            }
        )

        result = await fleet_commander_agent.execute(task)

        assert "worker_results" in result
        assert len(result["worker_results"]) == 2

    @pytest.mark.asyncio
    async def test_execute_parallel_strategy(self, fleet_commander_agent, qe_orchestrator, mocker):
        """Test parallel execution strategy"""
        # Mock decomposition
        mock_subtasks = [
            Instruct(
                instruction=f"Parallel task {i}",
                context={"agent_id": f"agent-{i}"}
            )
            for i in range(3)
        ]

        mock_decomposition = MagicMock()
        mock_decomposition.instruct_model = mock_subtasks

        mocker.patch.object(
            fleet_commander_agent,
            'operate',
            new=AsyncMock(return_value=mock_decomposition)
        )

        mock_parallel = mocker.patch.object(
            qe_orchestrator,
            'execute_parallel',
            new=AsyncMock(return_value=[{"result": i} for i in range(3)])
        )

        mocker.patch.object(
            fleet_commander_agent,
            'communicate',
            new=AsyncMock(return_value="Parallel synthesis")
        )

        task = QETask(
            task_type="hierarchical_coordination",
            context={
                "request": "Parallel execution request",
                "orchestrator": qe_orchestrator,
                "available_agents": ["agent-0", "agent-1", "agent-2"],
                "execution_strategy": "parallel"
            }
        )

        result = await fleet_commander_agent.execute(task)

        # Verify parallel execution was called
        mock_parallel.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_sequential_strategy(self, fleet_commander_agent, qe_orchestrator, mocker):
        """Test sequential execution strategy"""
        # Mock decomposition
        mock_subtasks = [
            Instruct(
                instruction=f"Sequential task {i}",
                context={"agent_id": f"agent-{i}"}
            )
            for i in range(3)
        ]

        mock_decomposition = MagicMock()
        mock_decomposition.instruct_model = mock_subtasks

        mocker.patch.object(
            fleet_commander_agent,
            'operate',
            new=AsyncMock(return_value=mock_decomposition)
        )

        mock_pipeline = mocker.patch.object(
            qe_orchestrator,
            'execute_pipeline',
            new=AsyncMock(return_value={"pipeline": "complete"})
        )

        mocker.patch.object(
            fleet_commander_agent,
            'communicate',
            new=AsyncMock(return_value="Sequential synthesis")
        )

        task = QETask(
            task_type="hierarchical_coordination",
            context={
                "request": "Sequential execution request",
                "orchestrator": qe_orchestrator,
                "available_agents": ["agent-0", "agent-1", "agent-2"],
                "execution_strategy": "sequential"
            }
        )

        result = await fleet_commander_agent.execute(task)

        # Verify pipeline execution was called
        mock_pipeline.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_without_orchestrator_fallback(self, fleet_commander_agent, mocker):
        """Test fallback when no orchestrator is provided"""
        # Mock decomposition
        mock_subtasks = [
            Instruct(
                instruction="Fallback task",
                context={"agent_id": "agent-1"}
            )
        ]

        mock_decomposition = MagicMock()
        mock_decomposition.instruct_model = mock_subtasks

        mocker.patch.object(
            fleet_commander_agent,
            'operate',
            new=AsyncMock(return_value=mock_decomposition)
        )

        mocker.patch.object(
            fleet_commander_agent,
            'communicate',
            new=AsyncMock(return_value="Simulated synthesis")
        )

        task = QETask(
            task_type="hierarchical_coordination",
            context={
                "request": "Fallback request",
                "orchestrator": None,  # No orchestrator
                "available_agents": ["agent-1"]
            }
        )

        result = await fleet_commander_agent.execute(task)

        # Should have simulated results
        assert "agent_results" in result
        assert result["agent_results"][0]["status"] == "simulated"

    @pytest.mark.asyncio
    async def test_synthesis_includes_all_results(self, fleet_commander_agent, qe_orchestrator, mocker):
        """Test synthesis includes all agent results"""
        # Mock decomposition
        mock_subtasks = [
            Instruct(
                instruction=f"Task {i}",
                context={"agent_id": f"agent-{i}"}
            )
            for i in range(3)
        ]

        mock_decomposition = MagicMock()
        mock_decomposition.instruct_model = mock_subtasks

        mocker.patch.object(
            fleet_commander_agent,
            'operate',
            new=AsyncMock(return_value=mock_decomposition)
        )

        mocker.patch.object(
            qe_orchestrator,
            'execute_parallel',
            new=AsyncMock(return_value=[
                {"agent": "agent-0", "result": "done"},
                {"agent": "agent-1", "result": "done"},
                {"agent": "agent-2", "result": "done"}
            ])
        )

        mock_communicate = mocker.patch.object(
            fleet_commander_agent,
            'communicate',
            new=AsyncMock(return_value="Complete synthesis")
        )

        task = QETask(
            task_type="hierarchical_coordination",
            context={
                "request": "Multi-agent request",
                "orchestrator": qe_orchestrator,
                "available_agents": ["agent-0", "agent-1", "agent-2"]
            }
        )

        result = await fleet_commander_agent.execute(task)

        # Verify communicate was called with all results
        mock_communicate.assert_called_once()
        call_context = mock_communicate.call_args[1]["context"]
        assert "agent_results" in call_context
        assert len(call_context["agent_results"]) == 3

    @pytest.mark.asyncio
    async def test_agent_assignment_extraction(self, fleet_commander_agent, mocker):
        """Test extracting agent assignments from subtasks"""
        # Mock decomposition with specific agent assignments
        mock_subtasks = [
            Instruct(
                instruction="Generate tests",
                context={"agent_id": "test-generator"}
            ),
            Instruct(
                instruction="Execute tests",
                context={"agent_id": "test-executor"}
            ),
            Instruct(
                instruction="Analyze coverage",
                context={"agent_id": "coverage-analyzer"}
            )
        ]

        mock_decomposition = MagicMock()
        mock_decomposition.instruct_model = mock_subtasks

        mocker.patch.object(
            fleet_commander_agent,
            'operate',
            new=AsyncMock(return_value=mock_decomposition)
        )

        mocker.patch.object(
            fleet_commander_agent,
            'communicate',
            new=AsyncMock(return_value="Synthesis")
        )

        task = QETask(
            task_type="hierarchical_coordination",
            context={
                "request": "Multi-agent workflow",
                "orchestrator": None,
                "available_agents": ["test-generator", "test-executor", "coverage-analyzer"]
            }
        )

        result = await fleet_commander_agent.execute(task)

        # Verify agent assignments
        assignments = result["agent_assignments"]
        assert "test-generator" in assignments
        assert "test-executor" in assignments
        assert "coverage-analyzer" in assignments

    @pytest.mark.asyncio
    async def test_default_execution_strategy(self, fleet_commander_agent, mocker):
        """Test default execution strategy is parallel"""
        mock_subtasks = [
            Instruct(
                instruction="Task",
                context={"agent_id": "agent-1"}
            )
        ]

        mock_decomposition = MagicMock()
        mock_decomposition.instruct_model = mock_subtasks

        mocker.patch.object(
            fleet_commander_agent,
            'operate',
            new=AsyncMock(return_value=mock_decomposition)
        )

        mocker.patch.object(
            fleet_commander_agent,
            'communicate',
            new=AsyncMock(return_value="Synthesis")
        )

        task = QETask(
            task_type="hierarchical_coordination",
            context={
                "request": "Default strategy request",
                "orchestrator": None,
                "available_agents": ["agent-1"]
                # No execution_strategy specified
            }
        )

        result = await fleet_commander_agent.execute(task)

        # Should default to parallel
        assert result["execution_strategy"] == "parallel"

    @pytest.mark.asyncio
    async def test_complex_request_handling(self, fleet_commander_agent, complex_task_context, mocker):
        """Test handling complex multi-faceted requests"""
        # Mock decomposition for complex request
        mock_subtasks = [
            Instruct(
                instruction="Generate unit tests for all endpoints",
                context={"agent_id": "test-generator"}
            ),
            Instruct(
                instruction="Execute integration tests",
                context={"agent_id": "test-executor"}
            ),
            Instruct(
                instruction="Perform security scanning",
                context={"agent_id": "security-scanner"}
            ),
            Instruct(
                instruction="Run performance benchmarks",
                context={"agent_id": "performance-tester"}
            ),
            Instruct(
                instruction="Validate API contracts",
                context={"agent_id": "api-contract-validator"}
            )
        ]

        mock_decomposition = MagicMock()
        mock_decomposition.instruct_model = mock_subtasks

        mocker.patch.object(
            fleet_commander_agent,
            'operate',
            new=AsyncMock(return_value=mock_decomposition)
        )

        mocker.patch.object(
            fleet_commander_agent,
            'communicate',
            new=AsyncMock(return_value="Comprehensive QE report complete")
        )

        task = QETask(
            task_type="hierarchical_coordination",
            context={
                **complex_task_context,
                "orchestrator": None,
                "available_agents": [
                    "test-generator",
                    "test-executor",
                    "security-scanner",
                    "performance-tester",
                    "api-contract-validator"
                ]
            }
        )

        result = await fleet_commander_agent.execute(task)

        # Should decompose into multiple subtasks
        assert len(result["decomposition"]) >= 3
        assert result["synthesis"] is not None

    @pytest.mark.asyncio
    async def test_fallback_agent_assignment(self, fleet_commander_agent, mocker):
        """Test fallback agent assignment when context missing"""
        # Mock subtask without agent_id in context
        mock_subtasks = [
            Instruct(
                instruction="Task without agent",
                context={}  # No agent_id
            )
        ]

        mock_decomposition = MagicMock()
        mock_decomposition.instruct_model = mock_subtasks

        mocker.patch.object(
            fleet_commander_agent,
            'operate',
            new=AsyncMock(return_value=mock_decomposition)
        )

        mocker.patch.object(
            fleet_commander_agent,
            'communicate',
            new=AsyncMock(return_value="Synthesis")
        )

        task = QETask(
            task_type="hierarchical_coordination",
            context={
                "request": "Request",
                "orchestrator": None,
                "available_agents": ["test-generator"]
            }
        )

        result = await fleet_commander_agent.execute(task)

        # Should fallback to test-generator
        assert "test-generator" in result["agent_assignments"]
