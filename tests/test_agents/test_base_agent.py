"""Unit tests for BaseQEAgent - Base agent functionality"""

import pytest
from unittest.mock import AsyncMock, Mock
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask
from lionagi_qe.core.memory import QEMemory
from lionagi import iModel


class TestAgent(BaseQEAgent):
    """Concrete test agent implementation"""

    def get_system_prompt(self) -> str:
        return "Test agent system prompt"

    async def execute(self, task: QETask):
        return {
            "task_type": task.task_type,
            "result": "executed"
        }


class TestBaseQEAgent:
    """Test BaseQEAgent initialization and core features"""

    @pytest.mark.asyncio
    async def test_init(self, qe_memory, simple_model):
        """Test agent initialization"""
        agent = TestAgent(
            agent_id="test-agent",
            model=simple_model,
            memory=qe_memory,
            skills=["skill1", "skill2"],
            enable_learning=True
        )

        assert agent.agent_id == "test-agent"
        assert agent.model == simple_model
        assert agent.memory == qe_memory
        assert agent.skills == ["skill1", "skill2"]
        assert agent.enable_learning is True
        assert agent.branch is not None

    @pytest.mark.asyncio
    async def test_metrics_initialization(self, qe_memory, simple_model):
        """Test agent metrics are initialized"""
        agent = TestAgent("test-agent", simple_model, qe_memory)

        assert agent.metrics["tasks_completed"] == 0
        assert agent.metrics["tasks_failed"] == 0
        assert agent.metrics["total_cost"] == 0.0
        assert agent.metrics["patterns_learned"] == 0

    @pytest.mark.asyncio
    async def test_get_system_prompt(self, qe_memory, simple_model):
        """Test get_system_prompt is implemented"""
        agent = TestAgent("test-agent", simple_model, qe_memory)

        prompt = agent.get_system_prompt()

        assert prompt == "Test agent system prompt"

    @pytest.mark.asyncio
    async def test_execute(self, qe_memory, simple_model):
        """Test execute method"""
        agent = TestAgent("test-agent", simple_model, qe_memory)

        task = QETask(task_type="test_task", context={})
        result = await agent.execute(task)

        assert result["task_type"] == "test_task"
        assert result["result"] == "executed"

    @pytest.mark.asyncio
    async def test_store_result(self, qe_memory, simple_model):
        """Test storing results in memory"""
        agent = TestAgent("test-agent", simple_model, qe_memory)

        await agent.store_result("test_key", {"data": "value"})

        # Verify stored
        stored = await qe_memory.retrieve("aqe/test-agent/test_key")
        assert stored == {"data": "value"}

    @pytest.mark.asyncio
    async def test_store_result_with_ttl(self, qe_memory, simple_model):
        """Test storing results with TTL"""
        import asyncio

        agent = TestAgent("test-agent", simple_model, qe_memory)

        await agent.store_result("ttl_key", "value", ttl=1)

        # Should exist immediately
        value = await qe_memory.retrieve("aqe/test-agent/ttl_key")
        assert value == "value"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired
        value = await qe_memory.retrieve("aqe/test-agent/ttl_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_store_result_custom_partition(self, qe_memory, simple_model):
        """Test storing results with custom partition"""
        agent = TestAgent("test-agent", simple_model, qe_memory)

        await agent.store_result(
            "partitioned_key",
            "value",
            partition="custom_partition"
        )

        # Check partition in internal store
        stored_data = qe_memory._store["aqe/test-agent/partitioned_key"]
        assert stored_data["partition"] == "custom_partition"

    @pytest.mark.asyncio
    async def test_retrieve_context(self, qe_memory, simple_model):
        """Test retrieving context from memory"""
        agent = TestAgent("test-agent", simple_model, qe_memory)

        # Store context
        await qe_memory.store("context_key", {"context": "data"})

        # Retrieve
        context = await agent.retrieve_context("context_key")

        assert context == {"context": "data"}

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_context(self, qe_memory, simple_model):
        """Test retrieving non-existent context returns None"""
        agent = TestAgent("test-agent", simple_model, qe_memory)

        context = await agent.retrieve_context("nonexistent")

        assert context is None

    @pytest.mark.asyncio
    async def test_search_memory(self, qe_memory, simple_model):
        """Test searching memory"""
        agent = TestAgent("test-agent", simple_model, qe_memory)

        # Store multiple keys
        await qe_memory.store("aqe/test/key1", "value1")
        await qe_memory.store("aqe/test/key2", "value2")
        await qe_memory.store("aqe/other/key3", "value3")

        # Search
        results = await agent.search_memory(r"aqe/test/.*")

        assert len(results) == 2
        assert "aqe/test/key1" in results
        assert "aqe/test/key2" in results

    @pytest.mark.asyncio
    async def test_get_learned_patterns(self, qe_memory, simple_model):
        """Test retrieving learned patterns"""
        agent = TestAgent("test-agent", simple_model, qe_memory)

        # Store patterns
        await qe_memory.store("aqe/patterns/test-agent/pattern1", {"type": "test"})
        await qe_memory.store("aqe/patterns/test-agent/pattern2", {"type": "coverage"})

        patterns = await agent.get_learned_patterns()

        assert len(patterns) == 2

    @pytest.mark.asyncio
    async def test_store_learned_pattern(self, qe_memory, simple_model):
        """Test storing learned patterns"""
        agent = TestAgent("test-agent", simple_model, qe_memory)

        initial_count = agent.metrics["patterns_learned"]

        await agent.store_learned_pattern(
            "new_pattern",
            {"strategy": "test_generation"}
        )

        # Verify stored
        pattern = await qe_memory.retrieve("aqe/patterns/test-agent/new_pattern")
        assert pattern == {"strategy": "test_generation"}

        # Verify metrics updated
        assert agent.metrics["patterns_learned"] == initial_count + 1

    @pytest.mark.asyncio
    async def test_pre_execution_hook(self, qe_memory, simple_model, caplog):
        """Test pre-execution hook"""
        agent = TestAgent("test-agent", simple_model, qe_memory)

        task = QETask(task_type="test_task")

        await agent.pre_execution_hook(task)

        # Check logging
        assert "Starting task" in caplog.text

    @pytest.mark.asyncio
    async def test_post_execution_hook(self, qe_memory, simple_model):
        """Test post-execution hook"""
        agent = TestAgent("test-agent", simple_model, qe_memory)

        task = QETask(task_type="test_task")
        result = {"success": True}

        initial_completed = agent.metrics["tasks_completed"]

        await agent.post_execution_hook(task, result)

        # Verify metrics updated
        assert agent.metrics["tasks_completed"] == initial_completed + 1

        # Verify result stored
        stored = await qe_memory.retrieve(f"aqe/test-agent/tasks/{task.task_id}/result")
        assert stored == result

    @pytest.mark.asyncio
    async def test_post_execution_hook_with_learning(self, qe_memory, simple_model):
        """Test post-execution hook with learning enabled"""
        agent = TestAgent(
            "test-agent",
            simple_model,
            qe_memory,
            enable_learning=True
        )

        task = QETask(task_type="test_task")
        result = {"success": True}

        await agent.post_execution_hook(task, result)

        # Verify learning trajectory stored
        trajectory = await qe_memory.retrieve(
            f"aqe/test-agent/learning/trajectories/{task.task_id}"
        )
        assert trajectory is not None
        assert trajectory["success"] is True

    @pytest.mark.asyncio
    async def test_error_handler(self, qe_memory, simple_model):
        """Test error handling"""
        agent = TestAgent("test-agent", simple_model, qe_memory)

        task = QETask(task_type="test_task")
        error = Exception("Test error")

        initial_failed = agent.metrics["tasks_failed"]

        await agent.error_handler(task, error)

        # Verify metrics updated
        assert agent.metrics["tasks_failed"] == initial_failed + 1

        # Verify error stored
        stored_error = await qe_memory.retrieve(
            f"aqe/test-agent/tasks/{task.task_id}/error"
        )
        assert stored_error is not None
        assert "Test error" in stored_error["error"]

    @pytest.mark.asyncio
    async def test_get_metrics(self, qe_memory, simple_model):
        """Test getting agent metrics"""
        agent = TestAgent(
            "test-agent",
            simple_model,
            qe_memory,
            skills=["skill1", "skill2"]
        )

        # Update some metrics
        agent.metrics["tasks_completed"] = 5
        agent.metrics["tasks_failed"] = 2

        metrics = await agent.get_metrics()

        assert metrics["agent_id"] == "test-agent"
        assert metrics["skills"] == ["skill1", "skill2"]
        assert metrics["tasks_completed"] == 5
        assert metrics["tasks_failed"] == 2

    @pytest.mark.asyncio
    async def test_communicate(self, qe_memory, simple_model, mocker):
        """Test agent communication"""
        agent = TestAgent("test-agent", simple_model, qe_memory)

        # Mock branch communicate
        mock_response = "Agent response"
        mocker.patch.object(
            agent.branch,
            'communicate',
            new=AsyncMock(return_value=mock_response)
        )

        response = await agent.communicate(
            instruction="Test instruction",
            context={"data": "test"}
        )

        assert response == mock_response

    @pytest.mark.asyncio
    async def test_operate(self, qe_memory, simple_model, mocker):
        """Test agent structured operation"""
        from pydantic import BaseModel, Field

        class TestResponse(BaseModel):
            result: str = Field(...)

        agent = TestAgent("test-agent", simple_model, qe_memory)

        # Mock branch operate
        mock_result = TestResponse(result="structured")
        mocker.patch.object(
            agent.branch,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        result = await agent.operate(
            instruction="Test instruction",
            context={"data": "test"},
            response_format=TestResponse
        )

        assert result.result == "structured"

    @pytest.mark.asyncio
    async def test_full_task_lifecycle(self, qe_memory, simple_model):
        """Test complete task execution lifecycle"""
        agent = TestAgent("test-agent", simple_model, qe_memory)

        task = QETask(task_type="lifecycle_test")

        # Pre-execution
        await agent.pre_execution_hook(task)

        # Execute
        result = await agent.execute(task)

        # Post-execution
        await agent.post_execution_hook(task, result)

        # Verify metrics
        assert agent.metrics["tasks_completed"] == 1
        assert agent.metrics["tasks_failed"] == 0

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, qe_memory, simple_model):
        """Test concurrent agent operations"""
        import asyncio

        agent = TestAgent("test-agent", simple_model, qe_memory)

        # Store multiple results concurrently
        tasks = [
            agent.store_result(f"key_{i}", f"value_{i}")
            for i in range(5)
        ]

        await asyncio.gather(*tasks)

        # Verify all stored
        for i in range(5):
            value = await qe_memory.retrieve(f"aqe/test-agent/key_{i}")
            assert value == f"value_{i}"

    @pytest.mark.asyncio
    async def test_skills_configuration(self, qe_memory, simple_model):
        """Test agent with skills configuration"""
        skills = [
            "agentic-quality-engineering",
            "tdd-london-chicago",
            "api-testing-patterns"
        ]

        agent = TestAgent(
            "skilled-agent",
            simple_model,
            qe_memory,
            skills=skills
        )

        assert agent.skills == skills

        metrics = await agent.get_metrics()
        assert metrics["skills"] == skills
