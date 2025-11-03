#!/bin/bash
# Setup script for LionAGI QE Fleet MCP integration

set -e

echo "🚀 Setting up LionAGI QE Fleet MCP Integration"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python 3.10+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"
echo ""

# Check Claude Code CLI
echo -e "${BLUE}Checking Claude Code CLI...${NC}"
if ! command -v claude &> /dev/null; then
    echo -e "${YELLOW}⚠ Claude Code CLI not found${NC}"
    echo "Install from: https://claude.ai/code"
    exit 1
fi
echo -e "${GREEN}✓ Claude Code CLI installed${NC}"
echo ""

# Install package
echo -e "${BLUE}Installing LionAGI QE Fleet...${NC}"
if [ "$1" == "--dev" ]; then
    echo "Installing in development mode..."
    pip install -e ".[mcp]"
else
    pip install ".[mcp]"
fi
echo -e "${GREEN}✓ Package installed${NC}"
echo ""

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MCP_CONFIG="$PROJECT_ROOT/mcp_config.json"

echo -e "${BLUE}Project root: $PROJECT_ROOT${NC}"
echo ""

# Add MCP server to Claude Code
echo -e "${BLUE}Adding MCP server to Claude Code...${NC}"

# Remove existing server if present
claude mcp remove lionagi-qe 2>/dev/null || true

# Add server
if [ -f "$MCP_CONFIG" ]; then
    echo "Using config file: $MCP_CONFIG"
    claude mcp add lionagi-qe --config "$MCP_CONFIG"
else
    echo "Config file not found, using manual setup..."
    claude mcp add lionagi-qe python -m lionagi_qe.mcp.mcp_server
    claude mcp env lionagi-qe PYTHONPATH "$PROJECT_ROOT/src"
fi

echo -e "${GREEN}✓ MCP server added${NC}"
echo ""

# Verify installation
echo -e "${BLUE}Verifying MCP server...${NC}"
if claude mcp list | grep -q "lionagi-qe"; then
    echo -e "${GREEN}✓ MCP server registered${NC}"
else
    echo -e "${RED}✗ MCP server registration failed${NC}"
    exit 1
fi
echo ""

# Test connection
echo -e "${BLUE}Testing MCP connection...${NC}"
python3 << 'PYTHON_TEST'
import asyncio
import sys

try:
    from lionagi_qe.mcp.mcp_server import create_mcp_server

    async def test():
        server = create_mcp_server()
        await server.initialize_fleet()
        print("\033[0;32m✓ Fleet initialized successfully\033[0m")

        status = await server.fleet.get_status()
        if status.get("initialized"):
            print("\033[0;32m✓ Fleet status: OK\033[0m")
        else:
            print("\033[0;31m✗ Fleet status: Not initialized\033[0m")
            sys.exit(1)

        await server.stop()

    asyncio.run(test())

except Exception as e:
    print(f"\033[0;31m✗ Test failed: {e}\033[0m")
    sys.exit(1)
PYTHON_TEST

echo ""

# Print success message
echo -e "${GREEN}=============================================="
echo -e "✓ MCP Integration Setup Complete!${NC}"
echo -e "${GREEN}==============================================\033[0m"
echo ""
echo "Available MCP Tools:"
echo "  • test_generate          - Generate comprehensive test suites"
echo "  • test_execute           - Execute tests with parallel processing"
echo "  • coverage_analyze       - Analyze coverage with O(log n) algorithms"
echo "  • quality_gate           - Intelligent quality gate"
echo "  • performance_test       - Load and performance testing"
echo "  • security_scan          - Multi-layer security scanning"
echo "  • fleet_orchestrate      - Multi-agent workflows"
echo "  • get_fleet_status       - Fleet status and metrics"
echo "  ... and 9 more advanced tools"
echo ""
echo "Usage in Claude Code:"
echo "  mcp__lionagi_qe__test_generate({code: '...', framework: 'pytest'})"
echo ""
echo "Or spawn agents via Task tool:"
echo "  Task('Generate tests', 'Create test suite', 'test-generator')"
echo ""
echo "Documentation:"
echo "  • MCP README:     $PROJECT_ROOT/src/lionagi_qe/mcp/README.md"
echo "  • Integration:    $PROJECT_ROOT/docs/mcp-integration.md"
echo "  • Examples:       $PROJECT_ROOT/examples/"
echo ""
echo "Next steps:"
echo "  1. Verify: claude mcp list"
echo "  2. Test: claude 'Use mcp__lionagi_qe__get_fleet_status'"
echo "  3. Read docs: cat $PROJECT_ROOT/src/lionagi_qe/mcp/README.md"
echo ""
