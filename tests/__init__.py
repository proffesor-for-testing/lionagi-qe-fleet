"""LionAGI QE Fleet Test Suite

Comprehensive unit tests for the LionAGI Quality Engineering Fleet.

Test Structure:
- test_core/: Core component tests (memory, router, task, orchestrator, fleet)
- test_agents/: Agent-specific tests (base, test generator, executor, commander)
- conftest.py: Shared fixtures and test utilities

Running Tests:
    pytest tests/                           # Run all tests
    pytest tests/test_core/                 # Run core tests only
    pytest tests/test_agents/               # Run agent tests only
    pytest tests/ -v                        # Verbose output
    pytest tests/ --cov=lionagi_qe         # With coverage
    pytest tests/ -k "test_memory"          # Run specific test pattern

Test Coverage Areas:
- QEMemory: Store, retrieve, search, TTL, partitions, state management
- ModelRouter: Complexity analysis, routing, cost optimization
- QETask: State management, lifecycle transitions
- QEOrchestrator: Pipeline, parallel, fan-out/fan-in workflows
- QEFleet: Initialization, agent registration, execution patterns
- BaseQEAgent: Hooks, memory integration, metrics, learning
- TestGeneratorAgent: Test generation, pattern learning, frameworks
- TestExecutorAgent: Test execution, coverage, flaky detection
- FleetCommanderAgent: Hierarchical coordination, decomposition, synthesis
"""

__version__ = "1.0.0"
