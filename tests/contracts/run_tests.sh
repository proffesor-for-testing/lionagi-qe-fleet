#!/bin/bash
# Contract Testing Execution Script
# Run all contract tests and breaking change detection

set -e  # Exit on error

echo "================================================"
echo "   LionAGI QE Fleet - Contract Testing Suite   "
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if in correct directory
if [ ! -f "requirements.txt" ]; then
    echo "${RED}Error: Must run from tests/contracts directory${NC}"
    exit 1
fi

# Install dependencies
echo "${YELLOW}[1/5] Installing dependencies...${NC}"
pip install -q -r requirements.txt
echo "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Run GitHub Actions consumer contracts
echo "${YELLOW}[2/5] Running GitHub Actions consumer contracts...${NC}"
pytest pact/github_actions_consumer.py -v --tb=short
echo "${GREEN}✓ GitHub Actions contracts verified${NC}"
echo ""

# Run GitLab CI consumer contracts
echo "${YELLOW}[3/5] Running GitLab CI consumer contracts...${NC}"
pytest pact/gitlab_ci_consumer.py -v --tb=short
echo "${GREEN}✓ GitLab CI contracts verified${NC}"
echo ""

# Run CLI consumer contracts
echo "${YELLOW}[4/5] Running CLI consumer contracts...${NC}"
pytest pact/cli_consumer.py -v --tb=short
echo "${GREEN}✓ CLI contracts verified${NC}"
echo ""

# Run breaking change detection
echo "${YELLOW}[5/5] Running breaking change detection...${NC}"
pytest breaking_changes_test.py -v --tb=short
echo "${GREEN}✓ Breaking change detection passed${NC}"
echo ""

# Summary
echo "================================================"
echo "${GREEN}   All Contract Tests Passed! ✓${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Publish contracts to Pact Broker"
echo "  2. Verify provider against contracts"
echo "  3. Integrate into CI/CD pipeline"
echo ""
