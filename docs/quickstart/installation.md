# Installation

Complete guide to installing and configuring the LionAGI QE Fleet.

## Prerequisites

### System Requirements
- Python 3.10 or higher
- 4GB RAM minimum (8GB recommended)
- pip 21.0+ or uv 0.1.0+

### API Keys Required
- OpenAI API key (required for most agents)
- Anthropic API key (optional, for Claude models)

## Installation Methods

### Method 1: Using pip (Recommended)

```bash
pip install lionagi-qe-fleet
```

### Method 2: Using uv (Faster)

```bash
uv pip install lionagi-qe-fleet
```

### Method 3: From Source (Development)

**Important**: Always use a virtual environment to avoid conflicts:

```bash
# Clone repository
git clone https://github.com/lionagi/lionagi-qe-fleet.git
cd lionagi-qe-fleet

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate  # On Windows

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

### Method 4: Local Build (Testing Before PyPI)

For testing the package locally before it's published to PyPI:

```bash
# Install build tools
pip install build

# Build the package
python -m build

# Install from local build
pip install dist/lionagi_qe_fleet-1.0.0-py3-none-any.whl

# Or install in editable mode (recommended for development)
pip install -e .
```

## API Key Configuration

### Option 1: Environment Variables (Recommended)

Create a `.env` file in your project root:

```bash
# Required for OpenAI models
OPENAI_API_KEY=sk-your-openai-key-here

# Optional for Anthropic models
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Optional: Enable advanced features
ENABLE_ROUTING=true
ENABLE_LEARNING=true
```

Load environment variables:

```python
from dotenv import load_dotenv
load_dotenv()
```

### Option 2: Export in Shell

```bash
export OPENAI_API_KEY=sk-your-openai-key-here
export ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

### Option 3: Programmatic Configuration

```python
import os

os.environ["OPENAI_API_KEY"] = "sk-your-openai-key-here"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-your-anthropic-key-here"
```

## Verify Installation

### Test 1: Import Check

```python
import lionagi
from lionagi_qe import QEOrchestrator
from lionagi_qe.agents import TestGeneratorAgent

print(f"LionAGI version: {lionagi.__version__}")
print("QE Fleet imported successfully!")
```

### Test 2: Quick Agent Test

```python
import asyncio
from lionagi import iModel
from lionagi_qe import QEOrchestrator

async def test_installation():
    orchestrator = QEOrchestrator()
    await orchestrator.initialize()
    print("QE Orchestrator initialized successfully!")

    # Test model connection
    model = iModel(provider="openai", model="gpt-3.5-turbo")
    print(f"Model configured: {model.provider}/{model.model}")

asyncio.run(test_installation())
```

Expected output:
```
QE Orchestrator initialized successfully!
Model configured: openai/gpt-3.5-turbo
```

### Test 3: Persistence Test (Optional)

```python
import asyncio
from lionagi_qe import QEOrchestrator

async def test_persistence():
    # Test PostgreSQL connection
    orchestrator = QEOrchestrator(
        memory_backend="postgres",
        postgres_url="postgresql://qe_user:secure_password@localhost:5432/lionagi_qe"
    )
    await orchestrator.initialize()

    # Store and retrieve test data
    await orchestrator.memory.store("test/key", {"value": "hello"})
    data = await orchestrator.memory.retrieve("test/key")

    print(f"Persistence test: {data}")  # Should print: {'value': 'hello'}
    print("Persistence working!")

asyncio.run(test_persistence())
```

## Persistence Setup (Production)

For production environments with persistent memory, you need a database backend.

### PostgreSQL Backend (Recommended)

**Install Dependencies:**
```bash
pip install lionagi-qe-fleet[postgres]
# or manually:
pip install asyncpg
```

**Setup PostgreSQL:**
```bash
# Using Docker (recommended)
docker run -d \
  --name lionagi-qe-postgres \
  -e POSTGRES_DB=lionagi_qe \
  -e POSTGRES_USER=qe_user \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 \
  postgres:16-alpine

# Initialize schema (reuses Q-Learning database!)
python -m lionagi_qe.persistence.init_db
```

**Configuration:**
```bash
# Add to .env file
POSTGRES_URL=postgresql://qe_user:secure_password@localhost:5432/lionagi_qe
```

**Benefits:**
- Reuses existing Q-Learning PostgreSQL infrastructure
- No additional database needed
- ACID compliance
- Production-ready

### Redis Backend (Fast, Ephemeral)

**Install Dependencies:**
```bash
pip install lionagi-qe-fleet[redis]
# or manually:
pip install redis aioredis
```

**Setup Redis:**
```bash
# Using Docker
docker run -d --name lionagi-qe-redis -p 6379:6379 redis:7-alpine
```

**Configuration:**
```bash
# Add to .env file
REDIS_URL=redis://localhost:6379/0
```

**Benefits:**
- High-speed caching
- Good for distributed systems
- Simple setup

### In-Memory (Development)

No setup needed - this is the default:
```python
from lionagi_qe import QEOrchestrator

orchestrator = QEOrchestrator(memory_backend="memory")
# Fast, no dependencies, data lost on restart
```

## Optional Dependencies

### For Enhanced Testing

```bash
pip install lionagi-qe-fleet[testing]
```

Includes:
- pytest
- pytest-asyncio
- hypothesis (property-based testing)
- coverage

### For Development

```bash
pip install lionagi-qe-fleet[dev]
```

Includes:
- All testing dependencies
- ruff (linting)
- mypy (type checking)
- black (formatting)

### For Documentation

```bash
pip install lionagi-qe-fleet[docs]
```

Includes:
- mkdocs
- mkdocs-material
- mkdocstrings

### All Extras

```bash
# Install everything (dev + postgres + redis)
pip install lionagi-qe-fleet[all]
```

## Configuration Options

### Fleet Configuration

Create `.agentic-qe/config/fleet.json`:

```json
{
  "topology": "hierarchical",
  "max_agents": 10,
  "testing_focus": ["unit", "integration"],
  "environments": ["development", "staging"],
  "frameworks": ["pytest", "jest"]
}
```

### Routing Configuration

Create `.agentic-qe/config/routing.json`:

```json
{
  "multiModelRouter": {
    "enabled": true,
    "models": {
      "simple": "gpt-3.5-turbo",
      "moderate": "gpt-4o-mini",
      "complex": "gpt-4",
      "critical": "claude-3-5-sonnet-20241022"
    }
  }
}
```

## Troubleshooting

**For comprehensive troubleshooting**, see [Troubleshooting Guide](troubleshooting.md).

### Common Issues

#### Issue: Import Error

**Symptom**: `ModuleNotFoundError: No module named 'lionagi_qe'`

**Solution**:
```bash
pip install --upgrade lionagi-qe-fleet
```

### Issue: API Key Not Found

**Symptom**: `ValueError: OPENAI_API_KEY not found`

**Solution**:
1. Verify `.env` file exists
2. Check key is correctly set: `echo $OPENAI_API_KEY`
3. Ensure `load_dotenv()` is called before imports

### Issue: Version Conflicts

**Symptom**: `ERROR: pip's dependency resolver does not currently take into account all the packages that are installed`

**Solution**:
```bash
pip install --upgrade pip
pip install lionagi-qe-fleet --no-deps
pip install lionagi pydantic aiohttp
```

### Issue: Slow Installation

**Symptom**: Installation takes more than 5 minutes

**Solution**: Use uv for faster installs:
```bash
pip install uv
uv pip install lionagi-qe-fleet
```

### Issue: Python Version

**Symptom**: `Requires-Python: >=3.10`

**Solution**: Upgrade Python:
```bash
# Using pyenv
pyenv install 3.11
pyenv local 3.11

# Using conda
conda create -n qe-fleet python=3.11
conda activate qe-fleet
```

## Platform-Specific Notes

### macOS

```bash
# Install Python 3.11 if needed
brew install python@3.11

# Install QE Fleet
python3.11 -m pip install lionagi-qe-fleet
```

### Linux (Ubuntu/Debian)

```bash
# Install Python 3.11
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Install QE Fleet
python3.11 -m pip install lionagi-qe-fleet
```

### Windows

```powershell
# Install using Python from python.org
py -3.11 -m pip install lionagi-qe-fleet

# Or use winget
winget install Python.Python.3.11
```

## Next Steps

Now that you're set up:

1. **Try your first agent** → [Your First Agent](your-first-agent.md)
2. **Explore workflows** → [Basic Workflows](basic-workflows.md)
3. **Understand architecture** → [System Overview](../architecture/system-overview.md)

## Getting Help

- Check [Common Issues](#troubleshooting) above
- Join [LionAGI Discord](https://discord.gg/lionagi)
- Open an issue on [GitHub](https://github.com/lion-agi/lionagi-qe-fleet)
- Read [LionAGI docs](https://khive-ai.github.io/lionagi/)

---

**Next**: [Your First Agent](your-first-agent.md) - Create your first QE agent →
