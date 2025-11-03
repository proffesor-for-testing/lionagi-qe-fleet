# Migration Guide: TypeScript Agentic QE Fleet → LionAGI QE Fleet

This guide helps you migrate from the TypeScript/Node.js Agentic QE Fleet to the Python/LionAGI implementation.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Key Differences](#key-differences)
3. [Migration Steps](#migration-steps)
4. [Agent Migration](#agent-migration)
5. [Memory Namespace Migration](#memory-namespace-migration)
6. [Workflow Patterns](#workflow-patterns)
7. [Testing](#testing)
8. [Deployment](#deployment)

## Overview

### Why Migrate to LionAGI?

**Advantages:**
- ✅ **Python Ecosystem**: Access to rich scientific and ML libraries
- ✅ **LionAGI Framework**: Built-in multi-model support, structured outputs, ReAct reasoning
- ✅ **Better Type Safety**: Pydantic validation throughout
- ✅ **Simplified Coordination**: Native async/await patterns
- ✅ **Cost Optimization**: Built-in multi-model routing
- ✅ **Learning Integration**: Q-learning support out of the box

**Trade-offs:**
- ⚠️ **Runtime**: Python vs Node.js (generally similar performance for AI workloads)
- ⚠️ **Ecosystem**: New dependencies and tooling
- ⚠️ **Migration Effort**: Code rewrite required (not 1:1 port)

## Key Differences

### Architecture Comparison

| Feature | TypeScript Fleet | LionAGI Fleet |
|---------|-----------------|---------------|
| **Language** | TypeScript | Python |
| **Framework** | Custom MCP | LionAGI |
| **Coordination** | AQE Hooks | LionAGI Session/Branch |
| **Memory** | Custom namespace | QEMemory class |
| **Routing** | Multi-model router | ModelRouter class |
| **Agents** | TypeScript classes | Python BaseQEAgent |
| **Workflows** | Event-driven | Builder/Operation graphs |
| **Testing** | Jest/Mocha | pytest |

### Conceptual Mapping

#### TypeScript → LionAGI

```typescript
// TypeScript Agent
class TestGeneratorAgent extends BaseAgent {
  async execute(task: Task): Promise<Result> {
    // Implementation
  }
}
```

```python
# LionAGI Agent
class TestGeneratorAgent(BaseQEAgent):
    async def execute(self, task: QETask) -> GeneratedTest:
        # Implementation
        pass
```

#### Memory Namespace

```typescript
// TypeScript
await memory.store('aqe/test-plan/generated', data);
const data = await memory.retrieve('aqe/test-plan/generated');
```

```python
# LionAGI
await self.memory.store('aqe/test-plan/generated', data)
data = await self.memory.retrieve('aqe/test-plan/generated')
```

#### Agent Coordination

```typescript
// TypeScript - MCP orchestration
const result = await mcp__agentic_qe__task_orchestrate({
  task: "generate_tests",
  agents: ["test-generator", "test-executor"]
});
```

```python
# LionAGI - Direct orchestration
result = await fleet.execute_pipeline(
    pipeline=["test-generator", "test-executor"],
    context={"instruction": "generate_tests"}
)
```

## Migration Steps

### Step 1: Environment Setup

#### Install Python and Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install LionAGI QE Fleet
pip install lionagi-qe-fleet

# Or for development
git clone <your-repo>
cd lionagi-qe-fleet
pip install -e ".[dev]"
```

#### Environment Variables

```bash
# .env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Optional
ENABLE_ROUTING=true
ENABLE_LEARNING=true
LOG_LEVEL=INFO
```

### Step 2: Project Structure Migration

#### TypeScript Structure
```
agentic-qe/
├── src/
│   ├── agents/
│   ├── core/
│   └── mcp/
├── tests/
└── .agentic-qe/
```

#### LionAGI Structure
```
lionagi-qe-fleet/
├── src/lionagi_qe/
│   ├── agents/
│   ├── core/
│   ├── skills/
│   └── utils/
├── tests/
├── examples/
└── docs/
```

### Step 3: Core Components Migration

#### 1. Memory System

**TypeScript:**
```typescript
class AQEMemory {
  async store(key: string, value: any, ttl?: number): Promise<void>
  async retrieve(key: string): Promise<any>
  async search(pattern: string): Promise<Record<string, any>>
}
```

**LionAGI:**
```python
class QEMemory:
    async def store(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        partition: str = "default"
    ):
        pass

    async def retrieve(self, key: str) -> Optional[Any]:
        pass

    async def search(self, pattern: str) -> Dict[str, Any]:
        pass
```

**Migration:**
- Same namespace structure (`aqe/*`)
- Additional `partition` parameter for organization
- Same TTL behavior
- Regex search remains unchanged

#### 2. Model Router

**TypeScript:**
```typescript
class ModelRouter {
  async route(task: string): Promise<[Model, number]>
  getRoutingStats(): RoutingStats
}
```

**LionAGI:**
```python
class ModelRouter:
    async def route(
        self,
        task_type: str,
        context: Dict[str, Any] = None
    ) -> Tuple[iModel, float, TaskComplexity]:
        pass

    async def get_routing_stats(self) -> Dict[str, Any]:
        pass
```

**Migration:**
- Returns complexity analysis in addition to model and cost
- Uses LionAGI `iModel` instead of custom model classes
- Enhanced statistics with distribution metrics

#### 3. Base Agent

**TypeScript:**
```typescript
abstract class BaseAgent {
  abstract execute(task: Task): Promise<Result>
  abstract getSystemPrompt(): string

  async preExecutionHook(task: Task): Promise<void>
  async postExecutionHook(task: Task, result: Result): Promise<void>
}
```

**LionAGI:**
```python
class BaseQEAgent(ABC):
    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    @abstractmethod
    async def execute(self, task: QETask) -> Dict[str, Any]:
        pass

    async def pre_execution_hook(self, task: QETask):
        pass

    async def post_execution_hook(
        self,
        task: QETask,
        result: Dict[str, Any]
    ):
        pass
```

**Migration:**
- Same hook lifecycle
- LionAGI `Branch` integration for conversations
- Built-in Pydantic validation for structured outputs
- Automatic memory integration

## Agent Migration

### Example: Test Generator Agent

#### TypeScript Implementation

```typescript
class TestGeneratorAgent extends BaseAgent {
  getSystemPrompt(): string {
    return "You are an expert test generation agent...";
  }

  async execute(task: Task): Promise<GeneratedTest> {
    const patterns = await this.memory.search('aqe/patterns/.*');

    const result = await this.llm.generate({
      prompt: this.buildPrompt(task),
      context: { patterns }
    });

    return this.parseResult(result);
  }
}
```

#### LionAGI Implementation

```python
from pydantic import BaseModel
from lionagi_qe.core.base_agent import BaseQEAgent

class GeneratedTest(BaseModel):
    test_name: str
    test_code: str
    framework: str
    # ... additional fields

class TestGeneratorAgent(BaseQEAgent):
    def get_system_prompt(self) -> str:
        return "You are an expert test generation agent..."

    async def execute(self, task: QETask) -> GeneratedTest:
        patterns = await self.get_learned_patterns()

        result = await self.operate(
            instruction=self.build_instruction(task),
            context={"patterns": patterns},
            response_format=GeneratedTest  # Pydantic validation!
        )

        return result
```

**Key Changes:**
1. ✅ Use Pydantic models for structured output
2. ✅ `operate()` method handles LLM interaction + validation
3. ✅ Built-in memory integration via `get_learned_patterns()`
4. ✅ Automatic type checking and validation

### Migrating All 19 Agents

#### Priority Order

**Phase 1: Core Testing** (Week 1)
1. TestGeneratorAgent ✓
2. TestExecutorAgent ✓
3. CoverageAnalyzerAgent
4. QualityGateAgent

**Phase 2: Coordination** (Week 2)
5. FleetCommanderAgent ✓
6. BaseTemplateGeneratorAgent

**Phase 3: Advanced Testing** (Week 3)
7. SecurityScannerAgent
8. PerformanceTesterAgent
9. FlakyTestHunterAgent
10. RegressionRiskAnalyzerAgent

**Phase 4: Specialized** (Week 4)
11-19. Remaining specialized agents

#### Migration Template

```python
# Template for migrating any agent

from pydantic import BaseModel
from lionagi_qe.core.base_agent import BaseQEAgent

class AgentResult(BaseModel):
    """Define structured output"""
    # ... fields

class NewAgent(BaseQEAgent):
    """Agent description from TypeScript version"""

    def get_system_prompt(self) -> str:
        """Copy system prompt from TypeScript"""
        return """..."""

    async def execute(self, task: QETask) -> AgentResult:
        """Migrate execute logic"""

        # 1. Get context
        context = task.context

        # 2. Retrieve learned patterns
        patterns = await self.get_learned_patterns()

        # 3. Execute with LionAGI
        result = await self.operate(
            instruction="...",
            context={...},
            response_format=AgentResult
        )

        # 4. Store results
        await self.store_result("key", result.model_dump())

        return result
```

## Memory Namespace Migration

### Namespace Structure (Unchanged)

```
aqe/
├── test-plan/          # Test planning
├── coverage/           # Coverage analysis
├── quality/            # Quality metrics
├── performance/        # Performance data
├── security/           # Security findings
├── patterns/           # Learned patterns
└── swarm/             # Coordination
    └── coordination
```

### Migration Code

```python
# TypeScript pattern
await memory.store('aqe/test-plan/generated', data, 3600);

# LionAGI equivalent
await self.memory.store(
    'aqe/test-plan/generated',
    data,
    ttl=3600,
    partition='test_planning'
)
```

## Workflow Patterns

### Sequential Pipeline

**TypeScript:**
```typescript
await orchestrator.executePipeline([
  'test-generator',
  'test-executor',
  'coverage-analyzer',
  'quality-gate'
], context);
```

**LionAGI:**
```python
await fleet.execute_pipeline(
    pipeline=[
        'test-generator',
        'test-executor',
        'coverage-analyzer',
        'quality-gate'
    ],
    context=context
)
```

### Parallel Execution

**TypeScript:**
```typescript
await orchestrator.executeParallel(
  ['test-gen', 'security', 'performance'],
  [task1, task2, task3]
);
```

**LionAGI:**
```python
await fleet.execute_parallel(
    agents=['test-gen', 'security', 'performance'],
    tasks=[task1, task2, task3]
)
```

### Fan-Out/Fan-In

**TypeScript:**
```typescript
await orchestrator.fanOutFanIn(
  'fleet-commander',
  ['agent1', 'agent2', 'agent3'],
  context
);
```

**LionAGI:**
```python
await fleet.execute_fan_out_fan_in(
    coordinator='fleet-commander',
    workers=['agent1', 'agent2', 'agent3'],
    context=context
)
```

## Testing

### Test Framework Migration

**TypeScript (Jest):**
```typescript
describe('TestGeneratorAgent', () => {
  it('should generate tests', async () => {
    const agent = new TestGeneratorAgent(...);
    const result = await agent.execute(task);
    expect(result.testCode).toBeDefined();
  });
});
```

**Python (pytest):**
```python
import pytest

@pytest.mark.asyncio
async def test_generate_tests():
    agent = TestGeneratorAgent(...)
    result = await agent.execute(task)
    assert result.test_code is not None
```

## Deployment

### TypeScript Deployment
```bash
npm run build
npm start
```

### LionAGI Deployment
```bash
# Development
python -m lionagi_qe

# Production with gunicorn (if using API)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app
```

## Checklist

### Pre-Migration
- [ ] Audit current TypeScript implementation
- [ ] Identify custom integrations and dependencies
- [ ] Document current workflows
- [ ] Set up Python development environment

### During Migration
- [ ] Migrate core components (Memory, Router, Orchestrator)
- [ ] Migrate agents by priority
- [ ] Migrate tests
- [ ] Migrate workflows and integration patterns
- [ ] Update documentation

### Post-Migration
- [ ] Verify functionality parity
- [ ] Run performance benchmarks
- [ ] Validate cost savings
- [ ] Train team on new system
- [ ] Deprecate TypeScript version

## Support

For migration assistance:
- 📖 [Architecture Guide](./LIONAGI_QE_FLEET_ARCHITECTURE.md)
- 💻 [Examples](../examples/)
- 🐛 [GitHub Issues](https://github.com/your-repo/issues)

## Next Steps

1. **Set up development environment**
2. **Run example workflows** (`examples/01_basic_usage.py`)
3. **Migrate one agent** as proof of concept
4. **Validate results** against TypeScript version
5. **Continue with remaining agents**
6. **Deploy to production**
