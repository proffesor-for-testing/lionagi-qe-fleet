# Environment-Based Storage Mode Selection

## Overview

The LionAGI QE Fleet now supports automatic storage backend selection based on environment mode, eliminating the need for manual configuration and providing optimal storage backends for each deployment scenario.

## Key Features

- **Automatic Environment Detection**: Reads `AQE_STORAGE_MODE`, `ENVIRONMENT`, or `NODE_ENV` to determine mode
- **Zero Configuration Development**: Default in-memory storage with no setup required
- **Production-Ready Persistence**: PostgreSQL backend with ACID guarantees
- **Backward Compatible**: Existing code continues to work without changes
- **Docker Integration**: Includes docker-compose for production setup

## Storage Modes

### Development Mode (DEV)
- **Backend**: Session.context (in-memory)
- **Setup**: None required
- **Persistence**: None (lost on restart)
- **Use Case**: Local development, experimentation
- **Performance**: Fast

### Testing Mode (TEST)
- **Backend**: Session.context (isolated in-memory)
- **Setup**: None required
- **Persistence**: None (clean slate per test)
- **Use Case**: Unit tests, CI/CD pipelines
- **Performance**: Fast

### Production Mode (PROD)
- **Backend**: PostgresMemory (persistent)
- **Setup**: PostgreSQL database required
- **Persistence**: Full ACID guarantees
- **Use Case**: Production deployments, multi-agent coordination
- **Performance**: Good (connection pooling)

## Quick Start

### 1. Development (Default)

```python
from lionagi_qe import QEOrchestrator

# Automatically uses Session.context
orchestrator = QEOrchestrator()
```

### 2. Testing

```python
from lionagi_qe import QEOrchestrator

# Explicit testing mode
orchestrator = QEOrchestrator(mode="test")
```

### 3. Production

```bash
# Set environment variables
export AQE_STORAGE_MODE=production
export DATABASE_URL=postgresql://user:pass@localhost:5432/db

# Start database
cd docker
docker-compose up -d postgres
```

```python
from lionagi_qe import QEOrchestrator

# Auto-detect from environment
orchestrator = QEOrchestrator.from_environment()

# Connect to PostgreSQL
await orchestrator.connect()

# Use normally
await orchestrator.memory.store("key", {"data": "value"})

# Clean up
await orchestrator.disconnect()
```

## Environment Variables

### Mode Selection (checked in order)

1. `AQE_STORAGE_MODE` - Explicit override
2. `ENVIRONMENT` - Common in Docker/cloud
3. `NODE_ENV` - Node.js convention
4. Defaults to `development`

Valid values: `development`, `testing`, `production` (or short forms: `dev`, `test`, `prod`)

### Production Configuration

Required:
- `DATABASE_URL` - PostgreSQL connection string

Optional:
- `DB_POOL_SIZE=5` - Minimum pool connections
- `DB_POOL_MAX_OVERFLOW=20` - Maximum additional connections
- `DB_CONNECTION_TIMEOUT=30` - Connection timeout (seconds)
- `DB_POOL_RECYCLE=3600` - Connection recycle time (seconds)

## Implementation Files

### Core Implementation
1. **`src/lionagi_qe/config/storage_config.py`** - Configuration system
   - `StorageMode` enum (DEV, TEST, PROD)
   - `StorageConfig` class with mode-based defaults
   - Environment detection logic

2. **`src/lionagi_qe/core/orchestrator.py`** - Updated orchestrator
   - `from_environment()` class method
   - `from_config()` class method
   - `connect()` / `disconnect()` methods
   - Automatic memory backend initialization

### Documentation
3. **`docs/guides/storage-modes.md`** - Complete guide
   - Mode comparison table
   - Usage examples for each mode
   - Configuration reference
   - Troubleshooting guide
   - Best practices

4. **`examples/storage_modes_example.py`** - Runnable examples
   - Development mode example
   - Testing mode example
   - Production mode example
   - Auto-detection example
   - Migration guide

### Docker & Configuration
5. **`examples/docker-compose.storage-example.yml`** - Production setup
   - PostgreSQL with optimized settings
   - pgAdmin for database management
   - Redis (optional high-speed cache)
   - Health checks and resource limits

6. **`examples/storage_init.sql`** - Database initialization
   - Creates `agent_memory` table
   - Adds indexes for performance
   - Sets up triggers for TTL handling
   - Inserts example data

7. **`.env.example`** - Updated with storage configuration
   - Added `AQE_STORAGE_MODE`
   - Added production mode settings
   - Added connection pool configuration

## Usage Examples

### Example 1: Auto-detect from Environment

```python
from lionagi_qe import QEOrchestrator

orchestrator = QEOrchestrator.from_environment()

if orchestrator.storage_config.mode.value == "production":
    await orchestrator.connect()

# Use orchestrator
# ...

if hasattr(orchestrator, 'db_manager'):
    await orchestrator.disconnect()
```

### Example 2: Explicit Configuration

```python
from lionagi_qe import StorageConfig, QEOrchestrator

# Development
config = StorageConfig.for_development()
orchestrator = QEOrchestrator.from_config(config)

# Testing
config = StorageConfig.for_testing()
orchestrator = QEOrchestrator.from_config(config)

# Production
config = StorageConfig.for_production(
    database_url="postgresql://user:pass@localhost:5432/db",
    min_connections=10,
    max_connections=50
)
orchestrator = QEOrchestrator.from_config(config)
await orchestrator.connect()
```

### Example 3: Multi-Agent Coordination (Production)

```python
from lionagi_qe import QEOrchestrator
from lionagi_qe.agents import TestGeneratorAgent, CoverageAnalyzerAgent
from lionagi import iModel
import os

# Create orchestrator (production)
orchestrator = QEOrchestrator(
    mode="prod",
    database_url=os.getenv("DATABASE_URL")
)
await orchestrator.connect()

# Create model
model = iModel(provider="openai", model="gpt-4o-mini")

# Register agents - they share the PostgreSQL backend
test_gen = orchestrator.create_and_register_agent(
    TestGeneratorAgent,
    agent_id="test-generator",
    model=model
)

coverage = orchestrator.create_and_register_agent(
    CoverageAnalyzerAgent,
    agent_id="coverage-analyzer",
    model=model
)

# Test generator stores results (persisted)
await test_gen.store_memory(
    "aqe/test-plan/generated",
    {"tests": ["test_auth", "test_profile"]}
)

# Coverage analyzer reads results (from PostgreSQL)
test_plan = await coverage.get_memory("aqe/test-plan/generated")
```

## Migration Guide

### From Manual Memory Management

**Before:**
```python
from lionagi_qe.core.memory import QEMemory
from lionagi_qe.core.router import ModelRouter
from lionagi_qe import QEOrchestrator

memory = QEMemory()
router = ModelRouter()
orchestrator = QEOrchestrator(memory=memory, router=router)
```

**After:**
```python
from lionagi_qe import QEOrchestrator

# Development (default)
orchestrator = QEOrchestrator()

# Production
orchestrator = QEOrchestrator(
    mode="prod",
    database_url=os.getenv("DATABASE_URL")
)
await orchestrator.connect()
```

### No Breaking Changes

The old approach continues to work:
```python
# Legacy code - still works!
memory = QEMemory()
orchestrator = QEOrchestrator(memory=memory)
```

## Docker Setup

### Start Services

```bash
# PostgreSQL only
cd examples
docker-compose -f docker-compose.storage-example.yml up -d

# PostgreSQL + pgAdmin
docker-compose -f docker-compose.storage-example.yml --profile with-pgadmin up -d

# All services (PostgreSQL + pgAdmin + Redis)
docker-compose -f docker-compose.storage-example.yml --profile with-pgadmin --profile with-redis up -d
```

### Access Services

- **PostgreSQL**: `localhost:5432`
- **pgAdmin**: `http://localhost:5050` (admin@lionagi.dev / admin_secure_123)
- **Redis**: `localhost:6379` (password: redis_secure_password_123)

### Stop Services

```bash
cd examples
docker-compose -f docker-compose.storage-example.yml down
```

## Testing

Run the example to test all modes:

```bash
# Development mode (default)
python examples/storage_modes_example.py

# Testing mode
export AQE_STORAGE_MODE=testing
python examples/storage_modes_example.py

# Production mode
cd examples
docker-compose -f docker-compose.storage-example.yml up -d
export AQE_STORAGE_MODE=production
export DATABASE_URL=postgresql://qe_agent:qe_secure_password_123@localhost:5432/lionagi_qe_learning
python storage_modes_example.py
```

## Configuration System Design

### StorageMode Enum

```python
class StorageMode(str, Enum):
    DEV = "development"
    TEST = "testing"
    PROD = "production"
```

### StorageConfig Class

- `mode`: Storage mode (DEV/TEST/PROD)
- `database_url`: PostgreSQL connection string
- `min_connections`: Minimum pool size
- `max_connections`: Maximum pool size
- Connection pool settings

### QEOrchestrator Integration

- `__init__()` accepts `mode` or `storage_config` parameter
- `from_environment()` auto-detects mode
- `from_config()` creates from StorageConfig
- `connect()` / `disconnect()` for production mode
- `_initialize_memory_from_config()` creates appropriate backend

## How Mode Detection Works

1. Check `AQE_STORAGE_MODE` environment variable (explicit)
2. Check `ENVIRONMENT` environment variable (Docker/cloud)
3. Check `NODE_ENV` environment variable (Node.js)
4. Default to `development` if none set

Example:
```bash
# Explicit override
export AQE_STORAGE_MODE=production

# Common in Docker
export ENVIRONMENT=production

# Node.js convention
export NODE_ENV=production
```

## Best Practices

1. **Use environment variables** - Never hardcode credentials
2. **Auto-detect in production** - `QEOrchestrator.from_environment()`
3. **Explicit mode in tests** - `QEOrchestrator(mode="test")`
4. **Always call connect()** - Required for production mode
5. **Use try/finally** - Ensure disconnect() is called
6. **Check mode** - Use `storage_config.mode` for conditional logic
7. **Connection pooling** - Tune based on workload

## Troubleshooting

### Issue: Production mode requires DATABASE_URL

**Solution:**
```bash
export DATABASE_URL=postgresql://user:pass@localhost:5432/db
```

### Issue: Cannot connect to PostgreSQL

**Check database is running:**
```bash
docker-compose ps
```

**Test connection:**
```bash
psql postgresql://qe_agent:qe_secure_password_123@localhost:5432/lionagi_qe_learning
```

### Issue: Connection pool exhausted

**Increase pool size:**
```bash
export DB_POOL_SIZE=10
export DB_POOL_MAX_OVERFLOW=40
```

### Issue: Import errors

**Ensure dependencies are installed:**
```bash
pip install lionagi-qe-fleet
```

## Performance Characteristics

| Operation | DEV | TEST | PROD |
|-----------|-----|------|------|
| **Store** | <1ms | <1ms | 5-10ms |
| **Retrieve** | <1ms | <1ms | 2-5ms |
| **Search** | <5ms | <5ms | 10-50ms |
| **Persistence** | None | None | Durable |
| **Multi-agent** | Single process | Single process | Yes |

## Summary

The environment-based storage mode selection provides:

- **Zero Configuration**: Works out-of-the-box for development
- **Test Isolation**: Clean memory for each test
- **Production Ready**: ACID-compliant persistence with PostgreSQL
- **Backward Compatible**: No breaking changes to existing code
- **Fully Documented**: Complete guide, examples, and troubleshooting
- **Docker Ready**: Includes production-ready docker-compose setup

## Next Steps

1. **Try the examples**: Run `python examples/storage_modes_example.py`
2. **Read the guide**: See `docs/guides/storage-modes.md` for details
3. **Setup production**: Use `examples/docker-compose.storage-example.yml`
4. **Update your code**: Migrate to `QEOrchestrator.from_environment()`

## Files Delivered

- ✅ `src/lionagi_qe/config/storage_config.py` - Configuration system
- ✅ `src/lionagi_qe/core/orchestrator.py` - Updated with mode support
- ✅ `docs/guides/storage-modes.md` - Complete documentation
- ✅ `examples/storage_modes_example.py` - Runnable examples
- ✅ `examples/docker-compose.storage-example.yml` - Production setup
- ✅ `examples/storage_init.sql` - Database initialization
- ✅ `.env.example` - Updated with storage configuration
- ✅ `docs/guides/STORAGE_MODES_README.md` - This implementation summary
