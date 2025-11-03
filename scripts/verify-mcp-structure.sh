#!/bin/bash
# Structure verification script (no dependencies required)

set -e

echo "🔍 Verifying MCP Integration Structure"
echo "======================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

ERRORS=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        ERRORS=$((ERRORS + 1))
    fi
}

# Check files
echo "Checking MCP module files..."
[ -f "src/lionagi_qe/mcp/__init__.py" ]; check "__init__.py"
[ -f "src/lionagi_qe/mcp/mcp_server.py" ]; check "mcp_server.py"
[ -f "src/lionagi_qe/mcp/mcp_tools.py" ]; check "mcp_tools.py"
[ -f "src/lionagi_qe/mcp/README.md" ]; check "README.md"
echo ""

echo "Checking configuration files..."
[ -f "mcp_config.json" ]; check "mcp_config.json"
[ -f "pyproject.toml" ]; check "pyproject.toml"
echo ""

echo "Checking scripts..."
[ -f "scripts/setup-mcp.sh" ]; check "setup-mcp.sh"
[ -x "scripts/setup-mcp.sh" ]; check "setup-mcp.sh is executable"
echo ""

echo "Checking documentation..."
[ -f "CLAUDE_CODE_INTEGRATION.md" ]; check "CLAUDE_CODE_INTEGRATION.md"
[ -f "docs/mcp-integration.md" ]; check "docs/mcp-integration.md"
[ -f "docs/mcp-quickstart.md" ]; check "docs/mcp-quickstart.md"
[ -f "MCP_INTEGRATION_SUMMARY.md" ]; check "MCP_INTEGRATION_SUMMARY.md"
echo ""

echo "Checking tests..."
[ -f "tests/mcp/__init__.py" ]; check "tests/__init__.py"
[ -f "tests/mcp/test_mcp_server.py" ]; check "test_mcp_server.py"
[ -f "tests/mcp/test_mcp_tools.py" ]; check "test_mcp_tools.py"
echo ""

echo "Checking examples..."
[ -f "examples/mcp_usage.py" ]; check "mcp_usage.py"
echo ""

# Count lines
echo "Code statistics..."
echo -n "Implementation: "
wc -l src/lionagi_qe/mcp/*.py | tail -1 | awk '{print $1 " lines"}'

echo -n "Tests: "
wc -l tests/mcp/*.py | tail -1 | awk '{print $1 " lines"}'

echo -n "Examples: "
wc -l examples/mcp_usage.py | awk '{print $1 " lines"}'

echo -n "Documentation: "
wc -l src/lionagi_qe/mcp/README.md docs/mcp-*.md CLAUDE_CODE_INTEGRATION.md MCP_INTEGRATION_SUMMARY.md 2>/dev/null | tail -1 | awk '{print $1 " lines"}'

echo ""
echo "======================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Structure Verification Complete!${NC}"
    echo "All files present and correctly structured."
else
    echo -e "${RED}✗ Verification Failed${NC}"
    echo "Missing files: $ERRORS"
    exit 1
fi

echo ""
echo "Summary of created files:"
echo "  • 3 implementation files (mcp_server.py, mcp_tools.py, __init__.py)"
echo "  • 2 configuration files (mcp_config.json, pyproject.toml update)"
echo "  • 2 setup scripts (setup-mcp.sh, verify-mcp-structure.sh)"
echo "  • 5 documentation files (README.md, integration guides, summary)"
echo "  • 3 test files (test_mcp_server.py, test_mcp_tools.py, __init__.py)"
echo "  • 1 example file (mcp_usage.py)"
echo ""
echo "Total: 16 files created/modified"
echo ""
echo "Next steps:"
echo "  1. Install dependencies: pip install -e .[mcp]"
echo "  2. Run setup: ./scripts/setup-mcp.sh"
echo "  3. Run tests: pytest tests/mcp/ -v"
echo "  4. Read docs: cat docs/mcp-quickstart.md"
echo ""
