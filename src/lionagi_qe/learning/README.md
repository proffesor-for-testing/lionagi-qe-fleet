# Q-Learning Module for LionAGI QE Fleet

Complete Q-Learning implementation for the 18 specialized QE agents in the LionAGI QE Fleet.

## Overview

This module implements classic Q-Learning with the Bellman equation to enable agents to learn optimal testing strategies through experience.

### Algorithm

**Q-Learning Update Rule (Bellman Equation):**

```
Q(s,a) ← Q(s,a) + α[r + γ·max(Q(s',a')) - Q(s,a)]
```

Where:
- `Q(s,a)`: Q-value for state `s` and action `a`
- `α`: Learning rate (default: 0.1)
- `r`: Reward received
- `γ`: Discount factor (default: 0.95)
- `max(Q(s',a'))`: Maximum Q-value for next state `s'`

**Epsilon-Greedy Action Selection:**

```python
if random() < ε:
    return random_action()  # Explore
else:
    return argmax(Q[s])     # Exploit
```

## Architecture

### Components

1. **QLearningService** (`qlearner.py`) - Main Q-Learning service
   - Bellman equation updates
   - Epsilon-greedy action selection
   - In-memory Q-table with PostgreSQL sync
   - Episode execution

2. **StateEncoder** (`state_encoder.py`) - State representation
   - Task context to discrete state encoding
   - SHA-256 hashing for fast lookups
   - Agent-specific feature extraction
   - Supports all 18 agent types

3. **RewardCalculator** (`reward_calculator.py`) - Reward computation
   - Multi-objective reward function
   - Weighted components:
     - Coverage gain (30%)
     - Quality improvement (25%)
     - Time efficiency (20%)
     - Pattern reuse (15%)
     - Cost efficiency (10%)
   - Agent-specific adjustments

4. **DatabaseManager** (`db_manager.py`) - PostgreSQL operations
   - Async CRUD operations
   - Connection pooling
   - Q-value persistence
   - Trajectory storage

## Usage

### Basic Integration

```python
from lionagi_qe.learning import QLearningService, DatabaseManager

# Initialize database
db_manager = DatabaseManager("postgresql://localhost:5432/qlearning")
await db_manager.connect()

# Create Q-Learning service
qlearner = QLearningService(
    agent_type="test-generator",
    agent_instance_id="test-gen-1",
    db_manager=db_manager,
    config={
        "learningRate": 0.1,
        "discountFactor": 0.95,
        "explorationRate": 0.2
    }
)

# Set action space
qlearner.set_action_space([
    "use_property_based",
    "use_example_based",
    "prioritize_branches",
    "generate_comprehensive"
])
```

### Execute Learning Episode

```python
async def execute_action(action: str, context: dict) -> dict:
    """Your agent's action execution logic"""
    result = await my_agent.execute(action, context)
    return {
        "success": result.success,
        "next_context": result.next_state,
        "done": result.complete,
        "actual_time_seconds": result.duration,
        "coverage_percentage": result.coverage
    }

# Run learning episode
episode_result = await qlearner.execute_learning_episode(
    initial_context={
        "task_type": "test_generation",
        "coverage_percentage": 60.0,
        "quality_score": 70.0,
        "lines_of_code": 500
    },
    execute_action_fn=execute_action,
    max_steps=10
)

print(f"Episode reward: {episode_result['total_reward']:.2f}")
print(f"Steps taken: {episode_result['steps']}")
print(f"Success rate: {episode_result['success_rate']:.2%}")
```

### Manual Q-Value Updates

```python
# Select action
action = await qlearner.select_action(
    task_context={"coverage_percentage": 60, "quality_score": 70},
    exploration=True  # Use epsilon-greedy
)

# Execute action and get result
result = await execute_action(action, context)

# Calculate reward
from lionagi_qe.learning import RewardCalculator
reward_calc = RewardCalculator()
reward = reward_calc.calculate_reward(
    state_before=context,
    action=action,
    state_after=result["next_context"],
    metadata=result
)

# Update Q-value
new_q = await qlearner.update_q_value(
    state_before=context,
    action=action,
    reward=reward,
    state_after=result["next_context"],
    done=result["done"]
)

print(f"Updated Q-value: {new_q:.4f}")
```

## Configuration

Configuration is loaded from `.agentic-qe/config/learning.json`:

```json
{
  "enabled": true,
  "learningRate": 0.1,
  "discountFactor": 0.95,
  "explorationRate": 0.2,
  "explorationDecay": 0.995,
  "minExplorationRate": 0.01,
  "updateFrequency": 10,
  "weights": {
    "coverage_gain": 0.30,
    "quality_improvement": 0.25,
    "time_efficiency": 0.20,
    "pattern_reuse": 0.15,
    "cost_efficiency": 0.10
  }
}
```

## Agent-Specific Features

### Test Generator Agent

**State Features:**
- Coverage gap (bucketed)
- Framework (pytest, jest, etc.)
- Test type (unit, integration, e2e)
- Number of functions

**Actions:**
- use_property_based
- use_example_based
- use_mutation_testing
- prioritize_branches
- prioritize_lines
- generate_simple
- generate_comprehensive
- reuse_pattern

**Reward Adjustments:**
- +5 points per edge case covered
- -2 points per test deviation from optimal count

### Coverage Analyzer Agent

**State Features:**
- Line coverage bucket
- Branch coverage bucket
- Critical paths uncovered

**Actions:**
- quick_scan
- detailed_analysis
- gap_prioritization
- use_linear_scan
- use_binary_search

### Flaky Test Hunter Agent

**State Features:**
- Failure rate bucket
- Failure pattern (intermittent/environmental/timing)
- External dependencies flag

**Actions:**
- statistical_analysis
- retry_test_nx
- isolate_test
- fix_timing_issue

**Reward (F1-Score Based):**
```python
precision = TP / (TP + FP)
recall = TP / (TP + FN)
f1_score = 2 * (precision * recall) / (precision + recall)
reward = f1_score * 100 - FN * 20 - FP * 5
```

## Database Schema

The module uses the PostgreSQL schema defined in `database/schema/qlearning_schema.sql`:

### Key Tables

- **q_values**: State-action-value tuples
- **trajectories**: Full episode recordings
- **agent_states**: Learning progress per agent
- **learning_stats**: Performance metrics

### Database Functions

- `upsert_q_value()`: Atomic Q-value upsert with visit count
- `get_best_action()`: Get optimal action for state
- `cleanup_expired_data()`: TTL enforcement

## Performance

### In-Memory Q-Table

Q-values are cached in memory for fast access:
- O(1) lookup time
- Periodic sync to PostgreSQL (configurable)
- Default sync every 10 updates

### Database Sync

```python
# Manual sync
await qlearner.save_to_database()

# Automatic sync happens every N updates
# Configured via updateFrequency in learning.json
```

## Statistics

```python
stats = qlearner.get_statistics()

# Returns:
{
    "agent_type": "test-generator",
    "total_episodes": 100,
    "successful_tasks": 85,
    "success_rate": 0.85,
    "total_reward": 4500.0,
    "avg_reward": 45.0,
    "q_table_size": 1234,
    "epsilon": 0.15,
    "learning_rate": 0.1
}
```

## Integration with BaseQEAgent

See `example_integration.py` for complete integration example.

Key integration points in `base_agent.py`:

```python
class BaseQEAgent(ABC):
    def __init__(self, ..., enable_learning=True):
        if enable_learning:
            self.q_learning = QLearningService(...)
            self._setup_action_space()

    async def execute_with_learning(self, task):
        return await self.q_learning.execute_learning_episode(
            initial_context=task,
            execute_action_fn=self._execute_action,
            max_steps=10
        )
```

## Testing

Run tests:
```bash
pytest tests/learning/ -v
```

## Dependencies

- `asyncpg>=0.29.0` - PostgreSQL async driver
- Python 3.10+
- PostgreSQL 14+

## References

- Research: `docs/research/q-learning-best-practices.md`
- Database Schema: `database/schema/qlearning_schema.sql`
- Integration Guide: `docs/q-learning-integration.md`

## License

MIT License - See LICENSE file for details
