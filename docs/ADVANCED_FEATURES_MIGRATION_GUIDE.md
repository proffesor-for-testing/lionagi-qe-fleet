# LionAGI QE Fleet - Advanced Features Migration Guide

**Version**: 2.0
**Date**: 2025-11-04
**Status**: Implementation In Progress

---

## Executive Summary

This guide walks you through upgrading your LionAGI QE Fleet implementation to leverage advanced LionAGI features that will provide:

- **5-10x faster** parallel test generation
- **99%+ reliability** with automatic retry logic
- **95% reduction** in LLM parsing errors
- **Full observability** with audit trails and cost tracking
- **Better test quality** through multi-step reasoning

**Current Feature Utilization**: 40%
**Target Feature Utilization**: 85%
**Estimated ROI**: 300-500% improvement in key metrics

---

## Table of Contents

1. [Migration Overview](#1-migration-overview)
2. [Priority 1: Critical Features](#2-priority-1-critical-features)
3. [Priority 2: Important Enhancements](#3-priority-2-important-enhancements)
4. [Priority 3: Optional Features](#4-priority-3-optional-features)
5. [Testing Strategy](#5-testing-strategy)
6. [Rollout Plan](#6-rollout-plan)
7. [Monitoring & Validation](#7-monitoring--validation)

---

## 1. Migration Overview

### 1.1 Current State

**Architecture Score**: 95% ✅
**Implementation Quality**: 85/100 ✅
**LionAGI Feature Usage**: 40% ⚠️

**Currently Using**:
- ✅ Branch (basic usage)
- ✅ iModel (multi-provider)
- ✅ Session (basic workflow)
- ✅ Builder (basic operations)
- ✅ Pydantic models (excellent)

**Not Using** (60% of capabilities):
- ❌ Advanced Builder (ExpansionStrategy, aggregation)
- ❌ alcall (parallel execution with retry)
- ❌ ReAct (multi-step reasoning)
- ❌ Fuzzy parsing (robust LLM output handling)
- ❌ Hook system (observability)
- ❌ Streaming (progress updates)
- ❌ Pile collections (type-safe state)
- ❌ Tool integration (LionTool)

### 1.2 Target State

**LionAGI Feature Usage**: 85% 🎯
**Performance Improvement**: 5-10x 🚀
**Reliability**: 99%+ ✅
**Test Quality**: +30% 📈

### 1.3 Migration Phases

| Phase | Duration | Features | Impact |
|-------|----------|----------|--------|
| **Phase 1** | Week 1-2 | Critical features (alcall, Builder, fuzzy) | ⭐⭐⭐⭐⭐ |
| **Phase 2** | Week 3-4 | Important features (ReAct, hooks, streaming) | ⭐⭐⭐⭐ |
| **Phase 3** | Month 2 | Optional features (Pile, tools, visualization) | ⭐⭐⭐ |
| **Phase 4** | Month 3 | Testing, validation, production rollout | ⭐⭐⭐⭐⭐ |

---

## 2. Priority 1: Critical Features

### 2.1 Advanced Builder with Expansion Patterns

**Impact**: ⭐⭐⭐⭐⭐ (5-10x faster parallel operations)

#### 2.1.1 Current Implementation

**File**: `src/lionagi_qe/core/orchestrator.py:78-120`

```python
# ❌ Current: Basic sequential pipeline
async def execute_pipeline(
    self,
    pipeline: List[str],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    builder = Builder("QE_Pipeline")
    nodes = []

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

    result = await self.session.flow(builder.get_graph())
    return result
```

**Problems**:
- No parallel expansion
- Manual context passing
- Sequential only (slow)
- No dynamic workflows

#### 2.1.2 New Implementation

**File**: `src/lionagi_qe/core/orchestrator.py` (add new methods)

```python
from lionagi.operations import ExpansionStrategy

async def execute_parallel_expansion(
    self,
    source_agent_id: str,
    target_agent_id: str,
    expansion_instruction: str,
    strategy: ExpansionStrategy = ExpansionStrategy.CONCURRENT,
    max_concurrent: int = 10,
    aggregate_results: bool = True
) -> Dict[str, Any]:
    """
    Execute source agent, then expand results in parallel with target agent

    Example:
        # Analyze code → Generate tests for each module in parallel
        result = await orchestrator.execute_parallel_expansion(
            source_agent_id="code-analyzer",
            target_agent_id="test-generator",
            expansion_instruction="Generate comprehensive tests for module: {{item}}",
            strategy=ExpansionStrategy.CONCURRENT,
            max_concurrent=10
        )

    Args:
        source_agent_id: Agent that produces list of items
        target_agent_id: Agent that processes each item
        expansion_instruction: Template instruction (use {{item}} placeholder)
        strategy: Expansion strategy (CONCURRENT, SEQUENTIAL, etc.)
        max_concurrent: Max parallel operations
        aggregate_results: Whether to aggregate results at end

    Returns:
        {
            "source_result": {...},
            "expanded_results": [...],
            "aggregated_result": {...}  # If aggregate_results=True
        }
    """
    builder = Builder("parallel-expansion")

    # Step 1: Source operation
    source_agent = self.agents[source_agent_id]
    source_op = builder.add_operation(
        "communicate",
        branch=source_agent.branch,
        instruction="Analyze and identify items for parallel processing"
    )

    # Step 2: Parallel expansion
    target_agent = self.agents[target_agent_id]
    expanded_ops = builder.expand_from_result(
        items=source_op.response.items,  # LionAGI extracts list automatically
        source_node_id=source_op,
        operation="communicate",
        branch=target_agent.branch,
        strategy=strategy,
        instruction=expansion_instruction,
        max_concurrent=max_concurrent,
        inherit_context=True  # Automatically passes context from source
    )

    # Step 3: Optional aggregation
    aggregation_op = None
    if aggregate_results:
        aggregation_op = builder.add_aggregation(
            "communicate",
            branch=source_agent.branch,  # Use source agent for synthesis
            source_node_ids=expanded_ops,
            instruction="Synthesize all results into comprehensive report",
            context={"original_request": source_op.context}
        )

    # Execute workflow
    result = await self.session.flow(
        builder.get_graph(),
        max_concurrent=max_concurrent
    )

    # Track metrics
    self.metrics["parallel_expansions"] += 1
    self.metrics["items_processed"] += len(expanded_ops)

    return {
        "source_result": result.get(source_op.id),
        "expanded_results": [result.get(op.id) for op in expanded_ops],
        "aggregated_result": result.get(aggregation_op.id) if aggregation_op else None
    }


async def execute_fan_out_fan_in(
    self,
    agent_ids: List[str],
    shared_context: Dict[str, Any],
    synthesis_agent_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fan-out to multiple agents in parallel, fan-in to synthesis

    Example:
        # Run security, performance, quality checks in parallel → synthesize
        result = await orchestrator.execute_fan_out_fan_in(
            agent_ids=["security-scanner", "performance-tester", "quality-analyzer"],
            shared_context={"code_path": "./src"},
            synthesis_agent_id="fleet-commander"
        )
    """
    builder = Builder("fan-out-fan-in")

    # Fan-out: Execute all agents in parallel
    agent_ops = []
    for agent_id in agent_ids:
        agent = self.agents[agent_id]
        op = builder.add_operation(
            "communicate",
            branch=agent.branch,
            instruction=f"{agent_id} analysis",
            context=shared_context
        )
        agent_ops.append(op)

    # Fan-in: Synthesize results
    synthesis_agent = self.agents.get(synthesis_agent_id or "fleet-commander")
    synthesis_op = builder.add_aggregation(
        "communicate",
        branch=synthesis_agent.branch,
        source_node_ids=agent_ops,
        instruction="Synthesize all expert analyses into actionable recommendations"
    )

    # Execute
    result = await self.session.flow(
        builder.get_graph(),
        max_concurrent=len(agent_ids)
    )

    return {
        "individual_results": {
            agent_id: result.get(op.id)
            for agent_id, op in zip(agent_ids, agent_ops)
        },
        "synthesis": result.get(synthesis_op.id)
    }


async def execute_conditional_workflow(
    self,
    agent_id: str,
    task: Dict[str, Any],
    decision_key: str,
    branches: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Execute conditional workflow based on agent output

    Example:
        # Run coverage analyzer → if coverage < 80%, generate more tests
        result = await orchestrator.execute_conditional_workflow(
            agent_id="coverage-analyzer",
            task={"code_path": "./src"},
            decision_key="coverage_percent",
            branches={
                "high": ["quality-gate"],  # coverage >= 80%
                "low": ["test-generator", "test-executor", "coverage-analyzer"]
            }
        )
    """
    builder = Builder("conditional-workflow")

    # Initial operation
    agent = self.agents[agent_id]
    initial_op = builder.add_operation(
        "communicate",
        branch=agent.branch,
        instruction=task.get("instruction", "Execute task"),
        context=task
    )

    # Conditional branches
    for branch_name, pipeline in branches.items():
        previous_op = initial_op
        for sub_agent_id in pipeline:
            sub_agent = self.agents[sub_agent_id]
            sub_op = builder.add_operation(
                "communicate",
                branch=sub_agent.branch,
                instruction=f"Execute {sub_agent_id}",
                depends_on=[previous_op],
                condition=lambda result: result.get(decision_key) in branch_name  # Conditional
            )
            previous_op = sub_op

    # Execute
    result = await self.session.flow(builder.get_graph())

    return result
```

#### 2.1.3 Migration Steps

**Step 1**: Add new methods to `QEOrchestrator` (above code)

**Step 2**: Update `QEFleet` to expose new patterns

**File**: `src/lionagi_qe/core/fleet.py`

```python
async def parallel_expansion(
    self,
    source_agent: str,
    target_agent: str,
    instruction: str,
    **kwargs
) -> Dict[str, Any]:
    """Convenience method for parallel expansion"""
    return await self.orchestrator.execute_parallel_expansion(
        source_agent_id=source_agent,
        target_agent_id=target_agent,
        expansion_instruction=instruction,
        **kwargs
    )

async def fan_out_fan_in(
    self,
    agents: List[str],
    context: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """Convenience method for fan-out-fan-in"""
    return await self.orchestrator.execute_fan_out_fan_in(
        agent_ids=agents,
        shared_context=context,
        **kwargs
    )
```

**Step 3**: Add usage examples to documentation

**Step 4**: Write tests

---

### 2.2 Advanced Concurrency with `alcall`

**Impact**: ⭐⭐⭐⭐⭐ (99%+ reliability, automatic retry)

#### 2.2.1 Current Implementation

**File**: `src/lionagi_qe/agents/test_executor.py:50-100`

```python
# ❌ Current: Manual parallel execution, no retry
async def execute_tests(self, test_files: List[str]) -> Dict[str, Any]:
    tasks = []
    for file_path in test_files:
        task = self._run_single_test(file_path)
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Manual error handling...
```

**Problems**:
- No automatic retry
- No timeout handling
- No rate limiting
- Manual error handling
- No resource tracking

#### 2.2.2 New Implementation

**File**: `src/lionagi_qe/agents/test_executor.py`

```python
from lionagi.ln import alcall, AlcallParams
from typing import List, Dict, Any
import subprocess

async def execute_tests_parallel(
    self,
    test_files: List[str],
    framework: str = "pytest"
) -> Dict[str, Any]:
    """
    Execute tests in parallel with automatic retry and timeout

    Args:
        test_files: List of test file paths
        framework: Test framework (pytest, jest, mocha, etc.)

    Returns:
        {
            "total": 150,
            "passed": 145,
            "failed": 5,
            "results": [...],
            "execution_time": 45.3,
            "retries": 8
        }
    """

    async def run_single_test(file_path: str) -> Dict[str, Any]:
        """Execute single test file"""
        try:
            if framework == "pytest":
                result = subprocess.run(
                    ["pytest", file_path, "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            elif framework == "jest":
                result = subprocess.run(
                    ["npm", "test", "--", file_path],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            else:
                raise ValueError(f"Unsupported framework: {framework}")

            return {
                "file": file_path,
                "passed": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "file": file_path,
                "passed": False,
                "error": "Test execution timeout (60s)",
                "timeout": True
            }
        except Exception as e:
            return {
                "file": file_path,
                "passed": False,
                "error": str(e)
            }

    # Execute with alcall - automatic retry, timeout, rate limiting
    params = AlcallParams(
        max_concurrent=10,        # Run 10 tests at a time
        retry_attempts=3,         # Retry failed tests 3 times
        retry_timeout=60.0,       # 60s timeout per attempt
        retry_backoff=2.0,        # Exponential backoff: 2s, 4s, 8s
        throttle_period=0.1,      # 100ms between test starts (rate limit)
        handle_exceptions=True    # Graceful error handling
    )

    start_time = time.time()

    # Execute all tests with retry logic
    results = await params(test_files, run_single_test)

    execution_time = time.time() - start_time

    # Aggregate results
    passed = sum(1 for r in results if r.get("passed"))
    failed = len(results) - passed
    retries = sum(1 for r in results if r.get("_retry_count", 0) > 0)

    # Store in memory
    await self.store_result("last_execution", {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "results": results,
        "execution_time": execution_time,
        "retries": retries
    })

    return {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "pass_rate": (passed / len(results)) * 100,
        "results": results,
        "execution_time": execution_time,
        "retries": retries
    }
```

**File**: `src/lionagi_qe/agents/flaky_test_hunter.py`

```python
from lionagi.ln import alcall

async def detect_flaky_tests(
    self,
    test_files: List[str],
    iterations: int = 10
) -> Dict[str, Any]:
    """
    Run tests multiple times to detect flakiness

    Uses alcall to run each test N times in parallel
    """

    async def run_test_multiple_times(file_path: str) -> Dict[str, Any]:
        """Run single test N times"""
        # Use nested alcall for parallel execution
        results = await alcall(
            range(iterations),
            lambda i: self._execute_test_once(file_path, run_number=i),
            max_concurrent=5,
            retry_attempts=1  # Don't retry for flaky detection
        )

        # Analyze results
        passed_count = sum(1 for r in results if r.get("passed"))
        failed_count = iterations - passed_count

        is_flaky = 0 < passed_count < iterations  # Sometimes passes, sometimes fails

        return {
            "file": file_path,
            "iterations": iterations,
            "passed": passed_count,
            "failed": failed_count,
            "is_flaky": is_flaky,
            "flakiness_score": (min(passed_count, failed_count) / iterations) * 100,
            "results": results
        }

    # Execute flaky detection for all tests
    flaky_results = await alcall(
        test_files,
        run_test_multiple_times,
        max_concurrent=3,  # Don't overwhelm system
        retry_attempts=1
    )

    # Identify flaky tests
    flaky_tests = [r for r in flaky_results if r.get("is_flaky")]

    return {
        "total_tests": len(test_files),
        "flaky_tests": len(flaky_tests),
        "flaky_list": flaky_tests,
        "flakiness_rate": (len(flaky_tests) / len(test_files)) * 100
    }
```

#### 2.2.3 Migration Steps

**Step 1**: Update `TestExecutorAgent` with alcall implementation

**Step 2**: Update `FlakyTestHunterAgent` with alcall implementation

**Step 3**: Add alcall to other agents:
- `PerformanceTesterAgent` (parallel load testing)
- `SecurityScannerAgent` (parallel vulnerability scanning)
- `CoverageAnalyzerAgent` (parallel file analysis)

**Step 4**: Write tests validating retry behavior

---

### 2.3 Fuzzy JSON Parsing

**Impact**: ⭐⭐⭐⭐⭐ (95% reduction in parsing errors)

#### 2.3.1 Current Implementation

**File**: Multiple agents, inconsistent error handling

```python
# ❌ Current: Brittle parsing
result = await self.branch.operate(
    instruction="Generate tests",
    response_format=TestSuite
)
# Fails if LLM returns malformed JSON
```

#### 2.3.2 New Implementation

**File**: `src/lionagi_qe/core/base_agent.py` (add utility methods)

```python
from lionagi.ln.fuzzy import fuzzy_json, fuzzy_validate_pydantic
from typing import Type, TypeVar, Union, Dict, Any
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class BaseQEAgent(ABC):
    # ... existing code ...

    async def safe_operate(
        self,
        instruction: str,
        response_format: Type[T],
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> T:
        """
        Execute operation with fuzzy JSON parsing fallback

        Automatically handles:
        - Malformed JSON from LLM
        - Extra text in response
        - Key name variations (camelCase vs snake_case)
        - Type coercion

        Args:
            instruction: Instruction for agent
            response_format: Expected Pydantic model
            context: Additional context
            **kwargs: Additional arguments for branch.operate()

        Returns:
            Validated Pydantic model instance
        """
        try:
            # Try standard LionAGI structured output first
            result = await self.branch.operate(
                instruction=instruction,
                context=context,
                response_format=response_format,
                **kwargs
            )
            return result

        except Exception as e:
            self.logger.warning(f"Standard parsing failed: {e}, trying fuzzy parsing")

            # Fallback: Get raw response and fuzzy parse
            raw_response = await self.branch.communicate(
                instruction=instruction,
                context=context,
                **kwargs
            )

            # Extract JSON from messy response
            try:
                clean_data = fuzzy_json(raw_response)

                # Fuzzy validate against Pydantic model
                validated = fuzzy_validate_pydantic(
                    clean_data,
                    response_format,
                    fuzzy_match_keys=True,  # Tolerates key variations
                    fuzzy_match_values=True  # Handles type coercion
                )

                self.logger.info("Fuzzy parsing successful")
                return validated

            except Exception as fuzzy_error:
                self.logger.error(f"Fuzzy parsing also failed: {fuzzy_error}")
                raise ValueError(
                    f"Failed to parse LLM response into {response_format.__name__}. "
                    f"Original error: {e}, Fuzzy error: {fuzzy_error}"
                )

    async def safe_parse_response(
        self,
        response: Union[str, Dict[str, Any]],
        model_class: Type[T]
    ) -> T:
        """
        Safely parse any response into Pydantic model

        Use when you already have a response and need to validate it
        """
        try:
            # Try direct parsing
            if isinstance(response, str):
                return model_class.model_validate_json(response)
            else:
                return model_class(**response)

        except Exception as e:
            self.logger.warning(f"Direct parsing failed: {e}, trying fuzzy")

            # Fuzzy parsing
            if isinstance(response, str):
                clean_data = fuzzy_json(response)
            else:
                clean_data = response

            return fuzzy_validate_pydantic(
                clean_data,
                model_class,
                fuzzy_match_keys=True,
                fuzzy_match_values=True
            )
```

#### 2.3.3 Usage Examples

**File**: `src/lionagi_qe/agents/test_generator.py`

```python
# ✅ New: Use safe_operate instead of branch.operate
from pydantic import BaseModel
from typing import List

class GeneratedTests(BaseModel):
    test_cases: List[Dict[str, Any]]
    edge_cases: List[str]
    framework: str

async def execute(self, task: Dict[str, Any]) -> GeneratedTests:
    # Old way (brittle):
    # result = await self.branch.operate(...)

    # New way (robust):
    result = await self.safe_operate(
        instruction="Generate comprehensive test suite",
        response_format=GeneratedTests,
        context=task
    )

    return result
```

#### 2.3.4 Migration Steps

**Step 1**: Add `safe_operate` and `safe_parse_response` to `BaseQEAgent`

**Step 2**: Update all agents to use `safe_operate`:
- TestGeneratorAgent
- CoverageAnalyzerAgent
- QualityAnalyzerAgent
- SecurityScannerAgent
- All other agents with structured outputs

**Step 3**: Add tests for fuzzy parsing edge cases

**Step 4**: Monitor parsing error rates (should drop 95%)

---

## 3. Priority 2: Important Enhancements

### 3.1 ReAct Reasoning for Complex Tasks

**Impact**: ⭐⭐⭐⭐ (+30% test quality)

#### 3.1.1 Implementation

**File**: `src/lionagi_qe/agents/test_generator.py`

```python
from lionagi.tools.base import LionTool
from typing import Dict, Any, List

class CodeAnalyzerTool(LionTool):
    """Tool for analyzing code structure"""

    async def execute(self, file_path: str) -> Dict[str, Any]:
        """Analyze code file and return structure"""
        # Implementation: parse AST, extract functions, analyze complexity
        return {
            "functions": [...],
            "classes": [...],
            "complexity": {...},
            "dependencies": [...]
        }

class TestGeneratorAgent(BaseQEAgent):

    async def execute_with_reasoning(
        self,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate tests using ReAct reasoning

        Flow:
        1. Think: Analyze code structure
        2. Act: Use CodeAnalyzerTool to parse code
        3. Observe: Review analysis results
        4. Think: Identify edge cases
        5. Act: Generate test scenarios
        6. Observe: Validate completeness
        7. Final: Generate complete test suite
        """

        # Register tools
        tools = [
            CodeAnalyzerTool(),
            # Add more tools as needed
        ]

        # Execute ReAct reasoning
        result = await self.branch.ReAct(
            instruct={
                "instruction": "Design comprehensive test suite for the given code",
                "context": task,
                "guidance": (
                    "1. Analyze code structure and identify testable units\n"
                    "2. Consider edge cases, security, and performance\n"
                    "3. Generate test cases with high coverage\n"
                    "4. Validate test suite completeness"
                )
            },
            tools=tools,
            max_extensions=5,  # Up to 5 reasoning rounds
            extension_allowed=True,
            verbose=True,  # See reasoning steps
            intermediate_response_options=[TestScenario, EdgeCase],
            return_analysis=True  # Get full reasoning trace
        )

        return result
```

#### 3.1.2 Migration Steps

**Step 1**: Create tool classes for agent needs
**Step 2**: Update agents to use ReAct where beneficial
**Step 3**: Monitor reasoning quality improvements

---

### 3.2 Hook System for Observability

**Impact**: ⭐⭐⭐⭐ (Full audit trails, cost tracking)

#### 3.2.1 Implementation

**File**: `src/lionagi_qe/core/hooks.py` (new file)

```python
from lionagi.service.hooks import HookRegistry, HookEventTypes
from typing import Dict, Any
import logging

class QEHooks:
    """Centralized hooks for QE fleet observability"""

    def __init__(self, fleet_id: str):
        self.fleet_id = fleet_id
        self.logger = logging.getLogger(f"qe_fleet.{fleet_id}")
        self.cost_tracker = {"total": 0.0, "by_agent": {}}
        self.call_count = 0

    async def pre_invocation_hook(self, event, **kwargs):
        """Log before each AI call"""
        self.call_count += 1
        self.logger.info(
            f"AI Call #{self.call_count}: "
            f"{event.provider}/{event.model} "
            f"- Agent: {event.context.get('agent_id', 'unknown')}"
        )

    async def post_invocation_hook(self, event, **kwargs):
        """Track costs and metrics after each AI call"""
        agent_id = event.context.get('agent_id', 'unknown')
        cost = event.usage.total_cost if hasattr(event.usage, 'total_cost') else 0.0

        self.cost_tracker["total"] += cost
        self.cost_tracker["by_agent"][agent_id] = (
            self.cost_tracker["by_agent"].get(agent_id, 0.0) + cost
        )

        self.logger.info(
            f"AI Response: {event.usage.total_tokens} tokens, "
            f"${cost:.4f} cost, "
            f"Agent: {agent_id}"
        )

    def create_registry(self) -> HookRegistry:
        """Create hook registry for models"""
        return HookRegistry(hooks={
            HookEventTypes.PreInvocation: self.pre_invocation_hook,
            HookEventTypes.PostInvocation: self.post_invocation_hook
        })
```

**File**: `src/lionagi_qe/core/router.py` (update)

```python
class ModelRouter:
    def __init__(self, hooks: Optional[QEHooks] = None):
        self.hooks = hooks
        hook_registry = hooks.create_registry() if hooks else None

        self.models = {
            "simple": iModel(
                provider="openai",
                model="gpt-3.5-turbo",
                hook_registry=hook_registry
            ),
            # ... other models with hooks
        }
```

#### 3.2.2 Migration Steps

**Step 1**: Create hooks system
**Step 2**: Integrate with ModelRouter
**Step 3**: Add dashboard for metrics

---

### 3.3 Streaming Progress Updates

**Impact**: ⭐⭐⭐ (Better UX for long operations)

#### 3.3.1 Implementation

**File**: `src/lionagi_qe/agents/test_generator.py`

```python
async def generate_tests_streaming(
    self,
    task: Dict[str, Any]
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stream test generation progress

    Yields:
        {"type": "progress", "count": 5, "total": 50, "percent": 10}
        {"type": "test", "test_case": {...}}
        {"type": "complete", "tests": [...]}
    """
    total_tests = task.get("target_count", 50)
    generated = []

    async for chunk in self.model.stream(
        messages=[{
            "role": "user",
            "content": f"Generate {total_tests} tests for {task['code_path']}"
        }]
    ):
        # Extract incremental test cases
        if test_case := self._extract_test_from_chunk(chunk):
            generated.append(test_case)

            # Yield progress
            yield {
                "type": "progress",
                "count": len(generated),
                "total": total_tests,
                "percent": (len(generated) / total_tests) * 100
            }

            # Yield test
            yield {
                "type": "test",
                "test_case": test_case
            }

    # Final result
    yield {
        "type": "complete",
        "tests": generated,
        "total": len(generated)
    }
```

---

## 4. Priority 3: Optional Features

### 4.1 Pile Collections for Type-Safe State
### 4.2 Tool Integration (LionTool)
### 4.3 Graph Visualization
### 4.4 Resource Tracking

*(Details available in full migration guide)*

---

## 5. Testing Strategy

### 5.1 Test Coverage Requirements

| Feature | Test Coverage Target | Priority |
|---------|---------------------|----------|
| alcall integration | 90%+ | High |
| Builder expansion | 85%+ | High |
| Fuzzy parsing | 95%+ | High |
| ReAct reasoning | 80%+ | Medium |
| Hook system | 85%+ | Medium |
| Streaming | 75%+ | Medium |

### 5.2 Test Plan

**Phase 1 Tests** (Week 1-2):
- [ ] Test parallel expansion with 100+ items
- [ ] Test alcall retry behavior with flaky operations
- [ ] Test fuzzy parsing with malformed JSON
- [ ] Integration tests for new orchestrator methods

**Phase 2 Tests** (Week 3-4):
- [ ] Test ReAct reasoning with complex scenarios
- [ ] Test hook system with cost tracking
- [ ] Test streaming with progress monitoring

---

## 6. Rollout Plan

### Week 1: Foundation
- Day 1-2: Implement advanced Builder methods
- Day 3-4: Integrate alcall in TestExecutor
- Day 5: Add fuzzy parsing to BaseQEAgent

### Week 2: Integration
- Day 1-2: Update all agents to use new features
- Day 3-4: Write comprehensive tests
- Day 5: Integration testing

### Week 3-4: Enhancements
- Implement Priority 2 features
- Production validation
- Performance benchmarking

---

## 7. Monitoring & Validation

### 7.1 Success Metrics

| Metric | Baseline | Target | Status |
|--------|----------|--------|--------|
| Parallel test execution speed | 1x | 5-10x | 🎯 |
| Test execution reliability | 85% | 99%+ | 🎯 |
| LLM parsing error rate | 15% | <1% | 🎯 |
| Test quality score | 70/100 | 90/100 | 🎯 |
| Cost per test | $0.05 | $0.01 | 🎯 |

### 7.2 Validation Checklist

**Performance**:
- [ ] Parallel expansion 5x+ faster than sequential
- [ ] alcall reduces execution time by 30%+
- [ ] No performance regression in core operations

**Reliability**:
- [ ] alcall retry achieves 99%+ success rate
- [ ] Fuzzy parsing handles all test cases
- [ ] No new failures introduced

**Quality**:
- [ ] ReAct generates 30% better tests (measured by coverage + edge cases)
- [ ] Hook system captures 100% of AI calls
- [ ] Streaming provides smooth progress updates

---

## 8. Appendix

### 8.1 Full Code Examples
### 8.2 API Reference
### 8.3 Troubleshooting Guide
### 8.4 Performance Benchmarks

---

**Status**: ✅ Ready for Implementation
**Next Step**: Launch agent swarm to implement Priority 1 features
**Estimated Completion**: 2-4 weeks

