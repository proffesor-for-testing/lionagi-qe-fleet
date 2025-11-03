# MCP Quick Start Guide

Get started with LionAGI QE Fleet MCP integration in 5 minutes.

## Prerequisites

- Python 3.10+
- Claude Code CLI
- pip

## Installation

### 1. Install the Package

```bash
# Install with MCP support
pip install lionagi-qe-fleet[mcp]

# Or install from source
git clone https://github.com/yourusername/lionagi-qe-fleet.git
cd lionagi-qe-fleet
pip install -e ".[mcp]"
```

### 2. Run Setup Script

```bash
# Automated setup
./scripts/setup-mcp.sh

# Or for development mode
./scripts/setup-mcp.sh --dev
```

The script will:
- ✓ Check Python version
- ✓ Verify Claude Code CLI
- ✓ Install dependencies
- ✓ Register MCP server
- ✓ Test connection

### 3. Manual Setup (Alternative)

```bash
# Add MCP server to Claude Code
claude mcp add lionagi-qe python -m lionagi_qe.mcp.mcp_server

# Set Python path
claude mcp env lionagi-qe PYTHONPATH /path/to/lionagi-qe-fleet/src

# Verify installation
claude mcp list
```

## First Test

### Option 1: Via Claude Code

```bash
# Start Claude Code
claude

# Use MCP tools
> Use mcp__lionagi_qe__get_fleet_status to check the fleet

# Or spawn an agent
> Task('Generate tests', 'Create comprehensive test suite for UserService', 'test-generator')
```

### Option 2: Programmatically

```python
from lionagi_qe.mcp.mcp_server import create_mcp_server
from lionagi_qe.mcp import mcp_tools
import asyncio

async def test():
    # Create and start server
    server = create_mcp_server()
    await server.start()

    # Get fleet status
    status = await mcp_tools.get_fleet_status()
    print(status)

    # Generate tests
    result = await mcp_tools.test_generate(
        code="def add(a, b): return a + b",
        framework="pytest"
    )
    print(result)

    await server.stop()

asyncio.run(test())
```

## Common Tasks

### Generate Tests

```python
result = await mcp_tools.test_generate(
    code=source_code,
    framework="pytest",
    test_type="unit",
    coverage_target=90.0
)
```

### Execute Tests

```python
result = await mcp_tools.test_execute(
    test_path="./tests",
    framework="pytest",
    parallel=True,
    coverage=True
)
```

### Analyze Coverage

```python
result = await mcp_tools.coverage_analyze(
    source_path="./src",
    test_path="./tests",
    threshold=80.0
)
```

### Run Quality Gate

```python
result = await mcp_tools.quality_gate(
    metrics={
        "coverage": 85.0,
        "complexity": 7.5
    }
)
```

### Orchestrate Workflow

```python
result = await mcp_tools.fleet_orchestrate(
    workflow="pipeline",
    agents=["test-generator", "test-executor", "coverage-analyzer"],
    context={"code_path": "./src"}
)
```

## Configuration

### Enable Multi-Model Routing (Cost Savings)

```bash
# Via environment
export AQE_ROUTING_ENABLED=true

# Or in mcp_config.json
{
  "configuration": {
    "enable_routing": true
  }
}
```

### Enable Q-Learning

```bash
export AQE_LEARNING_ENABLED=true
```

### Set Defaults

```bash
export AQE_DEFAULT_FRAMEWORK=pytest
export AQE_COVERAGE_THRESHOLD=80.0
```

## Troubleshooting

### MCP Server Not Found

```bash
# Check installation
claude mcp list

# Reinstall
claude mcp remove lionagi-qe
./scripts/setup-mcp.sh
```

### Import Errors

```bash
# Check Python path
echo $PYTHONPATH

# Reinstall package
pip install -e ".[mcp]"
```

### Connection Errors

```bash
# Test server directly
python -m lionagi_qe.mcp.mcp_server

# Check logs
tail -f ~/.local/share/claude/logs/lionagi-qe.log
```

## Next Steps

- [Full Documentation](./mcp-integration.md)
- [MCP API Reference](../src/lionagi_qe/mcp/README.md)
- [Usage Examples](../examples/mcp_usage.py)
- [Agent Specifications](./agents/)

## Support

- **GitHub Issues**: [Report bugs](https://github.com/yourusername/lionagi-qe-fleet/issues)
- **Documentation**: [Full docs](./mcp-integration.md)
- **Examples**: [Code examples](../examples/)
