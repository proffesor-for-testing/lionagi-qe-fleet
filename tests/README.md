# LionAGI QE Fleet Test Suite

Comprehensive unit tests for the LionAGI Quality Engineering Fleet.

## 📊 Test Coverage

### Test Statistics
- **Total Test Files**: 12
- **Total Test Lines**: 4,055+
- **Test Modules**: 9
- **Shared Fixtures**: 20+

### Coverage Areas

#### Core Components (5 test files)
1. **test_memory.py** - QEMemory shared namespace
   - Store/retrieve operations
   - TTL expiration
   - Partition management
   - Pattern searching
   - State export/import
   - Concurrent access
   - 35+ test cases

2. **test_router.py** - ModelRouter cost optimization
   - Complexity analysis
   - Model routing (simple → critical)
   - Cost tracking
   - Savings calculation
   - Statistics aggregation
   - 25+ test cases

3. **test_task.py** - QETask state management
   - Task lifecycle
   - State transitions
   - Priority levels
   - Result storage
   - Error handling
   - 20+ test cases

4. **test_orchestrator.py** - QEOrchestrator workflow coordination
   - Agent registration
   - Pipeline execution
   - Parallel execution
   - Fan-out/fan-in patterns
   - Hierarchical coordination
   - 25+ test cases

5. **test_fleet.py** - QEFleet main interface
   - Fleet initialization
   - Agent registration
   - Workflow execution
   - State management
   - Integration testing
   - 30+ test cases

#### Agent Tests (4 test files)
1. **test_base_agent.py** - BaseQEAgent core functionality
   - Memory integration
   - Execution hooks
   - Pattern learning
   - Metrics tracking
   - Communication
   - 25+ test cases

2. **test_test_generator.py** - TestGeneratorAgent
   - Test generation
   - Edge case detection
   - Pattern learning
   - Multi-framework support
   - Coverage estimation
   - 20+ test cases

3. **test_test_executor.py** - TestExecutorAgent
   - Test execution
   - Coverage reporting
   - Flaky test detection
   - Parallel execution
   - Result storage
   - 20+ test cases

4. **test_fleet_commander.py** - FleetCommanderAgent
   - Task decomposition
   - Agent assignment
   - Workflow synthesis
   - Execution strategies
   - Multi-agent coordination
   - 15+ test cases

## 🚀 Running Tests

### Basic Usage

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=lionagi_qe --cov-report=html

# Run specific test file
pytest tests/test_core/test_memory.py

# Run specific test class
pytest tests/test_core/test_memory.py::TestQEMemory

# Run specific test method
pytest tests/test_core/test_memory.py::TestQEMemory::test_store_and_retrieve

# Run tests matching pattern
pytest tests/ -k "test_memory"
```

### Test Categories

```bash
# Core component tests only
pytest tests/test_core/

# Agent tests only
pytest tests/test_agents/

# Async tests only
pytest tests/ -k "asyncio"

# Integration tests
pytest tests/ -k "integration"
```

### Advanced Options

```bash
# Run with markers
pytest tests/ -m "slow"

# Parallel execution (requires pytest-xdist)
pytest tests/ -n auto

# Stop on first failure
pytest tests/ -x

# Show slowest 10 tests
pytest tests/ --durations=10

# Generate JUnit XML report
pytest tests/ --junitxml=test-results.xml
```

## 📦 Test Dependencies

### Required Packages
```bash
pip install pytest pytest-asyncio pytest-mock
```

### Optional Packages
```bash
# Coverage reporting
pip install pytest-cov

# Parallel execution
pip install pytest-xdist

# BDD-style testing
pip install pytest-bdd
```

## 🧪 Test Structure

### Directory Layout
```
tests/
├── __init__.py                      # Test suite package
├── conftest.py                       # Shared fixtures
├── README.md                         # This file
├── test_core/                        # Core component tests
│   ├── __init__.py
│   ├── test_memory.py               # Memory namespace tests
│   ├── test_router.py               # Model routing tests
│   ├── test_task.py                 # Task management tests
│   ├── test_orchestrator.py         # Orchestration tests
│   └── test_fleet.py                # Fleet interface tests
└── test_agents/                      # Agent-specific tests
    ├── __init__.py
    ├── test_base_agent.py           # Base agent tests
    ├── test_test_generator.py       # Test generator tests
    ├── test_test_executor.py        # Test executor tests
    └── test_fleet_commander.py      # Fleet commander tests
```

### Fixture Overview

#### Core Fixtures (conftest.py)
- `qe_memory` - Fresh QEMemory instance
- `model_router` - ModelRouter with routing disabled
- `simple_model` - Basic iModel for testing
- `qe_orchestrator` - QEOrchestrator instance
- `qe_fleet` - Initialized QEFleet instance

#### Agent Fixtures
- `test_generator_agent` - TestGeneratorAgent instance
- `test_executor_agent` - TestExecutorAgent instance
- `fleet_commander_agent` - FleetCommanderAgent instance

#### Test Data Fixtures
- `sample_qe_task` - Sample task for testing
- `sample_code` - Python code samples
- `sample_test_suite` - Test suite examples
- `complex_task_context` - Complex coordination scenarios

#### Mock Fixtures
- `mock_lionagi_branch` - Mocked LionAGI Branch
- `mock_db` - Mock database for testing

## 🎯 Test Patterns

### Async Testing
All agent and orchestration tests use `pytest-asyncio`:

```python
@pytest.mark.asyncio
async def test_async_operation(qe_memory):
    await qe_memory.store("key", "value")
    result = await qe_memory.retrieve("key")
    assert result == "value"
```

### Mocking with pytest-mock
```python
@pytest.mark.asyncio
async def test_with_mocking(test_generator_agent, mocker):
    mock_result = GeneratedTest(...)
    mocker.patch.object(
        test_generator_agent,
        'operate',
        new=AsyncMock(return_value=mock_result)
    )
    result = await test_generator_agent.execute(task)
    assert result == mock_result
```

### Parametrized Testing
```python
@pytest.mark.parametrize("framework", ["pytest", "jest", "mocha"])
async def test_multiple_frameworks(test_generator_agent, framework):
    task = QETask(context={"framework": framework})
    result = await test_generator_agent.execute(task)
    assert result.framework == framework
```

## 📈 Coverage Goals

### Target Coverage
- **Statements**: >80%
- **Branches**: >75%
- **Functions**: >80%
- **Lines**: >80%

### Current Coverage Areas
✅ Core memory operations (store, retrieve, search, TTL)
✅ Model routing and cost optimization
✅ Task state management and lifecycle
✅ Pipeline and parallel orchestration
✅ Fleet initialization and coordination
✅ Agent execution hooks and learning
✅ Test generation and pattern learning
✅ Test execution and flaky detection
✅ Hierarchical task decomposition

## 🔍 Writing New Tests

### Test Naming Convention
```python
# Test files: test_<module_name>.py
# Test classes: Test<ClassName>
# Test methods: test_<what_it_tests>

class TestQEMemory:
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, qe_memory):
        """Test storing and retrieving values"""
        # Arrange
        key = "test_key"
        value = {"data": "test"}

        # Act
        await qe_memory.store(key, value)
        result = await qe_memory.retrieve(key)

        # Assert
        assert result == value
```

### Test Documentation
- Use descriptive test names
- Include docstrings explaining test purpose
- Follow AAA pattern (Arrange, Act, Assert)
- Test both success and failure cases
- Include edge cases and boundary conditions

### Async Test Template
```python
@pytest.mark.asyncio
async def test_new_feature(fixture_name, mocker):
    """Test description"""
    # Arrange: Set up test data and mocks
    test_data = {"key": "value"}
    mock_result = {"result": "success"}
    mocker.patch.object(obj, 'method', new=AsyncMock(return_value=mock_result))

    # Act: Execute the feature
    result = await feature_under_test(test_data)

    # Assert: Verify expectations
    assert result == mock_result
    assert some_condition is True
```

## 🐛 Debugging Tests

### Verbose Output
```bash
# Show print statements
pytest tests/ -s

# Very verbose
pytest tests/ -vv

# Show locals on failure
pytest tests/ -l
```

### Interactive Debugging
```python
# Add breakpoint in test
@pytest.mark.asyncio
async def test_with_debugging(qe_memory):
    await qe_memory.store("key", "value")
    import pdb; pdb.set_trace()  # Breakpoint
    result = await qe_memory.retrieve("key")
```

### Logging
```bash
# Show log output
pytest tests/ --log-cli-level=DEBUG
```

## ✅ Best Practices

1. **Isolation**: Each test should be independent
2. **Fast**: Unit tests should run quickly (<100ms each)
3. **Repeatable**: Tests should produce same results every time
4. **Self-validating**: Clear pass/fail with assertions
5. **Timely**: Write tests before or with code (TDD)
6. **One Assertion**: Focus each test on one behavior
7. **Fixtures**: Use fixtures for common setup
8. **Mocking**: Mock external dependencies
9. **Async**: Use pytest-asyncio for async tests
10. **Documentation**: Document complex test scenarios

## 📚 Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [pytest-mock Documentation](https://pytest-mock.readthedocs.io/)
- [LionAGI Documentation](https://lionagi.readthedocs.io/)

## 🤝 Contributing

When adding new tests:

1. Follow existing patterns and conventions
2. Add tests for new features
3. Update coverage goals if needed
4. Document complex test scenarios
5. Ensure all tests pass before committing
6. Run coverage analysis

```bash
# Before committing
pytest tests/ --cov=lionagi_qe --cov-report=term-missing
```

---

**Test Suite Version**: 1.0.0
**Last Updated**: 2025-11-03
**Maintainer**: LionAGI QE Fleet Team
