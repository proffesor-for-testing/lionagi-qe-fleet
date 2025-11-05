.PHONY: help setup up down restart logs ps psql pgadmin redis backup restore reset clean health test

# Default target
help:
	@echo "LionAGI QE Fleet - Docker Commands"
	@echo "==================================="
	@echo ""
	@echo "Setup & Startup:"
	@echo "  make setup          Setup environment and start services"
	@echo "  make up             Start all services (postgres, pgadmin)"
	@echo "  make up-redis       Start all services including Redis"
	@echo "  make down           Stop all services"
	@echo "  make restart        Restart all services"
	@echo ""
	@echo "Database:"
	@echo "  make psql           Connect to PostgreSQL interactively"
	@echo "  make backup         Backup database to SQL file"
	@echo "  make restore        Restore database from backup"
	@echo "  make reset          Reset development database (CAREFUL!)"
	@echo "  make reset-all      Reset everything including patterns (CAREFUL!)"
	@echo ""
	@echo "Management:"
	@echo "  make logs           View all service logs"
	@echo "  make logs-postgres  View PostgreSQL logs"
	@echo "  make logs-pgadmin   View pgAdmin logs"
	@echo "  make logs-redis     View Redis logs (requires with-redis)"
	@echo "  make ps             Show running containers"
	@echo "  make health         Check service health"
	@echo ""
	@echo "Testing & Monitoring:"
	@echo "  make test-db        Test database connection"
	@echo "  make test-redis     Test Redis connection"
	@echo "  make pgadmin        Open pgAdmin in browser"
	@echo "  make stats          Show database statistics"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          Remove containers and volumes"
	@echo "  make prune          Clean up Docker system (CAREFUL!)"
	@echo ""

# Setup environment file and start services
setup:
	@echo "Setting up LionAGI QE Fleet..."
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
		echo "✓ .env created. Please update with your credentials."; \
	else \
		echo "✓ .env already exists"; \
	fi
	@echo "Starting services..."
	@docker-compose up -d
	@echo "✓ Services started!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Wait for services to be healthy: make health"
	@echo "  2. Access pgAdmin: http://localhost:5050/pgadmin"
	@echo "  3. Connect to database: make psql"

# Start services
up:
	@echo "Starting services (postgres, pgadmin)..."
	@docker-compose up -d
	@echo "✓ Services started"
	@echo "pgAdmin: http://localhost:5050/pgadmin"

# Start with Redis
up-redis:
	@echo "Starting services with Redis..."
	@docker-compose --profile with-redis up -d
	@echo "✓ Services started with Redis"
	@echo "PostgreSQL: localhost:5432"
	@echo "pgAdmin: http://localhost:5050/pgadmin"
	@echo "Redis: localhost:6379"

# Stop services
down:
	@echo "Stopping services..."
	@docker-compose down
	@echo "✓ Services stopped"

# Restart services
restart:
	@echo "Restarting services..."
	@docker-compose restart
	@echo "✓ Services restarted"

# View logs
logs:
	@docker-compose logs -f

logs-postgres:
	@docker-compose logs -f postgres

logs-pgadmin:
	@docker-compose logs -f pgadmin

logs-redis:
	@docker-compose --profile with-redis logs -f redis

# Show running containers
ps:
	@docker-compose ps

# Health check
health:
	@echo "Checking service health..."
	@docker-compose ps
	@echo ""
	@echo "Detailed health status:"
	@docker inspect lionagi-qe-postgres | jq -r '.[0] | "PostgreSQL: " + .State.Health.Status' 2>/dev/null || echo "PostgreSQL: Unable to determine"
	@docker inspect lionagi-qe-pgadmin | jq -r '.[0] | "pgAdmin: " + .State.Health.Status' 2>/dev/null || echo "pgAdmin: Unable to determine"

# Connect to PostgreSQL
psql:
	@docker-compose exec postgres psql -U qe_agent -d lionagi_qe_learning

# Connect to PostgreSQL with specific command
psql-%:
	@docker-compose exec postgres psql -U qe_agent -d lionagi_qe_learning -c "$*"

# pgAdmin access
pgadmin:
	@echo "Opening pgAdmin..."
	@echo "URL: http://localhost:5050/pgadmin"
	@echo "Login: admin@lionagi.dev / admin_secure_123"
	@command -v open >/dev/null 2>&1 && open "http://localhost:5050/pgadmin" || \
	command -v xdg-open >/dev/null 2>&1 && xdg-open "http://localhost:5050/pgadmin" || \
	echo "Please open http://localhost:5050/pgadmin in your browser"

# Test database connection
test-db:
	@echo "Testing database connection..."
	@docker-compose exec postgres pg_isready -U qe_agent -d lionagi_qe_learning && \
	echo "✓ Database connection successful" || echo "✗ Database connection failed"

# Test Redis connection
test-redis:
	@echo "Testing Redis connection..."
	@docker-compose --profile with-redis exec redis redis-cli -a $$(grep REDIS_PASSWORD .env | cut -d= -f2) ping && \
	echo "✓ Redis connection successful" || echo "✗ Redis not running or connection failed"

# Database statistics
stats:
	@echo "Database Statistics:"
	@docker-compose exec postgres psql -U qe_agent -d lionagi_qe_learning -c "SELECT pg_size_pretty(pg_database_size('lionagi_qe_learning')) as database_size;"
	@echo ""
	@echo "Table Sizes:"
	@docker-compose exec postgres psql -U qe_agent -d lionagi_qe_learning -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema') ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
	@echo ""
	@echo "Active Connections:"
	@docker-compose exec postgres psql -U qe_agent -d lionagi_qe_learning -c "SELECT datname, count(*) as connections FROM pg_stat_activity GROUP BY datname;"

# Backup database
backup:
	@echo "Backing up database..."
	@BACKUP_FILE="backup_$$(date +%Y%m%d_%H%M%S).sql"; \
	docker-compose exec -T postgres pg_dump -U qe_agent -d lionagi_qe_learning > $$BACKUP_FILE; \
	echo "✓ Database backed up to $$BACKUP_FILE"

# Compressed backup
backup-gz:
	@echo "Backing up database (compressed)..."
	@BACKUP_FILE="backup_$$(date +%Y%m%d_%H%M%S).sql.gz"; \
	docker-compose exec -T postgres pg_dump -U qe_agent -d lionagi_qe_learning | gzip > $$BACKUP_FILE; \
	echo "✓ Database backed up to $$BACKUP_FILE"

# Schema-only backup
backup-schema:
	@echo "Backing up schema only..."
	@BACKUP_FILE="schema_$$(date +%Y%m%d_%H%M%S).sql"; \
	docker-compose exec -T postgres pg_dump -U qe_agent -d lionagi_qe_learning --schema-only > $$BACKUP_FILE; \
	echo "✓ Schema backed up to $$BACKUP_FILE"

# Restore from backup (FILE=backup.sql)
restore:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make restore FILE=backup.sql"; \
		exit 1; \
	fi
	@echo "Restoring from $(FILE)..."
	@cat $(FILE) | docker-compose exec -T postgres psql -U qe_agent -d lionagi_qe_learning
	@echo "✓ Database restored"

# Reset development database
reset:
	@echo "WARNING: This will delete all test execution data!"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose exec postgres psql -U qe_agent -d lionagi_qe_learning -c "SELECT qlearning.dev_reset_database(false);" && \
		echo "✓ Database reset (patterns preserved)"; \
	else \
		echo "Reset cancelled"; \
	fi

# Reset everything
reset-all:
	@echo "WARNING: This will DELETE ALL DATA including patterns and Q-values!"
	@read -p "Type 'DELETE' to confirm: " CONFIRM; \
	if [ "$$CONFIRM" = "DELETE" ]; then \
		docker-compose exec postgres psql -U qe_agent -d lionagi_qe_learning -c "SELECT qlearning.dev_reset_database(true);" && \
		echo "✓ Complete database reset"; \
	else \
		echo "Reset cancelled"; \
	fi

# Archive old data
archive:
	@echo "Archiving data older than 90 days..."
	@docker-compose exec postgres psql -U qe_agent -d lionagi_qe_learning -c "CALL qlearning.archive_old_data(90);"
	@echo "✓ Data archived"

# Clean (remove containers and volumes)
clean:
	@echo "WARNING: This will remove containers and volumes!"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v && \
		echo "✓ Containers and volumes removed"; \
	else \
		echo "Clean cancelled"; \
	fi

# Docker system prune
prune:
	@echo "WARNING: This will remove all unused Docker resources!"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker system prune -a --volumes && \
		echo "✓ Docker system cleaned"; \
	else \
		echo "Prune cancelled"; \
	fi

# Create directory if needed
.PHONY: ensure-env
ensure-env:
	@mkdir -p postgres pgadmin
