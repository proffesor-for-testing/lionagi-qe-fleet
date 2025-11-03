# LionAGI QE Fleet

**Agentic Quality Engineering powered by LionAGI**

A Python reimplementation of the Agentic QE Fleet using LionAGI as the orchestration framework. This fleet provides 19 specialized AI agents for comprehensive software testing and quality assurance.

## 🚀 Features

- **19 Specialized Agents**: From test generation to deployment readiness
- **Multi-Model Routing**: 70-81% cost savings through intelligent model selection
- **Parallel Execution**: Handle 10,000+ concurrent tests
- **Q-Learning Integration**: Continuous improvement from past executions
- **34 QE Skills**: World-class quality engineering practices
- **Framework Agnostic**: Works with pytest, Jest, Mocha, Cypress, and more

## 📦 Installation

### Using uv (recommended)

```bash
uv add lionagi-qe-fleet
```

### Using pip

```bash
pip install lionagi-qe-fleet
```

### Development Installation

```bash
git clone <repository-url>
cd lionagi-qe-fleet
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

## 🏃 Quick Start

### Basic Usage

```python
import asyncio
from lionagi_qe import QEFleet, QETask

async def main():
    # Initialize the QE fleet
    fleet = QEFleet()
    await fleet.initialize()

    # Create a test generation task
    task = QETask(
        task_type="generate_tests",
        context={
            "code": "def add(a, b): return a + b",
            "framework": "pytest"
        }
    )

    # Execute with test generator agent
    result = await fleet.execute("test-generator", task)
    print(result.test_code)

asyncio.run(main())
```

### Multi-Agent Pipeline

```python
async def quality_pipeline():
    fleet = QEFleet()
    await fleet.initialize()

    # Execute sequential pipeline
    result = await fleet.execute_pipeline(
        pipeline=[
            "test-generator",
            "test-executor",
            "coverage-analyzer",
            "quality-gate"
        ],
        context={
            "code_path": "./src",
            "coverage_threshold": 80
        }
    )

    print(f"Coverage: {result['coverage']}%")
    print(f"Quality Gate: {result['passed']}")
```

### Parallel Agent Execution

```python
async def parallel_analysis():
    fleet = QEFleet()
    await fleet.initialize()

    # Run multiple agents in parallel
    results = await fleet.execute_parallel(
        agents=["test-generator", "security-scanner", "performance-tester"],
        tasks=[
            {"task": "generate_tests", "code": code1},
            {"task": "security_scan", "path": "./src"},
            {"task": "load_test", "endpoint": "/api/users"}
        ]
    )

    for agent_id, result in zip(agents, results):
        print(f"{agent_id}: {result}")
```

## 🤖 Available Agents

### Core Testing (6 agents)
- **test-generator**: Generate comprehensive test suites with edge cases
- **test-executor**: Execute tests across multiple frameworks in parallel
- **coverage-analyzer**: Identify coverage gaps using O(log n) algorithms
- **quality-gate**: ML-driven quality validation and pass/fail decisions
- **quality-analyzer**: Integrate ESLint, SonarQube, Lighthouse metrics
- **code-complexity**: Analyze cyclomatic and cognitive complexity

### Performance & Security (2 agents)
- **performance-tester**: Load testing with k6, JMeter, Gatling
- **security-scanner**: SAST, DAST, dependency scanning

### Strategic Planning (3 agents)
- **requirements-validator**: Testability analysis with INVEST criteria
- **production-intelligence**: Incident replay and anomaly detection
- **fleet-commander**: Orchestrate 50+ agents hierarchically

### Advanced Testing (4 agents)
- **regression-risk-analyzer**: Smart test selection via ML patterns
- **test-data-architect**: Generate realistic test data (10k+ records/sec)
- **api-contract-validator**: Detect breaking changes in APIs
- **flaky-test-hunter**: 100% accuracy flaky test detection

### Specialized (3 agents)
- **deployment-readiness**: Multi-factor release risk assessment
- **visual-tester**: AI-powered UI regression detection
- **chaos-engineer**: Fault injection and resilience testing

### General Purpose (1 agent)
- **base-template-generator**: Create custom agent definitions

## 📋 Agent Coordination

Agents coordinate through a shared memory namespace (`aqe/*`):

```
aqe/
├── test-plan/      # Test requirements and plans
├── coverage/       # Coverage analysis results
├── quality/        # Quality metrics and gates
├── performance/    # Performance test results
├── security/       # Security scan findings
├── patterns/       # Learned test patterns
└── swarm/         # Multi-agent coordination
```

## 💡 Advanced Features

### Multi-Model Routing

Automatically route tasks to optimal models for cost efficiency:

```python
fleet = QEFleet(enable_routing=True)

# Simple tasks → GPT-3.5 ($0.0004)
# Moderate tasks → GPT-4o-mini ($0.0008)
# Complex tasks → GPT-4 ($0.0048)
# Critical tasks → Claude Sonnet 4.5 ($0.0065)
```

### Q-Learning Integration

Agents learn from past executions:

```python
# Enable learning mode
fleet = QEFleet(enable_learning=True)

# Agents automatically improve through experience
# Target: 20% improvement over baseline
```

### Custom Workflows

Build complex workflows with LionAGI's Builder:

```python
from lionagi import Builder

builder = Builder("CustomQEWorkflow")
node1 = builder.add_operation("test-generator", context=ctx)
node2 = builder.add_operation("security-scanner", depends_on=[node1])
node3 = builder.add_operation("quality-gate", depends_on=[node1, node2])

result = await fleet.execute_workflow(builder.get_graph())
```

## 📚 Documentation

- [Architecture Guide](docs/LIONAGI_QE_FLEET_ARCHITECTURE.md)
- [Migration Guide](docs/MIGRATION_GUIDE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Agent Specifications](docs/AGENT_SPECS.md)
- [Examples](examples/)

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/lionagi_qe --cov-report=html

# Run specific test category
pytest tests/test_agents.py
pytest tests/test_orchestration.py
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

Apache 2.0 - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built on [LionAGI](https://github.com/khive-ai/lionagi)
- Inspired by the original [Agentic QE Fleet](https://github.com/proffesor-for-testing/agentic-qe)

## 🔗 Links

- [LionAGI Documentation](https://khive-ai.github.io/lionagi/)
- [Original Agentic QE Fleet](https://github.com/proffesor-for-testing/agentic-qe)

---

**🦁 Powered by LionAGI - Because quality engineering demands intelligent agents**
