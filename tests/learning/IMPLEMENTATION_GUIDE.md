# Q-Learning Implementation Guide

This guide shows how to implement the Q-Learning components to pass all 142 tests.

## Quick Start

The test suite provides **Test-Driven Development (TDD)** guidance. Implement components in this order:

1. StateEncoder (35 tests) - Easiest, pure functions
2. RewardCalculator (44 tests) - Pure functions with math
3. QLearningService (34 tests) - Core algorithm, requires DB
4. BaseQEAgent Integration (29 tests) - Full integration

## 1. StateEncoder Implementation

### Required Interface

```python
# src/lionagi_qe/learning/state_encoder.py

class StateEncoder:
    """Encodes task states for Q-learning"""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize encoder with optional configuration"""
        self.complexity_buckets = config.get("complexity_buckets", [10, 20, 40]) if config else [10, 20, 40]
        self.size_buckets = config.get("size_buckets", [100, 300, 600]) if config else [100, 300, 600]
        self.coverage_buckets = config.get("coverage_buckets", [0.5, 0.7, 0.9]) if config else [0.5, 0.7, 0.9]

    def encode(self, task: QETask) -> str:
        """
        Encode task into state string

        Tests expect: "test_gen_complexity_medium_coverage_high_pytest"
        """
        features = self.extract_features(task)

        task_type = features.get("task_type", "unknown")
        complexity = self.bucket_complexity(features.get("complexity", 0))
        coverage = self.bucket_coverage(features.get("coverage", 0.0))
        framework = features.get("framework", "unknown")

        state = f"{task_type}_complexity_{complexity}_coverage_{coverage}_{framework}"
        return state

    def extract_features(self, task: QETask) -> Dict[str, Any]:
        """
        Extract features from task context

        Tests expect:
        - task_type from task.task_type
        - complexity from context["complexity"] or 0
        - coverage from context["coverage"] or 0.0
        - framework from context["framework"] or "unknown"
        """
        context = task.context or {}

        return {
            "task_type": task.task_type,
            "complexity": int(context.get("complexity", 0) or 0),
            "coverage": float(context.get("coverage", 0.0) or 0.0),
            "framework": str(context.get("framework", "unknown") or "unknown")
        }

    def bucket_complexity(self, complexity: int) -> str:
        """Bucket complexity into categories"""
        if complexity < self.complexity_buckets[0]:
            return "low"
        elif complexity < self.complexity_buckets[1]:
            return "medium"
        elif complexity < self.complexity_buckets[2]:
            return "high"
        else:
            return "very_high"

    def bucket_size(self, size: int) -> str:
        """Bucket size into categories"""
        if size < self.size_buckets[0]:
            return "small"
        elif size < self.size_buckets[1]:
            return "medium"
        elif size < self.size_buckets[2]:
            return "large"
        else:
            return "very_large"

    def bucket_coverage(self, coverage: float) -> str:
        """Bucket coverage into categories"""
        coverage = max(0.0, min(1.0, coverage))  # Clamp to [0, 1]

        if coverage < self.coverage_buckets[0]:
            return "low"
        elif coverage < self.coverage_buckets[1]:
            return "medium"
        elif coverage < self.coverage_buckets[2]:
            return "high"
        else:
            return "full"

    def hash_state(self, state_str: str) -> str:
        """Hash state string for compact representation"""
        import hashlib
        return hashlib.sha256(state_str.encode()).hexdigest()
```

### Running StateEncoder Tests

```bash
pytest tests/learning/test_state_encoder.py -v
```

Expected: 35 passed

## 2. RewardCalculator Implementation

### Required Interface

```python
# src/lionagi_qe/learning/reward_calculator.py

class RewardCalculator:
    """Calculates rewards from task execution results"""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """Initialize with reward component weights"""
        self.weights = weights or {
            "coverage": 0.30,
            "quality": 0.25,
            "time": 0.15,
            "cost": 0.10,
            "improvement": 0.10,
            "reusability": 0.10
        }

    def calculate(self, result: Dict[str, Any]) -> float:
        """
        Calculate total reward from execution result

        Tests expect:
        - Positive reward for good results (>0)
        - Negative reward for failures (<0)
        - Weighted sum of all components
        """
        if result.get("failed", False):
            return self.failure_penalty()

        # Calculate individual components
        coverage = self.coverage_reward(
            result.get("coverage", 0.0),
            result.get("previous_coverage", 0.0)
        )

        quality = self.quality_reward(
            result.get("bugs_found", 0),
            result.get("false_positives", 0),
            result.get("edge_cases_covered", 0)
        )

        time = self.time_reward(result.get("execution_time", 1.0))

        pattern = self.pattern_bonus(result.get("patterns_reused", 0))

        cost = self.cost_reward(result.get("cost", 0.1))

        # Weighted sum
        total_reward = (
            self.weights.get("coverage", 0.3) * coverage +
            self.weights.get("quality", 0.25) * quality +
            self.weights.get("time", 0.15) * time +
            self.weights.get("reusability", 0.1) * pattern +
            self.weights.get("cost", 0.1) * cost
        )

        return total_reward

    def coverage_reward(self, current: float, previous: float) -> float:
        """Reward for coverage improvement"""
        improvement = current - previous

        if improvement > 0:
            reward = improvement * 10  # Scale up
            if current >= 1.0:
                reward += 5  # Bonus for full coverage
            return reward
        elif improvement < 0:
            return improvement * 10  # Penalty for regression
        else:
            return 0.0

    def quality_reward(self, bugs: int, false_positives: int, edge_cases: int) -> float:
        """Reward for test quality"""
        bugs = max(0, bugs)
        false_positives = max(0, false_positives)
        edge_cases = max(0, edge_cases)

        # Bugs found are good
        bug_reward = bugs * 2.0

        # False positives are bad
        fp_penalty = false_positives * -1.5

        # Edge cases are good
        edge_reward = edge_cases * 0.5

        # Precision bonus
        if bugs + false_positives > 0:
            precision = bugs / (bugs + false_positives)
            precision_bonus = precision * 2.0
        else:
            precision_bonus = 0.0

        return bug_reward + fp_penalty + edge_reward + precision_bonus

    def time_reward(self, execution_time: float) -> float:
        """Reward for fast execution (inverted)"""
        execution_time = max(0.001, execution_time)  # Avoid division by zero

        # Inverted: faster = higher reward
        if execution_time < 1.0:
            return 5.0  # Very fast
        elif execution_time < 5.0:
            return 10.0 / execution_time  # Fast
        elif execution_time < 60.0:
            return 5.0 / execution_time  # Moderate
        else:
            return -5.0  # Timeout penalty

    def pattern_bonus(self, patterns_reused: int) -> float:
        """Bonus for reusing learned patterns"""
        patterns_reused = max(0, patterns_reused)

        if patterns_reused == 0:
            return 0.0

        # Diminishing returns
        import math
        return 2.0 * math.log1p(patterns_reused)

    def cost_reward(self, cost: float) -> float:
        """Reward for cost efficiency"""
        cost = max(0.0, cost)

        if cost < 0.01:
            return 5.0  # Very cheap
        elif cost < 0.1:
            return 3.0  # Cheap
        elif cost < 1.0:
            return 1.0  # Moderate
        else:
            return -cost  # Expensive penalty

    def failure_penalty(self) -> float:
        """Penalty for task failure"""
        return -10.0
```

### Running RewardCalculator Tests

```bash
pytest tests/learning/test_reward_calculator.py -v
```

Expected: 44 passed

## 3. QLearningService Implementation

### Required Interface

```python
# src/lionagi_qe/learning/qlearner.py

import random
from typing import Optional

class QLearningService:
    """Q-learning service for agent learning"""

    def __init__(
        self,
        agent_id: str,
        db_manager,
        alpha: float = 0.1,
        gamma: float = 0.95,
        epsilon: float = 0.2,
        min_epsilon: float = 0.01,
        max_epsilon: float = 1.0,
        epsilon_decay: float = 0.995,
        epsilon_strategy: str = "exponential",
        config: Optional[Dict] = None
    ):
        """Initialize Q-learning service"""
        if alpha < 0 or alpha > 1:
            raise ValueError("Learning rate must be in [0, 1]")
        if gamma < 0 or gamma > 1:
            raise ValueError("Discount factor must be in [0, 1]")

        self.agent_id = agent_id
        self.db_manager = db_manager

        # Override with config if provided
        if config:
            alpha = config.get("learning_rate", alpha)
            gamma = config.get("discount_factor", gamma)
            epsilon = config.get("initial_epsilon", epsilon)

        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.min_epsilon = min_epsilon
        self.max_epsilon = max_epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_strategy = epsilon_strategy

        # Metrics
        self.update_count = 0
        self.exploration_count = 0

    async def initialize(self):
        """Initialize Q-table in database"""
        await self.db_manager.initialize_q_table(self.agent_id)

    async def select_action(self, state: str, num_actions: int = 5) -> int:
        """
        ε-greedy action selection

        Tests expect:
        - ε=1.0: Always random (exploration)
        - ε=0.0: Always best (exploitation)
        - ε=0.2: 80% best, 20% random
        """
        if num_actions <= 0:
            raise ValueError("Number of actions must be positive")

        # Epsilon-greedy
        if random.random() < self.epsilon:
            # Explore: random action
            self.exploration_count += 1
            return random.randint(0, num_actions - 1)
        else:
            # Exploit: best action
            return await self.get_best_action(state, num_actions)

    async def update_q_value(
        self,
        state: str,
        action: int,
        reward: float,
        next_state: Optional[str],
        done: bool = False
    ):
        """
        Update Q-value using Bellman equation

        Q(s,a) ← Q(s,a) + α[r + γ·max Q(s',a') - Q(s,a)]

        Tests expect:
        - Correct Bellman update
        - Terminal state handling (done=True)
        - Positive reward increases Q-value
        - Negative reward decreases Q-value
        """
        # Get current Q-value
        current_q = await self.get_q_value(state, action)

        if done or next_state is None:
            # Terminal state: Q(s,a) = r
            target = reward
        else:
            # Bellman equation
            max_next_q = await self.get_max_q_value(next_state, num_actions=5)
            target = reward + self.gamma * max_next_q

        # Update: Q(s,a) ← Q(s,a) + α[target - Q(s,a)]
        new_q = current_q + self.alpha * (target - current_q)

        # Store in database
        await self.db_manager.update_q_value(self.agent_id, state, action, new_q)

        self.update_count += 1

    async def get_q_value(self, state: str, action: int) -> float:
        """Get Q-value for state-action pair"""
        return await self.db_manager.get_q_value(self.agent_id, state, action)

    async def get_best_action(self, state: str, num_actions: int) -> int:
        """Get action with highest Q-value"""
        return await self.db_manager.get_best_action(self.agent_id, state, num_actions)

    async def get_max_q_value(self, state: str, num_actions: int) -> float:
        """Get maximum Q-value for state"""
        return await self.db_manager.get_max_q_value(self.agent_id, state, num_actions)

    def decay_epsilon(self, reward: Optional[float] = None):
        """
        Decay epsilon for exploration/exploitation balance

        Tests expect:
        - Exponential: ε ← ε * decay_rate
        - Reward-based: ε increases on low reward, decreases on high reward
        - Respects min/max bounds
        """
        if self.epsilon_strategy == "exponential":
            self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        elif self.epsilon_strategy == "reward_based" and reward is not None:
            # RBED: Reward-Based Epsilon Decay
            if reward < 0:
                # Increase exploration on bad rewards
                self.epsilon = min(self.max_epsilon, self.epsilon * 1.05)
            else:
                # Decrease exploration on good rewards
                self.epsilon = max(self.min_epsilon, self.epsilon * 0.95)

    async def store_experience(
        self,
        state: str,
        action: int,
        reward: float,
        next_state: str,
        done: bool
    ):
        """Store experience in replay buffer"""
        await self.db_manager.store_experience(
            self.agent_id, state, action, reward, next_state, done
        )

    async def sample_experiences(self, batch_size: int = 32):
        """Sample experiences from replay buffer"""
        return await self.db_manager.sample_experiences(self.agent_id, batch_size)

    async def replay_experiences(self, batch_size: int = 32):
        """
        Replay sampled experiences for learning

        Tests expect:
        - Sample batch_size experiences
        - Update Q-value for each experience
        """
        experiences = await self.sample_experiences(batch_size)

        for exp in experiences:
            await self.update_q_value(
                exp["state"],
                exp["action"],
                exp["reward"],
                exp["next_state"],
                exp["done"]
            )

    def get_exploration_rate(self) -> float:
        """Get current exploration rate"""
        total = self.update_count + self.exploration_count
        if total == 0:
            return 0.0
        return self.exploration_count / total

    async def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return {
            "agent_id": self.agent_id,
            "epsilon": self.epsilon,
            "update_count": self.update_count,
            "exploration_count": self.exploration_count,
            "exploration_rate": self.get_exploration_rate()
        }
```

### Running QLearningService Tests

```bash
pytest tests/learning/test_qlearner.py -v
```

Expected: 34 passed

## 4. BaseQEAgent Integration

### Required Modifications

```python
# src/lionagi_qe/core/base_agent.py

from lionagi_qe.learning import QLearningService, StateEncoder, RewardCalculator

class BaseQEAgent:
    def __init__(
        self,
        agent_id: str,
        model: iModel,
        memory: QEMemory,
        skills: List[str] = None,
        enable_learning: bool = False  # NEW
    ):
        self.agent_id = agent_id
        self.model = model
        self.memory = memory
        self.skills = skills or []
        self.enable_learning = enable_learning  # NEW

        # Initialize Q-learning if enabled
        if self.enable_learning:
            self.state_encoder = StateEncoder()
            self.reward_calculator = RewardCalculator()
            self.q_service = QLearningService(
                agent_id=agent_id,
                db_manager=get_db_manager(),  # Get from dependency injection
                alpha=0.1,
                gamma=0.95,
                epsilon=0.2
            )
        else:
            self.q_service = None

        # Rest of initialization...

    async def execute_with_learning(self, task: QETask) -> Dict[str, Any]:
        """
        Execute task with Q-learning integration

        Tests expect:
        1. Encode task state
        2. Select action (ε-greedy)
        3. Execute task
        4. Calculate reward
        5. Update Q-value
        6. Store trajectory
        7. Return result + learning metrics
        """
        if not self.enable_learning or not self.q_service:
            # Fallback to regular execution
            result = await self.execute(task)
            return {"result": result, "learning": {}}

        # 1. Encode state
        state = self.state_encoder.encode(task)

        # 2. Select action
        action = await self.q_service.select_action(state, num_actions=5)

        # 3. Execute task
        result = await self.execute(task)

        # 4. Calculate reward
        reward = self.reward_calculator.calculate(result)

        # 5. Encode next state (after execution)
        # Simulate next state with updated coverage
        next_task_context = task.context.copy()
        next_task_context["coverage"] = result.get("coverage", 0.0)
        next_task = QETask(task_type=task.task_type, context=next_task_context)
        next_state = self.state_encoder.encode(next_task)

        # 6. Update Q-value
        await self.q_service.update_q_value(
            state, action, reward, next_state, done=False
        )

        # 7. Store trajectory
        await self._store_trajectory(task, state, action, reward, next_state, result)

        # 8. Decay epsilon
        self.q_service.decay_epsilon(reward)

        # Return result with learning metrics
        return {
            "result": result,
            "learning": {
                "state": state,
                "action_selected": action,
                "reward": reward,
                "next_state": next_state,
                "epsilon": self.q_service.epsilon
            }
        }

    async def _store_trajectory(
        self,
        task: QETask,
        state: str,
        action: int,
        reward: float,
        next_state: str,
        result: Dict
    ):
        """Store learning trajectory in memory"""
        from datetime import datetime

        trajectory = {
            "agent_id": self.agent_id,
            "task_id": task.task_id,
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "timestamp": datetime.now().isoformat(),
            "result": result
        }

        trajectory_key = f"aqe/{self.agent_id}/learning/trajectories/{task.task_id}"
        await self.memory.store(trajectory_key, trajectory)
```

### Running Integration Tests

```bash
pytest tests/learning/test_base_agent_integration.py -v
```

Expected: 29 passed

## 5. Database Manager (Optional)

For real PostgreSQL integration:

```python
# src/lionagi_qe/learning/db_manager.py

import asyncpg

class DatabaseManager:
    """Database manager for Q-learning persistence"""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None

    async def initialize(self):
        """Initialize connection pool"""
        self.pool = await asyncpg.create_pool(self.db_url)
        await self._create_tables()

    async def _create_tables(self):
        """Create Q-learning tables"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS q_values (
                    agent_id TEXT,
                    state TEXT,
                    action INTEGER,
                    q_value REAL,
                    visits INTEGER DEFAULT 1,
                    version INTEGER DEFAULT 1,
                    PRIMARY KEY (agent_id, state, action)
                )
            """)

    async def get_q_value(self, agent_id: str, state: str, action: int) -> float:
        """Get Q-value for state-action pair"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT q_value FROM q_values WHERE agent_id=$1 AND state=$2 AND action=$3",
                agent_id, state, action
            )
            return row["q_value"] if row else 0.0

    async def update_q_value(self, agent_id: str, state: str, action: int, q_value: float):
        """Update Q-value"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO q_values (agent_id, state, action, q_value, visits)
                VALUES ($1, $2, $3, $4, 1)
                ON CONFLICT (agent_id, state, action)
                DO UPDATE SET
                    q_value = $4,
                    visits = q_values.visits + 1,
                    version = q_values.version + 1
            """, agent_id, state, action, q_value)

    # ... other methods
```

## Running All Tests

```bash
# Run all Q-learning tests
pytest tests/learning/ -v

# Run with coverage
pytest tests/learning/ --cov=lionagi_qe.learning --cov-report=html

# Run specific component
pytest tests/learning/test_state_encoder.py -v

# Run with print output
pytest tests/learning/ -v -s
```

## Expected Output

```
tests/learning/test_state_encoder.py::TestStateEncoder::test_init PASSED [ 0%]
tests/learning/test_state_encoder.py::TestStateEncoder::test_init_with_custom_config PASSED [ 1%]
...
tests/learning/test_base_agent_integration.py::TestLearningLifecycle::test_learning_improves_over_time PASSED [100%]

====== 142 passed in 30.45s ======

Coverage: 95% for lionagi_qe.learning
```

## Troubleshooting

### Test Failures

1. **Import Errors**: Ensure `PYTHONPATH` includes project root
2. **Async Errors**: Check `conftest.py` has event_loop fixture
3. **Mock Errors**: Install `pytest-mock`
4. **Database Errors**: Use mocked DB manager for unit tests

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'lionagi_qe.learning'`
**Solution**: Create `src/lionagi_qe/learning/__init__.py` and import classes

**Issue**: Tests fail with "coroutine was never awaited"
**Solution**: Add `@pytest.mark.asyncio` decorator to async tests

**Issue**: Tests pass but coverage is low
**Solution**: Add edge case tests and error handling

## Next Steps

1. ✅ Implement StateEncoder
2. ✅ Run test_state_encoder.py (35 tests should pass)
3. ✅ Implement RewardCalculator
4. ✅ Run test_reward_calculator.py (44 tests should pass)
5. ✅ Implement QLearningService
6. ✅ Run test_qlearner.py (34 tests should pass)
7. ✅ Modify BaseQEAgent
8. ✅ Run test_base_agent_integration.py (29 tests should pass)
9. ✅ Run full suite (142 tests should pass)
10. ✅ Measure coverage (target 90%+)

---

**TDD Approach**: Write code to pass one test at a time, iterate until all 142 pass!
