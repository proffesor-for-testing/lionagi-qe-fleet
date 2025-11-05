# Q-Learning Tests - Quick Reference

## Test Suite Overview

```
tests/learning/
├── conftest.py                      # 444 lines - Fixtures
├── test_state_encoder.py            # 469 lines - 35 tests
├── test_reward_calculator.py        # 575 lines - 44 tests
├── test_qlearner.py                 # 689 lines - 34 tests
└── test_base_agent_integration.py   # 638 lines - 29 tests

Total: 2,815 lines, 142 tests
```

## Quick Commands

```bash
# Run all tests
pytest tests/learning/ -v

# Run specific file
pytest tests/learning/test_state_encoder.py -v

# Run with coverage
pytest tests/learning/ --cov=lionagi_qe.learning --cov-report=html

# Run single test
pytest tests/learning/test_qlearner.py::TestEpsilonGreedySelection::test_select_action_exploration -v

# Run with output
pytest tests/learning/ -v -s
```

## Test Counts by File

| File | Tests | Key Focus |
|------|-------|-----------|
| test_state_encoder.py | 35 | State encoding, bucketing, hashing |
| test_reward_calculator.py | 44 | Multi-objective rewards |
| test_qlearner.py | 34 | Bellman equation, ε-greedy |
| test_base_agent_integration.py | 29 | Full learning flow |

## Core Algorithms Tested

### 1. State Encoding
```python
state = f"{task_type}_complexity_{complexity}_coverage_{coverage}_{framework}"
# Example: "test_gen_complexity_medium_coverage_high_pytest"
```

### 2. Bellman Equation
```python
# Q(s,a) ← Q(s,a) + α[r + γ·max Q(s',a') - Q(s,a)]
new_q = current_q + alpha * (reward + gamma * max_next_q - current_q)
```

### 3. Epsilon-Greedy
```python
if random() < epsilon:
    action = random_action()  # Explore
else:
    action = best_action()    # Exploit
```

### 4. Multi-Objective Reward
```python
reward = (
    0.30 * coverage_reward +
    0.25 * quality_reward +
    0.15 * time_reward +
    0.10 * pattern_bonus +
    0.10 * cost_reward +
    0.10 * improvement_reward
)
```

## Fixtures Quick Reference

### Database
- `mock_db_pool`: Mocked asyncpg pool
- `mock_db_manager`: Mocked DatabaseManager
- `mock_db_connection`: Single connection

### Components
- `mock_state_encoder`: Returns encoded states
- `mock_reward_calculator`: Returns rewards
- `mock_q_service`: Full Q-learning service

### Data
- `sample_qe_task`: Basic task
- `sample_task_factory`: Task factory
- `sample_trajectory`: Learning trajectory
- `sample_q_values`: Q-table entries

### Agents
- `learning_enabled_agent`: Agent with Q-learning
- `qe_memory`: QE memory instance
- `simple_model`: Test iModel

## Expected Test Results

```
✅ test_state_encoder.py     → 35 passed
✅ test_reward_calculator.py → 44 passed
✅ test_qlearner.py          → 34 passed
✅ test_base_agent_integration.py → 29 passed

Total: 142 passed in ~30s
Coverage: 90%+ for lionagi_qe.learning
```

## Key Test Classes

### StateEncoder (7 classes, 35 tests)
- `TestStateEncoder`: Init (2)
- `TestFeatureExtraction`: Feature extraction (4)
- `TestBucketing`: Bucketing logic (13)
- `TestStateEncoding`: Full encoding (7)
- `TestStateHashing`: Hashing (3)
- `TestEdgeCases`: Edge cases (6)

### RewardCalculator (10 classes, 44 tests)
- `TestRewardCalculator`: Init (3)
- `TestCoverageReward`: Coverage (5)
- `TestQualityReward`: Quality (5)
- `TestTimeReward`: Time (5)
- `TestPatternBonus`: Patterns (4)
- `TestCostReward`: Cost (3)
- `TestWeightedReward`: Weighted sum (5)
- `TestFailurePenalty`: Failures (3)
- `TestEdgeCases`: Edge cases (9)
- `TestRewardNormalization`: Normalization (2)

### QLearningService (8 classes, 34 tests)
- `TestQLearningService`: Init (3)
- `TestEpsilonGreedySelection`: ε-greedy (4)
- `TestQValueUpdate`: Bellman (6)
- `TestQTableOperations`: CRUD (5)
- `TestEpsilonDecay`: Decay (3)
- `TestExperienceReplay`: Replay (3)
- `TestConcurrentAgents`: Concurrency (3)
- `TestLearningMetrics`: Metrics (3)
- `TestEdgeCases`: Edge cases (4)

### BaseQEAgent Integration (10 classes, 29 tests)
- `TestBackwardCompatibility`: Disabled (2)
- `TestLearningEnabled`: Enabled (3)
- `TestExecuteWithLearning`: Flow (6)
- `TestLearnFromExecution`: Learning (3)
- `TestTrajectoryStorage`: Storage (3)
- `TestLearningMetrics`: Metrics (2)
- `TestErrorHandling`: Errors (3)
- `TestConcurrentLearning`: Concurrency (2)
- `TestPatternLearningIntegration`: Patterns (3)
- `TestLearningLifecycle`: Lifecycle (2)

## Implementation Checklist

### StateEncoder
- [ ] `__init__(config)`
- [ ] `encode(task) -> str`
- [ ] `extract_features(task) -> Dict`
- [ ] `bucket_complexity(int) -> str`
- [ ] `bucket_size(int) -> str`
- [ ] `bucket_coverage(float) -> str`
- [ ] `hash_state(str) -> str`

### RewardCalculator
- [ ] `__init__(weights)`
- [ ] `calculate(result) -> float`
- [ ] `coverage_reward(current, previous) -> float`
- [ ] `quality_reward(bugs, fps, edges) -> float`
- [ ] `time_reward(time) -> float`
- [ ] `pattern_bonus(count) -> float`
- [ ] `cost_reward(cost) -> float`
- [ ] `failure_penalty() -> float`

### QLearningService
- [ ] `__init__(agent_id, db_manager, params)`
- [ ] `select_action(state, num_actions) -> int`
- [ ] `update_q_value(s, a, r, s', done)`
- [ ] `get_q_value(state, action) -> float`
- [ ] `get_best_action(state, num_actions) -> int`
- [ ] `get_max_q_value(state, num_actions) -> float`
- [ ] `decay_epsilon(reward)`
- [ ] `store_experience(s, a, r, s', done)`
- [ ] `sample_experiences(batch_size) -> List`
- [ ] `replay_experiences(batch_size)`

### BaseQEAgent
- [ ] Add `enable_learning` parameter
- [ ] Initialize Q-learning components if enabled
- [ ] Implement `execute_with_learning(task)`
- [ ] Implement `_store_trajectory(...)`
- [ ] Handle learning errors gracefully

## Common Test Patterns

### Testing Async Functions
```python
@pytest.mark.asyncio
async def test_async_function(fixture):
    result = await async_operation()
    assert result is not None
```

### Using Mocks
```python
mock_db_manager.get_q_value = AsyncMock(return_value=0.5)
q_value = await service.get_q_value("state", 1)
assert q_value == 0.5
```

### Testing Edge Cases
```python
# Missing fields
task = QETask(task_type="test", context={})
state = encoder.encode(task)
assert isinstance(state, str)

# None values
task = QETask(task_type="test", context={"coverage": None})
features = encoder.extract_features(task)
assert features["coverage"] == 0.0
```

### Testing Concurrency
```python
@pytest.mark.asyncio
async def test_concurrent():
    tasks = [operation(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    assert len(results) == 5
```

## Debugging Tests

```bash
# Run with print statements
pytest tests/learning/ -v -s

# Run with debugger
pytest tests/learning/ --pdb

# Run single test with logging
pytest tests/learning/test_qlearner.py::test_bellman_update -v -s --log-cli-level=DEBUG

# Show short traceback
pytest tests/learning/ -v --tb=short
```

## Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| StateEncoder | 100% | - |
| RewardCalculator | 100% | - |
| QLearningService | 100% | - |
| BaseQEAgent Integration | 90% | - |
| Overall | 95% | - |

## Key Parameters

### Q-Learning
```python
alpha = 0.1         # Learning rate
gamma = 0.95        # Discount factor
epsilon = 0.2       # Exploration rate
min_epsilon = 0.01  # Minimum exploration
epsilon_decay = 0.995
```

### Reward Weights
```python
{
    "coverage": 0.30,
    "quality": 0.25,
    "time": 0.15,
    "cost": 0.10,
    "improvement": 0.10,
    "reusability": 0.10
}
```

### Bucketing Thresholds
```python
complexity_buckets = [10, 20, 40]
size_buckets = [100, 300, 600]
coverage_buckets = [0.5, 0.7, 0.9]
```

## Resources

- **README.md**: Full documentation
- **TEST_SUMMARY.md**: Executive summary
- **IMPLEMENTATION_GUIDE.md**: Implementation examples
- **Q-Learning Research**: `docs/research/q-learning-summary.md`

---

**Quick Start**: `pytest tests/learning/ -v`
**Need Help**: See IMPLEMENTATION_GUIDE.md for code examples
