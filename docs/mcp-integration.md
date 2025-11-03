# MCP Integration Guide

Complete guide for integrating LionAGI QE Fleet with Claude Code via Model Context Protocol (MCP).

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage Examples](#usage-examples)
5. [Advanced Features](#advanced-features)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## Overview

The MCP integration enables seamless interaction between Claude Code and the LionAGI QE Fleet's 19 specialized testing agents.

### Architecture

```
┌─────────────────┐
│  Claude Code    │
│   (MCP Client)  │
└────────┬────────┘
         │ MCP Protocol
         ↓
┌─────────────────┐
│  MCP Server     │
│  (FastMCP)      │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  QE Fleet       │
│  (19 Agents)    │
└─────────────────┘
         │
         ↓
┌─────────────────┐
│  LionAGI Core   │
│  (Branch/Memory)│
└─────────────────┘
```

### Key Features

- **17 MCP Tools**: Direct access to all agent capabilities
- **Streaming Support**: Real-time progress for long operations
- **Fleet Orchestration**: Multi-agent workflows
- **Shared Memory**: Cross-agent coordination via `aqe/*` namespace
- **Multi-Model Routing**: 70-81% cost savings (optional)
- **Q-Learning**: Pattern learning from executions (optional)

## Installation

### Prerequisites

```bash
# Python 3.10+
python --version

# Claude Code CLI
claude --version
```

### Install LionAGI QE Fleet

```bash
# Standard installation
pip install lionagi-qe-fleet

# With MCP support
pip install lionagi-qe-fleet[mcp]

# With all features
pip install lionagi-qe-fleet[all]
```

### Add to Claude Code

**Option 1: Using config file**

```bash
# Clone or download mcp_config.json
claude mcp add lionagi-qe --config /path/to/lionagi-qe-fleet/mcp_config.json
```

**Option 2: Manual configuration**

```bash
# Add MCP server
claude mcp add lionagi-qe python -m lionagi_qe.mcp.mcp_server

# Set environment
claude mcp env lionagi-qe PYTHONPATH /path/to/lionagi-qe-fleet/src
```

**Option 3: Development mode**

```bash
# For development with live reload
cd /path/to/lionagi-qe-fleet
pip install -e .
claude mcp add lionagi-qe python -m lionagi_qe.mcp.mcp_server
```

### Verify Installation

```bash
# Check MCP servers
claude mcp list

# Expected output:
# lionagi-qe: python -m lionagi_qe.mcp.mcp_server - ✓ Connected

# Test a tool
claude "Use mcp__lionagi_qe__get_fleet_status to check the fleet"
```

## Configuration

### MCP Config File

The `mcp_config.json` file defines server settings, tools, and agents.

**Key Sections:**

```json
{
  "mcpServers": {
    "lionagi-qe": {
      "command": "python",
      "args": ["-m", "lionagi_qe.mcp.mcp_server"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
      },
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
# Core Settings
export AQE_ROUTING_ENABLED=true
export AQE_LEARNING_ENABLED=false
export AQE_DEFAULT_FRAMEWORK=pytest
export AQE_COVERAGE_THRESHOLD=80.0

# Logging
export LIONAGI_QE_LOG_LEVEL=INFO
export LIONAGI_QE_LOG_FILE=~/.local/share/lionagi-qe/logs/fleet.log

# Model Configuration
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
```

### Python Configuration

```python
from lionagi_qe.mcp import MCPServer

# Create custom server
server = MCPServer(
    name="lionagi-qe",
    enable_routing=True,
    enable_learning=False
)

# Start server
await server.start()
```

## Usage Examples

### Basic Testing Workflow

```javascript
// In Claude Code

// 1. Generate tests
const testResult = await mcp__lionagi_qe__test_generate({
    code: `
    class UserService {
        async getUser(id) {
            return await db.users.findById(id);
        }
    }
    `,
    framework: "jest",
    test_type: "unit",
    coverage_target: 90
});

// 2. Execute tests
const execResult = await mcp__lionagi_qe__test_execute({
    test_path: "./tests",
    framework: "jest",
    parallel: true,
    coverage: true
});

// 3. Analyze coverage
const coverage = await mcp__lionagi_qe__coverage_analyze({
    source_path: "./src",
    test_path: "./tests",
    threshold: 80.0
});

// 4. Quality gate
const gate = await mcp__lionagi_qe__quality_gate({
    metrics: {
        coverage: execResult.coverage,
        test_pass_rate: execResult.passed / (execResult.passed + execResult.failed)
    }
});
```

### Multi-Agent Pipeline

```javascript
// Sequential pipeline
const pipeline = await mcp__lionagi_qe__fleet_orchestrate({
    workflow: "pipeline",
    agents: [
        "test-generator",
        "test-executor",
        "coverage-analyzer",
        "quality-gate"
    ],
    context: {
        code_path: "./src/user-service.js",
        framework: "jest",
        coverage_threshold: 85
    }
});

console.log("Pipeline results:", pipeline.results);
```

### Parallel Execution

```javascript
// Execute multiple agents concurrently
const parallel = await mcp__lionagi_qe__fleet_orchestrate({
    workflow: "parallel",
    agents: [
        "test-generator",
        "security-scanner",
        "performance-tester"
    ],
    context: {
        code_path: "./src",
        framework: "pytest"
    }
});

console.log("Parallel results:", parallel.results);
```

### Streaming Progress

```javascript
// Real-time test execution
for await (const event of mcp__lionagi_qe__test_execute_stream({
    test_path: "./tests",
    framework: "pytest",
    parallel: true,
    coverage: true
})) {
    if (event.type === "progress") {
        console.log(`${event.percent}% - ${event.message}`);
    } else if (event.type === "result") {
        console.log("Final result:", event.data);
    }
}
```

### Advanced Agent Coordination

```javascript
// Fan-out/fan-in pattern
const coordination = await mcp__lionagi_qe__fleet_orchestrate({
    workflow: "fan-out-fan-in",
    agents: [
        "test-generator",
        "security-scanner",
        "performance-tester",
        "visual-tester"
    ],
    context: {
        coordinator: "fleet-commander",
        project_path: "./",
        target: "production"
    }
});

// Fleet commander synthesizes results from all workers
console.log("Coordinated analysis:", coordination.synthesis);
```

## Advanced Features

### Multi-Model Routing

Enable cost optimization with intelligent model selection:

```javascript
// Enable in config
{
  "configuration": {
    "enable_routing": true
  }
}

// Or via environment
process.env.AQE_ROUTING_ENABLED = "true";

// Router automatically selects:
// - GPT-3.5 for simple tasks (85% cheaper)
// - GPT-4 for complex tasks
// - Claude Sonnet 4.5 for critical tasks
```

**Cost Savings Example:**

| Without Routing | With Routing | Savings |
|----------------|--------------|---------|
| $1.00 (100 tasks @ GPT-4) | $0.19 (70 @ GPT-3.5, 30 @ GPT-4) | 81% |

### Q-Learning Integration

Enable pattern learning across executions:

```javascript
// Enable learning
{
  "configuration": {
    "enable_learning": true
  }
}

// Agents learn from:
// - Successful test patterns
// - High-coverage strategies
// - Edge case detection
// - Performance optimizations

// View learned patterns
const patterns = await mcp__lionagi_qe__get_fleet_status();
console.log(patterns.learned_patterns);
```

### Custom Workflows

```javascript
// Define custom workflow
const customWorkflow = {
    name: "comprehensive-qa",
    steps: [
        {
            agent: "requirements-validator",
            input: "user_stories"
        },
        {
            agent: "test-generator",
            input: "validated_requirements"
        },
        {
            agent: "test-executor",
            input: "generated_tests",
            parallel: true
        },
        {
            agent: "coverage-analyzer",
            input: "execution_results"
        },
        {
            agent: "security-scanner",
            input: "source_code",
            parallel_with: "coverage-analyzer"
        },
        {
            agent: "quality-gate",
            input: ["coverage", "security"]
        },
        {
            agent: "deployment-readiness",
            input: "quality_gate_result"
        }
    ]
};

// Execute custom workflow
const result = await fleet.execute_workflow(customWorkflow);
```

### Memory Coordination

```javascript
// Store context for other agents
await mcp__lionagi_qe__fleet_orchestrate({
    workflow: "pipeline",
    agents: ["test-generator"],
    context: {
        code: sourceCode,
        store_key: "aqe/test-plan/api-tests"
    }
});

// Another agent retrieves context
await mcp__lionagi_qe__fleet_orchestrate({
    workflow: "pipeline",
    agents: ["test-executor"],
    context: {
        retrieve_key: "aqe/test-plan/api-tests"
    }
});
```

## Best Practices

### 1. Batch Operations

```javascript
// ✅ Good: Batch related operations
[Single Message]:
  Task("Test Generator", "Generate tests", "test-generator")
  Task("Coverage Analyzer", "Analyze coverage", "coverage-analyzer")
  Task("Quality Gate", "Check quality", "quality-gate")

// ❌ Bad: Sequential messages
Message 1: Task("Test Generator", ...)
Message 2: Task("Coverage Analyzer", ...)
Message 3: Task("Quality Gate", ...)
```

### 2. Use Appropriate Workflows

```javascript
// Pipeline: Sequential dependencies
fleet_orchestrate({ workflow: "pipeline", ... })

// Parallel: Independent tasks
fleet_orchestrate({ workflow: "parallel", ... })

// Fan-out-fan-in: Coordination required
fleet_orchestrate({ workflow: "fan-out-fan-in", ... })
```

### 3. Memory Namespace Organization

```javascript
// Use consistent naming
aqe/test-plan/{component}/requirements
aqe/test-plan/{component}/generated-tests
aqe/coverage/{component}/gaps
aqe/quality/{component}/metrics
```

### 4. Error Handling

```javascript
try {
    const result = await mcp__lionagi_qe__test_execute({
        test_path: "./tests",
        timeout: 300
    });
} catch (error) {
    console.error("Test execution failed:", error);

    // Check error details in memory
    const errorDetails = await fleet.memory.retrieve(
        `aqe/test-executor/tasks/${taskId}/error`
    );
}
```

### 5. Performance Optimization

```javascript
// Enable parallel execution
{
  parallel: true,
  max_parallel_agents: 10
}

// Use sublinear algorithms
{
  algorithm: "sublinear"  // O(log n) vs O(n)
}

// Enable routing for cost savings
{
  enable_routing: true
}
```

## Troubleshooting

### Connection Issues

```bash
# Check MCP server status
claude mcp list

# Restart MCP server
claude mcp restart lionagi-qe

# View logs
cat ~/.local/share/claude/logs/lionagi-qe.log
```

### Tool Not Found

```bash
# List available tools
claude mcp tools lionagi-qe

# Verify server initialization
python -m lionagi_qe.mcp.mcp_server
```

### Fleet Not Initialized

```python
# Check initialization
result = await mcp__lionagi_qe__get_fleet_status()
print(result)

# Expected: {"initialized": true, "agents": [...]}
```

### Memory Issues

```python
# Check memory usage
status = await mcp__lionagi_qe__get_fleet_status()
print(status["memory_stats"])

# Clear old data
await fleet.memory.search("aqe/.*")  # View all keys
await fleet.memory.delete("aqe/old-key")
```

### Performance Issues

```bash
# Enable debug logging
export LIONAGI_QE_LOG_LEVEL=DEBUG

# Check agent metrics
result = await mcp__lionagi_qe__get_fleet_status()
print(result["performance_metrics"])

# Optimize with routing
export AQE_ROUTING_ENABLED=true
```

## Next Steps

- [API Reference](./api-reference.md)
- [Agent Specifications](./agents/)
- [Example Workflows](../examples/)
- [Contributing Guide](../CONTRIBUTING.md)
