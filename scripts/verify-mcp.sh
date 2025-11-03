#!/bin/bash
# Verification script for MCP integration

set -e

echo "🔍 Verifying MCP Integration"
echo "============================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

# Check function
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        ERRORS=$((ERRORS + 1))
    fi
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

# 1. Check files exist
echo "Checking file structure..."
[ -f "src/lionagi_qe/mcp/__init__.py" ]
check "MCP __init__.py exists"

[ -f "src/lionagi_qe/mcp/mcp_server.py" ]
check "MCP server exists"

[ -f "src/lionagi_qe/mcp/mcp_tools.py" ]
check "MCP tools exists"

[ -f "mcp_config.json" ]
check "MCP config exists"

[ -f "scripts/setup-mcp.sh" ]
check "Setup script exists"

[ -f "CLAUDE_CODE_INTEGRATION.md" ]
check "Integration doc exists"

echo ""

# 2. Check Python imports
echo "Checking Python imports..."
python3 -c "from lionagi_qe.mcp import MCPServer" 2>/dev/null
check "MCPServer import"

python3 -c "from lionagi_qe.mcp import mcp_tools" 2>/dev/null
check "mcp_tools import"

python3 -c "from lionagi_qe.mcp.mcp_server import create_mcp_server" 2>/dev/null
check "create_mcp_server import"

echo ""

# 3. Check dependencies
echo "Checking dependencies..."
python3 -c "import lionagi" 2>/dev/null
check "lionagi installed"

python3 -c "import pydantic" 2>/dev/null
check "pydantic installed"

python3 -c "from mcp.server.fastmcp import FastMCP" 2>/dev/null && check "FastMCP installed (optional)" || warn "FastMCP not installed (optional)"

echo ""

# 4. Check server initialization
echo "Checking server initialization..."
python3 << 'PYTHON_CHECK'
import sys
try:
    from lionagi_qe.mcp.mcp_server import create_mcp_server
    server = create_mcp_server()
    assert server.name == "lionagi-qe"
    assert server.enable_routing == True
    print("✓ Server creation successful")
except Exception as e:
    print(f"✗ Server creation failed: {e}")
    sys.exit(1)
PYTHON_CHECK

echo ""

# 5. Check tool registration
echo "Checking tool registration..."
python3 << 'PYTHON_CHECK'
import sys
try:
    from lionagi_qe.mcp.mcp_server import create_mcp_server
    server = create_mcp_server()
    mcp = server.get_server()

    expected_tools = [
        "test_generate",
        "test_execute",
        "coverage_analyze",
        "quality_gate",
        "performance_test",
        "security_scan",
        "fleet_orchestrate",
        "get_fleet_status"
    ]

    for tool in expected_tools:
        if tool in mcp._tools:
            print(f"✓ Tool registered: {tool}")
        else:
            print(f"✗ Tool missing: {tool}")
            sys.exit(1)

    print(f"✓ Total tools registered: {len(mcp._tools)}")

except Exception as e:
    print(f"✗ Tool registration check failed: {e}")
    sys.exit(1)
PYTHON_CHECK

echo ""

# 6. Check MCP config
echo "Checking MCP config..."
python3 << 'PYTHON_CHECK'
import json
import sys

try:
    with open("mcp_config.json") as f:
        config = json.load(f)

    assert "mcpServers" in config
    assert "lionagi-qe" in config["mcpServers"]

    server_config = config["mcpServers"]["lionagi-qe"]
    assert "tools" in server_config
    assert "agents" in server_config
    assert "configuration" in server_config

    print(f"✓ MCP config valid")
    print(f"✓ Tools defined: {len(server_config['tools'])}")
    print(f"✓ Agents defined: {len(server_config['agents'])}")

except Exception as e:
    print(f"✗ MCP config invalid: {e}")
    sys.exit(1)
PYTHON_CHECK

echo ""

# 7. Check documentation
echo "Checking documentation..."
[ -f "src/lionagi_qe/mcp/README.md" ]
check "MCP README exists"

[ -f "docs/mcp-integration.md" ]
check "Integration guide exists"

[ -f "docs/mcp-quickstart.md" ]
check "Quick start guide exists"

echo ""

# 8. Check tests
echo "Checking tests..."
[ -f "tests/mcp/test_mcp_server.py" ]
check "Server tests exist"

[ -f "tests/mcp/test_mcp_tools.py" ]
check "Tool tests exist"

echo ""

# 9. Summary
echo "============================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Verification Complete!${NC}"
    echo "All checks passed successfully."

    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
    fi
else
    echo -e "${RED}✗ Verification Failed${NC}"
    echo "Errors: $ERRORS"
    echo "Warnings: $WARNINGS"
    exit 1
fi

echo ""
echo "Next steps:"
echo "  1. Run setup: ./scripts/setup-mcp.sh"
echo "  2. Run tests: pytest tests/mcp/ -v"
echo "  3. Try example: python examples/mcp_usage.py"
echo "  4. Read docs: cat docs/mcp-quickstart.md"
echo ""
