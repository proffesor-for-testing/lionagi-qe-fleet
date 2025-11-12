#!/bin/bash
# Chaos Engineering Test Suite Runner
# Executes comprehensive chaos experiments for Phase 1 components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CHAOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS_DIR="${CHAOS_DIR}/results/$(date +%Y%m%d_%H%M%S)"
ENVIRONMENT="${ENVIRONMENT:-development}"

# Create results directory
mkdir -p "${RESULTS_DIR}"

echo "========================================="
echo "Chaos Engineering Test Suite"
echo "========================================="
echo "Environment: ${ENVIRONMENT}"
echo "Results Directory: ${RESULTS_DIR}"
echo ""

# Function to run a chaos experiment
run_chaos_experiment() {
    local experiment_file=$1
    local experiment_name=$(basename "${experiment_file}" .json)

    echo -e "${YELLOW}Running experiment: ${experiment_name}${NC}"

    if chaos run "${experiment_file}" --journal-path="${RESULTS_DIR}/${experiment_name}-journal.json"; then
        echo -e "${GREEN}✓ ${experiment_name} completed successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ ${experiment_name} failed${NC}"
        return 1
    fi
}

# Function to run pytest resilience tests
run_resilience_tests() {
    local test_file=$1
    local test_name=$(basename "${test_file}" .py)

    echo -e "${YELLOW}Running resilience tests: ${test_name}${NC}"

    if pytest "${test_file}" -v --tb=short --junitxml="${RESULTS_DIR}/${test_name}-results.xml"; then
        echo -e "${GREEN}✓ ${test_name} passed${NC}"
        return 0
    else
        echo -e "${RED}✗ ${test_name} failed${NC}"
        return 1
    fi
}

# Pre-flight checks
echo "========================================="
echo "Pre-Flight Checks"
echo "========================================="

# Check if Chaos Toolkit is installed
if ! command -v chaos &> /dev/null; then
    echo -e "${RED}✗ Chaos Toolkit not found. Install with: pip install chaostoolkit${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Chaos Toolkit installed${NC}"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}✗ pytest not found. Install with: pip install pytest${NC}"
    exit 1
fi
echo -e "${GREEN}✓ pytest installed${NC}"

# Check if services are running (optional, based on environment)
if [ "${ENVIRONMENT}" != "ci" ]; then
    if ! redis-cli ping &> /dev/null; then
        echo -e "${YELLOW}⚠ Redis not running (some tests may be skipped)${NC}"
    else
        echo -e "${GREEN}✓ Redis running${NC}"
    fi

    if ! pg_isready -q &> /dev/null; then
        echo -e "${YELLOW}⚠ PostgreSQL not running (some tests may be skipped)${NC}"
    else
        echo -e "${GREEN}✓ PostgreSQL running${NC}"
    fi
fi

echo ""

# Run Chaos Toolkit experiments
echo "========================================="
echo "Chaos Toolkit Experiments"
echo "========================================="

CHAOS_EXPERIMENTS=(
    "${CHAOS_DIR}/chaostoolkit/redis-failure-experiment.json"
    "${CHAOS_DIR}/chaostoolkit/postgres-failure-experiment.json"
    "${CHAOS_DIR}/chaostoolkit/storage-failure-experiment.json"
)

CHAOS_FAILED=0
for experiment in "${CHAOS_EXPERIMENTS[@]}"; do
    if [ -f "${experiment}" ]; then
        run_chaos_experiment "${experiment}" || CHAOS_FAILED=$((CHAOS_FAILED + 1))
        echo ""
    else
        echo -e "${YELLOW}⚠ Experiment not found: ${experiment}${NC}"
        echo ""
    fi
done

# Run pytest resilience tests
echo "========================================="
echo "Resilience Tests (pytest)"
echo "========================================="

RESILIENCE_TESTS=(
    "${CHAOS_DIR}/resilience/test_redis_resilience.py"
    "${CHAOS_DIR}/resilience/test_postgres_resilience.py"
    "${CHAOS_DIR}/resilience/test_storage_resilience.py"
    "${CHAOS_DIR}/resilience/test_network_resilience.py"
    "${CHAOS_DIR}/resilience/test_resource_exhaustion.py"
    "${CHAOS_DIR}/resilience/test_observability.py"
)

TESTS_FAILED=0
for test in "${RESILIENCE_TESTS[@]}"; do
    if [ -f "${test}" ]; then
        run_resilience_tests "${test}" || TESTS_FAILED=$((TESTS_FAILED + 1))
        echo ""
    else
        echo -e "${YELLOW}⚠ Test not found: ${test}${NC}"
        echo ""
    fi
done

# Generate summary report
echo "========================================="
echo "Summary Report"
echo "========================================="

TOTAL_CHAOS_EXPERIMENTS=${#CHAOS_EXPERIMENTS[@]}
TOTAL_RESILIENCE_TESTS=${#RESILIENCE_TESTS[@]}
TOTAL_TESTS=$((TOTAL_CHAOS_EXPERIMENTS + TOTAL_RESILIENCE_TESTS))
TOTAL_FAILED=$((CHAOS_FAILED + TESTS_FAILED))
TOTAL_PASSED=$((TOTAL_TESTS - TOTAL_FAILED))

echo "Chaos Toolkit Experiments:"
echo "  Total: ${TOTAL_CHAOS_EXPERIMENTS}"
echo "  Failed: ${CHAOS_FAILED}"
echo ""
echo "Resilience Tests:"
echo "  Total: ${TOTAL_RESILIENCE_TESTS}"
echo "  Failed: ${TESTS_FAILED}"
echo ""
echo "Overall:"
echo "  Total: ${TOTAL_TESTS}"
echo "  Passed: ${TOTAL_PASSED}"
echo "  Failed: ${TOTAL_FAILED}"
echo ""

if [ ${TOTAL_FAILED} -eq 0 ]; then
    echo -e "${GREEN}✓ All chaos experiments and tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ ${TOTAL_FAILED} experiments/tests failed${NC}"
    echo "Check results in: ${RESULTS_DIR}"
    exit 1
fi
