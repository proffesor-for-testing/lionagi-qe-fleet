# GitHub Issue Template for Ocean

Copy this to create a GitHub issue at `khive-ai/lionagi` repository.

---

**Title**: [qe-fleet] LionAGI v0 Pattern Alignment Review Request

---

## Context

We're refactoring **lionagi-qe-fleet** (v1.0.2) to align with LionAGI v0's 5-year evolution of multi-agent patterns. After studying your technical handoff, we've identified ~2,300 LOC of custom wrappers that duplicate LionAGI functionality.

**Project**: https://github.com/lionagi/lionagi-qe-fleet (public)
**Technical Handoff**: `/docs/research/technical_handoff.md`
**Improvement Plan**: `/docs/research/PHASE_3_IMPROVEMENT_PLAN.md` (59-page detailed plan)

---

## Current State

### What's Working Well ✅

The QE Fleet already uses LionAGI correctly in many places:

```python
# ✅ Session for workflow management
self.session = Session()

# ✅ Builder for graph-based workflows
builder = Builder("QE_Pipeline")
result = await self.session.flow(builder.get_graph())

# ✅ Branch for agent isolation
self.branch = Branch(
    system=self.get_system_prompt(),
    chat_model=model,
    name=agent_id
)

# ✅ alcall for parallel execution with retry
results = await alcall(items, process_func)

# ✅ Fuzzy parsing for robust LLM output
result = await agent.safe_operate(
    instruction=instruction,
    response_format=PydanticModel
)
```

**Assessment**: Core LionAGI integration is excellent!

---

## Issues Identified

### 1. Redundant Wrapper Layers (1,700 LOC)

**QEFleet** (500 LOC):
- Deprecated wrapper over QEOrchestrator
- Plan: Remove (already has deprecation warnings)

**QEMemory** (800 LOC):
- Custom in-memory dict, no persistence
- Plan: Replace with Session.context + Redis/PostgreSQL

**QETask** (400 LOC):
- Custom task abstraction
- Plan: Replace with dict contexts / Instruct pattern

### 2. QEOrchestrator (666 LOC) - Need Validation ⚠️

Provides valuable convenience methods but unsure if aligned:
- `execute_pipeline()` - Sequential execution
- `execute_parallel()` - Parallel with alcall
- `execute_fan_out_fan_in()` - Fan-out/fan-in pattern
- `execute_parallel_expansion()` - List expansion

**Question**: Is this orchestrator pattern aligned with LionAGI v0 best practices?

---

## Questions for Ocean

### Critical Question 1: QEOrchestrator Design Pattern

**Current Implementation**:
```python
class QEOrchestrator:
    """Orchestrate QE agent workflows"""

    def __init__(self, memory, router, enable_learning=False):
        self.memory = memory
        self.router = router
        self.session = Session()  # Single session instance

    async def execute_pipeline(
        self,
        pipeline: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute sequential pipeline using Builder"""
        builder = Builder(f"QE_Pipeline_{len(pipeline)}_agents")
        nodes = []

        for agent_id in pipeline:
            agent = self.get_agent(agent_id)
            node = builder.add_operation(
                "communicate",
                depends_on=nodes[-1:] if nodes else [],
                branch=agent.branch,
                instruction=context.get("instruction"),
                context=context
            )
            nodes.append(node)

        result = await self.session.flow(builder.get_graph())
        return result

    # Similar methods for parallel, fan-out/fan-in, conditional workflows
```

**Questions**:
1. **Is this wrapper pattern aligned with LionAGI v0 best practices?**
   - Or should users work directly with Session + Builder?

2. **Session lifecycle**: Is reusing a single Session instance correct?
   - Or should we create new Session per workflow execution?

3. **Convenience methods**: Are these workflow helpers valuable?
   - Or should we provide examples of direct Builder usage instead?

**Alternative Approach** (Direct Session usage):
```python
# No orchestrator, users work with Session directly
session = Session()
builder = Builder("QE_Pipeline")

# User builds workflow
n1 = builder.add_operation("step1", branch=agent1.branch)
n2 = builder.add_operation("step2", branch=agent2.branch, depends_on=[n1])

# Execute
result = await session.flow(builder.get_graph())
```

**Our Assessment**: The orchestrator provides convenience but adds 666 LOC. Worth it?

---

### Critical Question 2: Tool Registry Pattern for 18 Agents

**Current Pattern** (Class-based agents):
```python
class TestGeneratorAgent(BaseQEAgent):
    """Generate comprehensive test suites"""

    def __init__(self, agent_id, model, memory):
        super().__init__(agent_id, model, memory)
        self.metrics = {"tasks_completed": 0, "total_cost": 0.0}
        self.learned_patterns = []

    def get_system_prompt(self) -> str:
        return "You are an expert test generation agent..."

    async def execute(self, task: QETask) -> GeneratedTest:
        # 200+ LOC implementation
        # Uses self.metrics, self.learned_patterns
        result = await self.safe_operate(
            instruction=f"Generate {task.framework} tests",
            context=task.context,
            response_format=GeneratedTest
        )
        return result
```

**LionAGI v0 Tool Pattern** (from technical handoff):
```python
@Tool.register(name="test-generator")
async def generate_tests(code: str, framework: str = "pytest") -> GeneratedTest:
    """Generate comprehensive test suite"""
    # Stateless function
    return result

# Session automatically discovers
session.register_tool(generate_tests)
```

**Questions**:
1. **Should we convert 18 agents from classes to @Tool.register functions?**

2. **How to handle agent state** (metrics, learned patterns, Q-learning)?
   - Classes provide natural state management
   - Tools seem stateless by design

3. **Is this hybrid approach acceptable?**
   ```python
   class TestGeneratorAgent:
       def __init__(self):
           self.metrics = {}
           self.learned_patterns = []

       @Tool.register(name="generate-tests")
       async def generate(self, code: str, framework: str) -> GeneratedTest:
           """Tool method with access to instance state"""
           # Can access self.metrics, self.learned_patterns
           return result
   ```

**Tradeoffs**:
- **Full Tool Migration**: Aligns with v0, but lose state management
- **Keep Classes**: Easier state handling, but may not align with v0
- **Hybrid**: Best of both, but need to verify it's a valid pattern

**Our Preference**: Hybrid approach, but need your guidance on whether it aligns with LionAGI v0.

---

### Critical Question 3: Session.context vs Custom Memory

**Current** (Custom QEMemory):
```python
class QEMemory:
    """In-memory storage (not persistent)"""

    def __init__(self):
        self._storage: Dict[str, Any] = {}  # Lost on restart

    async def store(self, key, value, ttl=None, partition=None):
        self._storage[key] = value

    async def retrieve(self, key):
        return self._storage.get(key)
```

**Proposed Options**:

**Option A: Session.context only** (in-memory)
```python
session.context.set("aqe/coverage/results", data)
results = session.context.get("aqe/coverage/results")
```

**Option B: Session.context + Redis backend**
```python
# Session.context for short-lived workflow state
session.context.set("aqe/results", data)

# Redis for persistence across restarts
await redis_backend.store("aqe/results", data, ttl=3600)
```

**Option C: Abstraction layer** (current, but simplified)
```python
# Unified interface, swappable backends
await memory.store("aqe/results", data)

# Backend implementations:
# - InMemory (Session.context wrapper)
# - Redis
# - PostgreSQL
```

**Questions**:
1. **Does Session.context persist across Session instances?**
   - Or is it scoped to a single Session object?

2. **What's the recommended pattern for persistent memory in LionAGI v0?**
   - Direct Redis/PostgreSQL usage?
   - Some abstraction layer?
   - Session-level persistence?

3. **Should we use Session.context only for short-lived workflow state?**
   - And external storage (Redis/PostgreSQL) for long-term data?

**Our Assessment**: Option B (Session.context + Redis) seems cleanest, but need confirmation.

---

### Critical Question 4: Branch Lifecycle Management

**Current Pattern** (Branch per agent instance):
```python
class BaseQEAgent:
    def __init__(self, agent_id, model, memory):
        self.agent_id = agent_id
        self.model = model

        # Create branch once in __init__
        self.branch = Branch(
            system=self.get_system_prompt(),
            chat_model=model,
            name=agent_id
        )

    async def execute(self, task):
        # Reuse same branch for all executions
        result = await self.branch.communicate(
            instruction=task.instruction,
            context=task.context
        )
        return result
```

**Alternative Patterns**:

**Pattern A: Branch per agent instance** (current)
- Created once in agent __init__
- Reused across thousands of task executions
- Branch history accumulates (could be 10k+ messages)

**Pattern B: Branch per execution**
```python
async def execute(self, task):
    # Create fresh branch for each execution
    branch = Branch(
        system=self.get_system_prompt(),
        chat_model=self.model
    )
    result = await branch.communicate(...)
    return result
```

**Pattern C: Session manages branches**
```python
# Orchestrator creates branches explicitly
session = Session()
branch1 = session.new_branch("test-generator")
branch2 = session.new_branch("coverage-analyzer")

# Pass to agents
await agent1.execute_on_branch(branch1, task)
await agent2.execute_on_branch(branch2, task)
```

**Questions**:
1. **Which pattern is recommended in LionAGI v0?**

2. **Should branch history accumulate or be isolated per execution?**
   - For learning agents, history might be valuable
   - For stateless operations, fresh branches seem better

3. **How to handle high-throughput agents** (thousands of executions)?
   - Does accumulated branch history affect performance?
   - Memory management concerns?

**Our Assessment**: Pattern A works but unclear if it's optimal for production scale.

---

### Critical Question 5: Workflow Coordination for 18+ Agents

**Example Workflow** (Complex fan-out/fan-in):
```
                Requirements Validator (1 agent)
                            ↓
            Test Generator (spawns 10 parallel)
                            ↓
        ┌──────┬──────┬──────┬──────┬──────┐
        │Test 1│Test 2│Test 3│ ...  │Test10│
        └──────┴──────┴──────┴──────┴──────┘
        ┌──────┬──────┬──────┬──────┬──────┐
        │ Exec │ Exec │ Exec │ ...  │ Exec │
        └──────┴──────┴──────┴──────┴──────┘
                            ↓
            Coverage Analyzer (aggregates 10)
                            ↓
                    Quality Gate (pass/fail)
```

**Current Implementation**:
```python
async def execute_parallel_expansion(
    self,
    source_agent_id: str,
    target_agent_id: str,
    expansion_instruction: str,
    strategy: ExpansionStrategy = ExpansionStrategy.CONCURRENT,
    max_concurrent: int = 10
) -> Dict[str, Any]:
    """Execute source agent, then expand results in parallel"""

    builder = Builder("parallel-expansion")

    # Source operation
    source_agent = self.get_agent(source_agent_id)
    source_op = builder.add_operation(
        "communicate",
        branch=source_agent.branch,
        instruction="Analyze and identify items for parallel processing"
    )

    # Parallel expansion
    target_agent = self.get_agent(target_agent_id)
    expanded_ops = builder.expand_from_result(
        items=source_op.response.items,
        source_node_id=source_op,
        operation="communicate",
        branch=target_agent.branch,
        strategy=strategy,
        instruction=expansion_instruction,
        max_concurrent=max_concurrent
    )

    # Aggregation
    aggregation_op = builder.add_aggregation(
        "communicate",
        branch=source_agent.branch,
        source_node_ids=expanded_ops,
        instruction="Synthesize all results"
    )

    # Execute workflow
    result = await self.session.flow(
        builder.get_graph(),
        max_concurrent=max_concurrent
    )

    return {
        "source_result": result.get(source_op.id),
        "expanded_results": [result.get(op.id) for op in expanded_ops],
        "aggregated_result": result.get(aggregation_op.id)
    }
```

**Questions**:
1. **Is this Builder usage pattern correct for 18+ agent coordination?**

2. **How to handle dynamic agent spawning** (based on runtime decisions)?
   - E.g., spawn N agents where N is determined by first agent

3. **Best practice for result aggregation from 10+ parallel agents?**

4. **Memory/resource management for high agent counts** (50-100 agents)?

**Our Assessment**: Current pattern works but need validation for production scale (100+ agents).

---

## Additional Context

### Current Architecture
```
src/lionagi_qe/
├── core/
│   ├── orchestrator.py      666 LOC  (validate)
│   ├── base_agent.py      1,016 LOC  (excellent, keep)
│   ├── fleet.py             500 LOC  (remove - deprecated)
│   ├── memory.py            800 LOC  (remove - replace with Session.context)
│   ├── task.py              400 LOC  (remove - use dicts)
│   ├── router.py            300 LOC  (keep - multi-model routing)
│   └── hooks.py             200 LOC  (keep - observability)
│
├── agents/                4,500 LOC  (18 specialized agents)
│   ├── test_generator.py
│   ├── coverage_analyzer.py
│   ├── quality_gate.py
│   └── ... (15 more agents)
│
└── Total: ~8,882 LOC
```

### Proposed Changes
- **Remove**: QEFleet (500), QEMemory (800), QETask (400) = 1,700 LOC
- **Simplify**: QEOrchestrator (666 → 400) = 266 LOC
- **Add**: Redis backend (250), PostgreSQL backend (250) = 500 LOC
- **Net Reduction**: ~1,500 LOC (17%)

### Implementation Plan
- **Week 1**: Remove wrappers, validate orchestrator
- **Week 2**: Add persistence backends, research tool registry
- **Week 3**: Update documentation, pattern validation tests

**Timeline**: 14 days (2 weeks)

---

## Deliverables After Ocean Review

Based on your answers, we'll:
1. Finalize refactoring approach
2. Implement in 3-phase rollout:
   - v1.1.0: Deprecations + new features (backward compatible)
   - v1.2.0: New patterns as defaults
   - v2.0.0: Remove deprecated code (6-12 months later)
3. Document LionAGI v0 best practices for QE Fleet
4. Share learnings with community

---

## Request

**Could you review these 5 critical questions and provide guidance on LionAGI v0 best practices?**

**Available for Discussion**:
- Async chat (this issue)
- Video call if helpful (30-60 minutes)
- We can share screen to show current implementation

**Documentation to Review** (if helpful):
- Full 59-page improvement plan: `docs/research/PHASE_3_IMPROVEMENT_PLAN.md`
- Technical handoff: `docs/research/technical_handoff.md`
- Current implementation: https://github.com/lionagi/lionagi-qe-fleet

---

## Thank You!

Your technical handoff was incredibly valuable - it helped us understand that our LionAGI integration is fundamentally sound, just with too many wrapper layers.

Looking forward to aligning fully with LionAGI v0 patterns!

**-- LionAGI QE Fleet Team**

---

**Labels**: `question`, `enhancement`, `qe-fleet`, `architecture`
**Assignees**: @ohdearquant (Ocean)
**Priority**: Medium (not urgent, but would love guidance before proceeding)
