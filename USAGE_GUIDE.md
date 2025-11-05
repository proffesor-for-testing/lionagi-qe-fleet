# 🤖 LionAGI QE Fleet - Usage Guide

Complete guide to using the 18 specialized QE agents in your quality engineering workflow.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Agent Overview](#agent-overview)
3. [Basic Usage Pattern](#basic-usage-pattern)
4. [All 18 Agents](#all-18-agents)
5. [Agent Coordination](#agent-coordination)
6. [Memory System](#memory-system)
7. [Common Workflows](#common-workflows)
8. [Best Practices](#best-practices)

---

## Quick Start

### Installation

```bash
# Clone the repository
cd lionagi-qe-fleet

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env and add your API keys
```

### First Example (Direct Agent Usage)

```python
import asyncio
from dotenv import load_dotenv
from lionagi import iModel
from lionagi_qe import QETask
from lionagi_qe.agents import CoverageAnalyzerAgent

load_dotenv()

async def main():
    # 1. Initialize agent (no memory needed for single agent)
    model = iModel(provider="openai", model="gpt-4o-mini")
    agent = CoverageAnalyzerAgent("coverage-analyzer", model)

    # 2. Create task
    task = QETask(
        task_type="analyze_coverage",
        context={
            "coverage_data": {"overall": 78.5},
            "framework": "pytest",
            "target_coverage": 85
        }
    )

    # 3. Execute
    result = await agent.execute(task)
    print(f"Coverage: {result.overall_coverage}%")

asyncio.run(main())
```

### With Persistence (Production)

```python
from lionagi_qe import QEOrchestrator

async def main_with_persistence():
    # Initialize with PostgreSQL backend
    orchestrator = QEOrchestrator(
        memory_backend="postgres",
        postgres_url="postgresql://qe_user:password@localhost:5432/lionagi_qe"
    )
    await orchestrator.initialize()

    # Execute agent (results persist across restarts)
    result = await orchestrator.execute_agent("coverage-analyzer", task)
    print(f"Coverage: {result.overall_coverage}%")
```

---

## Agent Overview

### Core Testing (6 agents)

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **TestGeneratorAgent** | Generate comprehensive test suites | Need to create tests for new code |
| **TestExecutorAgent** | Execute tests with parallel support | Run test suites efficiently |
| **CoverageAnalyzerAgent** | Find gaps with O(log n) algorithms | Identify untested code paths |
| **QualityGateAgent** | GO/NO-GO deployment decisions | Before production deployments |
| **QualityAnalyzerAgent** | Comprehensive quality metrics | Regular quality assessments |
| **CodeComplexityAnalyzerAgent** | Analyze code complexity | Find refactoring opportunities |

### Performance & Security (2 agents)

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **PerformanceTesterAgent** | Load and stress testing | Validate performance requirements |
| **SecurityScannerAgent** | SAST/DAST security scanning | Detect security vulnerabilities |

### Strategic Planning (3 agents)

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **RequirementsValidatorAgent** | Validate testability of requirements | Before development starts |
| **ProductionIntelligenceAgent** | Convert prod data to test scenarios | Learn from production issues |
| **FleetCommanderAgent** | Coordinate multiple agents | Complex multi-agent workflows |

### Advanced Testing (4 agents)

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **APIContractValidatorAgent** | Detect API breaking changes | API versioning and compatibility |
| **RegressionRiskAnalyzerAgent** | Smart test selection (ML) | Optimize CI/CD test runs |
| **TestDataArchitectAgent** | Generate realistic test data | Need large datasets quickly |
| **FlakyTestHunterAgent** | Stabilize unreliable tests | High test flakiness |

### Specialized (3 agents)

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **DeploymentReadinessAgent** | Multi-factor deployment risk | Pre-deployment validation |
| **VisualTesterAgent** | Visual regression detection | UI/UX testing |
| **ChaosEngineerAgent** | Resilience and fault injection | Test system reliability |

---

## Basic Usage Pattern

All agents follow the same pattern:

### 1. Import Required Classes

```python
from dotenv import load_dotenv
from lionagi import iModel
from lionagi_qe.core.memory import QEMemory
from lionagi_qe.core.task import QETask
from lionagi_qe.agents import YourAgentClass
```

### 2. Initialize Components

**Option A: Direct Agent Usage (Simple)**
```python
load_dotenv()  # Load API keys

# Initialize model (supports OpenAI, Anthropic, Ollama)
model = iModel(provider="openai", model="gpt-4o-mini")

# Create agent (no shared memory needed)
agent = YourAgentClass(
    agent_id="unique-agent-id",
    model=model,
    skills=["relevant", "skills"],  # Optional
    enable_learning=False  # No persistence for single agent
)
```

**Option B: With QEOrchestrator (Multi-Agent + Persistence)**
```python
from lionagi_qe import QEOrchestrator

# Initialize orchestrator with persistence backend
orchestrator = QEOrchestrator(
    memory_backend="postgres",  # or "redis" or "memory"
    postgres_url="postgresql://user:pass@localhost:5432/lionagi_qe",
    enable_learning=True  # Q-learning with persistent storage
)
await orchestrator.initialize()

# Agents share memory automatically
agent = YourAgentClass(
    agent_id="unique-agent-id",
    model=model,
    memory=orchestrator.memory  # Shared persistence
)
orchestrator.register_agent(agent)
```

### 3. Create a Task

```python
task = QETask(
    task_type="specific_task_type",
    context={
        # Agent-specific context parameters
        "param1": "value1",
        "param2": "value2"
    }
)
```

### 4. Execute and Process Results

```python
result = await agent.execute(task)

# Result is a Pydantic model with typed fields
print(result.field1)
print(result.field2)
```

---

## All 18 Agents

### 1. Coverage Analyzer Agent

**Purpose**: Find test coverage gaps using O(log n) algorithms

```python
from lionagi_qe.agents import CoverageAnalyzerAgent

agent = CoverageAnalyzerAgent("coverage", model, memory)

task = QETask(
    task_type="analyze_coverage",
    context={
        "coverage_data": {
            "overall": 78.5,
            "files": {
                "src/module.py": {
                    "lines": {"covered": 85, "total": 100}
                }
            }
        },
        "framework": "pytest",  # pytest, jest, junit, mocha
        "codebase_path": "/src",
        "target_coverage": 85
    }
)

result = await agent.execute(task)
# Returns: CoverageAnalysisResult
print(f"Coverage: {result.overall_coverage}%")
print(f"Gaps: {len(result.gaps)}")
print(f"Critical Paths: {result.critical_paths}")
```

---

### 2. Quality Gate Agent

**Purpose**: Make GO/NO-GO deployment decisions

```python
from lionagi_qe.agents import QualityGateAgent

agent = QualityGateAgent("quality-gate", model, memory)

task = QETask(
    task_type="evaluate_quality",
    context={
        "test_results": {
            "total": 450,
            "passed": 445,
            "failed": 5
        },
        "coverage": {"overall": 92.5, "critical": 98.0},
        "code_quality": {"maintainability": 85, "complexity": 12},
        "security_scan": {"critical": 0, "high": 1, "medium": 3},
        "context": "production",  # development, staging, production
        "thresholds": {
            "min_coverage": 85,
            "max_failures": 10
        }
    }
)

result = await agent.execute(task)
# Returns: QualityGateResult
print(f"Decision: {result.decision}")  # GO, NO_GO, CONDITIONAL_GO
print(f"Score: {result.quality_score}/100")
print(f"Violations: {result.policy_violations}")
```

---

### 3. API Contract Validator Agent

**Purpose**: Detect breaking changes in API contracts

```python
from lionagi_qe.agents import APIContractValidatorAgent

agent = APIContractValidatorAgent("api-validator", model, memory)

task = QETask(
    task_type="api_contract_validation",
    context={
        "baseline_schema": openapi_spec_v1,  # OpenAPI/Swagger/GraphQL
        "candidate_schema": openapi_spec_v2,
        "current_version": "1.5.0",
        "proposed_version": "2.0.0",
        "consumers": ["mobile-app", "web-dashboard"]
    }
)

result = await agent.execute(task)
# Returns: APIContractValidatorResult
print(f"Valid: {result.validation.valid}")
print(f"Breaking Changes: {len(result.breaking_changes.breaking_changes)}")
print(f"Recommendation: {result.recommendation}")
```

---

### 4. Flaky Test Hunter Agent

**Purpose**: Detect and stabilize unreliable tests

```python
from lionagi_qe.agents import FlakyTestHunterAgent

agent = FlakyTestHunterAgent("flaky-hunter", model, memory)

# Provide historical test results
test_results = {
    "test_login": [True] * 20,  # Always passes
    "test_payment": [True, False, True, False] + [True] * 16,  # Flaky!
}

task = QETask(
    task_type="detect_flaky_tests",
    context={
        "test_results": test_results,
        "min_runs": 10,
        "auto_fix": False,
        "auto_quarantine": True,
        "target_reliability": 0.95
    }
)

result = await agent.execute(task)
# Returns: FlakyTestDetectionResult
print(f"Flaky Tests: {len(result.flaky_tests)}")
print(f"Reliability: {result.overall_reliability:.2%}")
for flaky in result.flaky_tests:
    print(f"  {flaky.test_name}: {flaky.reliability_score:.2%}")
```

---

### 5. Test Data Architect Agent

**Purpose**: Generate realistic test data at 10k+ records/sec

```python
from lionagi_qe.agents import TestDataArchitectAgent

agent = TestDataArchitectAgent("test-data", model, memory)

schema = {
    "User": {
        "fields": {
            "id": "uuid",
            "email": "email",
            "age": "integer[18:100]"
        },
        "relationships": {"orders": "hasMany:Order"}
    },
    "Order": {
        "fields": {
            "id": "uuid",
            "amount": "decimal[10:10000]"
        }
    }
}

task = QETask(
    task_type="generate_test_data",
    context={
        "schema_source": schema,
        "record_count": 1000,
        "include_edge_cases": True,
        "anonymize": True,  # GDPR compliance
        "compliance_standard": "GDPR"
    }
)

result = await agent.execute(task)
# Returns: TestDataGenerationResult
print(f"Records: {result.generation_summary.total_records}")
print(f"Speed: {result.generation_summary.records_per_second:.0f}/sec")
print(f"Quality: {result.quality_metrics.quality_score}/100")
```

---

### 6. Regression Risk Analyzer Agent

**Purpose**: Smart test selection using ML patterns (10x faster CI)

```python
from lionagi_qe.agents import RegressionRiskAnalyzerAgent

agent = RegressionRiskAnalyzerAgent("regression", model, memory)

code_changes = """
diff --git a/src/payment.py b/src/payment.py
+ added new currency conversion logic
"""

task = QETask(
    task_type="analyze_regression_risk",
    context={
        "code_changes": code_changes,
        "baseline_version": "v1.5.0",
        "confidence_threshold": 0.95,
        "commit_sha": "abc123",
        "author": "developer@example.com"
    }
)

result = await agent.execute(task)
# Returns: RegressionRiskAnalysisResult
print(f"Risk: {result.overall_risk}")
print(f"Recommended Tests: {len(result.recommended_tests)}")
print(f"Time Savings: {result.optimization.time_savings_percentage:.0f}%")
```

---

### 7. Chaos Engineer Agent

**Purpose**: Test system resilience with controlled fault injection

```python
from lionagi_qe.agents import ChaosEngineerAgent

agent = ChaosEngineerAgent("chaos", model, memory)

task = QETask(
    task_type="chaos_experiment",
    context={
        "experiment_type": "network_latency",  # or resource_exhaustion
        "target_service": "payment-api",
        "fault_config": {
            "type": "latency",
            "parameters": {"latency_ms": 2000, "variance_ms": 500}
        },
        "blast_radius": {
            "max_affected_percentage": 10,
            "max_downtime_seconds": 30
        },
        "steady_state_hypothesis": {
            "metrics": {
                "response_time_p95_ms": 200,
                "error_rate_percentage": 1.0
            }
        }
    }
)

result = await agent.execute(task)
# Returns: ChaosExperimentResult
print(f"Result: {result.result}")  # hypothesis_validated/failed
print(f"Resilience: {result.resilience_score}/100")
print(f"Recovery Time: {result.recovery_time_seconds}s")
```

---

### 8. Quality Analyzer Agent

**Purpose**: Comprehensive quality metrics with predictive analytics

```python
from lionagi_qe.agents import QualityAnalyzerAgent

agent = QualityAnalyzerAgent("quality", model, memory)

task = QETask(
    task_type="analyze_quality",
    context={
        "codebase_path": "/src",
        "static_analysis": {
            "complexity": 12,
            "duplication": 5.2,
            "maintainability": 78
        },
        "test_results": {
            "coverage": 85.5,
            "test_count": 450
        },
        "security_scan": {
            "vulnerabilities": 3,
            "severity_distribution": {"high": 1, "medium": 2}
        }
    }
)

result = await agent.execute(task)
# Returns: QualityAnalysisResult
print(f"Overall Score: {result.overall_quality_score}/100")
print(f"Trend: {result.trend.direction}")
print(f"Tech Debt: {result.technical_debt.debt_ratio:.1f}%")
```

---

## Persistence Configuration

### Memory Backend Options

**In-Memory (Development)**
```python
orchestrator = QEOrchestrator(memory_backend="memory")
# Fast, no dependencies, data lost on restart
```

**PostgreSQL (Production)**
```python
orchestrator = QEOrchestrator(
    memory_backend="postgres",
    postgres_url="postgresql://qe_user:password@localhost:5432/lionagi_qe"
)
# Persistent, ACID compliance, reuses Q-Learning infrastructure
```

**Redis (High-Speed Cache)**
```python
orchestrator = QEOrchestrator(
    memory_backend="redis",
    redis_url="redis://localhost:6379/0"
)
# Fast, ephemeral, good for distributed systems
```

### Setup PostgreSQL

**Using Docker:**
```bash
docker run -d \
  --name lionagi-qe-postgres \
  -e POSTGRES_DB=lionagi_qe \
  -e POSTGRES_USER=qe_user \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 \
  postgres:16-alpine

# Initialize schema (reuses Q-Learning schema!)
python -m lionagi_qe.persistence.init_db
```

**Benefits:**
- Reuses existing Q-Learning PostgreSQL infrastructure
- No additional database needed
- Same connection pooling (asyncpg)
- Already battle-tested with 7 tables

### Setup Redis

```bash
docker run -d --name lionagi-qe-redis -p 6379:6379 redis:7-alpine
```

## Agent Coordination

Agents share data through the **`aqe/*` memory namespace**:

### Sequential Pipeline

```python
# With QEOrchestrator
orchestrator = QEOrchestrator(memory_backend="postgres")
await orchestrator.initialize()

# Step 1: Coverage Analyzer finds gaps
coverage_result = await orchestrator.execute_agent("coverage-analyzer", coverage_task)
# Stores in: aqe/coverage/gaps (persists to PostgreSQL)

# Step 2: Test Generator reads from persistent memory
gaps = await orchestrator.memory.retrieve("aqe/coverage/gaps")
test_gen_task = QETask(
    task_type="generate_tests",
    context={"gaps": gaps}
)
test_result = await orchestrator.execute_agent("test-generator", test_gen_task)

# Step 3: Quality Gate evaluates readiness
gate_result = await orchestrator.execute_agent("quality-gate", gate_task)
```

### Parallel Execution

```python
# With QEOrchestrator
results = await orchestrator.execute_parallel(
    agents=["coverage-analyzer", "security-scanner", "performance-tester"],
    tasks=[coverage_task, security_task, perf_task]
)

coverage_result, security_result, perf_result = results

# Direct asyncio (no orchestrator)
import asyncio

results = await asyncio.gather(
    coverage_agent.execute(coverage_task),
    security_agent.execute(security_task),
    performance_agent.execute(perf_task)
)
```

---

## Memory System

All agents use the shared `aqe/*` memory namespace:

### Memory Keys by Agent

| Agent | Memory Keys |
|-------|-------------|
| Coverage Analyzer | `aqe/coverage/gaps`, `aqe/coverage/trends` |
| Quality Gate | `aqe/quality/decisions`, `aqe/quality/thresholds` |
| API Validator | `aqe/api/contracts/*`, `aqe/api/validation-history` |
| Flaky Hunter | `aqe/flaky-tests/*`, `aqe/test-stability/scores` |
| Test Data | `aqe/test-data/datasets/*` |
| Regression Risk | `aqe/regression/patterns`, `aqe/regression/risk-heat-map` |
| Chaos Engineer | `aqe/chaos-engineer/*`, `aqe/chaos/metrics` |
| Quality Analyzer | `aqe/quality/history`, `aqe/quality/patterns` |

### Using Memory

**With QEOrchestrator (Persistent):**
```python
orchestrator = QEOrchestrator(memory_backend="postgres")

# Store data (persists to database)
await orchestrator.memory.store(
    "aqe/my-key",
    {"data": "value"},
    ttl=86400  # 24 hours
)

# Retrieve data (from database)
data = await orchestrator.memory.retrieve("aqe/my-key")

# Search memory (regex search in database)
results = await orchestrator.memory.search("aqe/coverage/.*")
```

**Direct Agent Usage (No Persistence):**
```python
# Agents can work independently without shared memory
agent = CoverageAnalyzerAgent("coverage", model)
result = await agent.execute(task)
# Results are returned but not persisted
```

---

## Common Workflows

### Workflow 1: Pre-Deployment Check

```python
async def pre_deployment_check():
    # 1. Coverage analysis
    coverage = await coverage_agent.execute(coverage_task)

    # 2. Security scan
    security = await security_agent.execute(security_task)

    # 3. Quality gate decision
    gate_task = QETask(
        task_type="evaluate_quality",
        context={
            "coverage": coverage.model_dump(),
            "security_scan": security.model_dump()
        }
    )
    decision = await quality_gate.execute(gate_task)

    return decision.decision  # GO, NO_GO, CONDITIONAL_GO
```

### Workflow 2: Regression Testing Optimization

```python
async def optimize_regression_tests(code_changes):
    # 1. Analyze regression risk
    risk_result = await regression_agent.execute(
        QETask(task_type="analyze_regression_risk",
               context={"code_changes": code_changes})
    )

    # 2. Run only high-risk tests (10x faster)
    for test in risk_result.recommended_tests:
        await test_executor.execute(
            QETask(task_type="execute_test", context={"test": test})
        )
```

---

## Best Practices

### 1. Use Appropriate Models

```python
# Fast agents: use gpt-4o-mini
coverage_agent = CoverageAnalyzerAgent(
    "coverage",
    iModel(provider="openai", model="gpt-4o-mini"),
    memory
)

# Complex agents: use gpt-4 or claude-sonnet
api_validator = APIContractValidatorAgent(
    "api-validator",
    iModel(provider="anthropic", model="claude-sonnet-4-5"),
    memory
)
```

### 2. Enable Learning for Long-Running Agents

```python
agent = CoverageAnalyzerAgent(
    "coverage",
    model,
    memory,
    enable_learning=True  # Stores patterns for future improvements
)
```

### 3. Handle Errors Gracefully

```python
try:
    result = await agent.execute(task)
except Exception as e:
    # Check agent metrics for debugging
    metrics = await agent.get_metrics()
    print(f"Failed: {metrics['tasks_failed']}")
```

### 4. Monitor Costs

```python
# Use cost-effective models
model = iModel(provider="openai", model="gpt-4o-mini")

# Check agent costs
metrics = await agent.get_metrics()
print(f"Total cost: ${metrics['total_cost']:.4f}")
```

---

## Examples

Check the `examples/` directory for complete working examples:

- `quick_start.py` - Basic usage (2 agents)
- `demo_qe_agents.py` - All 8 advanced agents
- `01_basic_usage.py` - Single agent example
- `02_sequential_pipeline.py` - Multi-agent workflow
- `03_parallel_execution.py` - Concurrent agents

---

## Support

- **Documentation**: See `CLAUDE.md` for complete fleet documentation
- **Issues**: https://github.com/anthropics/lionagi-qe-fleet/issues
- **Examples**: Check the `examples/` directory

---

**Generated by**: LionAGI QE Fleet v1.4.1
**Last Updated**: 2025-11-04
