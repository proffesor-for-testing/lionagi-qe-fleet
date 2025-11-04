# LionAGI QE Fleet - Architecture Design

## Overview

This document outlines the architecture for rebuilding the Agentic QE Fleet using LionAGI as the orchestration framework, migrating from the TypeScript/Node.js implementation to Python.

## Why LionAGI for QE Fleet?

### Advantages

1. **Multi-Provider Support**: Built-in support for OpenAI, Anthropic, Ollama enables intelligent multi-model routing
2. **Async-First**: Perfect for parallel test execution (10,000+ concurrent tests)
3. **Structured Outputs**: Pydantic validation ensures type-safe agent responses
4. **Workflow Orchestration**: Builder/Operation graphs for complex QE pipelines
5. **ReAct Reasoning**: Advanced reasoning for intelligent test generation
6. **Session Management**: Built-in state persistence for agent coordination
7. **MCP Compatible**: Maintains integration with Claude Code and other tools
8. **Python Ecosystem**: Access to rich testing libraries (pytest, hypothesis, etc.)

### Key Design Principles

- **Agent Autonomy**: Each agent is self-contained with specific expertise
- **Event-Driven**: Agents communicate through shared memory and events
- **Hierarchical Coordination**: Fleet commander orchestrates specialized agents
- **Cost Optimization**: Intelligent model routing based on task complexity
- **Continuous Learning**: Q-learning integration for pattern improvement

## Architecture Layers

### Layer 1: Core Framework (LionAGI)

```
┌─────────────────────────────────────┐
│         LionAGI Core                │
│  - Branch (conversation context)    │
│  - iModel (multi-provider support)  │
│  - Session (state management)       │
│  - Builder (workflow graphs)        │
└─────────────────────────────────────┘
```

### Layer 2: QE Fleet Framework

```
┌─────────────────────────────────────┐
│      QE Fleet Framework             │
│  - BaseQEAgent (agent abstraction)  │
│  - QEMemory (shared namespace)      │
│  - QEOrchestrator (coordination)    │
│  - ModelRouter (cost optimization)  │
│  - SkillRegistry (34 QE skills)     │
└─────────────────────────────────────┘
```

### Layer 3: Specialized Agents (19 agents)

```
┌──────────────┬──────────────┬──────────────┐
│ Core Testing │ Performance  │  Strategic   │
│   (6 agents) │ & Security   │  Planning    │
│              │  (2 agents)  │  (3 agents)  │
├──────────────┼──────────────┼──────────────┤
│ Advanced     │ Specialized  │  General     │
│  Testing     │  (3 agents)  │  Purpose     │
│ (4 agents)   │              │  (1 agent)   │
└──────────────┴──────────────┴──────────────┘
```

## Component Design

### BaseQEAgent

All QE agents inherit from a common base class:

```python
from lionagi import Branch, iModel
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseQEAgent(ABC):
    """Base class for all QE agents"""

    def __init__(
        self,
        agent_id: str,
        model: iModel,
        memory: "QEMemory",
        skills: List[str] = None
    ):
        self.agent_id = agent_id
        self.model = model
        self.memory = memory
        self.skills = skills or []
        self.branch = Branch(
            system=self.get_system_prompt(),
            chat_model=model,
            name=agent_id
        )

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Define agent's expertise and behavior"""
        pass

    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent's primary function"""
        pass

    async def store_result(self, key: str, value: Any):
        """Store results in shared memory"""
        await self.memory.store(f"aqe/{self.agent_id}/{key}", value)

    async def retrieve_context(self, key: str) -> Any:
        """Retrieve context from shared memory"""
        return await self.memory.retrieve(key)
```

### QEMemory - Shared Memory Namespace

```python
from typing import Dict, Any, Optional
import asyncio

class QEMemory:
    """Shared memory namespace for agent coordination"""

    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    async def store(self, key: str, value: Any, ttl: Optional[int] = None):
        """Store value in memory namespace"""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            self._store[key] = {
                "value": value,
                "timestamp": asyncio.get_event_loop().time(),
                "ttl": ttl
            }

    async def retrieve(self, key: str) -> Any:
        """Retrieve value from memory"""
        if key in self._store:
            data = self._store[key]
            if self._is_expired(data):
                del self._store[key]
                return None
            return data["value"]
        return None

    async def search(self, pattern: str) -> Dict[str, Any]:
        """Search memory by pattern"""
        import re
        regex = re.compile(pattern)
        return {
            k: v["value"]
            for k, v in self._store.items()
            if regex.search(k) and not self._is_expired(v)
        }

    def _is_expired(self, data: Dict) -> bool:
        """Check if data has expired"""
        if data.get("ttl") is None:
            return False
        elapsed = asyncio.get_event_loop().time() - data["timestamp"]
        return elapsed > data["ttl"]
```

### ModelRouter - Multi-Model Cost Optimization

```python
from lionagi import iModel
from typing import Dict, Any, Literal
from pydantic import BaseModel

class TaskComplexity(BaseModel):
    level: Literal["simple", "moderate", "complex", "critical"]
    reasoning: str

class ModelRouter:
    """Route tasks to optimal models for cost efficiency"""

    def __init__(self):
        self.models = {
            "simple": iModel(provider="openai", model="gpt-3.5-turbo"),
            "moderate": iModel(provider="openai", model="gpt-4o-mini"),
            "complex": iModel(provider="openai", model="gpt-4"),
            "critical": iModel(
                provider="anthropic",
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000
            )
        }
        self.costs = {
            "simple": 0.0004,
            "moderate": 0.0008,
            "complex": 0.0048,
            "critical": 0.0065
        }

    async def analyze_complexity(self, task: str) -> TaskComplexity:
        """Analyze task complexity using a lightweight model"""
        analyzer = iModel(provider="openai", model="gpt-3.5-turbo")
        branch = Branch(
            system="Analyze task complexity for QE operations",
            chat_model=analyzer
        )

        result = await branch.operate(
            instruction=f"Classify this QE task complexity: {task}",
            response_format=TaskComplexity
        )
        return result

    async def route(self, task: str) -> tuple[iModel, float]:
        """Route task to appropriate model and return estimated cost"""
        complexity = await self.analyze_complexity(task)
        model = self.models[complexity.level]
        cost = self.costs[complexity.level]
        return model, cost
```

### QEOrchestrator - Fleet Coordination

```python
from lionagi import Builder, Session
from typing import List, Dict, Any

class QEOrchestrator:
    """Orchestrate QE agent workflows"""

    def __init__(self, memory: QEMemory, router: ModelRouter):
        self.memory = memory
        self.router = router
        self.agents: Dict[str, BaseQEAgent] = {}
        self.session = Session()

    def register_agent(self, agent: BaseQEAgent):
        """Register a QE agent"""
        self.agents[agent.agent_id] = agent

    async def execute_pipeline(
        self,
        pipeline: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a sequential QE pipeline"""
        builder = Builder("QE_Pipeline")
        nodes = []

        # Build workflow graph
        for i, agent_id in enumerate(pipeline):
            agent = self.agents[agent_id]
            node = builder.add_operation(
                "communicate",
                depends_on=nodes[-1:] if nodes else [],
                branch=agent.branch,
                instruction=context.get("instruction"),
                context=context
            )
            nodes.append(node)

        # Execute workflow
        result = await self.session.flow(builder.get_graph())
        return result

    async def execute_parallel(
        self,
        agent_ids: List[str],
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute agents in parallel"""
        from lionagi.ln import alcall

        async def run_agent(agent_id: str, task: Dict[str, Any]):
            agent = self.agents[agent_id]
            return await agent.execute(task)

        tasks_with_agents = [(aid, task) for aid, task in zip(agent_ids, tasks)]
        results = await alcall(
            tasks_with_agents,
            lambda x: run_agent(x[0], x[1])
        )
        return results
```

## Agent Implementations

### Example: TestGeneratorAgent

```python
from pydantic import BaseModel
from typing import List

class GeneratedTest(BaseModel):
    test_name: str
    test_code: str
    framework: str
    assertions: List[str]
    edge_cases: List[str]

class TestGeneratorAgent(BaseQEAgent):
    """Generate comprehensive test suites"""

    def get_system_prompt(self) -> str:
        return """You are an expert test generation agent specializing in:
        - Property-based testing
        - Edge case detection
        - Multiple framework support (Jest, Pytest, Mocha, Cypress)
        - TDD and BDD patterns

        Generate comprehensive, maintainable test suites with high coverage."""

    async def execute(self, task: Dict[str, Any]) -> GeneratedTest:
        """Generate tests for given code"""
        code = task.get("code")
        framework = task.get("framework", "pytest")

        # Check existing patterns from memory
        patterns = await self.memory.search(r"aqe/patterns/.*")

        result = await self.branch.operate(
            instruction=f"Generate tests for this code using {framework}",
            context={
                "code": code,
                "learned_patterns": patterns,
                "framework": framework
            },
            response_format=GeneratedTest
        )

        # Store generated test in memory
        await self.store_result("last_generated", result.model_dump())

        return result
```

### Example: FleetCommanderAgent

```python
class FleetCommanderAgent(BaseQEAgent):
    """Hierarchical coordinator for 50+ agents"""

    def get_system_prompt(self) -> str:
        return """You are the fleet commander coordinating QE operations.

        Your responsibilities:
        - Analyze incoming QE requests
        - Decompose into subtasks
        - Assign to specialized agents
        - Monitor progress
        - Synthesize results

        You coordinate test-generator, coverage-analyzer, security-scanner,
        performance-tester, and other specialized agents."""

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate multi-agent QE workflow"""
        from lionagi.fields import LIST_INSTRUCT_FIELD_MODEL, Instruct

        # Step 1: Analyze and decompose
        decomposition = await self.branch.operate(
            instruct=Instruct(
                instruction="Decompose this QE task into parallel subtasks",
                context=task,
                guidance="Assign each subtask to appropriate specialized agents"
            ),
            field_models=[LIST_INSTRUCT_FIELD_MODEL]
        )

        # Step 2: Fan-out to specialized agents
        subtasks = decomposition.instruct_model
        agent_assignments = [st.context.get("agent_id") for st in subtasks]

        # Step 3: Execute in parallel
        orchestrator = task.get("orchestrator")
        results = await orchestrator.execute_parallel(
            agent_assignments,
            [st.to_dict() for st in subtasks]
        )

        # Step 4: Synthesize results
        synthesis = await self.branch.communicate(
            "Synthesize QE results into final report",
            context={"agent_results": results}
        )

        return {
            "decomposition": subtasks,
            "agent_results": results,
            "synthesis": synthesis
        }
```

## Workflow Patterns

### Pattern 1: Sequential Pipeline

```
test-generator → test-executor → coverage-analyzer → quality-gate
```

### Pattern 2: Parallel Fan-Out/Fan-In

```
              ┌─→ test-generator ─┐
fleet-commander ─→ security-scanner ──→ synthesis
              └─→ performance-tester ─┘
```

### Pattern 3: Hierarchical Coordination

```
fleet-commander
    ├─→ core-testing-coordinator
    │       ├─→ test-generator
    │       ├─→ test-executor
    │       └─→ coverage-analyzer
    ├─→ security-coordinator
    │       ├─→ security-scanner
    │       └─→ chaos-engineer
    └─→ performance-coordinator
            └─→ performance-tester
```

## Memory Namespace Structure

```
aqe/
├── test-plan/
│   ├── requirements
│   ├── generated-tests
│   └── execution-plan
├── coverage/
│   ├── current
│   ├── gaps
│   └── targets
├── quality/
│   ├── metrics
│   ├── gates
│   └── violations
├── performance/
│   ├── benchmarks
│   ├── baselines
│   └── results
├── security/
│   ├── scans
│   ├── vulnerabilities
│   └── compliance
├── patterns/
│   ├── test-patterns
│   ├── bug-patterns
│   └── learned-patterns
└── swarm/
    └── coordination
```

## Integration Points

### 1. LionAGI Integration
- Use `Branch` for agent conversations
- Use `iModel` for multi-provider support
- Use `Session` for state management
- Use `Builder` for workflow graphs

### 2. Test Framework Integration
- pytest for Python testing
- hypothesis for property-based testing
- coverage.py for coverage analysis
- bandit/safety for security scanning

### 3. MCP Integration
- Maintain compatibility with Claude Code
- Support external tool integration
- Enable cross-platform coordination

## Migration Strategy

### Phase 1: Core Framework (Week 1-2)
1. Implement BaseQEAgent
2. Implement QEMemory
3. Implement ModelRouter
4. Implement QEOrchestrator

### Phase 2: Core Agents (Week 3-4)
1. TestGeneratorAgent
2. TestExecutorAgent
3. CoverageAnalyzerAgent
4. QualityGateAgent

### Phase 3: Advanced Agents (Week 5-6)
1. SecurityScannerAgent
2. PerformanceTesterAgent
3. FlakyTestHunterAgent
4. FleetCommanderAgent

### Phase 4: Integration & Testing (Week 7-8)
1. End-to-end workflows
2. Performance optimization
3. Documentation
4. Migration guides

## Success Metrics

- **Coverage**: Maintain 19 specialized agents
- **Performance**: 10,000+ concurrent test execution
- **Cost**: 70-81% savings through model routing
- **Quality**: 85%+ pattern matching accuracy
- **Reliability**: 100% flaky test detection accuracy

## Next Steps

1. Set up project structure
2. Implement base classes
3. Create example agents
4. Build sample workflows
5. Document usage patterns
