# Claude Code Integration - LionAGI QE Fleet

Complete integration guide for using LionAGI QE Fleet with Claude Code via MCP.

## Overview

LionAGI QE Fleet is now fully integrated with Claude Code through the Model Context Protocol (MCP). This enables:

- ✅ **17 MCP Tools** - Direct access to all QE agents
- ✅ **Streaming Progress** - Real-time updates for long operations
- ✅ **Fleet Orchestration** - Multi-agent workflows (pipeline, parallel, fan-out-fan-in)
- ✅ **Shared Memory** - Cross-agent coordination via `aqe/*` namespace
- ✅ **Multi-Model Routing** - 70-81% cost savings (optional)
- ✅ **Q-Learning** - Pattern learning from executions (optional)

## Quick Start

### Installation

```bash
# Install package with MCP support
pip install lionagi-qe-fleet[mcp]

# Run automated setup
./scripts/setup-mcp.sh

# Verify connection
claude mcp list
# Should show: lionagi-qe: python -m lionagi_qe.mcp.mcp_server - ✓ Connected
```

### First Use

In Claude Code:

```javascript
// Check fleet status
mcp__lionagi_qe__get_fleet_status()

// Generate tests
mcp__lionagi_qe__test_generate({
    code: "def add(a, b): return a + b",
    framework: "pytest",
    coverage_target: 90
})

// Or use Task tool (recommended)
Task("Generate tests", "Create comprehensive test suite", "test-generator")
```

## Available MCP Tools

### Core Testing (4 tools)

| Tool | Description | Category |
|------|-------------|----------|
| `test_generate` | Generate comprehensive test suites with edge cases | Testing |
| `test_execute` | Execute tests with parallel processing | Testing |
| `coverage_analyze` | O(log n) coverage gap detection | Testing |
| `quality_gate` | Intelligent quality gate with risk assessment | Quality |

### Performance & Security (2 tools)

| Tool | Description | Category |
|------|-------------|----------|
| `performance_test` | Load testing (k6, JMeter, Locust) | Performance |
| `security_scan` | SAST, DAST, dependency scanning | Security |

### Fleet Orchestration (2 tools)

| Tool | Description | Category |
|------|-------------|----------|
| `fleet_orchestrate` | Multi-agent workflows | Orchestration |
| `get_fleet_status` | Fleet status and metrics | Monitoring |

### Advanced Testing (9 tools)

| Tool | Description | Category |
|------|-------------|----------|
| `requirements_validate` | INVEST criteria + BDD generation | Requirements |
| `flaky_test_hunt` | Statistical flakiness detection | Testing |
| `api_contract_validate` | Breaking change detection | API |
| `regression_risk_analyze` | ML-based test selection | Testing |
| `test_data_generate` | 10k+ records/sec generation | Data |
| `visual_test` | AI-powered visual regression | Testing |
| `chaos_test` | Resilience testing | Reliability |
| `deployment_readiness` | Multi-factor risk assessment | Deployment |
| `test_execute_stream` | Real-time progress streaming | Testing |

## Usage Patterns

### 1. Basic Testing Workflow

```javascript
// Sequential pipeline
[Single Message]:
  // Generate tests
  const tests = mcp__lionagi_qe__test_generate({
      code: sourceCode,
      framework: "pytest",
      coverage_target: 90
  })

  // Execute tests
  const results = mcp__lionagi_qe__test_execute({
      test_path: "./tests",
      parallel: true,
      coverage: true
  })

  // Analyze coverage
  const coverage = mcp__lionagi_qe__coverage_analyze({
      source_path: "./src",
      test_path: "./tests",
      threshold: 80
  })

  // Quality gate
  const gate = mcp__lionagi_qe__quality_gate({
      metrics: {
          coverage: results.coverage,
          test_pass_rate: results.passed / (results.passed + results.failed)
      }
  })
```

### 2. Multi-Agent Orchestration

```javascript
// Pipeline: Sequential execution
mcp__lionagi_qe__fleet_orchestrate({
    workflow: "pipeline",
    agents: ["test-generator", "test-executor", "coverage-analyzer", "quality-gate"],
    context: {
        code_path: "./src/user-service.js",
        framework: "jest",
        coverage_threshold: 85
    }
})

// Parallel: Concurrent execution
mcp__lionagi_qe__fleet_orchestrate({
    workflow: "parallel",
    agents: ["test-generator", "security-scanner", "performance-tester"],
    context: {
        code_path: "./src",
        framework: "pytest"
    }
})

// Fan-out-fan-in: Coordinator + workers
mcp__lionagi_qe__fleet_orchestrate({
    workflow: "fan-out-fan-in",
    agents: ["test-generator", "security-scanner", "performance-tester", "visual-tester"],
    context: {
        coordinator: "fleet-commander",
        project_path: "./",
        target: "production"
    }
})
```

### 3. Streaming Progress

```javascript
// Real-time test execution
for await (const event of mcp__lionagi_qe__test_execute_stream({
    test_path: "./tests",
    framework: "pytest"
})) {
    if (event.type === "progress") {
        console.log(`${event.percent}% - ${event.message}`)
    } else if (event.type === "result") {
        console.log("Complete:", event.data)
    }
}
```

### 4. Task Tool Integration (Recommended)

```javascript
// Spawn agents via Claude Code's Task tool
[Single Message]:
  Task("Test Generator", "Generate comprehensive test suite for UserService", "test-generator")
  Task("Coverage Analyzer", "Analyze coverage gaps using O(log n) algorithms", "coverage-analyzer")
  Task("Security Scanner", "Run comprehensive security scan", "security-scanner")
  Task("Quality Gate", "Validate quality metrics and thresholds", "quality-gate")
```

## Agent Coordination

### Memory Namespace

All agents share state via the `aqe/*` memory namespace:

```
aqe/
├── test-plan/          # Test planning and requirements
│   ├── {component}/requirements
│   └── {component}/generated-tests
├── coverage/           # Coverage analysis
│   └── {component}/gaps
├── quality/            # Quality metrics
│   └── {component}/metrics
├── performance/        # Performance results
│   └── {component}/benchmarks
├── security/           # Security findings
│   └── {component}/vulnerabilities
└── swarm/             # Cross-agent coordination
    └── coordination
```

### Coordination Example

```javascript
// Agent 1: Generate tests (stores in memory)
mcp__lionagi_qe__test_generate({
    code: code,
    framework: "pytest"
})
// → Stores: aqe/test-generator/tasks/{task_id}/result

// Agent 2: Execute tests (reads from memory)
mcp__lionagi_qe__test_execute({
    test_path: "./tests"
})
// → Reads: aqe/test-generator/tasks/{task_id}/result
// → Stores: aqe/test-executor/tasks/{task_id}/result

// Agent 3: Analyze coverage (reads from memory)
mcp__lionagi_qe__coverage_analyze({
    source_path: "./src",
    test_path: "./tests"
})
// → Reads: aqe/test-executor/tasks/{task_id}/result
// → Stores: aqe/coverage-analyzer/gaps
```

## Configuration

### MCP Server Config

Edit `mcp_config.json`:

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

### Environment Variables

```bash
# Enable multi-model routing (70-81% cost savings)
export AQE_ROUTING_ENABLED=true

# Enable Q-learning
export AQE_LEARNING_ENABLED=true

# Set defaults
export AQE_DEFAULT_FRAMEWORK=pytest
export AQE_COVERAGE_THRESHOLD=80.0

# Logging
export LIONAGI_QE_LOG_LEVEL=INFO
```

## Performance Optimization

### Multi-Model Routing

When enabled, the router automatically selects optimal models for cost savings:

| Task Complexity | Model | Cost | Savings |
|----------------|-------|------|---------|
| Simple | GPT-3.5 | $0.0004 | 85% |
| Moderate | GPT-3.5 | $0.0008 | 85% |
| Complex | GPT-4 | $0.0048 | Baseline |
| Critical | Claude Sonnet 4.5 | $0.0065 | Premium |

**Average savings**: 70-81% across typical workloads

### Parallel Execution

```javascript
// Enable parallel processing
{
  parallel: true,
  max_parallel_agents: 10
}

// Use sublinear algorithms
{
  algorithm: "sublinear"  // O(log n) vs O(n)
}
```

## Best Practices

### 1. Batch Operations in Single Messages

```javascript
// ✅ Good: All operations in one message
[Single Message]:
  Task("Test Generator", "...", "test-generator")
  Task("Coverage Analyzer", "...", "coverage-analyzer")
  Task("Quality Gate", "...", "quality-gate")

// ❌ Bad: Sequential messages
Message 1: Task("Test Generator", ...)
Message 2: Task("Coverage Analyzer", ...)
Message 3: Task("Quality Gate", ...)
```

### 2. Use Appropriate Workflow Types

- **Pipeline**: Sequential dependencies
- **Parallel**: Independent tasks
- **Fan-out-fan-in**: Coordination required

### 3. Organize Memory Keys

```javascript
// Consistent naming convention
aqe/{agent-type}/{component}/{data-type}
aqe/test-generator/user-service/requirements
aqe/coverage-analyzer/user-service/gaps
```

### 4. Handle Errors Gracefully

```javascript
try {
    const result = await mcp__lionagi_qe__test_execute({...})
} catch (error) {
    // Check error details in memory
    const errorDetails = await fleet.memory.retrieve(
        `aqe/test-executor/tasks/${taskId}/error`
    )
}
```

## Troubleshooting

### Connection Issues

```bash
# Check MCP server status
claude mcp list

# Restart server
claude mcp restart lionagi-qe

# View logs
tail -f ~/.local/share/claude/logs/lionagi-qe.log
```

### Tool Execution Errors

```bash
# Test server directly
python -m lionagi_qe.mcp.mcp_server

# Check fleet status
claude "Use mcp__lionagi_qe__get_fleet_status"
```

### Performance Issues

```bash
# Enable debug logging
export LIONAGI_QE_LOG_LEVEL=DEBUG

# Enable routing for cost optimization
export AQE_ROUTING_ENABLED=true

# Check agent metrics
claude "Use mcp__lionagi_qe__get_fleet_status and show performance_metrics"
```

## Examples

See [`examples/mcp_usage.py`](./examples/mcp_usage.py) for complete examples:

- Basic test generation
- Pipeline workflows
- Parallel execution
- Streaming progress
- Quality gates
- Security scanning
- Fleet status monitoring

## Documentation

- [MCP Quick Start](./docs/mcp-quickstart.md) - Get started in 5 minutes
- [MCP Integration Guide](./docs/mcp-integration.md) - Complete integration guide
- [MCP API Reference](./src/lionagi_qe/mcp/README.md) - Detailed API docs
- [Agent Specifications](./docs/agents/) - Individual agent docs

## Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/lionagi-qe-fleet/issues)
- **Documentation**: [Read the full docs](./docs/)
- **Examples**: [Browse code examples](./examples/)
- **Discord**: [Join the community](https://discord.gg/lionagi)

## License

MIT License - see [LICENSE](./LICENSE) file for details.
