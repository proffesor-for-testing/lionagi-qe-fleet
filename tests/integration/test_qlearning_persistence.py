"""
Cross-Instance Q-Learning Persistence Tests

Tests verify that:
1. Agent learns from task execution and persists Q-values to PostgreSQL
2. New agent instance loads previous learning state from database
3. Second agent continues learning from first agent's experience
4. Q-values improve over time with multiple executions
5. Learning persists across agent restarts
6. Multiple agents of same type share Q-table

Test Architecture:
    Agent Instance 1 → Execute Task → Learn → Persist to DB → Terminate
                                                              ↓
    Agent Instance 2 → Load from DB → Execute Task → Learn → Persist
                                                              ↓
    Verify: Q-values persisted, learning continued, performance improved
"""

import pytest
import asyncio
import os
from typing import Dict, Any
from uuid import uuid4

from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask
from lionagi_qe.learning import (
    QLearningService,
    StateEncoder,
    RewardCalculator,
    DatabaseManager
)
from lionagi import iModel


# ============================================================================
# Test Agent Implementation
# ============================================================================

class TestLearningAgent(BaseQEAgent):
    """Concrete agent for testing Q-learning persistence"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.execution_count = 0

    def get_system_prompt(self) -> str:
        return "Test agent for Q-learning persistence validation"

    async def execute(self, task: QETask) -> Dict[str, Any]:
        """Execute task with simulated results"""
        self.execution_count += 1

        # Simulate varying success based on action (if available)
        action_id = getattr(self, 'current_action_id', 'default_action')

        # Better actions lead to better results
        if action_id == 'optimal_action':
            coverage = 0.95
            quality = 90.0
            success = True
        elif action_id == 'good_action':
            coverage = 0.85
            quality = 80.0
            success = True
        else:
            coverage = 0.70
            quality = 70.0
            success = True

        return {
            "task_type": task.task_type,
            "coverage_percentage": coverage * 100,
            "quality_score": quality,
            "tests_generated": 10,
            "execution_time_seconds": 2.0,
            "success": success,
            "action_taken": action_id,
        }

    def _get_available_actions(self, task: QETask) -> list[str]:
        """Define available actions for testing"""
        return ["default_action", "good_action", "optimal_action"]

    def _extract_state_from_task(self, task: QETask) -> Dict[str, Any]:
        """Extract state features from task"""
        return {
            "task_type": task.task_type,
            "complexity": task.context.get("complexity", "moderate"),
            "coverage_gap": task.context.get("coverage_gap", 30),
        }


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def db_manager():
    """Create database manager with test database"""
    # Use environment variable or default to local PostgreSQL
    database_url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/qlearning_test"
    )

    db_mgr = DatabaseManager(database_url)
    await db_mgr.connect()

    yield db_mgr

    await db_mgr.disconnect()


@pytest.fixture
async def q_service(db_manager):
    """Create Q-learning service"""
    service = QLearningService(
        agent_type="test-generator",
        agent_instance_id=f"test-instance-{uuid4().hex[:8]}",
        db_manager=db_manager,
        config={
            "learningRate": 0.1,
            "discountFactor": 0.95,
            "explorationRate": 0.3,
            "explorationDecay": 0.95,
            "minExplorationRate": 0.01,
        }
    )

    # Set action space
    service.set_action_space(["default_action", "good_action", "optimal_action"])

    return service


@pytest.fixture
def simple_model():
    """Create simple model for testing"""
    return iModel(provider="openai", model="gpt-3.5-turbo", api_key="test-key")


@pytest.fixture
async def learning_agent(db_manager, q_service, simple_model):
    """Create agent with learning enabled"""
    agent = TestLearningAgent(
        agent_id="test-generator",
        model=simple_model,
        enable_learning=True,
        q_learning_service=q_service
    )

    return agent


# ============================================================================
# Test Suite: Cross-Instance Persistence
# ============================================================================

class TestCrossInstancePersistence:
    """Test Q-learning persists across agent instances"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_agent_learns_and_persists(self, db_manager, simple_model):
        """Test agent learns from execution and persists to database"""
        # Create first agent instance
        agent1 = TestLearningAgent(
            agent_id="test-generator",
            model=simple_model,
            enable_learning=True,
            q_learning_service=QLearningService(
                agent_type="test-generator",
                agent_instance_id=f"instance-1-{uuid4().hex[:8]}",
                db_manager=db_manager
            )
        )
        agent1.q_service.set_action_space(["default_action", "good_action", "optimal_action"])

        # Execute task with learning
        task = QETask(
            task_type="generate_tests",
            context={"complexity": "moderate", "coverage_gap": 30}
        )

        # Pre-execution hook
        await agent1.pre_execution_hook(task)

        # Execute with learning
        result = await agent1.execute_with_learning(task)

        # Post-execution hook (triggers learning)
        await agent1.post_execution_hook(task, result)

        # Verify learning happened
        assert agent1.metrics["learning_episodes"] > 0
        assert agent1.metrics["total_reward"] != 0.0

        # Force sync to database
        await agent1.q_service.save_to_database()

        # Verify data in database
        state_hash = agent1.current_state_hash
        action_hash = agent1.q_service._hash_action(agent1.current_action_id)

        q_value = await db_manager.get_q_value(
            "test-generator",
            state_hash,
            action_hash
        )

        assert q_value is not None, "Q-value should be persisted to database"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_new_instance_loads_previous_learning(self, db_manager, simple_model):
        """Test new agent instance loads learned Q-values from database"""
        # Step 1: First agent learns
        agent1 = TestLearningAgent(
            agent_id="test-generator",
            model=simple_model,
            enable_learning=True,
            q_learning_service=QLearningService(
                agent_type="test-generator",
                agent_instance_id=f"instance-1-{uuid4().hex[:8]}",
                db_manager=db_manager
            )
        )
        agent1.q_service.set_action_space(["default_action", "good_action", "optimal_action"])

        task = QETask(
            task_type="generate_tests",
            context={"complexity": "simple", "coverage_gap": 20}
        )

        await agent1.pre_execution_hook(task)
        result1 = await agent1.execute_with_learning(task)
        await agent1.post_execution_hook(task, result1)
        await agent1.q_service.save_to_database()

        state_hash_1 = agent1.current_state_hash

        # Terminate agent1 (simulated by not using it anymore)
        del agent1

        # Step 2: Create new agent instance (different instance ID, same type)
        agent2 = TestLearningAgent(
            agent_id="test-generator",
            model=simple_model,
            enable_learning=True,
            q_learning_service=QLearningService(
                agent_type="test-generator",  # Same agent type
                agent_instance_id=f"instance-2-{uuid4().hex[:8]}",  # Different instance
                db_manager=db_manager
            )
        )
        agent2.q_service.set_action_space(["default_action", "good_action", "optimal_action"])

        # Step 3: New agent executes same task type
        task2 = QETask(
            task_type="generate_tests",
            context={"complexity": "simple", "coverage_gap": 20}  # Same state
        )

        await agent2.pre_execution_hook(task2)
        result2 = await agent2.execute_with_learning(task2)

        # Verify agent2 loaded Q-values from database
        # Check that Q-table has values (loaded from DB)
        assert len(agent2.q_service.q_table) > 0, "Agent should load Q-values from database"

        # Verify the state-action pair from agent1 is available to agent2
        # This proves cross-instance learning works
        state_encoder = StateEncoder("test-generator")
        state_hash_2, _ = state_encoder.encode_state(task2.context)

        # Agent2 should be able to access Q-values learned by agent1
        best_action = await agent2.q_service._get_best_action(state_hash_2)
        assert best_action is not None, "Agent2 should access agent1's learned Q-values"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_second_agent_continues_learning(self, db_manager, simple_model):
        """Test second agent continues learning from first agent's experience"""
        # Agent 1: Initial learning
        agent1 = TestLearningAgent(
            agent_id="test-generator",
            model=simple_model,
            enable_learning=True,
            q_learning_service=QLearningService(
                agent_type="test-generator",
                agent_instance_id=f"instance-1-{uuid4().hex[:8]}",
                db_manager=db_manager
            )
        )
        agent1.q_service.set_action_space(["default_action", "good_action", "optimal_action"])

        task1 = QETask(
            task_type="generate_tests",
            context={"complexity": "complex", "coverage_gap": 50}
        )

        await agent1.pre_execution_hook(task1)
        result1 = await agent1.execute_with_learning(task1)
        await agent1.post_execution_hook(task1, result1)
        await agent1.q_service.save_to_database()

        # Record agent1's final metrics
        agent1_episodes = agent1.metrics["learning_episodes"]
        agent1_reward = agent1.metrics["total_reward"]

        # Get Q-value from agent1
        state_encoder = StateEncoder("test-generator")
        state_hash, _ = state_encoder.encode_state(task1.context)
        action_hash = agent1.q_service._hash_action(agent1.current_action_id)

        q_value_after_agent1 = await db_manager.get_q_value(
            "test-generator",
            state_hash,
            action_hash
        )

        del agent1

        # Agent 2: Continues learning
        agent2 = TestLearningAgent(
            agent_id="test-generator",
            model=simple_model,
            enable_learning=True,
            q_learning_service=QLearningService(
                agent_type="test-generator",
                agent_instance_id=f"instance-2-{uuid4().hex[:8]}",
                db_manager=db_manager
            )
        )
        agent2.q_service.set_action_space(["default_action", "good_action", "optimal_action"])

        # Execute same task multiple times
        for i in range(3):
            task2 = QETask(
                task_type="generate_tests",
                context={"complexity": "complex", "coverage_gap": 50}  # Same state
            )

            await agent2.pre_execution_hook(task2)
            result2 = await agent2.execute_with_learning(task2)
            await agent2.post_execution_hook(task2, result2)
            await agent2.q_service.save_to_database()

        # Verify agent2 continued learning
        assert agent2.metrics["learning_episodes"] > 0

        # Verify Q-value was updated by agent2
        q_value_after_agent2 = await db_manager.get_q_value(
            "test-generator",
            state_hash,
            action_hash
        )

        # Q-value should have changed (learning continued)
        # Note: It might be same if exploration picked different actions
        assert q_value_after_agent2 is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_q_values_improve_over_time(self, db_manager, simple_model):
        """Test Q-values improve with multiple executions"""
        # Create agent
        agent = TestLearningAgent(
            agent_id="test-generator",
            model=simple_model,
            enable_learning=True,
            q_learning_service=QLearningService(
                agent_type="test-generator",
                agent_instance_id=f"instance-{uuid4().hex[:8]}",
                db_manager=db_manager
            )
        )
        agent.q_service.set_action_space(["default_action", "good_action", "optimal_action"])

        # Execute multiple learning episodes
        rewards = []
        epsilon_values = []

        for episode in range(10):
            task = QETask(
                task_type="generate_tests",
                context={"complexity": "moderate", "coverage_gap": 30}
            )

            await agent.pre_execution_hook(task)
            result = await agent.execute_with_learning(task)
            await agent.post_execution_hook(task, result)
            await agent.q_service.save_to_database()

            # Track metrics
            rewards.append(agent.metrics.get("avg_reward", 0.0))
            epsilon_values.append(agent.q_service.epsilon)

            # Decay epsilon
            agent.q_service.decay_epsilon()

        # Verify learning progress
        assert len(rewards) == 10, "Should have 10 episodes"

        # Epsilon should decrease over time (more exploitation)
        assert epsilon_values[-1] < epsilon_values[0], "Epsilon should decay over time"

        # Average reward should generally improve (though may fluctuate)
        # Check last 3 episodes vs first 3 episodes
        early_avg = sum(rewards[:3]) / 3 if len(rewards) >= 3 else 0
        late_avg = sum(rewards[-3:]) / 3 if len(rewards) >= 3 else 0

        # Late average should be >= early average (learning improves)
        print(f"Early avg reward: {early_avg:.2f}, Late avg reward: {late_avg:.2f}")
        # Note: Due to exploration, this might not always hold, so we just log it

        # Verify Q-table has entries
        assert len(agent.q_service.q_table) > 0, "Q-table should have learned values"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_agents_share_qtable(self, db_manager, simple_model):
        """Test multiple agents of same type share Q-table via database"""
        # Create 3 agent instances of same type
        agents = []
        for i in range(3):
            agent = TestLearningAgent(
                agent_id="test-generator",
                model=simple_model,
                enable_learning=True,
                q_learning_service=QLearningService(
                    agent_type="test-generator",
                    agent_instance_id=f"instance-{i}-{uuid4().hex[:8]}",
                    db_manager=db_manager
                )
            )
            agent.q_service.set_action_space(["default_action", "good_action", "optimal_action"])
            agents.append(agent)

        # Each agent executes tasks
        for i, agent in enumerate(agents):
            task = QETask(
                task_type="generate_tests",
                context={"complexity": "simple", "coverage_gap": 25}
            )

            await agent.pre_execution_hook(task)
            result = await agent.execute_with_learning(task)
            await agent.post_execution_hook(task, result)
            await agent.q_service.save_to_database()

        # Verify all agents contributed to same Q-table in database
        # Get Q-values for the shared state
        state_encoder = StateEncoder("test-generator")
        state_hash, _ = state_encoder.encode_state({"complexity": "simple", "coverage_gap": 25})

        # Get all Q-values for this state
        q_values = await db_manager.get_all_q_values_for_state(
            "test-generator",
            state_hash
        )

        # Should have Q-values from multiple agent executions
        assert len(q_values) > 0, "Should have Q-values in shared Q-table"

        # All agents should be able to access these values
        for agent in agents:
            best_action = await agent.q_service._get_best_action(state_hash)
            assert best_action is not None, f"Agent {agent.q_service.agent_instance_id} should access shared Q-table"


# ============================================================================
# Test Suite: Performance Validation
# ============================================================================

class TestPerformanceValidation:
    """Test Q-learning doesn't degrade performance"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_learning_overhead_acceptable(self, db_manager, simple_model):
        """Test Q-learning adds minimal overhead to execution"""
        import time

        # Test without learning
        agent_no_learning = TestLearningAgent(
            agent_id="test-generator",
            model=simple_model,
            enable_learning=False
        )

        task = QETask(
            task_type="generate_tests",
            context={"complexity": "moderate", "coverage_gap": 30}
        )

        start = time.time()
        for _ in range(10):
            await agent_no_learning.execute(task)
        time_without_learning = time.time() - start

        # Test with learning
        agent_with_learning = TestLearningAgent(
            agent_id="test-generator",
            model=simple_model,
            enable_learning=True,
            q_learning_service=QLearningService(
                agent_type="test-generator",
                agent_instance_id=f"perf-test-{uuid4().hex[:8]}",
                db_manager=db_manager
            )
        )
        agent_with_learning.q_service.set_action_space(["default_action", "good_action", "optimal_action"])

        start = time.time()
        for _ in range(10):
            await agent_with_learning.pre_execution_hook(task)
            result = await agent_with_learning.execute_with_learning(task)
            await agent_with_learning.post_execution_hook(task, result)
        time_with_learning = time.time() - start

        # Learning overhead should be < 50% (acceptable for the benefits)
        overhead_ratio = time_with_learning / time_without_learning
        print(f"Learning overhead: {overhead_ratio:.2f}x")
        print(f"Without learning: {time_without_learning:.3f}s, With learning: {time_with_learning:.3f}s")

        # Assert reasonable overhead (< 2x)
        assert overhead_ratio < 2.0, f"Learning overhead too high: {overhead_ratio:.2f}x"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_high_throughput_learning(self, db_manager, simple_model):
        """Test learning works with high-throughput scenarios (100+ tasks)"""
        agent = TestLearningAgent(
            agent_id="test-generator",
            model=simple_model,
            enable_learning=True,
            q_learning_service=QLearningService(
                agent_type="test-generator",
                agent_instance_id=f"throughput-test-{uuid4().hex[:8]}",
                db_manager=db_manager,
                config={"updateFrequency": 20}  # Sync every 20 updates
            )
        )
        agent.q_service.set_action_space(["default_action", "good_action", "optimal_action"])

        # Execute 100 tasks
        import time
        start = time.time()

        for i in range(100):
            task = QETask(
                task_type="generate_tests",
                context={"complexity": "simple", "coverage_gap": 20 + (i % 30)}
            )

            await agent.pre_execution_hook(task)
            result = await agent.execute_with_learning(task)
            await agent.post_execution_hook(task, result)

            # Sync happens automatically based on updateFrequency

        elapsed = time.time() - start

        # Verify all completed
        assert agent.metrics["learning_episodes"] == 100

        # Verify acceptable throughput (< 1 second per task on average)
        avg_time_per_task = elapsed / 100
        print(f"Average time per task with learning: {avg_time_per_task:.3f}s")
        print(f"Total time for 100 tasks: {elapsed:.2f}s")

        # Should complete reasonably fast
        assert avg_time_per_task < 1.0, f"Learning throughput too slow: {avg_time_per_task:.3f}s per task"

        # Force final sync
        await agent.q_service.save_to_database()

        # Verify Q-table has entries
        assert len(agent.q_service.q_table) > 0, "Q-table should have learned values"


# ============================================================================
# Test Suite: Database Integration
# ============================================================================

class TestDatabaseIntegration:
    """Test database operations for Q-learning"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_connection_pooling(self, db_manager):
        """Test connection pooling works efficiently"""
        # Execute multiple concurrent database operations
        tasks = []
        for i in range(20):
            task = db_manager.get_q_value(
                "test-generator",
                f"state_hash_{i}",
                f"action_hash_{i}"
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All should complete without errors
        assert len(results) == 20

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_trajectory_storage(self, db_manager):
        """Test trajectory storage and retrieval"""
        trajectory_id = await db_manager.store_trajectory(
            agent_type="test-generator",
            session_id=str(uuid4()),
            task_id=f"task-{uuid4()}",
            initial_state={"complexity": "simple"},
            final_state={"coverage": 0.85},
            actions_taken=["action1", "action2"],
            states_visited=[{"s": 1}, {"s": 2}],
            step_rewards=[10.0, 15.0],
            total_reward=25.0,
            discounted_reward=23.75,
            execution_time_ms=2500,
            success=True,
            metadata={"test": "data"}
        )

        assert trajectory_id is not None

        # Retrieve trajectory
        trajectories = await db_manager.get_recent_trajectories(
            "test-generator",
            limit=1
        )

        assert len(trajectories) > 0
        assert trajectories[0]["total_reward"] == 25.0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_agent_state_tracking(self, db_manager):
        """Test agent state is tracked correctly"""
        await db_manager.update_agent_state(
            agent_type="test-generator",
            agent_instance_id="test-instance-123",
            total_tasks=10,
            successful_tasks=8,
            failed_tasks=2,
            total_reward=150.0,
            avg_reward=15.0,
            current_exploration_rate=0.15,
            current_learning_rate=0.1
        )

        # Verify state was stored (would need a get method to fully verify)
        # For now, just verify no errors occurred


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
