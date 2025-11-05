# Storage Modes Guide

Environment-based storage backend selection for LionAGI QE Fleet.

## Overview

The QE Fleet supports automatic storage backend selection based on environment mode:

- **Development Mode (DEV)**: Session.context (in-memory, zero setup)
- **Testing Mode (TEST)**: Session.context (isolated, fast tests)
- **Production Mode (PROD)**: PostgresMemory (durable, ACID guarantees)

## Quick Start

### Development (Default)

No configuration required - just create an orchestrator:

```python
from lionagi_qe.core.orchestrator import QEOrchestrator

orchestrator = QEOrchestrator()
# Uses Session.context automatically
```

### Testing

Explicitly set testing mode for isolated in-memory storage:

```python
orchestrator = QEOrchestrator(mode="test")
# Perfect for unit tests and CI/CD
```

### Production

Requires PostgreSQL database:

```python
import os
orchestrator = QEOrchestrator(
    mode="production",
    database_url=os.getenv("DATABASE_URL")
)
await orchestrator.connect()  # Required for production
```

## Environment Detection

The system automatically detects the environment by checking (in order):

1. `AQE_STORAGE_MODE` - Explicit override
2. `ENVIRONMENT` - Common in Docker/cloud platforms
3. `NODE_ENV` - Node.js convention
4. Defaults to `development` if none set

### Setting Environment Variables

```bash
# Development (default)
# No variables needed

# Testing
export AQE_STORAGE_MODE=testing

# Production
export AQE_STORAGE_MODE=production
export DATABASE_URL=postgresql://user:pass@localhost:5432/db
```

## Configuration

### StorageConfig Class

Create configurations programmatically:

```python
from lionagi_qe.config import StorageConfig, StorageMode

# Option 1: Auto-detect from environment
config = StorageConfig.from_environment()

# Option 2: Development
config = StorageConfig.for_development()

# Option 3: Testing
config = StorageConfig.for_testing()

# Option 4: Production
config = StorageConfig.for_production(
    database_url="postgresql://user:pass@localhost:5432/db",
    min_connections=5,
    max_connections=20
)

# Create orchestrator from config
orchestrator = QEOrchestrator.from_config(config)
```

### Connection Pooling (Production)

Configure PostgreSQL connection pool via environment variables:

```bash
# Connection pool settings
DB_POOL_SIZE=5               # Minimum connections
DB_POOL_MAX_OVERFLOW=20      # Maximum additional connections
DB_CONNECTION_TIMEOUT=30     # Timeout in seconds
DB_POOL_RECYCLE=3600         # Connection recycle time
```

Or programmatically:

```python
config = StorageConfig(
    mode=StorageMode.PROD,
    database_url="postgresql://...",
    min_connections=10,
    max_connections=50,
    connection_timeout=60,
    pool_recycle=7200
)
```

## Mode Comparison

| Feature | DEV | TEST | PROD |
|---------|-----|------|------|
| **Backend** | Session.context | Session.context | PostgresMemory |
| **Setup** | None | None | PostgreSQL required |
| **Persistence** | None | None | Full ACID |
| **Speed** | Fast | Fast | Good |
| **Multi-agent** | Single process | Single process | Yes |
| **Use case** | Development | Unit tests | Production |

## Usage Examples

### Example 1: Development Mode

```python
from lionagi_qe.core.orchestrator import QEOrchestrator

# Auto-detect (defaults to DEV)
orchestrator = QEOrchestrator()

# Store data
await orchestrator.memory.store(
    "aqe/test-plan/example",
    {"module": "user_service", "priority": "high"},
    ttl=3600
)

# Retrieve data
plan = await orchestrator.memory.retrieve("aqe/test-plan/example")
```

### Example 2: Testing Mode

```python
import pytest
from lionagi_qe.core.orchestrator import QEOrchestrator

@pytest.fixture
def orchestrator():
    return QEOrchestrator(mode="test")

async def test_coverage_analysis(orchestrator):
    # Each test gets clean, isolated memory
    await orchestrator.memory.store(
        "aqe/coverage/test_run",
        {"line_coverage": 85.5}
    )

    coverage = await orchestrator.memory.retrieve("aqe/coverage/test_run")
    assert coverage["line_coverage"] == 85.5
```

### Example 3: Production Mode

```python
import os
from lionagi_qe.core.orchestrator import QEOrchestrator

# Auto-detect from environment
orchestrator = QEOrchestrator.from_environment()

try:
    # Connect to PostgreSQL
    await orchestrator.connect()

    # Store persistent data
    await orchestrator.memory.store(
        "aqe/quality/metrics",
        {
            "total_tests": 1250,
            "coverage": 94.5,
            "quality_score": 98.2
        },
        ttl=86400,  # 24 hours
        partition="production_metrics"
    )

    # Data persists across restarts
    metrics = await orchestrator.memory.retrieve("aqe/quality/metrics")

finally:
    # Clean up
    await orchestrator.disconnect()
```

### Example 4: Multi-Agent Coordination

```python
from lionagi_qe.core.orchestrator import QEOrchestrator
from lionagi_qe.agents import TestGeneratorAgent, CoverageAnalyzerAgent
from lionagi import iModel

# Create orchestrator (production mode)
orchestrator = QEOrchestrator(
    mode="prod",
    database_url=os.getenv("DATABASE_URL")
)
await orchestrator.connect()

# Create model
model = iModel(provider="openai", model="gpt-4o-mini")

# Register agents with shared memory
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

# Agents automatically share the same PostgreSQL backend
# Test generator stores results
await test_gen.store_memory(
    "aqe/test-plan/generated",
    {"tests": [...]}
)

# Coverage analyzer reads results
test_plan = await coverage.get_memory("aqe/test-plan/generated")
```

## Docker Setup (Production)

### Start PostgreSQL

```bash
# Option 1: Use example docker-compose
cd examples
docker-compose -f docker-compose.storage-example.yml up -d

# Option 2: Use main docker setup
cd docker
docker-compose up -d postgres
```

### Configure Environment

```bash
export AQE_STORAGE_MODE=production
export DATABASE_URL=postgresql://qe_agent:qe_secure_password_123@localhost:5432/lionagi_qe_learning
```

### Run Application

```python
from lionagi_qe.core.orchestrator import QEOrchestrator

orchestrator = QEOrchestrator.from_environment()
await orchestrator.connect()

# Ready to use!
```

## Migration Guide

### From QEMemory to Environment-based Storage

**Before (Manual):**

```python
from lionagi_qe.core.memory import QEMemory
from lionagi_qe.core.router import ModelRouter
from lionagi_qe.core.orchestrator import QEOrchestrator

memory = QEMemory()
router = ModelRouter()
orchestrator = QEOrchestrator(memory=memory, router=router)
```

**After (Automatic):**

```python
from lionagi_qe.core.orchestrator import QEOrchestrator

# Development (default)
orchestrator = QEOrchestrator()

# Testing
orchestrator = QEOrchestrator(mode="test")

# Production
orchestrator = QEOrchestrator(
    mode="prod",
    database_url=os.getenv("DATABASE_URL")
)
await orchestrator.connect()
```

### Backward Compatibility

The old approach still works - no breaking changes!

```python
# Legacy code continues to work
memory = QEMemory()
orchestrator = QEOrchestrator(memory=memory)
```

## Best Practices

1. **Use environment variables for configuration**
   - Avoid hardcoding database URLs
   - Use `.env` files for local development
   - Use platform secrets for production

2. **Auto-detect mode in production**
   ```python
   orchestrator = QEOrchestrator.from_environment()
   ```

3. **Explicit mode in tests**
   ```python
   orchestrator = QEOrchestrator(mode="test")
   ```

4. **Always call connect() for production**
   ```python
   if orchestrator.storage_config.mode == StorageMode.PROD:
       await orchestrator.connect()
   ```

5. **Use try/finally for cleanup**
   ```python
   try:
       await orchestrator.connect()
       # ... use orchestrator ...
   finally:
       await orchestrator.disconnect()
   ```

6. **Check mode before operations**
   ```python
   if orchestrator.storage_config:
       print(f"Mode: {orchestrator.storage_config.mode.value}")
       print(orchestrator.storage_config.get_description())
   ```

## Environment Variables Reference

### Storage Mode Selection

| Variable | Description | Valid Values | Default |
|----------|-------------|--------------|---------|
| `AQE_STORAGE_MODE` | Explicit mode override | dev, test, prod | - |
| `ENVIRONMENT` | Common environment indicator | development, testing, production | - |
| `NODE_ENV` | Node.js convention | development, test, production | - |

### Production Mode Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required for prod |
| `DB_POOL_SIZE` | Minimum pool connections | 5 |
| `DB_POOL_MAX_OVERFLOW` | Maximum additional connections | 20 |
| `DB_CONNECTION_TIMEOUT` | Connection timeout (seconds) | 30 |
| `DB_POOL_RECYCLE` | Connection recycle time (seconds) | 3600 |

## Troubleshooting

### Problem: Production mode requires DATABASE_URL

**Solution:** Set the DATABASE_URL environment variable:

```bash
export DATABASE_URL=postgresql://user:pass@localhost:5432/db
```

### Problem: Cannot connect to PostgreSQL

**Check database is running:**

```bash
docker-compose ps
```

**Test connection:**

```bash
psql postgresql://qe_agent:qe_secure_password_123@localhost:5432/lionagi_qe_learning
```

### Problem: Connection pool exhausted

**Increase pool size:**

```bash
export DB_POOL_SIZE=10
export DB_POOL_MAX_OVERFLOW=40
```

Or programmatically:

```python
config = StorageConfig.for_production(
    database_url="postgresql://...",
    min_connections=10,
    max_connections=50
)
```

### Problem: Stale connections

**Reduce recycle time:**

```bash
export DB_POOL_RECYCLE=1800  # 30 minutes
```

## Additional Resources

- **Example Code:** `examples/storage_modes_example.py`
- **Docker Setup:** `examples/docker-compose.storage-example.yml`
- **Configuration:** `src/lionagi_qe/config/storage_config.py`
- **Orchestrator:** `src/lionagi_qe/core/orchestrator.py`
- **Memory Backends:** `examples/memory_backends_comparison.py`
