#!/bin/bash
# Quick script to run integration tests with proper setup

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}LionAGI QE Fleet Integration Tests${NC}"
echo -e "${GREEN}====================================${NC}\n"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo -e "${YELLOW}Step 1/4: Starting test databases...${NC}"
docker-compose -f docker-compose-test.yml up -d

echo -e "${YELLOW}Step 2/4: Waiting for databases to be ready...${NC}"
echo "Waiting for PostgreSQL..."
for i in {1..30}; do
    if docker exec lionagi-qe-postgres-test pg_isready -U qe_agent_test -d lionagi_qe_test > /dev/null 2>&1; then
        echo -e "${GREEN}PostgreSQL is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}PostgreSQL failed to start${NC}"
        docker-compose -f docker-compose-test.yml logs postgres-test
        exit 1
    fi
    sleep 1
done

echo "Waiting for Redis..."
for i in {1..30}; do
    if docker exec lionagi-qe-redis-test redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}Redis is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Redis failed to start${NC}"
        docker-compose -f docker-compose-test.yml logs redis-test
        exit 1
    fi
    sleep 1
done

echo -e "\n${YELLOW}Step 3/4: Running integration tests...${NC}\n"

# Parse command line arguments
TEST_ARGS=""
RUN_TYPE="all"

while [[ $# -gt 0 ]]; do
    case $1 in
        --postgres)
            RUN_TYPE="postgres"
            shift
            ;;
        --redis)
            RUN_TYPE="redis"
            shift
            ;;
        --e2e)
            RUN_TYPE="e2e"
            shift
            ;;
        --slow)
            TEST_ARGS="$TEST_ARGS -m integration"
            shift
            ;;
        --fast)
            TEST_ARGS="$TEST_ARGS -m 'integration and not slow'"
            shift
            ;;
        --coverage)
            TEST_ARGS="$TEST_ARGS --cov=src/lionagi_qe/persistence --cov-report=html --cov-report=term"
            shift
            ;;
        --parallel)
            TEST_ARGS="$TEST_ARGS -n auto"
            shift
            ;;
        *)
            TEST_ARGS="$TEST_ARGS $1"
            shift
            ;;
    esac
done

# Run appropriate tests
case $RUN_TYPE in
    postgres)
        echo "Running PostgreSQL integration tests..."
        pytest tests/integration/test_postgres_memory_integration.py -v -m postgres $TEST_ARGS
        ;;
    redis)
        echo "Running Redis integration tests..."
        pytest tests/integration/test_redis_memory_integration.py -v -m redis $TEST_ARGS
        ;;
    e2e)
        echo "Running end-to-end tests..."
        pytest tests/integration/test_agent_memory_e2e.py -v $TEST_ARGS
        ;;
    all)
        echo "Running all integration tests..."
        pytest tests/integration -v -m integration $TEST_ARGS
        ;;
esac

TEST_EXIT_CODE=$?

echo -e "\n${YELLOW}Step 4/4: Cleanup...${NC}"

# Ask user if they want to stop containers
echo -e "\n${YELLOW}Do you want to stop the test databases? (y/N)${NC}"
read -t 10 -n 1 STOP_CONTAINERS || STOP_CONTAINERS="n"
echo

if [[ $STOP_CONTAINERS =~ ^[Yy]$ ]]; then
    echo "Stopping containers..."
    docker-compose -f docker-compose-test.yml down
    echo -e "${GREEN}Containers stopped${NC}"
else
    echo -e "${YELLOW}Containers left running for next test run${NC}"
    echo "To stop manually: docker-compose -f docker-compose-test.yml down -v"
fi

# Exit with test exit code
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}\n"
else
    echo -e "\n${RED}✗ Some tests failed${NC}\n"
fi

exit $TEST_EXIT_CODE
