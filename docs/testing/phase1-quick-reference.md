# Phase 1 Test Specifications - Quick Reference

## 🎯 Coverage Goals

| Component | Target | Critical Paths |
|-----------|--------|----------------|
| MCP Server | 95% | Init: 100% |
| MCP Tools | 90% | Core: 100% |
| Base Agent | 95% | Memory: 100% |
| Storage | 85% | Store/Retrieve: 100% |
| **Overall** | **85%** | **Auth/API: 100%** |

**Mutation Score Target**: >80%

---

## 📦 Test File Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── mcp/                 # MCP server & tools
│   ├── persistence/         # Storage backends
│   ├── agents/              # Agent implementations
│   └── core/                # Core components
├── integration/             # Integration tests (real backends)
│   ├── test_mcp_server_integration.py
│   ├── test_api_storage_integration.py
│   ├── test_queue_integration.py
│   └── test_websocket_streaming.py
├── api/                     # API endpoint tests
│   ├── test_endpoints.py
│   └── test_contracts.py    # Pact contract tests
├── performance/             # Load tests
│   ├── test_load_locust.py
│   └── test_load_k6.js
└── mutation/                # Mutation testing
    └── test_mutation_coverage.py
```

---

## 🧪 Quick Test Commands

```bash
# Run all tests with coverage
pytest -v --cov=src/lionagi_qe --cov-report=html --cov-report=term

# Run unit tests only (fast)
pytest tests/unit/ -v

# Run integration tests (requires backends)
pytest tests/integration/ -v -m integration

# Run specific test file
pytest tests/unit/mcp/test_mcp_server_unit.py -v

# Run tests matching pattern
pytest -k "test_mcp" -v

# Run with specific markers
pytest -m "redis" -v              # Redis tests only
pytest -m "postgres" -v           # PostgreSQL tests only
pytest -m "not slow" -v           # Skip slow tests

# Generate coverage report
pytest --cov=src/lionagi_qe --cov-report=html
open htmlcov/index.html

# Run mutation testing
mutmut run
mutmut results
```

---

## 📋 Test Case Examples

### Unit Test: MCP Server Initialization

```python
def test_server_init_default_settings(self):
    """Test server initializes with default configuration"""
    # GIVEN: Default initialization parameters
    server = MCPServer()

    # THEN: Server has correct defaults
    assert server.name == "lionagi-qe"
    assert server.enable_routing == True
    assert server.enable_learning == False
    assert server.fleet is None
```

### Unit Test: MCP Tool Execution

```python
@pytest.mark.asyncio
async def test_test_generate_basic(self, mock_fleet):
    """Test test_generate() with default parameters"""
    # GIVEN: Mock fleet with test-generator agent
    set_fleet_instance(mock_fleet)
    mock_fleet.execute.return_value = {
        "test_code": "def test_add(): assert add(1,2) == 3",
        "test_name": "test_add",
        "assertions": ["assert add(1,2) == 3"],
        "framework": "pytest"
    }

    # WHEN: test_generate() called
    result = await test_generate(code="def add(a,b): return a+b")

    # THEN: Returns test code
    assert "test_code" in result
    assert result["framework"] == "pytest"
    mock_fleet.execute.assert_called_once()
```

### Integration Test: API → Storage

```python
@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.asyncio
async def test_test_generation_stores_in_redis(self, redis_memory):
    """Test test generation stores results in Redis"""
    # GIVEN: Fleet with Redis memory backend
    fleet = QEFleet()
    await fleet.initialize()
    agent = TestGeneratorAgent(
        agent_id="test-gen",
        model=iModel(provider="openai", model="gpt-4"),
        memory=redis_memory
    )
    fleet.register_agent(agent)

    # WHEN: test_generate() tool called
    task = QETask(task_type="test_generation", context={
        "code": "def add(a, b): return a + b"
    })
    result = await fleet.execute("test-gen", task)

    # THEN: Generated tests stored in Redis
    stored = await redis_memory.retrieve("aqe/test-gen/tasks/*/result")
    assert stored is not None
    assert "test_code" in stored
```

### API Test: POST Endpoint

```python
def test_post_test_generate_success(self, client):
    """Test POST /tools/test_generate endpoint"""
    # GIVEN: Valid request payload
    payload = {
        "code": "def add(a, b): return a + b",
        "framework": "pytest"
    }

    # WHEN: POST request sent
    response = client.post("/tools/test_generate", json=payload)

    # THEN: Returns 200 OK with test code
    assert response.status_code == 200
    data = response.json()
    assert "test_code" in data
    assert "pytest" in data["test_code"]
```

### Load Test: Locust

```python
from locust import HttpUser, task, between

class MCPLoadTest(HttpUser):
    wait_time = between(1, 3)

    @task
    def test_generate(self):
        self.client.post("/tools/test_generate", json={
            "code": "def example(): pass",
            "framework": "pytest"
        })
```

---

## 🔍 Test Markers

```python
# In conftest.py
def pytest_configure(config):
    config.addinivalue_line("markers", "integration: integration test")
    config.addinivalue_line("markers", "postgres: requires PostgreSQL")
    config.addinivalue_line("markers", "redis: requires Redis")
    config.addinivalue_line("markers", "slow: slow running test")

# Usage in tests
@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.asyncio
async def test_redis_integration():
    pass
```

---

## 📊 Key Test Metrics

### Unit Tests
- **Count**: ~150 tests
- **Execution Time**: <30 seconds
- **Coverage**: 85-95% per module
- **Isolation**: 100% (no external dependencies)

### Integration Tests
- **Count**: ~30 tests
- **Execution Time**: 2-5 minutes
- **Coverage**: Critical paths 100%
- **Backends**: PostgreSQL, Redis, Celery

### API Tests
- **Count**: ~40 tests
- **Execution Time**: <1 minute
- **Coverage**: All endpoints 100%
- **Contract Tests**: 10+ Pact contracts

### Load Tests
- **Scenarios**: 5 key endpoints
- **Virtual Users**: 10-100
- **Duration**: 60 seconds per test
- **Thresholds**:
  - Response time P95 < 500ms
  - Error rate < 1%

---

## 🎯 Priority Test Cases

### P0 (Critical - Must Pass)
1. MCP server initialization
2. Fleet initialization with agents
3. Tool registration (17 tools)
4. Core tool execution (test_generate, test_execute)
5. Memory store/retrieve operations
6. API authentication
7. Agent task execution

### P1 (High Priority)
8. Tool error handling
9. Fleet lifecycle (start/stop)
10. Storage backend integration
11. API endpoint validation
12. Agent memory coordination
13. Q-learning integration
14. Fuzzy parsing fallback

### P2 (Medium Priority)
15. Streaming tools
16. WebSocket integration
17. Celery queue integration
18. Advanced tools (flaky test hunt, chaos, etc.)
19. Contract testing
20. Load testing

---

## 🛠️ Test Dependencies

### Required
```bash
pytest>=8.0.0
pytest-asyncio>=1.1.0
pytest-cov>=6.0.0
pytest-mock>=3.12.0
hypothesis>=6.100.0
coverage>=7.0.0
```

### Optional (Integration Tests)
```bash
redis>=5.0.0              # Redis integration
asyncpg>=0.29.0           # PostgreSQL integration
celery>=5.3.0             # Queue integration
websockets>=12.0          # WebSocket integration
```

### Optional (Load Tests)
```bash
locust>=2.20.0            # Load testing
```

### Optional (Contract Tests)
```bash
pact-python>=2.0.0        # Contract testing
```

---

## 📝 Test Template (Minimal)

```python
"""Test {MODULE_NAME}"""
import pytest

class Test{ClassName}:
    """Test {ClassName} functionality"""

    def test_basic_functionality(self):
        """Test basic functionality"""
        # GIVEN: Setup
        instance = ClassName()

        # WHEN: Execute
        result = instance.method()

        # THEN: Verify
        assert result == expected

    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality"""
        # GIVEN: Setup
        instance = ClassName()

        # WHEN: Execute
        result = await instance.async_method()

        # THEN: Verify
        assert result == expected
```

---

## 🚀 Implementation Order

### Week 1: Foundation
- [ ] MCP server initialization tests
- [ ] MCP tools unit tests (core tools)
- [ ] Redis memory unit tests
- [ ] Base agent unit tests

### Week 2: Core Functionality
- [ ] Test generation tool tests
- [ ] Test execution tool tests
- [ ] Coverage analysis tool tests
- [ ] API → Storage integration tests

### Week 3: Advanced Features
- [ ] Streaming tools tests
- [ ] WebSocket integration tests
- [ ] Celery queue integration tests
- [ ] API endpoint tests

### Week 4: Load & Contract Testing
- [ ] Load tests (locust)
- [ ] Load tests (k6)
- [ ] Contract tests (pact-python)
- [ ] Mutation testing

---

**Document Version**: 1.0
**Last Updated**: 2025-11-12
**Full Specifications**: `docs/testing/phase1-test-specifications.md`
