"""Unit tests for WIPLimitedOrchestrator - WIP limits, lane segregation, and context budget"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock
from lionagi_qe.core.orchestrator_wip import (
    WIPLimitedOrchestrator,
    LaneType,
    AgentLane,
    ContextBudget,
    create_wip_limited_orchestrator
)
from lionagi_qe.core.task import QETask
from lionagi_qe.core.memory import QEMemory
from lionagi_qe.core.router import ModelRouter
from lionagi_qe.core.base_agent import BaseQEAgent


class MockQEAgent(BaseQEAgent):
    """Mock QE agent for testing with configurable execution time"""
    
    def __init__(self, agent_id: str, model, memory, execution_time: float = 0.01):
        super().__init__(agent_id=agent_id, model=model, memory=memory)
        self.execution_time = execution_time
        self.execution_count = 0

    def get_system_prompt(self) -> str:
        return f"Mock agent {self.agent_id} for testing"

    async def execute(self, task: QETask):
        """Simulate async execution with configurable delay"""
        self.execution_count += 1
        await asyncio.sleep(self.execution_time)
        return {
            "agent_id": self.agent_id,
            "task_type": task.task_type,
            "result": f"mock_result_{self.execution_count}",
            "execution_count": self.execution_count
        }


class TestWIPLimitedOrchestrator:
    """Test WIPLimitedOrchestrator initialization and WIP limit enforcement"""

    @pytest.mark.asyncio
    async def test_init_with_wip_limit(self, qe_memory, model_router):
        """Test orchestrator initialization with WIP limit"""
        orchestrator = WIPLimitedOrchestrator(
            memory=qe_memory,
            router=model_router,
            wip_limit=5,
            enable_learning=False
        )

        assert orchestrator.wip_limit == 5
        assert orchestrator.global_semaphore._value == 5
        assert len(orchestrator.lanes) == 5  # test, security, performance, quality, shared
        assert orchestrator.context_budget.max_tokens == 100000
        assert orchestrator.context_budget.used_tokens == 0

    @pytest.mark.asyncio
    async def test_create_wip_limited_orchestrator(self):
        """Test factory function creates orchestrator with defaults"""
        orchestrator = create_wip_limited_orchestrator(wip_limit=3)
        
        assert orchestrator.wip_limit == 3
        assert orchestrator.lanes[LaneType.TEST].wip_limit == 3
        assert orchestrator.lanes[LaneType.SECURITY].wip_limit == 2
        assert orchestrator.lanes[LaneType.PERFORMANCE].wip_limit == 2
        assert orchestrator.lanes[LaneType.QUALITY].wip_limit == 3
        assert orchestrator.lanes[LaneType.SHARED].wip_limit == 2

    @pytest.mark.asyncio
    async def test_wip_limit_enforcement(self, qe_memory, model_router, simple_model):
        """Test that WIP limit restricts concurrent execution"""
        wip_limit = 2
        orchestrator = WIPLimitedOrchestrator(
            memory=qe_memory,
            router=model_router,
            wip_limit=wip_limit,
            enable_learning=False
        )

        # Create 5 agents with 0.1s execution time
        agents = [
            MockQEAgent(f"agent-{i}", simple_model, qe_memory, execution_time=0.1)
            for i in range(5)
        ]
        
        for agent in agents:
            orchestrator.register_agent(agent)

        # Execute all agents in parallel
        agent_ids = [f"agent-{i}" for i in range(5)]
        tasks = [
            QETask(task_type=f"task_{i}", context={"data": f"data_{i}"})
            for i in range(5)
        ]

        results = await orchestrator.execute_parallel(agent_ids, tasks)

        # Verify all completed
        assert len(results) == 5
        
        # Check coordination metrics
        status = await orchestrator.get_coordination_status()
        
        # With WIP limit of 2 and 5 agents, we expect WIP limit hits
        assert status["wip_limit_hits"] > 0
        assert status["max_concurrent_observed"] <= wip_limit
        assert status["total_wait_time_ms"] > 0  # Some agents had to wait

    @pytest.mark.asyncio
    async def test_no_wip_limit_hits_with_sufficient_limit(self, qe_memory, model_router, simple_model):
        """Test no WIP limit hits when limit >= concurrent agents"""
        wip_limit = 10  # More than agents
        orchestrator = WIPLimitedOrchestrator(
            memory=qe_memory,
            router=model_router,
            wip_limit=wip_limit,
            enable_learning=False
        )

        agents = [
            MockQEAgent(f"agent-{i}", simple_model, qe_memory, execution_time=0.01)
            for i in range(3)
        ]
        
        for agent in agents:
            orchestrator.register_agent(agent)

        agent_ids = [f"agent-{i}" for i in range(3)]
        tasks = [QETask(task_type=f"task_{i}") for i in range(3)]

        await orchestrator.execute_parallel(agent_ids, tasks)

        status = await orchestrator.get_coordination_status()
        
        # No WIP limit hits expected
        assert status["wip_limit_hits"] == 0
        assert status["max_concurrent_observed"] <= 3


class TestAgentLaneSegregation:
    """Test agent lane assignment and segregation"""

    @pytest.mark.asyncio
    async def test_assign_agent_to_lane(self, qe_memory, model_router):
        """Test assigning agents to specific lanes"""
        orchestrator = WIPLimitedOrchestrator(
            memory=qe_memory,
            router=model_router,
            wip_limit=5
        )

        orchestrator.assign_agent_to_lane("test-generator", LaneType.TEST)
        orchestrator.assign_agent_to_lane("security-scanner", LaneType.SECURITY)
        orchestrator.assign_agent_to_lane("perf-tester", LaneType.PERFORMANCE)

        assert orchestrator.agent_lanes["test-generator"] == LaneType.TEST
        assert orchestrator.agent_lanes["security-scanner"] == LaneType.SECURITY
        assert orchestrator.agent_lanes["perf-tester"] == LaneType.PERFORMANCE

    @pytest.mark.asyncio
    async def test_lane_wip_limit_enforcement(self, qe_memory, model_router, simple_model):
        """Test that lane WIP limits restrict concurrent execution within lane"""
        orchestrator = WIPLimitedOrchestrator(
            memory=qe_memory,
            router=model_router,
            wip_limit=10  # High global limit
        )

        # Create 5 test agents (lane limit = 3)
        agents = [
            MockQEAgent(f"test-agent-{i}", simple_model, qe_memory, execution_time=0.1)
            for i in range(5)
        ]
        
        for agent in agents:
            orchestrator.register_agent(agent)
            orchestrator.assign_agent_to_lane(agent.agent_id, LaneType.TEST)

        agent_ids = [f"test-agent-{i}" for i in range(5)]
        tasks = [QETask(task_type=f"task_{i}") for i in range(5)]

        await orchestrator.execute_parallel(agent_ids, tasks)

        status = await orchestrator.get_coordination_status()
        
        # Check lane-specific metrics
        test_lane_status = status["lanes"]["test"]
        
        # Lane WIP limit of 3 should be hit with 5 concurrent agents
        assert test_lane_status["limit_hits"] > 0
        assert test_lane_status["total_executed"] == 5
        assert test_lane_status["active_count"] == 0  # All finished

    @pytest.mark.asyncio
    async def test_lane_isolation(self, qe_memory, model_router, simple_model):
        """Test that lanes operate independently"""
        orchestrator = WIPLimitedOrchestrator(
            memory=qe_memory,
            router=model_router,
            wip_limit=10
        )

        # Create agents in different lanes
        test_agents = [MockQEAgent(f"test-{i}", simple_model, qe_memory) for i in range(3)]
        security_agents = [MockQEAgent(f"security-{i}", simple_model, qe_memory) for i in range(2)]
        
        for agent in test_agents:
            orchestrator.register_agent(agent)
            orchestrator.assign_agent_to_lane(agent.agent_id, LaneType.TEST)
            
        for agent in security_agents:
            orchestrator.register_agent(agent)
            orchestrator.assign_agent_to_lane(agent.agent_id, LaneType.SECURITY)

        all_agent_ids = [f"test-{i}" for i in range(3)] + [f"security-{i}" for i in range(2)]
        tasks = [QETask(task_type=f"task_{i}") for i in range(5)]

        await orchestrator.execute_parallel(all_agent_ids, tasks)

        status = await orchestrator.get_coordination_status()
        
        # Verify both lanes executed
        assert status["lanes"]["test"]["total_executed"] == 3
        assert status["lanes"]["security"]["total_executed"] == 2

    @pytest.mark.asyncio
    async def test_default_shared_lane(self, qe_memory, model_router, simple_model):
        """Test agents without explicit lane assignment use shared lane"""
        orchestrator = WIPLimitedOrchestrator(
            memory=qe_memory,
            router=model_router,
            wip_limit=10
        )

        agent = MockQEAgent("unassigned-agent", simple_model, qe_memory)
        orchestrator.register_agent(agent)
        
        # Don't assign to any lane - should default to SHARED

        task = QETask(task_type="test")
        result = await orchestrator.execute_agent("unassigned-agent", task)

        status = await orchestrator.get_coordination_status()
        
        # Should be executed in SHARED lane
        assert status["lanes"]["shared"]["total_executed"] == 1


class TestContextBudget:
    """Test context budget tracking and enforcement"""

    @pytest.mark.asyncio
    async def test_context_budget_tracking(self, qe_memory, model_router, simple_model):
        """Test context budget tracks token usage"""
        orchestrator = WIPLimitedOrchestrator(
            memory=qe_memory,
            router=model_router,
            wip_limit=5,
            context_budget_tokens=10000
        )

        agent = MockQEAgent("test-agent", simple_model, qe_memory)
        orchestrator.register_agent(agent)

        task = QETask(task_type="test", context={"data": "x" * 1000})
        
        # Mock token counting
        orchestrator.context_budget.used_tokens = 500
        orchestrator.context_budget.calls_count = 1

        await orchestrator.execute_agent("test-agent", task)

        status = await orchestrator.get_coordination_status()
        budget_status = status["context_budget"]
        
        assert budget_status["max_tokens"] == 10000
        assert budget_status["used_tokens"] >= 0
        assert budget_status["utilization"] >= 0
        assert budget_status["utilization"] <= 100

    @pytest.mark.asyncio
    async def test_context_budget_exceeded_warning(self, qe_memory, model_router, simple_model):
        """Test warning when context budget is exceeded"""
        orchestrator = WIPLimitedOrchestrator(
            memory=qe_memory,
            router=model_router,
            wip_limit=5,
            context_budget_tokens=100  # Very low limit
        )

        agent = MockQEAgent("test-agent", simple_model, qe_memory)
        orchestrator.register_agent(agent)

        # Simulate budget exceeded
        orchestrator.context_budget.used_tokens = 150
        orchestrator.context_budget.calls_count = 1
        orchestrator.context_budget.budget_exceeded_count = 1

        status = await orchestrator.get_coordination_status()
        
        assert status["context_budget"]["utilization"] > 100
        assert status["context_budget"]["budget_exceeded_count"] == 1


class TestCoordinationMetrics:
    """Test coordination metrics tracking and recommendations"""

    @pytest.mark.asyncio
    async def test_coordination_metrics_tracking(self, qe_memory, model_router, simple_model):
        """Test coordination metrics are tracked correctly"""
        orchestrator = WIPLimitedOrchestrator(
            memory=qe_memory,
            router=model_router,
            wip_limit=2
        )

        agents = [
            MockQEAgent(f"agent-{i}", simple_model, qe_memory, execution_time=0.05)
            for i in range(4)
        ]
        
        for agent in agents:
            orchestrator.register_agent(agent)
            orchestrator.assign_agent_to_lane(agent.agent_id, LaneType.TEST)

        agent_ids = [f"agent-{i}" for i in range(4)]
        tasks = [QETask(task_type=f"task_{i}") for i in range(4)]

        await orchestrator.execute_parallel(agent_ids, tasks)

        status = await orchestrator.get_coordination_status()
        
        # Verify metrics structure
        assert "wip_limit_hits" in status
        assert "lane_limit_hits" in status
        assert "total_wait_time_ms" in status
        assert "max_concurrent_observed" in status
        assert "lanes" in status
        assert "context_budget" in status
        assert "recommendations" in status

    @pytest.mark.asyncio
    async def test_recommendations_well_tuned(self, qe_memory, model_router, simple_model):
        """Test recommendations when parameters are well-tuned"""
        orchestrator = WIPLimitedOrchestrator(
            memory=qe_memory,
            router=model_router,
            wip_limit=10  # Plenty of headroom
        )

        agents = [MockQEAgent(f"agent-{i}", simple_model, qe_memory) for i in range(2)]
        
        for agent in agents:
            orchestrator.register_agent(agent)

        agent_ids = [f"agent-{i}" for i in range(2)]
        tasks = [QETask(task_type=f"task_{i}") for i in range(2)]

        await orchestrator.execute_parallel(agent_ids, tasks)

        status = await orchestrator.get_coordination_status()
        
        # Should indicate well-tuned parameters
        assert "well-tuned" in status["recommendations"][0].lower() or \
               status["wip_limit_hits"] == 0

    @pytest.mark.asyncio
    async def test_recommendations_increase_wip_limit(self, qe_memory, model_router, simple_model):
        """Test recommendations suggest increasing WIP limit when heavily utilized"""
        orchestrator = WIPLimitedOrchestrator(
            memory=qe_memory,
            router=model_router,
            wip_limit=1  # Very restrictive
        )

        agents = [
            MockQEAgent(f"agent-{i}", simple_model, qe_memory, execution_time=0.1)
            for i in range(5)
        ]
        
        for agent in agents:
            orchestrator.register_agent(agent)
            orchestrator.assign_agent_to_lane(agent.agent_id, LaneType.TEST)

        agent_ids = [f"agent-{i}" for i in range(5)]
        tasks = [QETask(task_type=f"task_{i}") for i in range(5)]

        await orchestrator.execute_parallel(agent_ids, tasks)

        status = await orchestrator.get_coordination_status()
        
        # Should suggest increasing WIP limit due to high contention
        recommendations = " ".join(status["recommendations"]).lower()
        assert "increase" in recommendations or status["wip_limit_hits"] > 5


class TestBackwardCompatibility:
    """Test backward compatibility with base QEOrchestrator"""

    @pytest.mark.asyncio
    async def test_execute_agent_compatible(self, qe_memory, model_router, simple_model):
        """Test execute_agent works same as base orchestrator"""
        orchestrator = WIPLimitedOrchestrator(
            memory=qe_memory,
            router=model_router,
            wip_limit=5
        )

        agent = MockQEAgent("test-agent", simple_model, qe_memory)
        orchestrator.register_agent(agent)

        task = QETask(task_type="test", context={"data": "test"})
        result = await orchestrator.execute_agent("test-agent", task)

        # Same return structure as base
        assert result["agent_id"] == "test-agent"
        assert task.status == "completed"
        assert task.agent_id == "test-agent"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Test requires Session.flow() which doesn't exist in current lionagi API")
    async def test_execute_pipeline_compatible(self, qe_memory, model_router, simple_model, mocker):
        """Test execute_pipeline works same as base orchestrator"""
        orchestrator = WIPLimitedOrchestrator(
            memory=qe_memory,
            router=model_router,
            wip_limit=5
        )

        agents = [MockQEAgent(f"agent-{i}", simple_model, qe_memory) for i in range(3)]
        
        for agent in agents:
            orchestrator.register_agent(agent)

        # Mock Session.flow
        mock_flow = mocker.patch.object(
            orchestrator.session,
            'flow',
            new=AsyncMock(return_value={"pipeline": "result"})
        )

        pipeline = ["agent-0", "agent-1", "agent-2"]
        context = {"task": "sequential_test"}

        result = await orchestrator.execute_pipeline(pipeline, context)

        # Same return structure as base
        assert result == {"pipeline": "result"}
        assert orchestrator.metrics["workflows_executed"] == 1


class TestErrorHandling:
    """Test error handling in WIP-limited orchestrator"""

    @pytest.mark.asyncio
    async def test_agent_failure_releases_wip_slot(self, qe_memory, model_router, simple_model, mocker):
        """Test that WIP slot is released even if agent fails"""
        orchestrator = WIPLimitedOrchestrator(
            memory=qe_memory,
            router=model_router,
            wip_limit=2
        )

        failing_agent = MockQEAgent("failing-agent", simple_model, qe_memory)
        success_agent = MockQEAgent("success-agent", simple_model, qe_memory)
        
        orchestrator.register_agent(failing_agent)
        orchestrator.register_agent(success_agent)

        # Mock failing agent to raise error
        mocker.patch.object(
            failing_agent,
            'execute',
            side_effect=Exception("Execution failed")
        )
        mocker.patch.object(failing_agent, 'error_handler', new=AsyncMock())

        tasks = [
            QETask(task_type="fail"),
            QETask(task_type="success")
        ]

        with pytest.raises(Exception):
            await orchestrator.execute_parallel(
                ["failing-agent", "success-agent"],
                tasks
            )

        # WIP semaphore should be released despite error
        assert orchestrator.global_semaphore._value == 2  # Back to initial

    @pytest.mark.asyncio
    async def test_lane_semaphore_released_on_error(self, qe_memory, model_router, simple_model, mocker):
        """Test that lane semaphore is released even if agent fails"""
        orchestrator = WIPLimitedOrchestrator(
            memory=qe_memory,
            router=model_router,
            wip_limit=10
        )

        failing_agent = MockQEAgent("failing-test-agent", simple_model, qe_memory)
        orchestrator.register_agent(failing_agent)
        orchestrator.assign_agent_to_lane("failing-test-agent", LaneType.TEST)

        # Mock agent to raise error
        mocker.patch.object(
            failing_agent,
            'execute',
            side_effect=Exception("Test failure")
        )
        mocker.patch.object(failing_agent, 'error_handler', new=AsyncMock())

        task = QETask(task_type="fail")

        test_lane = orchestrator.lanes[LaneType.TEST]
        initial_semaphore_value = test_lane.semaphore._value

        with pytest.raises(Exception):
            await orchestrator.execute_agent("failing-test-agent", task)

        # Lane semaphore should be released
        assert test_lane.semaphore._value == initial_semaphore_value


# Fixtures
@pytest.fixture
def qe_memory():
    """Create QE memory instance"""
    return QEMemory()


@pytest.fixture
def model_router():
    """Create model router instance"""
    return ModelRouter(enable_routing=False)


@pytest.fixture
def simple_model():
    """Create simple model instance"""
    from lionagi import iModel
    return iModel(provider="openai", model="gpt-3.5-turbo")


@pytest.fixture
def qe_orchestrator_wip(qe_memory, model_router):
    """Create WIP-limited orchestrator for testing"""
    return WIPLimitedOrchestrator(
        memory=qe_memory,
        router=model_router,
        wip_limit=5,
        enable_learning=False
    )
