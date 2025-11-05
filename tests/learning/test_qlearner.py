"""Unit tests for QLearningService - Core Q-Learning implementation

Tests cover:
- Epsilon-greedy action selection
- Q-value update (Bellman equation)
- Exploration vs exploitation
- Q-table initialization
- Max Q-value retrieval
- Best action selection
- Epsilon decay
- Database synchronization
- Concurrent agent execution
- Experience replay
"""

import pytest
import asyncio
from typing import Dict, List
from unittest.mock import AsyncMock, Mock
from lionagi_qe.learning.qlearner import QLearningService


class TestQLearningService:
    """Test QLearningService initialization and configuration"""

    @pytest.mark.asyncio
    async def test_init(self, mock_db_manager):
        """Test service initialization"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            alpha=0.1,
            gamma=0.95,
            epsilon=0.2
        )

        assert service.agent_id == "test-agent"
        assert service.alpha == 0.1
        assert service.gamma == 0.95
        assert service.epsilon == 0.2
        assert service.db_manager == mock_db_manager

    @pytest.mark.asyncio
    async def test_init_default_params(self, mock_db_manager):
        """Test initialization with default parameters"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager
        )

        # Should have reasonable defaults
        assert 0 < service.alpha < 1
        assert 0 < service.gamma < 1
        assert 0 < service.epsilon < 1

    @pytest.mark.asyncio
    async def test_init_with_config(self, mock_db_manager, q_learning_config):
        """Test initialization with configuration dict"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            config=q_learning_config
        )

        assert service.alpha == q_learning_config["learning_rate"]
        assert service.gamma == q_learning_config["discount_factor"]
        assert service.epsilon == q_learning_config["initial_epsilon"]


class TestEpsilonGreedySelection:
    """Test epsilon-greedy action selection"""

    @pytest.mark.asyncio
    async def test_select_action_exploration(self, mock_db_manager):
        """Test epsilon-greedy selects random action with probability epsilon"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            epsilon=1.0  # Always explore
        )

        state = "test_state"
        actions = []

        # Select action 100 times
        for _ in range(100):
            action = await service.select_action(state, num_actions=5)
            actions.append(action)

        # Should have variety (not always same action)
        unique_actions = set(actions)
        assert len(unique_actions) > 1
        assert all(0 <= a < 5 for a in actions)

    @pytest.mark.asyncio
    async def test_select_action_exploitation(self, mock_db_manager):
        """Test epsilon-greedy selects best action with probability 1-epsilon"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            epsilon=0.0  # Never explore
        )

        # Mock best action
        mock_db_manager.get_best_action = AsyncMock(return_value=2)

        state = "test_state"
        actions = []

        # Select action 100 times
        for _ in range(100):
            action = await service.select_action(state, num_actions=5)
            actions.append(action)

        # Should always select same (best) action
        assert len(set(actions)) == 1
        assert actions[0] == 2

    @pytest.mark.asyncio
    async def test_select_action_mixed(self, mock_db_manager):
        """Test epsilon-greedy with mixed exploration/exploitation"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            epsilon=0.2  # 20% exploration
        )

        # Mock best action
        mock_db_manager.get_best_action = AsyncMock(return_value=2)

        state = "test_state"
        actions = []

        # Select action many times
        for _ in range(500):
            action = await service.select_action(state, num_actions=5)
            actions.append(action)

        # Should mostly select best action (2), but some random
        best_action_count = actions.count(2)
        assert best_action_count > 350  # At least 70%
        assert best_action_count < 500  # Not always

        # Should have some exploration
        unique_actions = set(actions)
        assert len(unique_actions) > 1

    @pytest.mark.asyncio
    async def test_select_action_updates_exploration_count(self, mock_db_manager):
        """Test action selection updates exploration count"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            epsilon=1.0
        )

        initial_count = service.exploration_count
        await service.select_action("state", num_actions=3)

        assert service.exploration_count == initial_count + 1


class TestQValueUpdate:
    """Test Q-value updates using Bellman equation"""

    @pytest.mark.asyncio
    async def test_update_q_value_bellman(self, mock_db_manager):
        """Test Q-value update using Bellman equation"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            alpha=0.1,
            gamma=0.95
        )

        # Mock current and max Q-values
        mock_db_manager.get_q_value = AsyncMock(return_value=0.5)
        mock_db_manager.get_max_q_value = AsyncMock(return_value=0.8)
        mock_db_manager.update_q_value = AsyncMock()

        state = "state1"
        action = 1
        reward = 10.0
        next_state = "state2"

        await service.update_q_value(state, action, reward, next_state)

        # Verify update was called
        mock_db_manager.update_q_value.assert_called_once()

        # Verify Bellman equation applied
        call_args = mock_db_manager.update_q_value.call_args
        new_q_value = call_args[0][2]  # Third argument is new Q-value

        # new_q = old_q + alpha * (reward + gamma * max_next_q - old_q)
        # new_q = 0.5 + 0.1 * (10.0 + 0.95 * 0.8 - 0.5)
        # new_q = 0.5 + 0.1 * (10.0 + 0.76 - 0.5)
        # new_q = 0.5 + 0.1 * 10.26 = 0.5 + 1.026 = 1.526
        expected_q = 0.5 + 0.1 * (10.0 + 0.95 * 0.8 - 0.5)
        assert abs(new_q_value - expected_q) < 0.01

    @pytest.mark.asyncio
    async def test_update_q_value_increases_with_positive_reward(self, mock_db_manager):
        """Test Q-value increases with positive reward"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            alpha=0.1,
            gamma=0.95
        )

        initial_q = 0.5
        mock_db_manager.get_q_value = AsyncMock(return_value=initial_q)
        mock_db_manager.get_max_q_value = AsyncMock(return_value=0.6)
        mock_db_manager.update_q_value = AsyncMock()

        await service.update_q_value("state", 1, 10.0, "next_state")

        # Get new Q-value from call
        new_q = mock_db_manager.update_q_value.call_args[0][2]

        # Should increase with positive reward
        assert new_q > initial_q

    @pytest.mark.asyncio
    async def test_update_q_value_decreases_with_negative_reward(self, mock_db_manager):
        """Test Q-value decreases with negative reward"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            alpha=0.1,
            gamma=0.95
        )

        initial_q = 0.5
        mock_db_manager.get_q_value = AsyncMock(return_value=initial_q)
        mock_db_manager.get_max_q_value = AsyncMock(return_value=0.4)
        mock_db_manager.update_q_value = AsyncMock()

        await service.update_q_value("state", 1, -10.0, "next_state")

        new_q = mock_db_manager.update_q_value.call_args[0][2]

        # Should decrease with negative reward
        assert new_q < initial_q

    @pytest.mark.asyncio
    async def test_update_q_value_terminal_state(self, mock_db_manager):
        """Test Q-value update for terminal state (no next state)"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            alpha=0.1,
            gamma=0.95
        )

        mock_db_manager.get_q_value = AsyncMock(return_value=0.5)
        mock_db_manager.update_q_value = AsyncMock()

        await service.update_q_value("state", 1, 10.0, None, done=True)

        # Terminal state: new_q = old_q + alpha * (reward - old_q)
        new_q = mock_db_manager.update_q_value.call_args[0][2]
        expected_q = 0.5 + 0.1 * (10.0 - 0.5)
        assert abs(new_q - expected_q) < 0.01

    @pytest.mark.asyncio
    async def test_update_q_value_learning_rate_effect(self, mock_db_manager):
        """Test learning rate affects update magnitude"""
        # Small learning rate
        small_alpha = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            alpha=0.01,
            gamma=0.95
        )

        # Large learning rate
        large_alpha = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            alpha=0.5,
            gamma=0.95
        )

        mock_db_manager.get_q_value = AsyncMock(return_value=0.5)
        mock_db_manager.get_max_q_value = AsyncMock(return_value=0.8)
        mock_db_manager.update_q_value = AsyncMock()

        await small_alpha.update_q_value("state", 1, 10.0, "next")
        small_q = mock_db_manager.update_q_value.call_args[0][2]

        await large_alpha.update_q_value("state", 1, 10.0, "next")
        large_q = mock_db_manager.update_q_value.call_args[0][2]

        # Large alpha should change Q-value more
        small_change = abs(small_q - 0.5)
        large_change = abs(large_q - 0.5)
        assert large_change > small_change


class TestQTableOperations:
    """Test Q-table operations"""

    @pytest.mark.asyncio
    async def test_get_q_value(self, mock_db_manager):
        """Test retrieving Q-value for state-action pair"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager
        )

        mock_db_manager.get_q_value = AsyncMock(return_value=0.75)

        q_value = await service.get_q_value("state1", 2)

        assert q_value == 0.75
        mock_db_manager.get_q_value.assert_called_once_with("test-agent", "state1", 2)

    @pytest.mark.asyncio
    async def test_get_q_value_new_state(self, mock_db_manager):
        """Test Q-value for new state-action returns default"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager
        )

        mock_db_manager.get_q_value = AsyncMock(return_value=0.0)  # Default

        q_value = await service.get_q_value("new_state", 1)

        assert q_value == 0.0

    @pytest.mark.asyncio
    async def test_get_best_action(self, mock_db_manager):
        """Test retrieving best action for state"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager
        )

        mock_db_manager.get_best_action = AsyncMock(return_value=2)

        best_action = await service.get_best_action("state1", num_actions=5)

        assert best_action == 2
        mock_db_manager.get_best_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_max_q_value(self, mock_db_manager):
        """Test retrieving maximum Q-value for state"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager
        )

        mock_db_manager.get_max_q_value = AsyncMock(return_value=0.9)

        max_q = await service.get_max_q_value("state1", num_actions=5)

        assert max_q == 0.9
        mock_db_manager.get_max_q_value.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_q_table(self, mock_db_manager):
        """Test Q-table initialization for agent"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager
        )

        mock_db_manager.initialize_q_table = AsyncMock()

        await service.initialize()

        mock_db_manager.initialize_q_table.assert_called_once_with("test-agent")


class TestEpsilonDecay:
    """Test epsilon decay strategies"""

    @pytest.mark.asyncio
    async def test_decay_epsilon_exponential(self, mock_db_manager):
        """Test exponential epsilon decay"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            epsilon=0.5,
            min_epsilon=0.01,
            epsilon_decay=0.99
        )

        initial_epsilon = service.epsilon

        # Decay several times
        for _ in range(10):
            service.decay_epsilon()

        # Should decrease
        assert service.epsilon < initial_epsilon

        # Should not go below minimum
        for _ in range(1000):
            service.decay_epsilon()

        assert service.epsilon >= 0.01

    @pytest.mark.asyncio
    async def test_decay_epsilon_reward_based(self, mock_db_manager):
        """Test reward-based epsilon decay (RBED)"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            epsilon=0.5,
            epsilon_strategy="reward_based"
        )

        initial_epsilon = service.epsilon

        # High rewards should decrease exploration
        for _ in range(5):
            service.decay_epsilon(reward=10.0)

        assert service.epsilon < initial_epsilon

        # Low rewards should increase exploration
        service.epsilon = 0.1
        service.decay_epsilon(reward=-5.0)

        assert service.epsilon > 0.1

    @pytest.mark.asyncio
    async def test_epsilon_bounds(self, mock_db_manager):
        """Test epsilon stays within bounds"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            epsilon=0.5,
            min_epsilon=0.01,
            max_epsilon=1.0
        )

        # Decay many times
        for _ in range(1000):
            service.decay_epsilon()

        # Should be within bounds
        assert 0.01 <= service.epsilon <= 1.0


class TestExperienceReplay:
    """Test experience replay functionality"""

    @pytest.mark.asyncio
    async def test_store_experience(self, mock_db_manager, sample_trajectory):
        """Test storing experience in replay buffer"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager
        )

        mock_db_manager.store_experience = AsyncMock()

        await service.store_experience(
            sample_trajectory["state"],
            sample_trajectory["action"],
            sample_trajectory["reward"],
            sample_trajectory["next_state"],
            sample_trajectory["done"]
        )

        mock_db_manager.store_experience.assert_called_once()

    @pytest.mark.asyncio
    async def test_sample_experiences(self, mock_db_manager, sample_experiences):
        """Test sampling experiences from replay buffer"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager
        )

        mock_db_manager.sample_experiences = AsyncMock(return_value=sample_experiences)

        experiences = await service.sample_experiences(batch_size=32)

        assert len(experiences) == len(sample_experiences)
        mock_db_manager.sample_experiences.assert_called_once_with("test-agent", 32)

    @pytest.mark.asyncio
    async def test_replay_experiences(self, mock_db_manager, sample_experiences):
        """Test replaying sampled experiences for learning"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            alpha=0.1,
            gamma=0.95
        )

        mock_db_manager.sample_experiences = AsyncMock(return_value=sample_experiences)
        mock_db_manager.get_q_value = AsyncMock(return_value=0.5)
        mock_db_manager.get_max_q_value = AsyncMock(return_value=0.7)
        mock_db_manager.update_q_value = AsyncMock()

        await service.replay_experiences(batch_size=3)

        # Should update Q-values for each experience
        assert mock_db_manager.update_q_value.call_count == len(sample_experiences)


class TestConcurrentAgents:
    """Test Q-learning with multiple agents concurrently"""

    @pytest.mark.asyncio
    async def test_multiple_agents_concurrent_updates(self, mock_db_manager):
        """Test multiple agents can update Q-values concurrently"""
        agents = [
            QLearningService(f"agent-{i}", mock_db_manager)
            for i in range(5)
        ]

        # Mock DB operations
        mock_db_manager.get_q_value = AsyncMock(return_value=0.5)
        mock_db_manager.get_max_q_value = AsyncMock(return_value=0.7)
        mock_db_manager.update_q_value = AsyncMock()

        # Update concurrently
        updates = [
            agent.update_q_value(f"state_{i}", i % 3, 10.0, f"next_{i}")
            for i, agent in enumerate(agents)
        ]

        await asyncio.gather(*updates)

        # All updates should complete
        assert mock_db_manager.update_q_value.call_count == 5

    @pytest.mark.asyncio
    async def test_multiple_agents_independent_epsilon(self, mock_db_manager):
        """Test agents maintain independent epsilon values"""
        agent1 = QLearningService("agent-1", mock_db_manager, epsilon=0.5)
        agent2 = QLearningService("agent-2", mock_db_manager, epsilon=0.2)

        # Decay agent1 epsilon
        for _ in range(10):
            agent1.decay_epsilon()

        # Agent2 epsilon should be unchanged
        assert agent2.epsilon == 0.2

    @pytest.mark.asyncio
    async def test_agents_share_q_table(self, mock_db_manager):
        """Test agents can share Q-table through database"""
        agent1 = QLearningService("agent-1", mock_db_manager)
        agent2 = QLearningService("agent-1", mock_db_manager)  # Same agent_id

        # Both should access same Q-values
        mock_db_manager.get_q_value = AsyncMock(return_value=0.8)

        q1 = await agent1.get_q_value("state", 1)
        q2 = await agent2.get_q_value("state", 1)

        assert q1 == q2 == 0.8


class TestLearningMetrics:
    """Test learning metrics and monitoring"""

    @pytest.mark.asyncio
    async def test_track_update_count(self, mock_db_manager):
        """Test tracking number of Q-value updates"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager
        )

        mock_db_manager.get_q_value = AsyncMock(return_value=0.5)
        mock_db_manager.get_max_q_value = AsyncMock(return_value=0.7)
        mock_db_manager.update_q_value = AsyncMock()

        initial_count = service.update_count

        # Perform updates
        for i in range(10):
            await service.update_q_value(f"state_{i}", i % 3, 5.0, f"next_{i}")

        assert service.update_count == initial_count + 10

    @pytest.mark.asyncio
    async def test_track_exploration_rate(self, mock_db_manager):
        """Test tracking exploration vs exploitation rate"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager,
            epsilon=0.2
        )

        mock_db_manager.get_best_action = AsyncMock(return_value=1)

        # Select many actions
        for _ in range(100):
            await service.select_action("state", num_actions=3)

        exploration_rate = service.get_exploration_rate()

        # Should be close to epsilon (0.2)
        assert 0.1 < exploration_rate < 0.3

    @pytest.mark.asyncio
    async def test_get_learning_stats(self, mock_db_manager):
        """Test retrieving learning statistics"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager
        )

        stats = await service.get_learning_stats()

        assert "agent_id" in stats
        assert "epsilon" in stats
        assert "update_count" in stats
        assert "exploration_count" in stats
        assert stats["agent_id"] == "test-agent"


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_update_with_nan_reward(self, mock_db_manager):
        """Test handling NaN reward"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager
        )

        mock_db_manager.get_q_value = AsyncMock(return_value=0.5)

        # Should handle gracefully (skip or use 0)
        try:
            await service.update_q_value("state", 1, float('nan'), "next")
        except ValueError:
            pass  # Expected to raise error or handle gracefully

    @pytest.mark.asyncio
    async def test_update_with_infinite_reward(self, mock_db_manager):
        """Test handling infinite reward"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager
        )

        mock_db_manager.get_q_value = AsyncMock(return_value=0.5)

        # Should handle gracefully (clip or error)
        try:
            await service.update_q_value("state", 1, float('inf'), "next")
        except (ValueError, OverflowError):
            pass  # Expected to raise error or handle gracefully

    @pytest.mark.asyncio
    async def test_select_action_zero_actions(self, mock_db_manager):
        """Test handling zero available actions"""
        service = QLearningService(
            agent_id="test-agent",
            db_manager=mock_db_manager
        )

        with pytest.raises(ValueError):
            await service.select_action("state", num_actions=0)

    @pytest.mark.asyncio
    async def test_negative_learning_rate(self, mock_db_manager):
        """Test handling negative learning rate"""
        with pytest.raises(ValueError):
            QLearningService(
                agent_id="test-agent",
                db_manager=mock_db_manager,
                alpha=-0.1
            )

    @pytest.mark.asyncio
    async def test_learning_rate_over_1(self, mock_db_manager):
        """Test handling learning rate > 1"""
        with pytest.raises(ValueError):
            QLearningService(
                agent_id="test-agent",
                db_manager=mock_db_manager,
                alpha=1.5
            )
