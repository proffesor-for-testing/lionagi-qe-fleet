# LionAGI QE Fleet - MCP Integration

Model Context Protocol (MCP) integration for seamless Claude Code compatibility.

## Overview

This module exposes all 19 LionAGI QE agents as MCP tools, enabling:

- **Tool Discovery**: Automatic detection by Claude Code
- **Direct Invocation**: Call agents as `mcp__lionagi_qe__<tool_name>`
- **Streaming Results**: Real-time progress for long-running operations
- **Fleet Orchestration**: Multi-agent workflows via MCP

## Quick Start

### 1. Install Dependencies

```bash
pip install lionagi-qe-fleet[mcp]
```

### 2. Add to Claude Code

```bash
# Using the configuration file
claude mcp add lionagi-qe --config /path/to/mcp_config.json

# Or manually
claude mcp add lionagi-qe python -m lionagi_qe.mcp.mcp_server
```

### 3. Verify Connection

```bash
claude mcp list
# Should show: lionagi-qe: python -m lionagi_qe.mcp.mcp_server - ✓ Connected
```

## Available MCP Tools

### Core Testing Tools

#### `test_generate`
Generate comprehensive test suites with AI-powered edge case detection.

```python
mcp__lionagi_qe__test_generate({
    "code": "def add(a, b): return a + b",
    "framework": "pytest",
    "test_type": "unit",
    "coverage_target": 90.0
})
```

**Returns:**
- `test_code`: Generated test code
- `test_name`: Test name
- `assertions`: List of assertions
- `edge_cases`: Edge cases covered
- `coverage_estimate`: Estimated coverage %

#### `test_execute`
Execute test suites with parallel processing and coverage.

```python
mcp__lionagi_qe__test_execute({
    "test_path": "./tests",
    "framework": "pytest",
    "parallel": true,
    "coverage": true,
    "timeout": 300
})
```

**Returns:**
- `passed`, `failed`, `skipped`: Test counts
- `coverage`: Coverage percentage
- `duration`: Execution time
- `failures`: Failure details

#### `coverage_analyze`
Analyze coverage with O(log n) gap detection.

```python
mcp__lionagi_qe__coverage_analyze({
    "source_path": "./src",
    "test_path": "./tests",
    "threshold": 80.0,
    "algorithm": "sublinear"
})
```

**Returns:**
- `overall_coverage`: Total coverage %
- `file_coverage`: Per-file breakdown
- `gaps`: Coverage gaps with priorities
- `recommendations`: AI-generated suggestions

#### `quality_gate`
Intelligent quality gate with risk assessment.

```python
mcp__lionagi_qe__quality_gate({
    "metrics": {
        "coverage": 85.0,
        "complexity": 8.5,
        "duplication": 3.2
    },
    "thresholds": {
        "coverage": 80.0,
        "complexity": 10.0
    }
})
```

**Returns:**
- `passed`: Gate pass/fail
- `score`: Quality score (0-100)
- `violations`: Threshold violations
- `risks`: Identified risks

### Performance & Security

#### `performance_test`
Run load tests with k6, JMeter, or Locust.

```python
mcp__lionagi_qe__performance_test({
    "endpoint": "https://api.example.com/users",
    "duration": 60,
    "users": 100,
    "ramp_up": 10,
    "tool": "locust"
})
```

#### `security_scan`
Multi-layer security scanning (SAST, DAST, dependencies).

```python
mcp__lionagi_qe__security_scan({
    "path": "./src",
    "scan_type": "comprehensive",
    "severity_threshold": "medium"
})
```

### Fleet Orchestration

#### `fleet_orchestrate`
Orchestrate multi-agent workflows.

```python
mcp__lionagi_qe__fleet_orchestrate({
    "workflow": "pipeline",
    "agents": ["test-generator", "test-executor", "coverage-analyzer"],
    "context": {
        "code_path": "./src",
        "framework": "pytest"
    }
})
```

**Workflow Types:**
- `pipeline`: Sequential execution
- `parallel`: Concurrent execution
- `fan-out-fan-in`: Coordinator + workers pattern

#### `get_fleet_status`
Get comprehensive fleet status.

```python
mcp__lionagi_qe__get_fleet_status()
```

### Advanced Tools

#### `requirements_validate`
INVEST criteria validation and BDD generation.

#### `flaky_test_hunt`
Statistical flakiness detection and auto-stabilization.

#### `api_contract_validate`
Breaking change detection across API versions.

#### `regression_risk_analyze`
Smart test selection with ML-based risk analysis.

#### `test_data_generate`
Realistic test data generation (10k+ records/sec).

#### `visual_test`
Visual regression with AI-powered comparison.

#### `chaos_test`
Resilience testing with fault injection.

#### `deployment_readiness`
Multi-factor deployment risk assessment.

### Streaming Tools

#### `test_execute_stream`
Execute tests with real-time progress.

```python
async for event in mcp__lionagi_qe__test_execute_stream({
    "test_path": "./tests",
    "framework": "pytest"
}):
    if event["type"] == "progress":
        print(f"Progress: {event['percent']}%")
    elif event["type"] == "result":
        print(f"Complete: {event['data']}")
```

## Agent Coordination

### Memory Namespace

All agents share state via the `aqe/*` memory namespace:

- `aqe/test-plan/*` - Test planning
- `aqe/coverage/*` - Coverage analysis
- `aqe/quality/*` - Quality metrics
- `aqe/performance/*` - Performance results
- `aqe/security/*` - Security findings
- `aqe/swarm/coordination` - Cross-agent coordination

### Example Coordination

```python
# Agent 1: Generate tests
mcp__lionagi_qe__test_generate({
    "code": code,
    "framework": "pytest"
})
# → Stores results in aqe/test-generator/tasks/{task_id}/result

# Agent 2: Execute tests (reads from memory)
mcp__lionagi_qe__test_execute({
    "test_path": "./tests"
})
# → Stores results in aqe/test-executor/tasks/{task_id}/result

# Agent 3: Analyze coverage (reads from memory)
mcp__lionagi_qe__coverage_analyze({
    "source_path": "./src",
    "test_path": "./tests"
})
# → Stores gaps in aqe/coverage-analyzer/gaps
```

## Configuration

### Environment Variables

```bash
# Enable multi-model routing (70-81% cost savings)
export AQE_ROUTING_ENABLED=true

# Enable Q-learning
export AQE_LEARNING_ENABLED=true

# Set default framework
export AQE_DEFAULT_FRAMEWORK=pytest

# Set coverage threshold
export AQE_COVERAGE_THRESHOLD=80.0
```

### MCP Configuration

Edit `mcp_config.json` to customize:

```json
{
  "mcpServers": {
    "lionagi-qe": {
      "configuration": {
        "enable_routing": true,
        "enable_learning": false,
        "default_framework": "pytest",
        "default_coverage_threshold": 80.0,
        "max_parallel_agents": 10
      }
    }
  }
}
```

## Claude Code Integration

### Using in Claude Code

```javascript
// Spawn agent via Task tool (recommended)
Task("Generate tests", "Create comprehensive test suite for UserService", "test-generator")

// Or call MCP tool directly
mcp__lionagi_qe__test_generate({
    code: userServiceCode,
    framework: "pytest",
    coverage_target: 90
})

// Batch multiple agents
[Single Message]:
  Task("Test Generator", "Generate tests for UserService", "test-generator")
  Task("Coverage Analyzer", "Analyze coverage gaps", "coverage-analyzer")
  Task("Quality Gate", "Run quality validation", "quality-gate")
```

### Parallel Execution

```javascript
// Execute multiple agents concurrently
mcp__lionagi_qe__fleet_orchestrate({
    workflow: "parallel",
    agents: ["test-generator", "security-scanner", "performance-tester"],
    context: {
        code_path: "./src",
        framework: "pytest"
    }
})
```

## Performance

### Multi-Model Routing

When enabled, the router automatically selects optimal models:

| Task Complexity | Model | Cost Reduction |
|----------------|-------|----------------|
| Simple | GPT-3.5 | 85% cheaper |
| Moderate | GPT-3.5 | 85% cheaper |
| Complex | GPT-4 | Baseline |
| Critical | Claude Sonnet 4.5 | Premium |

**Average Savings**: 70-81% cost reduction

### Benchmarks

- **Test Generation**: <2s for unit tests
- **Coverage Analysis**: O(log n) algorithm, <1s for 10k LOC
- **Test Execution**: Parallel processing, 2-4x speedup
- **Data Generation**: 10k+ records/sec

## Troubleshooting

### Check MCP Connection

```bash
claude mcp list
```

### View Logs

```bash
# Enable debug logging
export LIONAGI_QE_LOG_LEVEL=DEBUG

# View server logs
tail -f ~/.local/share/claude/logs/lionagi-qe.log
```

### Test MCP Server

```bash
# Run server directly
python -m lionagi_qe.mcp.mcp_server

# Test a tool
python -c "
from lionagi_qe.mcp.mcp_tools import test_generate
import asyncio

async def test():
    result = await test_generate(
        code='def add(a, b): return a + b',
        framework='pytest'
    )
    print(result)

asyncio.run(test())
"
```

### Common Issues

**Issue**: `Fleet not initialized`
```python
# Solution: Fleet initializes automatically on first tool call
# Or manually:
from lionagi_qe.mcp.mcp_server import create_mcp_server
server = create_mcp_server()
await server.start()
```

**Issue**: `Agent not found`
```python
# Solution: Check registered agents
result = await mcp__lionagi_qe__get_fleet_status()
print(result['agents'])
```

## Development

### Running Tests

```bash
pytest tests/mcp/
```

### Adding New Tools

1. Define tool in `mcp_tools.py`:
```python
async def my_new_tool(param: str) -> Dict[str, Any]:
    """Tool description"""
    # Implementation
    pass
```

2. Register in `mcp_server.py`:
```python
self.mcp.tool()(mcp_tools.my_new_tool)
```

3. Add to `mcp_config.json`:
```json
{
  "tools": [
    {
      "name": "my_new_tool",
      "description": "Tool description",
      "category": "category"
    }
  ]
}
```

## Resources

- **LionAGI Docs**: https://docs.lionagi.ai
- **MCP Specification**: https://modelcontextprotocol.io
- **Claude Code**: https://claude.ai/code
- **QE Fleet GitHub**: https://github.com/yourusername/lionagi-qe-fleet

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/lionagi-qe-fleet/issues
- Discord: https://discord.gg/lionagi
- Email: support@lionagi.ai
