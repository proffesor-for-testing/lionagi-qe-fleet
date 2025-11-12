# Phase 1 Test Files - Implementation Checklist

**Generated**: 2025-11-12
**Total Test Files**: 25 files
**Total Test Cases**: ~250 tests

---

## 📋 Test Files Checklist

### Unit Tests (9 files, 150 tests)

#### MCP Layer (2 files, 65 tests)
- [ ] `tests/unit/mcp/test_mcp_server_unit.py` (25 tests, 95% coverage)
  - TestMCPServerInitialization (5 tests)
  - TestFleetInitialization (4 tests)
  - TestToolRegistration (6 tests)
  - TestServerLifecycle (4 tests)
  - TestServerFactory (6 tests)

- [ ] `tests/unit/mcp/test_mcp_tools_unit.py` (40 tests, 90% coverage)
  - TestFleetInstanceManagement (3 tests)
  - TestCoreTestingTools (12 tests)
  - TestPerformanceSecurityTools (4 tests)
  - TestFleetOrchestrationTools (5 tests)
  - TestAdvancedTools (14 tests)
  - TestStreamingTools (2 tests)

#### Persistence Layer (2 files, 45 tests)
- [ ] `tests/unit/persistence/test_redis_memory_unit.py` (20 tests, 85% coverage)
  - TestRedisMemoryInitialization (5 tests)
  - TestRedisMemoryStore (3 tests)
  - TestRedisMemoryRetrieve (3 tests)
  - TestRedisMemorySearch (2 tests)
  - TestRedisMemoryPartitions (2 tests)
  - TestRedisMemoryStats (5 tests)

- [ ] `tests/unit/persistence/test_postgres_memory_unit.py` (25 tests, 85% coverage)
  - TestPostgresMemoryInitialization (5 tests)
  - TestPostgresMemoryStore (4 tests)
  - TestPostgresMemoryRetrieve (4 tests)
  - TestPostgresMemorySearch (3 tests)
  - TestPostgresMemoryTransactions (4 tests)
  - TestPostgresMemoryStats (5 tests)

#### Agent Layer (3 files, 70 tests)
- [ ] `tests/unit/agents/test_base_agent_unit.py` (30 tests, 95% coverage)
  - TestBaseAgentInitialization (6 tests)
  - TestMemoryBackendType (3 tests)
  - TestMemoryOperations (4 tests)
  - TestQLearningIntegration (3 tests)
  - TestFuzzyParsing (4 tests)
  - TestExecutionHooks (5 tests)
  - TestMetrics (5 tests)

- [ ] `tests/unit/agents/test_test_generator_unit.py` (20 tests, 90% coverage)
  - TestTestGeneratorInitialization (3 tests)
  - TestTestGeneration (8 tests)
  - TestEdgeCaseDetection (5 tests)
  - TestFrameworkIntegration (4 tests)

- [ ] `tests/unit/agents/test_test_executor_unit.py` (20 tests, 90% coverage)
  - TestTestExecutorInitialization (3 tests)
  - TestTestExecution (8 tests)
  - TestParallelExecution (5 tests)
  - TestCoverageCollection (4 tests)

#### Core Layer (2 files, 20 tests)
- [ ] `tests/unit/core/test_task_unit.py` (10 tests, 90% coverage)
  - TestQETaskCreation (3 tests)
  - TestQETaskLifecycle (4 tests)
  - TestQETaskSerialization (3 tests)

- [ ] `tests/unit/core/test_router_unit.py` (10 tests, 85% coverage)
  - TestModelRouter (5 tests)
  - TestModelSelection (3 tests)
  - TestCostTracking (2 tests)

---

### Integration Tests (4 files, 30 tests)

- [ ] `tests/integration/test_mcp_server_integration.py` (10 tests)
  - TestMCPServerIntegration (3 tests)
  - TestToolExecutionEndToEnd (4 tests)
  - TestFleetCoordination (3 tests)

- [ ] `tests/integration/test_api_storage_integration.py` (8 tests)
  - TestAPIStorageIntegration (3 tests)
  - TestRedisIntegration (2 tests)
  - TestPostgresIntegration (2 tests)
  - TestCrossAgentMemory (1 test)

- [ ] `tests/integration/test_queue_integration.py` (6 tests)
  - TestCeleryQueueIntegration (3 tests)
  - TestAsyncTaskProcessing (2 tests)
  - TestRetryMechanism (1 test)

- [ ] `tests/integration/test_websocket_streaming.py` (4 tests)
  - TestWebSocketStreaming (2 tests)
  - TestStreamingProgress (2 tests)

---

### API Tests (2 files, 40 tests)

- [ ] `tests/api/test_endpoints.py` (32 tests, 100% coverage)
  - TestTestGenerateEndpoint (4 tests)
  - TestTestExecuteEndpoint (4 tests)
  - TestCoverageAnalyzeEndpoint (4 tests)
  - TestQualityGateEndpoint (4 tests)
  - TestPerformanceTestEndpoint (4 tests)
  - TestSecurityScanEndpoint (4 tests)
  - TestFleetOrchestrateEndpoint (4 tests)
  - TestGetFleetStatusEndpoint (4 tests)

- [ ] `tests/api/test_contracts.py` (10 tests)
  - TestPactContracts (10 tests)
    - test_generate_contract (2 tests)
    - test_execute_contract (2 tests)
    - coverage_analyze_contract (2 tests)
    - quality_gate_contract (2 tests)
    - Additional contracts (2 tests)

---

### Performance Tests (3 files, 5 scenarios)

- [ ] `tests/performance/test_load_locust.py` (3 scenarios)
  - TestGenerationLoad (1 scenario)
  - CoverageAnalysisLoad (1 scenario)
  - FleetOrchestrationLoad (1 scenario)

- [ ] `tests/performance/test_load_k6.js` (2 scenarios)
  - TestGenerationThroughput (1 scenario)
  - APIEndpointLatency (1 scenario)

- [ ] `tests/performance/test_performance_thresholds.py` (5 tests)
  - TestResponseTimeThresholds (2 tests)
  - TestErrorRateThresholds (2 tests)
  - TestThroughputThresholds (1 test)

---

### Mutation Testing (1 file)

- [ ] `tests/mutation/test_mutation_coverage.py` (configuration)
  - Configuration for mutmut
  - Critical path mutation tests
  - Mutation score validation

---

### Configuration Files (2 files)

- [ ] `tests/conftest.py` (shared fixtures)
  - pytest configuration
  - pytest_configure (markers)
  - event_loop fixture
  - qe_memory fixture
  - model_router fixture
  - simple_model fixture
  - qe_orchestrator fixture
  - qe_fleet fixture
  - Agent fixtures (test_generator, test_executor, etc.)
  - Mock objects (mock_lionagi_branch, mock_db)
  - Test data generators
  - Assertion helpers

- [ ] `pytest.ini` or `pyproject.toml` (pytest config)
  - asyncio_mode = "auto"
  - testpaths = ["tests"]
  - python_files = ["test_*.py"]
  - addopts = "-v --cov=src/lionagi_qe --cov-report=html"

---

## 📊 Implementation Progress Tracker

### Week 1: Foundation (75 tests)
```
Priority: P0 (Critical)
Duration: 5 days
Target Coverage: 85-95%

[ ] Day 1: MCP Server unit tests (25 tests)
[ ] Day 2: MCP Tools unit tests - Core tools (20 tests)
[ ] Day 3: MCP Tools unit tests - Advanced tools (20 tests)
[ ] Day 4: Redis memory unit tests (20 tests)
[ ] Day 5: Base agent unit tests (30 tests) - START
```

### Week 2: Core Functionality (60 tests)
```
Priority: P0-P1
Duration: 5 days
Target Coverage: 90-100%

[ ] Day 1: Base agent unit tests (COMPLETE) + Test generator (10 tests)
[ ] Day 2: Test generator unit tests (COMPLETE - 20 tests total)
[ ] Day 3: Test executor unit tests (20 tests)
[ ] Day 4: API → Storage integration tests (8 tests)
[ ] Day 5: Review and fix failing tests
```

### Week 3: Advanced Features (50 tests)
```
Priority: P1-P2
Duration: 5 days
Target Coverage: 85-90%

[ ] Day 1: PostgreSQL memory unit tests (25 tests)
[ ] Day 2: Core layer unit tests (20 tests)
[ ] Day 3: MCP Server integration tests (10 tests)
[ ] Day 4: Queue integration tests (6 tests)
[ ] Day 5: WebSocket streaming tests (4 tests) + API endpoint tests start
```

### Week 4: Load & Contract Testing (25+ tests)
```
Priority: P2
Duration: 5 days
Target: Performance baselines + Contract validation

[ ] Day 1: API endpoint tests complete (32 tests)
[ ] Day 2: Contract tests (10 tests)
[ ] Day 3: Locust load tests (3 scenarios)
[ ] Day 4: k6 load tests (2 scenarios) + Performance thresholds (5 tests)
[ ] Day 5: Mutation testing setup + Final review
```

---

## 🎯 Quick Reference Commands

### Create Test File Template
```bash
# Create unit test file
cat > tests/unit/mcp/test_mcp_server_unit.py << 'EOF'
"""Unit tests for MCP Server"""
import pytest
from lionagi_qe.mcp.mcp_server import MCPServer

class TestMCPServerInitialization:
    def test_server_init_default_settings(self):
        """Test server initializes with default configuration"""
        # GIVEN: Default initialization
        server = MCPServer()

        # THEN: Server has correct defaults
        assert server.name == "lionagi-qe"
        assert server.enable_routing == True
        assert server.enable_learning == False
EOF
```

### Run Tests for Specific File
```bash
# Run single test file
pytest tests/unit/mcp/test_mcp_server_unit.py -v

# Run with coverage
pytest tests/unit/mcp/test_mcp_server_unit.py --cov=src/lionagi_qe.mcp.mcp_server --cov-report=term

# Run specific test class
pytest tests/unit/mcp/test_mcp_server_unit.py::TestMCPServerInitialization -v

# Run specific test method
pytest tests/unit/mcp/test_mcp_server_unit.py::TestMCPServerInitialization::test_server_init_default_settings -v
```

### Check Test File Coverage
```bash
# Coverage for single module
pytest tests/unit/mcp/ --cov=src/lionagi_qe.mcp --cov-report=term-missing

# Show missing lines
pytest --cov=src/lionagi_qe.mcp.mcp_server --cov-report=term-missing tests/unit/mcp/test_mcp_server_unit.py
```

---

## 📝 Test File Template

```python
"""
{Test file description}

Tests cover:
- {Category 1}
- {Category 2}
- {Category 3}
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from {module_path} import {ClassName}


class Test{ClassName}{TestCategory}:
    """Test {ClassName} {test category}"""

    def test_{test_case_name}(self):
        """Test {test case description}"""
        # GIVEN: {Setup preconditions}

        # WHEN: {Execute action}

        # THEN: {Verify outcome}

    @pytest.mark.asyncio
    async def test_{async_test_case_name}(self):
        """Test {async test case description}"""
        # GIVEN: {Setup preconditions}

        # WHEN: {Execute async action}
        result = await async_function()

        # THEN: {Verify outcome}
        assert result == expected
```

---

## 🔍 Coverage Tracking

### Per-File Coverage Goals
| File | Target | Critical | Status |
|------|--------|----------|--------|
| test_mcp_server_unit.py | 95% | 100% | 🔴 Not Started |
| test_mcp_tools_unit.py | 90% | 100% | 🔴 Not Started |
| test_redis_memory_unit.py | 85% | 100% | 🔴 Not Started |
| test_postgres_memory_unit.py | 85% | 100% | 🔴 Not Started |
| test_base_agent_unit.py | 95% | 100% | 🔴 Not Started |
| test_test_generator_unit.py | 90% | 100% | 🔴 Not Started |
| test_test_executor_unit.py | 90% | 100% | 🔴 Not Started |
| test_task_unit.py | 90% | N/A | 🔴 Not Started |
| test_router_unit.py | 85% | N/A | 🔴 Not Started |

### Integration Test Coverage
| File | Critical Paths | Status |
|------|---------------|--------|
| test_mcp_server_integration.py | 100% | 🔴 Not Started |
| test_api_storage_integration.py | 100% | 🔴 Not Started |
| test_queue_integration.py | 100% | 🔴 Not Started |
| test_websocket_streaming.py | 100% | 🔴 Not Started |

### API Test Coverage
| File | Endpoints | Status |
|------|-----------|--------|
| test_endpoints.py | 8/8 (100%) | 🔴 Not Started |
| test_contracts.py | 4+ contracts | 🔴 Not Started |

---

## ✅ Completion Criteria

**Phase 1 is complete when**:

- [ ] All 25 test files created
- [ ] ~250 test cases implemented
- [ ] Overall coverage ≥85%
- [ ] Critical path coverage = 100%
- [ ] All P0 tests passing
- [ ] Unit tests run <30 seconds
- [ ] Integration tests run <5 minutes
- [ ] API tests achieve 100% endpoint coverage
- [ ] Load tests validate performance thresholds
- [ ] Mutation score >80%
- [ ] CI/CD pipeline integrated with pytest

---

**Document Version**: 1.0
**Last Updated**: 2025-11-12
**Status**: Ready for implementation
