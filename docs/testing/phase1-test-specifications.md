# Phase 1: Comprehensive Test Specifications
## LionAGI QE Fleet - Test Strategy & Implementation Guide

**Generated**: 2025-11-12
**Target Coverage**: 85% minimum (100% for critical paths)
**Mutation Score**: >80%
**Framework**: pytest, pytest-asyncio, pytest-mock, httpx, locust, pact-python

---

## 1. Unit Test Strategy

### 1.1 MCP Server Tests (`tests/mcp/test_mcp_server_unit.py`)

**Target Module**: `src/lionagi_qe/mcp/mcp_server.py`

#### Test Categories

**A. Initialization & Configuration**
```python
class TestMCPServerInitialization:
    """Test MCP server initialization and configuration"""

    def test_server_init_default_settings(self):
        """Test server initializes with default configuration"""
        # GIVEN: Default initialization parameters
        # WHEN: MCPServer is created
        # THEN: Server has correct name, routing enabled, learning disabled

    def test_server_init_custom_name(self):
        """Test server accepts custom name"""
        # GIVEN: Custom server name "custom-qe"
        # WHEN: MCPServer is created with name="custom-qe"
        # THEN: Server name is "custom-qe"

    def test_server_init_routing_disabled(self):
        """Test server can disable routing"""
        # GIVEN: enable_routing=False
        # WHEN: MCPServer is created
        # THEN: Routing is disabled

    def test_server_init_learning_enabled(self):
        """Test server can enable Q-learning"""
        # GIVEN: enable_learning=True
        # WHEN: MCPServer is created
        # THEN: Learning is enabled
```

**B. Fleet Initialization**
```python
class TestFleetInitialization:
    """Test QE Fleet initialization within MCP server"""

    @pytest.mark.asyncio
    async def test_initialize_fleet_creates_fleet(self):
        """Test fleet initialization creates QEFleet instance"""
        # GIVEN: MCPServer instance
        # WHEN: initialize_fleet() is called
        # THEN: self.fleet is not None and is QEFleet instance

    @pytest.mark.asyncio
    async def test_initialize_fleet_registers_agents(self):
        """Test fleet initialization registers core agents"""
        # GIVEN: Initialized MCPServer
        # WHEN: initialize_fleet() completes
        # THEN: test-generator, test-executor, fleet-commander agents registered

    @pytest.mark.asyncio
    async def test_initialize_fleet_idempotent(self):
        """Test fleet initialization is idempotent"""
        # GIVEN: Already initialized fleet
        # WHEN: initialize_fleet() called again
        # THEN: Warning logged, fleet unchanged, no error raised

    @pytest.mark.asyncio
    async def test_initialize_fleet_sets_fleet_instance(self, mocker):
        """Test fleet initialization calls set_fleet_instance"""
        # GIVEN: MCPServer instance
        # WHEN: initialize_fleet() is called
        # THEN: mcp_tools.set_fleet_instance() called with fleet
```

**C. Tool Registration**
```python
class TestToolRegistration:
    """Test MCP tool registration"""

    def test_register_tools_count(self):
        """Test correct number of tools registered"""
        # GIVEN: MCPServer instance
        # WHEN: Tools are registered
        # THEN: 17 tools registered (per mcp_tools.py)

    def test_register_core_testing_tools(self):
        """Test core testing tools registered"""
        # GIVEN: MCPServer instance
        # WHEN: _register_tools() is called
        # THEN: test_generate, test_execute, coverage_analyze, quality_gate registered

    def test_register_performance_security_tools(self):
        """Test performance & security tools registered"""
        # GIVEN: MCPServer instance
        # WHEN: _register_tools() is called
        # THEN: performance_test, security_scan registered

    def test_register_fleet_orchestration_tools(self):
        """Test fleet orchestration tools registered"""
        # GIVEN: MCPServer instance
        # WHEN: _register_tools() is called
        # THEN: fleet_orchestrate, get_fleet_status registered

    def test_register_advanced_tools(self):
        """Test advanced tools registered"""
        # GIVEN: MCPServer instance
        # WHEN: _register_tools() is called
        # THEN: requirements_validate, flaky_test_hunt, api_contract_validate,
        #       regression_risk_analyze, test_data_generate, visual_test,
        #       chaos_test, deployment_readiness registered

    def test_register_streaming_tools(self):
        """Test streaming tools registered"""
        # GIVEN: MCPServer instance
        # WHEN: _register_tools() is called
        # THEN: test_execute_stream registered
```

**D. Server Lifecycle**
```python
class TestServerLifecycle:
    """Test MCP server lifecycle management"""

    @pytest.mark.asyncio
    async def test_start_initializes_fleet(self, mocker):
        """Test start() calls initialize_fleet()"""
        # GIVEN: MCPServer instance
        # WHEN: start() is called
        # THEN: initialize_fleet() was called

    @pytest.mark.asyncio
    async def test_stop_exports_state(self, mocker):
        """Test stop() exports fleet state"""
        # GIVEN: MCPServer with initialized fleet
        # WHEN: stop() is called
        # THEN: fleet.export_state() was called

    @pytest.mark.asyncio
    async def test_stop_handles_no_fleet(self):
        """Test stop() handles case when fleet is None"""
        # GIVEN: MCPServer without initialized fleet
        # WHEN: stop() is called
        # THEN: No error raised

    def test_get_server_returns_fastmcp(self):
        """Test get_server() returns FastMCP instance"""
        # GIVEN: MCPServer instance
        # WHEN: get_server() is called
        # THEN: Returns FastMCP instance
```

**E. Factory & Entrypoint**
```python
class TestServerFactory:
    """Test MCP server factory functions"""

    def test_create_mcp_server_default(self):
        """Test create_mcp_server() with defaults"""
        # GIVEN: No parameters
        # WHEN: create_mcp_server() is called
        # THEN: Returns MCPServer with default settings

    def test_create_mcp_server_custom_config(self):
        """Test create_mcp_server() with custom config"""
        # GIVEN: Custom name, routing, learning parameters
        # WHEN: create_mcp_server(...) is called
        # THEN: Returns MCPServer with custom settings

    @pytest.mark.asyncio
    async def test_run_mcp_server_starts_server(self, mocker):
        """Test run_mcp_server() starts server"""
        # GIVEN: Mocked server.start() and server.get_server().run()
        # WHEN: run_mcp_server() is called (with timeout)
        # THEN: server.start() and server.get_server().run() called
```

**Coverage Target**: 95% (critical initialization path = 100%)

---

### 1.2 MCP Tools Tests (`tests/mcp/test_mcp_tools_unit.py`)

**Target Module**: `src/lionagi_qe/mcp/mcp_tools.py`

#### Test Categories

**A. Fleet Instance Management**
```python
class TestFleetInstanceManagement:
    """Test global fleet instance management"""

    def test_set_fleet_instance(self):
        """Test setting global fleet instance"""
        # GIVEN: A QEFleet instance
        # WHEN: set_fleet_instance(fleet) is called
        # THEN: Global _fleet_instance is set

    def test_get_fleet_instance_when_set(self):
        """Test retrieving fleet instance when set"""
        # GIVEN: Fleet instance has been set
        # WHEN: get_fleet_instance() is called
        # THEN: Returns the fleet instance

    def test_get_fleet_instance_raises_when_not_set(self):
        """Test get_fleet_instance() raises when not initialized"""
        # GIVEN: Fleet instance not set (reset global state)
        # WHEN: get_fleet_instance() is called
        # THEN: Raises RuntimeError with message "Fleet not initialized"
```

**B. Core Testing Tools**
```python
class TestCoreTestingTools:
    """Test core testing tool functions"""

    @pytest.mark.asyncio
    async def test_test_generate_basic(self, mock_fleet):
        """Test test_generate() with default parameters"""
        # GIVEN: Mock fleet with test-generator agent
        # WHEN: test_generate(code="def add(a,b): return a+b") called
        # THEN: Returns dict with test_code, test_name, assertions, edge_cases

    @pytest.mark.asyncio
    async def test_test_generate_custom_framework(self, mock_fleet):
        """Test test_generate() with custom framework"""
        # GIVEN: Mock fleet
        # WHEN: test_generate(..., framework=TestFramework.JEST) called
        # THEN: Task context contains framework="jest"

    @pytest.mark.asyncio
    async def test_test_generate_coverage_target(self, mock_fleet):
        """Test test_generate() with coverage target"""
        # GIVEN: Mock fleet
        # WHEN: test_generate(..., coverage_target=90.0) called
        # THEN: Task context contains coverage_target=90.0

    @pytest.mark.asyncio
    async def test_test_execute_basic(self, mock_fleet):
        """Test test_execute() with default parameters"""
        # GIVEN: Mock fleet with test-executor agent
        # WHEN: test_execute(test_path="tests/") called
        # THEN: Returns dict with passed, failed, skipped, coverage, duration

    @pytest.mark.asyncio
    async def test_test_execute_parallel_disabled(self, mock_fleet):
        """Test test_execute() with parallel disabled"""
        # GIVEN: Mock fleet
        # WHEN: test_execute(..., parallel=False) called
        # THEN: Task context contains parallel=False

    @pytest.mark.asyncio
    async def test_test_execute_timeout(self, mock_fleet):
        """Test test_execute() with custom timeout"""
        # GIVEN: Mock fleet
        # WHEN: test_execute(..., timeout=600) called
        # THEN: Task context contains timeout=600

    @pytest.mark.asyncio
    async def test_coverage_analyze_basic(self, mock_fleet):
        """Test coverage_analyze() with default parameters"""
        # GIVEN: Mock fleet with coverage-analyzer agent
        # WHEN: coverage_analyze(source_path="src/", test_path="tests/") called
        # THEN: Returns dict with overall_coverage, file_coverage, gaps

    @pytest.mark.asyncio
    async def test_coverage_analyze_algorithm(self, mock_fleet):
        """Test coverage_analyze() with sublinear algorithm"""
        # GIVEN: Mock fleet
        # WHEN: coverage_analyze(..., algorithm="sublinear") called
        # THEN: Task context contains algorithm="sublinear"

    @pytest.mark.asyncio
    async def test_quality_gate_default_thresholds(self, mock_fleet):
        """Test quality_gate() with default thresholds"""
        # GIVEN: Mock fleet with quality-gate agent
        # WHEN: quality_gate(metrics={"coverage": 85}) called
        # THEN: Uses default thresholds (coverage: 80, complexity: 10, etc.)

    @pytest.mark.asyncio
    async def test_quality_gate_custom_thresholds(self, mock_fleet):
        """Test quality_gate() with custom thresholds"""
        # GIVEN: Mock fleet
        # WHEN: quality_gate(metrics={}, thresholds={"coverage": 95}) called
        # THEN: Uses custom thresholds
```

**C. Performance & Security Tools**
```python
class TestPerformanceSecurityTools:
    """Test performance and security tool functions"""

    @pytest.mark.asyncio
    async def test_performance_test_basic(self, mock_fleet):
        """Test performance_test() with default parameters"""
        # GIVEN: Mock fleet with performance-tester agent
        # WHEN: performance_test(endpoint="http://api.example.com") called
        # THEN: Returns dict with requests_per_second, response_time_p50/p95/p99

    @pytest.mark.asyncio
    async def test_performance_test_tool_selection(self, mock_fleet):
        """Test performance_test() with different tools"""
        # GIVEN: Mock fleet
        # WHEN: performance_test(..., tool="k6") called
        # THEN: Task context contains tool="k6"

    @pytest.mark.asyncio
    async def test_security_scan_comprehensive(self, mock_fleet):
        """Test security_scan() with comprehensive scan"""
        # GIVEN: Mock fleet with security-scanner agent
        # WHEN: security_scan(path="src/", scan_type=ScanType.COMPREHENSIVE) called
        # THEN: Returns dict with vulnerabilities, severity_counts, risk_score

    @pytest.mark.asyncio
    async def test_security_scan_sast_only(self, mock_fleet):
        """Test security_scan() with SAST only"""
        # GIVEN: Mock fleet
        # WHEN: security_scan(..., scan_type=ScanType.SAST) called
        # THEN: Task context contains scan_type="sast"
```

**D. Fleet Orchestration Tools**
```python
class TestFleetOrchestrationTools:
    """Test fleet orchestration tool functions"""

    @pytest.mark.asyncio
    async def test_fleet_orchestrate_pipeline(self, mock_fleet):
        """Test fleet_orchestrate() with pipeline workflow"""
        # GIVEN: Mock fleet with execute_pipeline method
        # WHEN: fleet_orchestrate(workflow="pipeline", ...) called
        # THEN: fleet.execute_pipeline() was called

    @pytest.mark.asyncio
    async def test_fleet_orchestrate_parallel(self, mock_fleet):
        """Test fleet_orchestrate() with parallel workflow"""
        # GIVEN: Mock fleet with execute_parallel method
        # WHEN: fleet_orchestrate(workflow="parallel", ...) called
        # THEN: fleet.execute_parallel() was called

    @pytest.mark.asyncio
    async def test_fleet_orchestrate_fan_out_fan_in(self, mock_fleet):
        """Test fleet_orchestrate() with fan-out-fan-in workflow"""
        # GIVEN: Mock fleet with execute_fan_out_fan_in method
        # WHEN: fleet_orchestrate(workflow="fan-out-fan-in", ...) called
        # THEN: fleet.execute_fan_out_fan_in() was called

    @pytest.mark.asyncio
    async def test_fleet_orchestrate_unknown_workflow(self, mock_fleet):
        """Test fleet_orchestrate() with unknown workflow raises error"""
        # GIVEN: Mock fleet
        # WHEN: fleet_orchestrate(workflow="unknown", ...) called
        # THEN: Raises ValueError with message "Unknown workflow type"

    @pytest.mark.asyncio
    async def test_get_fleet_status(self, mock_fleet):
        """Test get_fleet_status() returns status dict"""
        # GIVEN: Mock fleet with get_status method
        # WHEN: get_fleet_status() called
        # THEN: Returns dict with initialized, agents, memory_stats, etc.
```

**E. Advanced Tools (Sample)**
```python
class TestAdvancedTools:
    """Test advanced tool functions (sample tests)"""

    @pytest.mark.asyncio
    async def test_flaky_test_hunt_basic(self, mock_fleet):
        """Test flaky_test_hunt() with default parameters"""
        # GIVEN: Mock fleet with flaky-test-hunter agent
        # WHEN: flaky_test_hunt(test_path="tests/") called
        # THEN: Returns dict with flaky_tests, stability_scores, root_causes

    @pytest.mark.asyncio
    async def test_api_contract_validate_single_version(self, mock_fleet):
        """Test api_contract_validate() with single version"""
        # GIVEN: Mock fleet with api-contract-validator agent
        # WHEN: api_contract_validate(spec_path="api.yaml", version_a="v1") called
        # THEN: Returns dict with valid, warnings, recommendations

    @pytest.mark.asyncio
    async def test_test_data_generate_realistic(self, mock_fleet):
        """Test test_data_generate() with realistic data"""
        # GIVEN: Mock fleet with test-data-architect agent
        # WHEN: test_data_generate(schema={...}, count=1000, realistic=True) called
        # THEN: Returns dict with data, record_count, records_per_second
```

**F. Streaming Tools**
```python
class TestStreamingTools:
    """Test streaming tool functions"""

    @pytest.mark.asyncio
    async def test_test_execute_stream_yields_progress(self, mock_fleet):
        """Test test_execute_stream() yields progress events"""
        # GIVEN: Mock fleet
        # WHEN: test_execute_stream(test_path="tests/") iterated
        # THEN: Yields progress events with type="progress"

    @pytest.mark.asyncio
    async def test_test_execute_stream_yields_result(self, mock_fleet):
        """Test test_execute_stream() yields final result"""
        # GIVEN: Mock fleet
        # WHEN: test_execute_stream(test_path="tests/") fully iterated
        # THEN: Final event has type="result" with test execution data
```

**Coverage Target**: 90% (core tools = 100%)

---

### 1.3 Storage Backend Tests

#### A. Redis Memory Tests (`tests/persistence/test_redis_memory_unit.py`)

**Target Module**: `src/lionagi_qe/persistence/redis_memory.py`

```python
class TestRedisMemoryInitialization:
    """Test Redis memory initialization"""

    def test_init_default_settings(self, mocker):
        """Test initialization with default settings"""
        # GIVEN: Default host, port, db
        # WHEN: RedisMemory() is created
        # THEN: Connects to localhost:6379, db=0

    def test_init_custom_settings(self, mocker):
        """Test initialization with custom settings"""
        # GIVEN: Custom host="redis-host", port=6380, db=1
        # WHEN: RedisMemory(...) is created
        # THEN: Connects with custom settings

    def test_init_connection_pool(self, mocker):
        """Test connection pool created with correct size"""
        # GIVEN: max_connections=20
        # WHEN: RedisMemory(max_connections=20) is created
        # THEN: Connection pool has max_connections=20

    def test_init_ping_success(self, mocker):
        """Test successful Redis ping on initialization"""
        # GIVEN: Mock Redis client
        # WHEN: RedisMemory() is created
        # THEN: client.ping() was called

    def test_init_connection_failure_raises(self, mocker):
        """Test connection failure raises exception"""
        # GIVEN: Mock Redis client that raises ConnectionError on ping
        # WHEN: RedisMemory() is created
        # THEN: Raises redis.ConnectionError


class TestRedisMemoryStore:
    """Test Redis memory store operations"""

    @pytest.mark.asyncio
    async def test_store_with_ttl(self, redis_memory, mocker):
        """Test storing value with TTL"""
        # GIVEN: RedisMemory instance
        # WHEN: store("key", "value", ttl=3600) called
        # THEN: client.setex("key", 3600, json_data) called

    @pytest.mark.asyncio
    async def test_store_without_ttl(self, redis_memory, mocker):
        """Test storing value without TTL"""
        # GIVEN: RedisMemory instance
        # WHEN: store("key", "value", ttl=None) called
        # THEN: client.set("key", json_data) called

    @pytest.mark.asyncio
    async def test_store_includes_metadata(self, redis_memory, mocker):
        """Test stored value includes metadata"""
        # GIVEN: RedisMemory instance
        # WHEN: store("key", {"data": 123}, partition="test") called
        # THEN: Stored JSON contains value, partition, created_at


class TestRedisMemoryRetrieve:
    """Test Redis memory retrieve operations"""

    @pytest.mark.asyncio
    async def test_retrieve_existing_key(self, redis_memory, mocker):
        """Test retrieving existing key"""
        # GIVEN: Key exists in Redis with value
        # WHEN: retrieve("key") called
        # THEN: Returns stored value

    @pytest.mark.asyncio
    async def test_retrieve_non_existing_key(self, redis_memory, mocker):
        """Test retrieving non-existing key returns None"""
        # GIVEN: Key does not exist in Redis
        # WHEN: retrieve("key") called
        # THEN: Returns None

    @pytest.mark.asyncio
    async def test_retrieve_expired_key(self, redis_memory, mocker):
        """Test retrieving expired key returns None"""
        # GIVEN: Key existed but TTL expired
        # WHEN: retrieve("key") called
        # THEN: Returns None


class TestRedisMemorySearch:
    """Test Redis memory search operations"""

    @pytest.mark.asyncio
    async def test_search_pattern_match(self, redis_memory, mocker):
        """Test search with pattern returns matching keys"""
        # GIVEN: Keys "aqe/test-plan/v1", "aqe/test-plan/v2" exist
        # WHEN: search("aqe/test-plan/*") called
        # THEN: Returns dict with both keys and values

    @pytest.mark.asyncio
    async def test_search_no_match(self, redis_memory, mocker):
        """Test search with no matches returns empty dict"""
        # GIVEN: No keys match pattern
        # WHEN: search("nonexistent/*") called
        # THEN: Returns empty dict {}


class TestRedisMemoryPartitions:
    """Test Redis memory partition operations"""

    @pytest.mark.asyncio
    async def test_clear_partition(self, redis_memory, mocker):
        """Test clearing partition deletes matching keys"""
        # GIVEN: Multiple keys in "test-plan" partition
        # WHEN: clear_partition("test-plan") called
        # THEN: All keys in partition deleted

    @pytest.mark.asyncio
    async def test_clear_partition_empty(self, redis_memory, mocker):
        """Test clearing empty partition"""
        # GIVEN: No keys in partition
        # WHEN: clear_partition("empty") called
        # THEN: No error, log shows "already empty"


class TestRedisMemoryStats:
    """Test Redis memory statistics"""

    @pytest.mark.asyncio
    async def test_get_stats(self, redis_memory, mocker):
        """Test get_stats returns statistics"""
        # GIVEN: RedisMemory with data
        # WHEN: get_stats() called
        # THEN: Returns dict with total_keys, memory_used, etc.
```

**Coverage Target**: 85%

#### B. PostgreSQL Memory Tests (`tests/persistence/test_postgres_memory_unit.py`)

**Target Module**: `src/lionagi_qe/persistence/postgres_memory.py`

*(Similar structure to Redis tests but focused on PostgreSQL-specific features like ACID guarantees, Q-learning table reuse, etc.)*

---

### 1.4 Base Agent Tests (`tests/agents/test_base_agent_unit.py`)

**Target Module**: `src/lionagi_qe/core/base_agent.py`

```python
class TestBaseAgentInitialization:
    """Test BaseQEAgent initialization"""

    def test_init_with_memory_instance(self, simple_model):
        """Test initialization with memory instance"""
        # GIVEN: Memory instance (PostgresMemory/RedisMemory)
        # WHEN: BaseQEAgent(..., memory=memory) created
        # THEN: Agent uses provided memory

    def test_init_with_qememory_shows_warning(self, simple_model):
        """Test initialization with QEMemory shows deprecation warning"""
        # GIVEN: QEMemory instance
        # WHEN: BaseQEAgent(..., memory=qe_memory) created
        # THEN: DeprecationWarning raised

    def test_init_with_memory_config_postgres(self, simple_model, mocker):
        """Test auto-initialization with PostgreSQL config"""
        # GIVEN: memory_config={"type": "postgres", "db_manager": mock_db}
        # WHEN: BaseQEAgent(...) created
        # THEN: PostgresMemory initialized

    def test_init_with_memory_config_redis(self, simple_model, mocker):
        """Test auto-initialization with Redis config"""
        # GIVEN: memory_config={"type": "redis", "host": "localhost"}
        # WHEN: BaseQEAgent(...) created
        # THEN: RedisMemory initialized

    def test_init_with_memory_config_session(self, simple_model):
        """Test auto-initialization with Session.context"""
        # GIVEN: memory_config={"type": "session"}
        # WHEN: BaseQEAgent(...) created
        # THEN: Session.context used as memory

    def test_init_default_memory(self, simple_model):
        """Test default memory uses Session.context"""
        # GIVEN: No memory parameter
        # WHEN: BaseQEAgent(...) created
        # THEN: Session.context used as memory


class TestMemoryBackendType:
    """Test memory backend type detection"""

    def test_memory_backend_type_postgres(self, base_agent_postgres):
        """Test detecting PostgreSQL backend"""
        # GIVEN: Agent with PostgresMemory
        # WHEN: memory_backend_type property accessed
        # THEN: Returns "postgres"

    def test_memory_backend_type_redis(self, base_agent_redis):
        """Test detecting Redis backend"""
        # GIVEN: Agent with RedisMemory
        # WHEN: memory_backend_type property accessed
        # THEN: Returns "redis"

    def test_memory_backend_type_session(self, base_agent_session):
        """Test detecting Session.context backend"""
        # GIVEN: Agent with Session.context
        # WHEN: memory_backend_type property accessed
        # THEN: Returns "session"


class TestMemoryOperations:
    """Test agent memory operations"""

    @pytest.mark.asyncio
    async def test_store_result(self, base_agent):
        """Test storing result in memory"""
        # GIVEN: BaseQEAgent instance
        # WHEN: store_result("test", {"data": 123}) called
        # THEN: Memory contains "aqe/{agent_id}/test" with value

    @pytest.mark.asyncio
    async def test_retrieve_context(self, base_agent):
        """Test retrieving context from memory"""
        # GIVEN: Value stored at "aqe/context"
        # WHEN: retrieve_context("aqe/context") called
        # THEN: Returns stored value

    @pytest.mark.asyncio
    async def test_get_memory_with_default(self, base_agent):
        """Test get_memory returns default for missing key"""
        # GIVEN: Key does not exist
        # WHEN: get_memory("missing", default="fallback") called
        # THEN: Returns "fallback"

    @pytest.mark.asyncio
    async def test_search_memory_pattern(self, base_agent):
        """Test searching memory with pattern"""
        # GIVEN: Multiple keys matching pattern
        # WHEN: search_memory("aqe/test-*") called
        # THEN: Returns dict of matching keys


class TestQLearningIntegration:
    """Test Q-learning integration in BaseQEAgent"""

    @pytest.mark.asyncio
    async def test_execute_with_learning_selects_action(self, base_agent_qlearn, mocker):
        """Test execute_with_learning selects action"""
        # GIVEN: Agent with Q-learning enabled
        # WHEN: execute_with_learning(task) called
        # THEN: q_service.select_action() called

    @pytest.mark.asyncio
    async def test_learn_from_execution_updates_q_value(self, base_agent_qlearn, mocker):
        """Test _learn_from_execution updates Q-value"""
        # GIVEN: Task completed with result
        # WHEN: _learn_from_execution(task, result) called
        # THEN: q_service.update_q_value() called

    @pytest.mark.asyncio
    async def test_learn_from_execution_stores_trajectory(self, base_agent_qlearn, mocker):
        """Test _learn_from_execution stores trajectory"""
        # GIVEN: Task completed with result
        # WHEN: _learn_from_execution(task, result) called
        # THEN: q_service.store_experience() called


class TestFuzzyParsing:
    """Test fuzzy parsing methods"""

    @pytest.mark.asyncio
    async def test_safe_operate_standard_parsing_success(self, base_agent, mocker):
        """Test safe_operate with successful standard parsing"""
        # GIVEN: LLM returns well-formed JSON
        # WHEN: safe_operate(instruction, response_format) called
        # THEN: Returns parsed Pydantic model

    @pytest.mark.asyncio
    async def test_safe_operate_fuzzy_fallback(self, base_agent, mocker):
        """Test safe_operate falls back to fuzzy parsing"""
        # GIVEN: LLM returns malformed JSON
        # WHEN: safe_operate(instruction, response_format) called
        # THEN: Fuzzy parsing used, returns valid model

    @pytest.mark.asyncio
    async def test_safe_parse_response_direct_success(self, base_agent):
        """Test safe_parse_response with valid JSON"""
        # GIVEN: Valid JSON response
        # WHEN: safe_parse_response(response, model_class) called
        # THEN: Returns parsed model

    @pytest.mark.asyncio
    async def test_safe_parse_response_fuzzy_fallback(self, base_agent):
        """Test safe_parse_response fuzzy fallback"""
        # GIVEN: Malformed JSON response
        # WHEN: safe_parse_response(response, model_class) called
        # THEN: Fuzzy parsing used, returns valid model
```

**Coverage Target**: 95% (critical agent base = 100%)

---

## 2. Integration Test Strategy

### 2.1 MCP Server Integration (`tests/integration/test_mcp_server_integration.py`)

**Focus**: Full MCP server lifecycle with real fleet coordination

```python
class TestMCPServerIntegration:
    """Integration tests for MCP server with real fleet"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_server_full_lifecycle(self):
        """Test complete server initialization, tool execution, shutdown"""
        # GIVEN: MCPServer instance
        # WHEN: Start server, execute tool, stop server
        # THEN: All operations succeed, state exported

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_execution_end_to_end(self):
        """Test tool execution from MCP layer to agent"""
        # GIVEN: Initialized MCP server
        # WHEN: test_generate() tool called with real code
        # THEN: Agent executes, returns valid test code

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fleet_coordination_via_mcp(self):
        """Test multi-agent coordination via MCP tools"""
        # GIVEN: Initialized MCP server with multiple agents
        # WHEN: fleet_orchestrate() called with pipeline workflow
        # THEN: Agents execute in sequence, results aggregated
```

### 2.2 API → Storage Integration (`tests/integration/test_api_storage_integration.py`)

**Focus**: MCP tool calls → Fleet → Memory backends

```python
class TestAPIStorageIntegration:
    """Integration tests for API → Storage flow"""

    @pytest.mark.integration
    @pytest.mark.redis
    @pytest.mark.asyncio
    async def test_test_generation_stores_in_redis(self, redis_memory):
        """Test test generation stores results in Redis"""
        # GIVEN: Fleet with Redis memory backend
        # WHEN: test_generate() tool called
        # THEN: Generated tests stored in Redis at aqe/test-generator/tasks/{task_id}/result

    @pytest.mark.integration
    @pytest.mark.postgres
    @pytest.mark.asyncio
    async def test_coverage_analysis_stores_in_postgres(self, postgres_memory):
        """Test coverage analysis stores results in PostgreSQL"""
        # GIVEN: Fleet with PostgreSQL memory backend
        # WHEN: coverage_analyze() tool called
        # THEN: Coverage data stored in PostgreSQL

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cross_agent_memory_sharing(self):
        """Test agents share data via memory"""
        # GIVEN: Test generator stores test plan
        # WHEN: Test executor retrieves test plan
        # THEN: Test executor receives correct data
```

### 2.3 Celery + Redis Queue Integration (`tests/integration/test_queue_integration.py`)

**Focus**: Asynchronous task processing with Celery and Redis

```python
class TestCeleryQueueIntegration:
    """Integration tests for Celery + Redis queue"""

    @pytest.mark.integration
    @pytest.mark.redis
    @pytest.mark.asyncio
    async def test_async_test_generation_via_queue(self, celery_app, redis_broker):
        """Test asynchronous test generation via Celery"""
        # GIVEN: Celery app configured with Redis broker
        # WHEN: test_generate.delay(code) called
        # THEN: Task queued, processed asynchronously, result retrieved

    @pytest.mark.integration
    @pytest.mark.redis
    @pytest.mark.asyncio
    async def test_queue_multiple_tasks(self, celery_app):
        """Test queueing multiple tasks in parallel"""
        # GIVEN: 10 test generation tasks
        # WHEN: All tasks submitted to queue
        # THEN: All tasks processed, results collected

    @pytest.mark.integration
    @pytest.mark.redis
    @pytest.mark.asyncio
    async def test_task_retry_on_failure(self, celery_app, mocker):
        """Test task retry mechanism on failure"""
        # GIVEN: Task that fails once then succeeds
        # WHEN: Task submitted to queue
        # THEN: Task retries automatically, succeeds on retry
```

### 2.4 WebSocket Streaming Integration (`tests/integration/test_websocket_streaming.py`)

**Focus**: Real-time progress streaming via WebSocket

```python
class TestWebSocketStreaming:
    """Integration tests for WebSocket streaming"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_test_execution_stream_websocket(self, websocket_server):
        """Test streaming test execution progress via WebSocket"""
        # GIVEN: WebSocket server connected to streaming tool
        # WHEN: test_execute_stream() started, client connects
        # THEN: Client receives progress events in real-time

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_coverage_analysis_stream_websocket(self, websocket_server):
        """Test streaming coverage analysis via WebSocket"""
        # GIVEN: WebSocket server connected to coverage_analyze_stream()
        # WHEN: Analysis started, client connects
        # THEN: Client receives gap discovery events in real-time
```

---

## 3. Test Coverage Goals

### 3.1 Minimum Coverage Requirements

| Component | Target Coverage | Critical Paths |
|-----------|----------------|----------------|
| **MCP Server** | 95% | Initialization: 100% |
| **MCP Tools** | 90% | Core tools: 100% |
| **Base Agent** | 95% | Memory ops: 100% |
| **Redis Memory** | 85% | Store/Retrieve: 100% |
| **PostgreSQL Memory** | 85% | Store/Retrieve: 100% |
| **Test Generator Agent** | 90% | Test generation: 100% |
| **Test Executor Agent** | 90% | Test execution: 100% |
| **Coverage Analyzer** | 90% | Gap detection: 100% |
| **Fleet Commander** | 85% | Orchestration: 100% |
| **Authentication** | 100% | All auth paths |
| **API Endpoints** | 100% | All endpoints |

### 3.2 Mutation Testing Score

**Target**: >80% mutation score across codebase

**Critical Components**: 100% mutation score
- Authentication logic
- Storage operations (store, retrieve, delete)
- API endpoint handlers
- Agent task execution

---

## 4. Test Frameworks & Tools

### 4.1 Core Testing Frameworks

```toml
# pytest configuration (from pyproject.toml)
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=src/lionagi_qe --cov-report=html --cov-report=term"
```

**Dependencies** (from `pyproject.toml`):
- `pytest>=8.0.0` - Core test framework
- `pytest-asyncio>=1.1.0` - Async test support
- `pytest-cov>=6.0.0` - Coverage measurement
- `pytest-mock>=3.12.0` - Mocking utilities
- `hypothesis>=6.100.0` - Property-based testing
- `coverage>=7.0.0` - Coverage reporting

### 4.2 API Testing

**Framework**: FastAPI TestClient + httpx

```python
# Example API test structure
from fastapi.testclient import TestClient
import httpx

class TestMCPAPIEndpoints:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_test_generate_endpoint(self, client):
        """Test POST /tools/test_generate endpoint"""
        response = client.post("/tools/test_generate", json={
            "code": "def add(a, b): return a + b",
            "framework": "pytest"
        })
        assert response.status_code == 200
        assert "test_code" in response.json()
```

### 4.3 Load Testing

**Framework**: locust + k6

```python
# Locust load test example
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

**k6 script example**:
```javascript
// k6 load test for MCP API
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  vus: 50,
  duration: '60s',
};

export default function () {
  let response = http.post('http://localhost:8000/tools/test_generate', JSON.stringify({
    code: 'def example(): pass',
    framework: 'pytest'
  }));
  check(response, { 'status was 200': (r) => r.status == 200 });
}
```

### 4.4 Contract Testing

**Framework**: pact-python

```python
# Pact consumer test example
from pact import Consumer, Provider

pact = Consumer('mcp-client').has_pact_with(Provider('mcp-server'))

def test_test_generate_contract():
    """Test contract for test_generate tool"""
    (pact
     .given('a valid code snippet')
     .upon_receiving('a test generation request')
     .with_request('post', '/tools/test_generate')
     .will_respond_with(200, body={
         'test_code': 'def test_example(): ...',
         'test_name': 'test_example',
         'assertions': ['assert True']
     }))

    with pact:
        # Execute actual API call
        result = test_generate(code="def example(): pass")
        assert result['test_code'] is not None
```

---

## 5. Test File Structure

```
tests/
├── conftest.py                          # Shared fixtures
├── unit/
│   ├── mcp/
│   │   ├── test_mcp_server_unit.py      # MCP server unit tests
│   │   └── test_mcp_tools_unit.py       # MCP tools unit tests
│   ├── persistence/
│   │   ├── test_redis_memory_unit.py    # Redis memory unit tests
│   │   └── test_postgres_memory_unit.py # PostgreSQL memory unit tests
│   ├── agents/
│   │   ├── test_base_agent_unit.py      # Base agent unit tests
│   │   ├── test_test_generator_unit.py  # Test generator unit tests
│   │   └── test_test_executor_unit.py   # Test executor unit tests
│   └── core/
│       ├── test_task_unit.py            # Task unit tests
│       └── test_router_unit.py          # Router unit tests
├── integration/
│   ├── test_mcp_server_integration.py   # MCP server integration
│   ├── test_api_storage_integration.py  # API → Storage integration
│   ├── test_queue_integration.py        # Celery + Redis integration
│   └── test_websocket_streaming.py      # WebSocket streaming integration
├── api/
│   ├── test_endpoints.py                # API endpoint tests
│   └── test_contracts.py                # Contract tests (Pact)
├── performance/
│   ├── test_load_locust.py              # Locust load tests
│   └── test_load_k6.js                  # k6 load tests
└── mutation/
    └── test_mutation_coverage.py        # Mutation testing
```

---

## 6. Test Case Templates

### 6.1 Unit Test Template

```python
"""
Unit tests for {MODULE_NAME}

Tests cover:
- Initialization and configuration
- Core functionality
- Error handling
- Edge cases
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from {module_path} import {ClassName}


class Test{ClassName}Initialization:
    """Test {ClassName} initialization"""

    def test_init_default_settings(self):
        """Test initialization with default settings"""
        # GIVEN: Default initialization parameters
        instance = {ClassName}()

        # THEN: Instance has expected default values
        assert instance.attribute == expected_value

    def test_init_custom_settings(self):
        """Test initialization with custom settings"""
        # GIVEN: Custom initialization parameters
        instance = {ClassName}(custom_param=custom_value)

        # THEN: Instance uses custom values
        assert instance.custom_param == custom_value


class Test{ClassName}CoreFunctionality:
    """Test {ClassName} core functionality"""

    @pytest.mark.asyncio
    async def test_method_success(self):
        """Test method executes successfully"""
        # GIVEN: Instance with valid state
        instance = {ClassName}()

        # WHEN: Method called with valid inputs
        result = await instance.method(valid_input)

        # THEN: Returns expected result
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_method_error_handling(self):
        """Test method handles errors gracefully"""
        # GIVEN: Instance with error condition
        instance = {ClassName}()

        # WHEN: Method called with invalid inputs
        # THEN: Raises expected exception
        with pytest.raises(ExpectedException):
            await instance.method(invalid_input)


class Test{ClassName}EdgeCases:
    """Test {ClassName} edge cases"""

    def test_edge_case_empty_input(self):
        """Test method handles empty input"""
        # GIVEN: Instance
        instance = {ClassName}()

        # WHEN: Method called with empty input
        result = instance.method([])

        # THEN: Returns expected default result
        assert result == default_result
```

### 6.2 Integration Test Template

```python
"""
Integration tests for {COMPONENT_NAME}

Tests cover:
- End-to-end workflows
- Component interactions
- Real backend integration
- Data persistence
"""

import pytest
from {module_path} import {ComponentA}, {ComponentB}


@pytest.mark.integration
class Test{Component}Integration:
    """Test {Component} integration with real backends"""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, real_backend):
        """Test complete workflow from A to B"""
        # GIVEN: Real backend and components
        component_a = {ComponentA}(backend=real_backend)
        component_b = {ComponentB}(backend=real_backend)

        # WHEN: Execute workflow
        result_a = await component_a.execute(input_data)
        result_b = await component_b.execute(result_a)

        # THEN: Final result is correct
        assert result_b.status == "completed"
        assert result_b.data == expected_data

        # AND: Data persisted correctly
        stored_data = await real_backend.retrieve(key)
        assert stored_data == expected_stored_data

    @pytest.mark.redis
    @pytest.mark.asyncio
    async def test_redis_integration(self, redis_backend):
        """Test integration with Redis backend"""
        # GIVEN: Component with Redis backend
        component = {Component}(backend=redis_backend)

        # WHEN: Execute operation
        await component.execute(data)

        # THEN: Data stored in Redis
        stored = await redis_backend.retrieve(key)
        assert stored == data

    @pytest.mark.postgres
    @pytest.mark.asyncio
    async def test_postgres_integration(self, postgres_backend):
        """Test integration with PostgreSQL backend"""
        # GIVEN: Component with PostgreSQL backend
        component = {Component}(backend=postgres_backend)

        # WHEN: Execute operation
        await component.execute(data)

        # THEN: Data stored in PostgreSQL
        stored = await postgres_backend.retrieve(key)
        assert stored == data
```

### 6.3 API Test Template

```python
"""
API endpoint tests for {ENDPOINT_NAME}

Tests cover:
- HTTP methods (GET, POST, PUT, DELETE)
- Request validation
- Response format
- Error responses
- Authentication
"""

import pytest
from fastapi.testclient import TestClient
from {app_module} import app


class Test{Endpoint}API:
    """Test {ENDPOINT} API endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_post_success(self, client):
        """Test POST request with valid data"""
        # GIVEN: Valid request payload
        payload = {
            "field1": "value1",
            "field2": "value2"
        }

        # WHEN: POST request sent
        response = client.post("/endpoint", json=payload)

        # THEN: Returns 200 OK with expected data
        assert response.status_code == 200
        assert response.json()["result"] == "expected"

    def test_post_validation_error(self, client):
        """Test POST request with invalid data"""
        # GIVEN: Invalid request payload
        payload = {"field1": "value1"}  # Missing required field2

        # WHEN: POST request sent
        response = client.post("/endpoint", json=payload)

        # THEN: Returns 422 Unprocessable Entity
        assert response.status_code == 422
        assert "field2" in response.json()["detail"][0]["loc"]

    def test_authentication_required(self, client):
        """Test endpoint requires authentication"""
        # GIVEN: No authentication token
        payload = {"field1": "value1", "field2": "value2"}

        # WHEN: POST request sent without token
        response = client.post("/endpoint", json=payload)

        # THEN: Returns 401 Unauthorized
        assert response.status_code == 401
```

---

## 7. Memory Keys for Test Coordination

**Purpose**: Store test specifications in shared memory for agent coordination

### Memory Key Structure

```
aqe/test-plan/phase1-test-specs
├── unit-tests/
│   ├── mcp-server/          # MCP server unit test specs
│   ├── mcp-tools/           # MCP tools unit test specs
│   ├── storage-backends/    # Storage backend unit test specs
│   └── base-agent/          # Base agent unit test specs
├── integration-tests/
│   ├── mcp-server/          # MCP server integration specs
│   ├── api-storage/         # API → Storage integration specs
│   ├── queue/               # Celery + Redis queue specs
│   └── websocket/           # WebSocket streaming specs
├── coverage-goals/
│   ├── minimum-coverage     # 85% minimum coverage target
│   └── critical-paths       # 100% coverage for critical paths
├── frameworks/
│   ├── pytest-config        # pytest configuration
│   ├── api-testing          # FastAPI TestClient + httpx
│   ├── load-testing         # locust + k6 configuration
│   └── contract-testing     # pact-python configuration
└── metadata/
    ├── generated-date       # 2025-11-12
    ├── version              # "1.0.0"
    └── phase                # "phase1"
```

---

## 8. Next Steps

### 8.1 Immediate Actions

1. **Generate Test Files**: Use test templates to create test files
2. **Setup Test Fixtures**: Implement shared fixtures in `conftest.py`
3. **Configure pytest**: Ensure pytest.ini / pyproject.toml configured
4. **Setup Coverage**: Configure coverage.py for HTML + terminal reports
5. **Implement Mock Objects**: Create mock LionAGI, mock database, mock Redis

### 8.2 Test Implementation Order

**Phase 1A: Foundation (Week 1)**
- Unit tests for MCP server initialization
- Unit tests for MCP tools (core tools only)
- Unit tests for Redis memory store/retrieve
- Unit tests for Base agent memory operations

**Phase 1B: Core Functionality (Week 2)**
- Unit tests for test generation tool
- Unit tests for test execution tool
- Unit tests for coverage analysis tool
- Integration tests for API → Storage

**Phase 1C: Advanced Features (Week 3)**
- Unit tests for streaming tools
- Integration tests for WebSocket streaming
- Integration tests for Celery + Redis queue
- API endpoint tests

**Phase 1D: Load & Contract Testing (Week 4)**
- Load tests with locust (test generation endpoint)
- Load tests with k6 (coverage analysis endpoint)
- Contract tests with pact-python
- Mutation testing setup

### 8.3 Continuous Improvement

- **Daily**: Run pytest with coverage reporting
- **Weekly**: Review coverage reports, identify gaps
- **Bi-weekly**: Run mutation testing, improve test quality
- **Monthly**: Performance benchmarking with load tests

---

## 9. Appendix: Test Data Examples

### 9.1 Sample Test Code for Generation

```python
# Simple function (basic test case)
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

# Complex function (edge cases)
def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate price after discount"""
    if price < 0:
        raise ValueError("Price cannot be negative")
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")
    return price * (1 - discount_percent / 100)

# Class with dependencies (mocking required)
class PaymentProcessor:
    def __init__(self, payment_gateway):
        self.gateway = payment_gateway

    def process_payment(self, amount: float, card_token: str) -> dict:
        """Process payment via gateway"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        return self.gateway.charge(amount, card_token)
```

### 9.2 Sample Coverage Report

```json
{
  "overall_coverage": 87.5,
  "line_coverage": 90.2,
  "branch_coverage": 82.8,
  "file_coverage": {
    "src/lionagi_qe/mcp/mcp_server.py": {
      "coverage": 95.0,
      "lines_covered": 190,
      "lines_total": 200,
      "missing_lines": [45, 78, 120, 135, 160, 175, 185, 195, 210, 225]
    },
    "src/lionagi_qe/mcp/mcp_tools.py": {
      "coverage": 92.5,
      "lines_covered": 740,
      "lines_total": 800,
      "missing_lines": [/* ... */]
    }
  },
  "gaps": [
    {
      "file": "src/lionagi_qe/mcp/mcp_server.py",
      "line_start": 120,
      "line_end": 135,
      "type": "uncovered_branch",
      "severity": "high",
      "suggested_test": "test_initialize_fleet_error_handling"
    }
  ]
}
```

### 9.3 Sample Test Execution Result

```json
{
  "passed": 145,
  "failed": 2,
  "skipped": 5,
  "coverage": 87.5,
  "duration": 12.34,
  "failures": [
    {
      "test_name": "test_test_generate_with_invalid_framework",
      "error": "AssertionError: Expected ValueError, got None",
      "file": "tests/unit/mcp/test_mcp_tools_unit.py",
      "line": 234
    },
    {
      "test_name": "test_redis_connection_failure",
      "error": "redis.ConnectionError: Connection refused",
      "file": "tests/unit/persistence/test_redis_memory_unit.py",
      "line": 67
    }
  ],
  "success": false
}
```

---

**Document Status**: ✅ Complete
**Review Required**: Yes
**Stored in Memory**: `aqe/test-plan/phase1-test-specs`
