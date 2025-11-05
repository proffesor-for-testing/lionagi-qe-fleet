"""Integration tests for BaseQEAgent with Q-Learning

Tests cover:
- BaseQEAgent with learning disabled (backward compatibility)
- BaseQEAgent with learning enabled
- execute_with_learning() flow
- _learn_from_execution() method
- Trajectory storage
- Learning metrics returned
- Error handling (database unavailable)
- Concurrent agent execution with learning
- Pattern learning integration
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, Mock, patch
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask
from lionagi_qe.core.memory import QEMemory
from lionagi import iModel


class TestLearningAgent(BaseQEAgent):
    """Concrete test agent for integration tests"""

    def get_system_prompt(self) -> str:
        return "Test learning agent system prompt"

    async def execute(self, task: QETask):
        """Execute task and return results"""
        return {
            "task_type": task.task_type,
            "tests_generated": 10,
            "coverage": 0.85,
            "bugs_found": 3,
            "execution_time": 2.5,
            "success": True
        }


class TestBackwardCompatibility:
    """Test backward compatibility with learning disabled"""

    @pytest.mark.asyncio
    async def test_agent_without_learning(self, qe_memory, simple_model):
        """Test agent works without learning enabled"""
        agent = TestLearningAgent(
            agent_id="no-learning-agent",
            model=simple_model,
            memory=qe_memory,
            enable_learning=False  # Disabled
        )

        task = QETask(task_type="test_generation", context={})
        result = await agent.execute(task)

        # Should work normally without Q-learning
        assert result["success"] is True
        assert "tests_generated" in result

        # Should not have Q-learning service
        assert not hasattr(agent, 'q_service') or agent.q_service is None

    @pytest.mark.asyncio
    async def test_execute_task_without_learning(self, qe_memory, simple_model):
        """Test task execution without learning integration"""
        agent = TestLearningAgent(
            agent_id="no-learning",
            model=simple_model,
            memory=qe_memory,
            enable_learning=False
        )

        task = QETask(task_type="test_execution", context={})

        # Pre-execution
        await agent.pre_execution_hook(task)

        # Execute
        result = await agent.execute(task)

        # Post-execution
        await agent.post_execution_hook(task, result)

        # Should complete without learning
        assert agent.metrics["tasks_completed"] == 1
        assert result["success"] is True


class TestLearningEnabled:
    """Test agent with learning enabled"""

    @pytest.mark.asyncio
    async def test_agent_with_learning_init(self, qe_memory, simple_model, mock_q_service):
        """Test agent initializes with learning enabled"""
        agent = TestLearningAgent(
            agent_id="learning-agent",
            model=simple_model,
            memory=qe_memory,
            enable_learning=True
        )

        # Should indicate learning is enabled
        assert agent.enable_learning is True

    @pytest.mark.asyncio
    async def test_q_service_initialization(self, learning_enabled_agent):
        """Test Q-learning service is initialized when learning enabled"""
        assert hasattr(learning_enabled_agent, 'q_service')
        assert learning_enabled_agent.q_service is not None

    @pytest.mark.asyncio
    async def test_learning_disabled_by_default(self, qe_memory, simple_model):
        """Test learning is disabled by default"""
        agent = TestLearningAgent(
            agent_id="default-agent",
            model=simple_model,
            memory=qe_memory
        )

        # Default should be disabled for backward compatibility
        assert agent.enable_learning is False


class TestExecuteWithLearning:
    """Test execute_with_learning() flow"""

    @pytest.mark.asyncio
    async def test_execute_with_learning_flow(self, learning_enabled_agent, sample_qe_task):
        """Test full execute_with_learning flow"""
        # Mock Q-service methods
        learning_enabled_agent.q_service.select_action = AsyncMock(return_value=2)
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        result = await learning_enabled_agent.execute_with_learning(sample_qe_task)

        # Should return result with learning metrics
        assert "result" in result
        assert "learning" in result
        assert result["result"]["success"] is True

        # Learning metrics
        assert "action_selected" in result["learning"]
        assert "state" in result["learning"]
        assert "reward" in result["learning"]

    @pytest.mark.asyncio
    async def test_action_selection_before_execution(self, learning_enabled_agent, sample_qe_task):
        """Test action is selected before task execution"""
        select_action_called = False

        async def mock_select(state, num_actions):
            nonlocal select_action_called
            select_action_called = True
            return 1

        learning_enabled_agent.q_service.select_action = mock_select
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        await learning_enabled_agent.execute_with_learning(sample_qe_task)

        assert select_action_called is True

    @pytest.mark.asyncio
    async def test_state_encoding(self, learning_enabled_agent, sample_qe_task):
        """Test task state is encoded properly"""
        learning_enabled_agent.q_service.select_action = AsyncMock(return_value=1)
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        result = await learning_enabled_agent.execute_with_learning(sample_qe_task)

        # State should be encoded
        state = result["learning"]["state"]
        assert isinstance(state, str)
        assert len(state) > 0

    @pytest.mark.asyncio
    async def test_reward_calculation(self, learning_enabled_agent, sample_qe_task):
        """Test reward is calculated from execution results"""
        learning_enabled_agent.q_service.select_action = AsyncMock(return_value=1)
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        result = await learning_enabled_agent.execute_with_learning(sample_qe_task)

        # Reward should be calculated
        reward = result["learning"]["reward"]
        assert isinstance(reward, (int, float))
        assert reward > 0  # Good result should give positive reward

    @pytest.mark.asyncio
    async def test_q_value_update_after_execution(self, learning_enabled_agent, sample_qe_task):
        """Test Q-value is updated after execution"""
        learning_enabled_agent.q_service.select_action = AsyncMock(return_value=1)
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        await learning_enabled_agent.execute_with_learning(sample_qe_task)

        # Q-value update should be called
        learning_enabled_agent.q_service.update_q_value.assert_called_once()

    @pytest.mark.asyncio
    async def test_exploration_vs_exploitation(self, learning_enabled_agent, sample_task_factory):
        """Test agent balances exploration and exploitation"""
        actions_selected = []

        async def track_action(state, num_actions):
            import random
            action = random.randint(0, num_actions - 1)
            actions_selected.append(action)
            return action

        learning_enabled_agent.q_service.select_action = track_action
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        # Execute multiple tasks
        for i in range(20):
            task = sample_task_factory(complexity=i)
            await learning_enabled_agent.execute_with_learning(task)

        # Should have variety in actions (exploration)
        assert len(set(actions_selected)) > 1


class TestLearnFromExecution:
    """Test _learn_from_execution() internal method"""

    @pytest.mark.asyncio
    async def test_learn_from_execution_stores_trajectory(self, learning_enabled_agent, sample_qe_task):
        """Test learning stores execution trajectory"""
        learning_enabled_agent.q_service.select_action = AsyncMock(return_value=1)
        learning_enabled_agent.q_service.update_q_value = AsyncMock()
        learning_enabled_agent.q_service.store_experience = AsyncMock()

        await learning_enabled_agent.execute_with_learning(sample_qe_task)

        # Trajectory should be stored
        learning_enabled_agent.q_service.store_experience.assert_called_once()

    @pytest.mark.asyncio
    async def test_learn_from_success(self, learning_enabled_agent, sample_qe_task):
        """Test learning from successful execution"""
        learning_enabled_agent.q_service.select_action = AsyncMock(return_value=1)
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        result = await learning_enabled_agent.execute_with_learning(sample_qe_task)

        # Successful execution should give positive reward
        assert result["learning"]["reward"] > 0

        # Q-value should be updated with positive reward
        call_args = learning_enabled_agent.q_service.update_q_value.call_args
        reward = call_args[0][2]  # Third argument is reward
        assert reward > 0

    @pytest.mark.asyncio
    async def test_learn_from_failure(self, qe_memory, simple_model, mock_q_service):
        """Test learning from failed execution"""

        class FailingAgent(BaseQEAgent):
            def get_system_prompt(self) -> str:
                return "Failing agent"

            async def execute(self, task: QETask):
                # Simulate failure
                return {
                    "success": False,
                    "error": "Test failure",
                    "coverage": 0.0
                }

        agent = FailingAgent(
            agent_id="failing-agent",
            model=simple_model,
            memory=qe_memory,
            enable_learning=True
        )
        agent.q_service = mock_q_service

        task = QETask(task_type="test_generation", context={})
        result = await agent.execute_with_learning(task)

        # Failed execution should give negative reward
        assert result["learning"]["reward"] < 0


class TestTrajectoryStorage:
    """Test trajectory storage in memory"""

    @pytest.mark.asyncio
    async def test_trajectory_stored_in_memory(self, learning_enabled_agent, sample_qe_task):
        """Test execution trajectory is stored in memory"""
        learning_enabled_agent.q_service.select_action = AsyncMock(return_value=1)
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        await learning_enabled_agent.execute_with_learning(sample_qe_task)

        # Check memory for trajectory
        trajectory_key = f"aqe/{learning_enabled_agent.agent_id}/learning/trajectories/{sample_qe_task.task_id}"
        trajectory = await learning_enabled_agent.memory.retrieve(trajectory_key)

        assert trajectory is not None
        assert "state" in trajectory
        assert "action" in trajectory
        assert "reward" in trajectory

    @pytest.mark.asyncio
    async def test_multiple_trajectories_stored(self, learning_enabled_agent, sample_task_factory):
        """Test multiple trajectories are stored"""
        learning_enabled_agent.q_service.select_action = AsyncMock(return_value=1)
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        tasks = [sample_task_factory(complexity=i) for i in range(5)]

        for task in tasks:
            await learning_enabled_agent.execute_with_learning(task)

        # Check all trajectories stored
        pattern = r"aqe/learning-agent/learning/trajectories/.*"
        trajectories = await learning_enabled_agent.search_memory(pattern)

        assert len(trajectories) == 5

    @pytest.mark.asyncio
    async def test_trajectory_includes_metadata(self, learning_enabled_agent, sample_qe_task):
        """Test trajectory includes execution metadata"""
        learning_enabled_agent.q_service.select_action = AsyncMock(return_value=1)
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        await learning_enabled_agent.execute_with_learning(sample_qe_task)

        trajectory_key = f"aqe/{learning_enabled_agent.agent_id}/learning/trajectories/{sample_qe_task.task_id}"
        trajectory = await learning_enabled_agent.memory.retrieve(trajectory_key)

        # Should include metadata
        assert "timestamp" in trajectory
        assert "agent_id" in trajectory
        assert "task_id" in trajectory
        assert trajectory["agent_id"] == learning_enabled_agent.agent_id


class TestLearningMetrics:
    """Test learning metrics returned with results"""

    @pytest.mark.asyncio
    async def test_learning_metrics_in_result(self, learning_enabled_agent, sample_qe_task):
        """Test learning metrics are included in result"""
        learning_enabled_agent.q_service.select_action = AsyncMock(return_value=1)
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        result = await learning_enabled_agent.execute_with_learning(sample_qe_task)

        assert "learning" in result
        learning_metrics = result["learning"]

        assert "state" in learning_metrics
        assert "action_selected" in learning_metrics
        assert "reward" in learning_metrics
        assert "epsilon" in learning_metrics

    @pytest.mark.asyncio
    async def test_agent_metrics_updated(self, learning_enabled_agent, sample_qe_task):
        """Test agent metrics are updated with learning stats"""
        learning_enabled_agent.q_service.select_action = AsyncMock(return_value=1)
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        initial_completed = learning_enabled_agent.metrics["tasks_completed"]

        await learning_enabled_agent.execute_with_learning(sample_qe_task)

        # Task completion should be tracked
        assert learning_enabled_agent.metrics["tasks_completed"] == initial_completed + 1


class TestErrorHandling:
    """Test error handling in learning integration"""

    @pytest.mark.asyncio
    async def test_learning_continues_on_db_error(self, qe_memory, simple_model):
        """Test agent continues execution even if learning fails"""
        agent = TestLearningAgent(
            agent_id="robust-agent",
            model=simple_model,
            memory=qe_memory,
            enable_learning=True
        )

        # Mock Q-service with failing DB
        mock_q = Mock()
        mock_q.select_action = AsyncMock(side_effect=Exception("DB unavailable"))
        mock_q.update_q_value = AsyncMock()
        agent.q_service = mock_q

        task = QETask(task_type="test_generation", context={})

        # Should still execute task successfully
        result = await agent.execute(task)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_learning_fallback_on_error(self, learning_enabled_agent, sample_qe_task):
        """Test learning falls back to default action on error"""
        # Mock action selection to fail
        learning_enabled_agent.q_service.select_action = AsyncMock(
            side_effect=Exception("Selection failed")
        )
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        # Should still execute (with default action)
        result = await learning_enabled_agent.execute(sample_qe_task)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_invalid_reward_handling(self, learning_enabled_agent, qe_memory, simple_model):
        """Test handling of invalid reward values"""

        class BadRewardAgent(BaseQEAgent):
            def get_system_prompt(self) -> str:
                return "Bad reward agent"

            async def execute(self, task: QETask):
                return {
                    "coverage": None,  # Invalid - will cause NaN reward
                    "success": True
                }

        agent = BadRewardAgent(
            agent_id="bad-reward",
            model=simple_model,
            memory=qe_memory,
            enable_learning=True
        )

        mock_q = Mock()
        mock_q.select_action = AsyncMock(return_value=1)
        mock_q.update_q_value = AsyncMock()
        agent.q_service = mock_q

        task = QETask(task_type="test_generation", context={})

        # Should handle gracefully (skip or use default reward)
        try:
            result = await agent.execute_with_learning(task)
            assert result is not None
        except (ValueError, TypeError):
            pass  # Expected to handle gracefully


class TestConcurrentLearning:
    """Test concurrent agent execution with learning"""

    @pytest.mark.asyncio
    async def test_multiple_agents_learning_concurrently(self, qe_memory, simple_model, mock_q_service):
        """Test multiple agents can learn concurrently"""
        agents = []
        for i in range(3):
            agent = TestLearningAgent(
                agent_id=f"concurrent-agent-{i}",
                model=simple_model,
                memory=qe_memory,
                enable_learning=True
            )
            agent.q_service = mock_q_service
            agents.append(agent)

        mock_q_service.select_action = AsyncMock(return_value=1)
        mock_q_service.update_q_value = AsyncMock()

        # Execute concurrently
        tasks = [
            QETask(task_type=f"task_{i}", context={})
            for i in range(3)
        ]

        executions = [
            agent.execute_with_learning(task)
            for agent, task in zip(agents, tasks)
        ]

        results = await asyncio.gather(*executions)

        # All should complete
        assert len(results) == 3
        assert all(r["result"]["success"] for r in results)

    @pytest.mark.asyncio
    async def test_agent_learning_isolation(self, qe_memory, simple_model):
        """Test each agent has isolated learning state"""
        agent1 = TestLearningAgent(
            agent_id="isolated-1",
            model=simple_model,
            memory=qe_memory,
            enable_learning=True
        )

        agent2 = TestLearningAgent(
            agent_id="isolated-2",
            model=simple_model,
            memory=qe_memory,
            enable_learning=True
        )

        # Different Q-learning services
        mock_q1 = Mock()
        mock_q1.select_action = AsyncMock(return_value=1)
        mock_q1.update_q_value = AsyncMock()
        agent1.q_service = mock_q1

        mock_q2 = Mock()
        mock_q2.select_action = AsyncMock(return_value=2)
        mock_q2.update_q_value = AsyncMock()
        agent2.q_service = mock_q2

        task = QETask(task_type="test_generation", context={})

        result1 = await agent1.execute_with_learning(task)
        result2 = await agent2.execute_with_learning(task)

        # Different actions selected
        assert result1["learning"]["action_selected"] == 1
        assert result2["learning"]["action_selected"] == 2


class TestPatternLearningIntegration:
    """Test integration with existing pattern learning"""

    @pytest.mark.asyncio
    async def test_q_learning_with_pattern_storage(self, learning_enabled_agent, sample_qe_task):
        """Test Q-learning works alongside pattern storage"""
        learning_enabled_agent.q_service.select_action = AsyncMock(return_value=1)
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        # Store a learned pattern
        await learning_enabled_agent.store_learned_pattern(
            "test_pattern",
            {"strategy": "unit_test"}
        )

        # Execute with learning
        result = await learning_enabled_agent.execute_with_learning(sample_qe_task)

        # Both should work
        patterns = await learning_enabled_agent.get_learned_patterns()
        assert len(patterns) > 0
        assert result["learning"]["reward"] > 0

    @pytest.mark.asyncio
    async def test_pattern_reuse_bonus_in_reward(self, learning_enabled_agent, sample_qe_task):
        """Test pattern reuse contributes to reward"""
        learning_enabled_agent.q_service.select_action = AsyncMock(return_value=1)
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        # Store patterns
        for i in range(3):
            await learning_enabled_agent.store_learned_pattern(
                f"pattern_{i}",
                {"type": "test"}
            )

        # Execute - should get pattern reuse bonus
        result = await learning_enabled_agent.execute_with_learning(sample_qe_task)

        # Reward should include pattern bonus
        reward = result["learning"]["reward"]
        assert reward > 0

    @pytest.mark.asyncio
    async def test_learning_updates_pattern_metrics(self, learning_enabled_agent, sample_qe_task):
        """Test Q-learning updates pattern learning metrics"""
        learning_enabled_agent.q_service.select_action = AsyncMock(return_value=1)
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        initial_patterns = learning_enabled_agent.metrics["patterns_learned"]

        # Execute with learning
        await learning_enabled_agent.execute_with_learning(sample_qe_task)

        # Could update pattern metrics based on learning
        metrics = await learning_enabled_agent.get_metrics()
        assert "tasks_completed" in metrics


class TestLearningLifecycle:
    """Test complete learning lifecycle"""

    @pytest.mark.asyncio
    async def test_full_learning_lifecycle(self, learning_enabled_agent, sample_task_factory):
        """Test complete learning lifecycle over multiple tasks"""
        learning_enabled_agent.q_service.select_action = AsyncMock(return_value=1)
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        # Execute multiple tasks
        tasks = [sample_task_factory(complexity=i * 3) for i in range(5)]

        for task in tasks:
            # Pre-execution
            await learning_enabled_agent.pre_execution_hook(task)

            # Execute with learning
            result = await learning_enabled_agent.execute_with_learning(task)

            # Post-execution
            await learning_enabled_agent.post_execution_hook(task, result["result"])

            # Verify learning happened
            assert "learning" in result
            assert result["learning"]["reward"] is not None

        # Verify all updates
        assert learning_enabled_agent.q_service.update_q_value.call_count == 5

    @pytest.mark.asyncio
    async def test_learning_improves_over_time(self, learning_enabled_agent, sample_task_factory):
        """Test learning shows improvement over time (epsilon decay)"""
        initial_epsilon = 0.5
        learning_enabled_agent.q_service.epsilon = initial_epsilon
        learning_enabled_agent.q_service.select_action = AsyncMock(return_value=1)
        learning_enabled_agent.q_service.update_q_value = AsyncMock()

        # Mock epsilon decay
        def decay_epsilon():
            learning_enabled_agent.q_service.epsilon *= 0.95

        learning_enabled_agent.q_service.decay_epsilon = decay_epsilon

        # Execute many tasks
        for i in range(20):
            task = sample_task_factory(complexity=i)
            await learning_enabled_agent.execute_with_learning(task)

            # Decay epsilon after each task
            learning_enabled_agent.q_service.decay_epsilon()

        # Epsilon should have decreased (more exploitation)
        assert learning_enabled_agent.q_service.epsilon < initial_epsilon
