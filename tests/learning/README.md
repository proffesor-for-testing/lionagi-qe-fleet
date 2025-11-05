# Q-Learning Test Suite

Comprehensive test suite for Q-Learning implementation in the LionAGI QE Fleet.

## Overview

- **Total Lines**: ~2,840 lines of test code
- **Test Functions**: 142 test functions
- **Coverage Target**: 100% for core Q-learning logic, 90%+ for integration
- **Test Framework**: pytest with pytest-asyncio

## Test Files

### 1. conftest.py (444 lines)
Shared fixtures and test utilities for all Q-learning tests.

**Fixtures Provided**:
- **Database Fixtures**: `mock_db_pool`, `mock_db_connection`, `mock_db_manager`
- **Q-Learning Components**: `mock_state_encoder`, `mock_reward_calculator`, `mock_q_service`
- **Sample Data**: `sample_qe_task`, `sample_trajectory`, `sample_q_values`, `sample_experiences`
- **Agent Fixtures**: `learning_enabled_agent`, `qe_memory`, `simple_model`
- **Test Data Generators**: `sample_task_factory`, `generate_states`, `generate_q_table`
- **Assertion Helpers**: `assert_q_value_in_range`, `assert_state_encoded`, `assert_trajectory_valid`

### 2. test_state_encoder.py (469 lines, 35 tests)
Tests for StateEncoder - encoding task states for Q-learning.

**Test Classes**:
- `TestStateEncoder`: Initialization and basic functionality (2 tests)
- `TestFeatureExtraction`: Feature extraction from task context (4 tests)
- `TestBucketing`: Continuous value bucketing (complexity, size, coverage) (13 tests)
- `TestStateEncoding`: Full state encoding (7 tests)
- `TestStateHashing`: State hashing for compact representation (3 tests)
- `TestEdgeCases`: Edge cases and error handling (6 tests)

**Key Tests**:
- State encoding determinism (same input → same output)
- Feature extraction with missing/None values
- Bucketing of complexity (low/medium/high/very_high)
- All 18 agent types produce unique states
- Special character handling and type coercion

### 3. test_reward_calculator.py (575 lines, 44 tests)
Tests for RewardCalculator - computing rewards from execution results.

**Test Classes**:
- `TestRewardCalculator`: Initialization and configuration (3 tests)
- `TestCoverageReward`: Coverage-based reward calculation (5 tests)
- `TestQualityReward`: Quality-based reward (bugs, false positives, edge cases) (5 tests)
- `TestTimeReward`: Time-based reward (inverted - faster is better) (5 tests)
- `TestPatternBonus`: Pattern reuse bonus (4 tests)
- `TestCostReward`: Cost efficiency reward (3 tests)
- `TestWeightedReward`: Weighted sum of all components (5 tests)
- `TestFailurePenalty`: Penalty for task failures (3 tests)
- `TestEdgeCases`: Edge cases (negative values, NaN, overflow) (9 tests)
- `TestRewardNormalization`: Reward normalization and scaling (2 tests)

**Key Tests**:
- Multi-objective reward with configurable weights
- Positive/negative rewards for improvement/degradation
- Inverted time reward (faster = higher reward)
- Failure penalty handling
- Edge case handling (NaN, infinity, negative values)

### 4. test_qlearner.py (689 lines, 34 tests)
Tests for QLearningService - core Q-learning algorithm implementation.

**Test Classes**:
- `TestQLearningService`: Initialization and configuration (3 tests)
- `TestEpsilonGreedySelection`: ε-greedy action selection (4 tests)
- `TestQValueUpdate`: Q-value updates using Bellman equation (6 tests)
- `TestQTableOperations`: Q-table CRUD operations (5 tests)
- `TestEpsilonDecay`: ε decay strategies (exponential, reward-based) (3 tests)
- `TestExperienceReplay`: Experience replay buffer (3 tests)
- `TestConcurrentAgents`: Multiple agents learning concurrently (3 tests)
- `TestLearningMetrics`: Learning metrics and monitoring (3 tests)
- `TestEdgeCases`: Edge cases and error handling (4 tests)

**Key Tests**:
- ε-greedy exploration vs exploitation (ε=1.0, ε=0.0, ε=0.2)
- Bellman equation: `Q(s,a) ← Q(s,a) + α[r + γ·max Q(s',a') - Q(s,a)]`
- Learning rate effect on update magnitude
- Reward-based epsilon decay (RBED)
- Experience replay for improved sample efficiency
- Concurrent agent updates with database

### 5. test_base_agent_integration.py (638 lines, 29 tests)
Integration tests for BaseQEAgent with Q-learning enabled.

**Test Classes**:
- `TestBackwardCompatibility`: Learning disabled (backward compatibility) (2 tests)
- `TestLearningEnabled`: Agent with learning enabled (3 tests)
- `TestExecuteWithLearning`: Full execute_with_learning flow (6 tests)
- `TestLearnFromExecution`: Internal learning method (3 tests)
- `TestTrajectoryStorage`: Trajectory storage in memory (3 tests)
- `TestLearningMetrics`: Learning metrics in results (2 tests)
- `TestErrorHandling`: Error handling and fallbacks (3 tests)
- `TestConcurrentLearning`: Concurrent agent execution (2 tests)
- `TestPatternLearningIntegration`: Integration with pattern learning (3 tests)
- `TestLearningLifecycle`: Complete learning lifecycle (2 tests)

**Key Tests**:
- Backward compatibility (learning disabled works as before)
- Full learning flow: state encoding → action selection → execution → reward → Q-value update
- Trajectory storage in memory (`aqe/{agent_id}/learning/trajectories/{task_id}`)
- Learning metrics returned with results
- Error handling when database unavailable
- Concurrent learning across multiple agents
- Integration with existing pattern learning system

## Running Tests

### Run All Q-Learning Tests
```bash
pytest tests/learning/ -v
```

### Run Specific Test File
```bash
pytest tests/learning/test_qlearner.py -v
```

### Run Specific Test Class
```bash
pytest tests/learning/test_qlearner.py::TestEpsilonGreedySelection -v
```

### Run Specific Test Function
```bash
pytest tests/learning/test_qlearner.py::TestEpsilonGreedySelection::test_select_action_exploration -v
```

### Run with Coverage
```bash
pytest tests/learning/ --cov=lionagi_qe.learning --cov-report=html
```

### Run Only Integration Tests
```bash
pytest tests/learning/test_base_agent_integration.py -v
```

### Run with Markers
```bash
# Run only async tests
pytest tests/learning/ -m asyncio -v

# Run excluding slow tests
pytest tests/learning/ -m "not slow" -v
```

## Test Organization

### Unit Tests (115 tests)
- `test_state_encoder.py`: 35 tests
- `test_reward_calculator.py`: 44 tests
- `test_qlearner.py`: 30 tests (algorithm tests)

### Integration Tests (29 tests)
- `test_base_agent_integration.py`: 29 tests
- `test_qlearner.py`: 4 tests (concurrent agents)

## Coverage Goals

| Component | Target Coverage | Key Areas |
|-----------|----------------|-----------|
| StateEncoder | 100% | encode(), extract_features(), bucketing |
| RewardCalculator | 100% | calculate(), all reward components |
| QLearningService | 100% | select_action(), update_q_value(), Bellman |
| BaseQEAgent Integration | 90% | execute_with_learning(), error handling |

## Test Data

### Sample Q-Learning Parameters
```python
alpha = 0.1         # Learning rate
gamma = 0.95        # Discount factor
epsilon = 0.2       # Initial exploration rate
min_epsilon = 0.01  # Minimum exploration
epsilon_decay = 0.995
```

### Sample Reward Weights
```python
{
    "coverage": 0.30,      # 30% weight
    "quality": 0.25,       # 25% weight
    "time": 0.15,          # 15% weight
    "cost": 0.10,          # 10% weight
    "improvement": 0.10,   # 10% weight
    "reusability": 0.10    # 10% weight
}
```

### Sample State Encoding
```
"test_gen_complexity_medium_coverage_high_pytest"
```

### Sample Trajectory
```python
{
    "agent_id": "test-generator",
    "state": "test_gen_complexity_medium_coverage_high",
    "action": 2,
    "reward": 10.5,
    "next_state": "test_gen_complexity_medium_coverage_higher",
    "done": False,
    "timestamp": "2025-11-05T13:55:00Z"
}
```

## Mocking Strategy

### Database Mocking
All tests use mocked PostgreSQL connections to avoid requiring a real database:
- `mock_db_pool`: Mocked asyncpg connection pool
- `mock_db_manager`: Mocked DatabaseManager with all Q-learning operations
- Tests can optionally run against real PostgreSQL in Docker for integration testing

### Q-Learning Component Mocking
- `mock_state_encoder`: Returns deterministic encoded states
- `mock_reward_calculator`: Returns configurable rewards
- `mock_q_service`: Full Q-learning service with configurable behavior

### Agent Mocking
- `TestLearningAgent`: Concrete BaseQEAgent implementation for testing
- Returns predictable results for reward calculation
- Can be configured to succeed or fail

## Testing Best Practices

### 1. Use Fixtures
```python
@pytest.mark.asyncio
async def test_with_fixtures(learning_enabled_agent, sample_qe_task):
    result = await learning_enabled_agent.execute_with_learning(sample_qe_task)
    assert result["success"] is True
```

### 2. Test Async Code
```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

### 3. Mock Database Operations
```python
mock_db_manager.get_q_value = AsyncMock(return_value=0.5)
q_value = await service.get_q_value("state", 1)
assert q_value == 0.5
```

### 4. Test Edge Cases
```python
# Test with missing fields
task = QETask(task_type="test", context={})
features = encoder.extract_features(task)
assert "complexity" in features  # Should use default

# Test with None values
task = QETask(task_type="test", context={"coverage": None})
state = encoder.encode(task)
assert isinstance(state, str)  # Should handle gracefully
```

### 5. Test Concurrent Operations
```python
@pytest.mark.asyncio
async def test_concurrent():
    tasks = [operation(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    assert len(results) == 5
```

## Integration with Real PostgreSQL

To run tests against real PostgreSQL (optional):

### 1. Start PostgreSQL in Docker
```bash
docker-compose up -d postgres
```

### 2. Set Environment Variable
```bash
export AQE_DB_URL="postgresql://user:pass@localhost:5432/qe_learning"
```

### 3. Run Integration Tests
```bash
pytest tests/learning/ --integration -v
```

### 4. Schema Setup
The test suite will automatically create required tables:
- `q_tables`: Agent Q-table metadata
- `q_values`: State-action-value pairs
- `learning_experiences`: Experience replay buffer
- `learning_stats`: Convergence monitoring

## Debugging Tests

### Run with Print Statements
```bash
pytest tests/learning/ -v -s
```

### Run with PDB Debugger
```bash
pytest tests/learning/ --pdb
```

### Run Single Test with Logging
```bash
pytest tests/learning/test_qlearner.py::test_bellman_update -v -s --log-cli-level=DEBUG
```

### View Test Output
```bash
pytest tests/learning/ -v --tb=short
```

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# .github/workflows/test.yml
- name: Run Q-Learning Tests
  run: |
    pytest tests/learning/ \
      --cov=lionagi_qe.learning \
      --cov-report=xml \
      --cov-report=html \
      --junitxml=junit.xml
```

## Performance Benchmarks

### Test Execution Speed
- Unit tests: ~2-5 seconds per file
- Integration tests: ~10-15 seconds
- Full suite: ~30-40 seconds

### Coverage Report Generation
- HTML report: ~5 seconds
- XML report: ~2 seconds

## Troubleshooting

### Import Errors
If you see import errors:
```bash
export PYTHONPATH=/workspaces/lionagi-qe-fleet:$PYTHONPATH
pytest tests/learning/
```

### Async Event Loop Errors
If you see event loop errors, check `conftest.py` has:
```python
@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

### Mock Not Working
Verify pytest-mock is installed:
```bash
pip install pytest-mock
pytest tests/learning/ -v
```

## Future Test Additions

Potential areas for expansion:

1. **Performance Tests**: Benchmark Q-value lookup speed, update latency
2. **Stress Tests**: Test with 1000+ states, 100+ concurrent agents
3. **Database Tests**: Test against real PostgreSQL with transactions
4. **Property-Based Tests**: Use Hypothesis for fuzzing state encodings
5. **Mutation Tests**: Verify tests catch introduced bugs (mutation testing)
6. **Snapshot Tests**: Verify Q-table state over time
7. **A/B Testing**: Compare learned vs baseline policies

## Contributing

When adding new tests:

1. Follow existing naming conventions (`test_<functionality>`)
2. Use descriptive test names (`test_epsilon_greedy_exploration`)
3. Add docstrings explaining what the test validates
4. Use fixtures from `conftest.py` rather than creating new ones
5. Test both success and failure paths
6. Include edge case tests
7. Update this README with new test counts

## References

- [Q-Learning Research](../../docs/research/q-learning-summary.md)
- [Q-Learning Best Practices](../../docs/research/q-learning-best-practices.md)
- [Q-Learning Architecture](../../docs/research/q-learning-architecture-diagram.md)
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

---

**Last Updated**: 2025-11-05
**Test Suite Version**: 1.0.0
**Total Test Functions**: 142
**Total Lines of Code**: 2,840
