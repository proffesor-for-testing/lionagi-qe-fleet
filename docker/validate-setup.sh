#!/bin/bash

# LionAGI QE Fleet - Docker Setup Validation Script
# Validates that all Docker services are properly configured and running

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Status variables
ISSUES=0
WARNINGS=0
CHECKS_PASSED=0

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ((ISSUES++))
}

check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

# ============================================================================
# Main Validation
# ============================================================================

main() {
    echo ""
    print_header "LionAGI QE Fleet - Docker Setup Validator"
    echo ""

    # Check prerequisites
    print_header "Checking Prerequisites"
    check_command docker
    check_command docker-compose
    check_command grep
    echo ""

    # Check environment file
    print_header "Checking Configuration Files"
    if [ -f .env ]; then
        print_success ".env file exists"
        if grep -q "POSTGRES_PASSWORD" .env; then
            print_success "POSTGRES_PASSWORD is configured"
        else
            print_warning "POSTGRES_PASSWORD not found in .env"
        fi
    else
        print_warning ".env file not found (using defaults)"
    fi

    if [ -f docker-compose.yml ]; then
        print_success "docker-compose.yml exists"
    else
        print_error "docker-compose.yml not found"
    fi

    if [ -f postgres/schema.sql ]; then
        print_success "postgres/schema.sql exists"
    else
        print_error "postgres/schema.sql not found"
    fi
    echo ""

    # Check Docker daemon
    print_header "Checking Docker Daemon"
    if docker ps &> /dev/null; then
        print_success "Docker daemon is running"
    else
        print_error "Docker daemon is not running"
        return 1
    fi
    echo ""

    # Check ports
    print_header "Checking Port Availability"
    POSTGRES_PORT=${POSTGRES_PORT:-5432}
    PGADMIN_PORT=${PGADMIN_PORT:-5050}
    REDIS_PORT=${REDIS_PORT:-6379}

    if ! nc -z localhost $POSTGRES_PORT 2>/dev/null; then
        print_success "Port $POSTGRES_PORT is available (PostgreSQL)"
    else
        print_warning "Port $POSTGRES_PORT is in use"
    fi

    if ! nc -z localhost $PGADMIN_PORT 2>/dev/null; then
        print_success "Port $PGADMIN_PORT is available (pgAdmin)"
    else
        print_warning "Port $PGADMIN_PORT is in use"
    fi

    if ! nc -z localhost $REDIS_PORT 2>/dev/null; then
        print_success "Port $REDIS_PORT is available (Redis)"
    else
        print_warning "Port $REDIS_PORT is in use (Redis not started)"
    fi
    echo ""

    # Check container status
    print_header "Checking Running Containers"

    # Check if containers exist and are running
    if docker ps --format "{{.Names}}" | grep -q "lionagi-qe-postgres"; then
        print_success "PostgreSQL container is running"
        # Check health
        HEALTH=$(docker inspect lionagi-qe-postgres --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
        if [ "$HEALTH" = "healthy" ]; then
            print_success "PostgreSQL is healthy"
        elif [ "$HEALTH" = "starting" ]; then
            print_warning "PostgreSQL is starting (wait a bit longer)"
        else
            print_warning "PostgreSQL health status: $HEALTH"
        fi
    else
        print_warning "PostgreSQL container not running"
    fi

    if docker ps --format "{{.Names}}" | grep -q "lionagi-qe-pgadmin"; then
        print_success "pgAdmin container is running"
        HEALTH=$(docker inspect lionagi-qe-pgadmin --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
        if [ "$HEALTH" = "healthy" ]; then
            print_success "pgAdmin is healthy"
        elif [ "$HEALTH" = "starting" ]; then
            print_warning "pgAdmin is starting (wait a bit longer)"
        else
            print_warning "pgAdmin health status: $HEALTH"
        fi
    else
        print_warning "pgAdmin container not running"
    fi

    if docker ps --format "{{.Names}}" | grep -q "lionagi-qe-redis"; then
        print_success "Redis container is running"
        HEALTH=$(docker inspect lionagi-qe-redis --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
        if [ "$HEALTH" = "healthy" ]; then
            print_success "Redis is healthy"
        else
            print_warning "Redis health status: $HEALTH"
        fi
    else
        print_warning "Redis container not running (optional)"
    fi
    echo ""

    # Test database connectivity
    print_header "Testing Database Connectivity"
    if docker ps --format "{{.Names}}" | grep -q "lionagi-qe-postgres"; then
        if docker-compose exec -T postgres pg_isready -U qe_agent -d lionagi_qe_learning &> /dev/null; then
            print_success "PostgreSQL accepts connections"

            # Test simple query
            if docker-compose exec -T postgres psql -U qe_agent -d lionagi_qe_learning -c "SELECT 1;" &> /dev/null; then
                print_success "Can execute SQL queries"
            else
                print_error "Cannot execute SQL queries"
            fi

            # Check schemas
            SCHEMAS=$(docker-compose exec -T postgres psql -U qe_agent -d lionagi_qe_learning -t -c "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name LIKE 'qlearning%';" 2>/dev/null)
            if [ "$SCHEMAS" -ge 1 ]; then
                print_success "Q-Learning schemas exist"
            else
                print_warning "Q-Learning schemas not found (may need to initialize)"
            fi

            # Check tables
            TABLES=$(docker-compose exec -T postgres psql -U qe_agent -d lionagi_qe_learning -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'qlearning';" 2>/dev/null)
            if [ "$TABLES" -gt 0 ]; then
                print_success "Q-Learning tables exist ($TABLES tables)"
            else
                print_warning "Q-Learning tables not found (may need to initialize)"
            fi
        else
            print_error "PostgreSQL not accepting connections"
        fi
    fi
    echo ""

    # Test pgAdmin accessibility (optional)
    print_header "Testing pgAdmin Accessibility"
    if command -v curl &> /dev/null; then
        if curl -s http://localhost:5050/pgadmin &> /dev/null; then
            print_success "pgAdmin web interface is accessible"
        else
            print_warning "pgAdmin web interface not accessible (may be starting)"
        fi
    else
        print_warning "curl not installed, skipping pgAdmin connectivity test"
    fi
    echo ""

    # Test Redis connectivity (if running)
    print_header "Testing Redis Connectivity"
    if docker ps --format "{{.Names}}" | grep -q "lionagi-qe-redis"; then
        if docker-compose --profile with-redis exec -T redis redis-cli -a redis_secure_password_123 ping &> /dev/null; then
            print_success "Redis accepts connections"
        else
            print_error "Redis not accepting connections"
        fi
    else
        print_warning "Redis not running (optional - use 'docker-compose --profile with-redis up' to enable)"
    fi
    echo ""

    # Check file permissions
    print_header "Checking File Permissions"
    if [ -r postgres/schema.sql ]; then
        print_success "postgres/schema.sql is readable"
    else
        print_error "postgres/schema.sql is not readable"
    fi

    if [ -r postgres/init.sql ]; then
        print_success "postgres/init.sql is readable"
    else
        print_error "postgres/init.sql is not readable"
    fi
    echo ""

    # Summary
    print_header "Validation Summary"
    echo "Passed:  $CHECKS_PASSED"
    echo "Warnings: $WARNINGS"
    echo "Issues:  $ISSUES"
    echo ""

    if [ $ISSUES -eq 0 ]; then
        echo -e "${GREEN}✓ Setup validation successful!${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Connect to database: docker-compose exec postgres psql -U qe_agent -d lionagi_qe_learning"
        echo "  2. Access pgAdmin: http://localhost:5050/pgadmin"
        echo "  3. View logs: docker-compose logs -f"
        return 0
    else
        echo -e "${RED}✗ Validation found $ISSUES issue(s)${NC}"
        echo ""
        echo "Troubleshooting tips:"
        echo "  - Check that Docker daemon is running"
        echo "  - Verify ports are not in use: lsof -i :5432 :5050 :6379"
        echo "  - Review logs: docker-compose logs"
        echo "  - Ensure containers are healthy: docker-compose ps"
        return 1
    fi
}

# Run main function
main "$@"
