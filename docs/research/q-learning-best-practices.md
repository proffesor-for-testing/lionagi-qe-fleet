# Q-Learning Best Practices for Multi-Agent QE Systems

**Research Report**
**Date**: 2025-11-05
**Project**: LionAGI QE Fleet
**Scope**: Reinforcement learning implementation for 18 specialized QE agents

---

## Executive Summary

This report provides research-backed recommendations for implementing Q-Learning across the LionAGI QE Fleet's 18 specialized agents. Based on analysis of recent academic research (2024-2025), production RL systems, and the existing codebase architecture, we recommend:

1. **Hybrid Q-Table Strategy**: Per-agent Q-tables with hierarchical aggregation
2. **Specialized State Spaces**: Task-specific state representations per agent type
3. **PostgreSQL Schema**: Optimized for concurrent updates with MVCC
4. **Production Monitoring**: Real-time convergence tracking with A/B testing capabilities
5. **Team-Wide Learning**: Centralized aggregation with conflict resolution

---

## 1. State/Action/Reward Design for QE Agents

### 1.1 Research Foundation

Recent research on RL for software testing (2024-2025) shows that state-action space design is critical for learning effectiveness. Key findings:

- **Testing-Specific States**: DQN (Deep Q-Networks) outperformed traditional Q-learning in 2/3 test scenarios when properly modeling continuous state space
- **Reward Augmentation**: Sparse natural rewards in testing require augmentation; RL-based testing on RedisRaft, Etcd, and RSL significantly outperformed baselines when using augmented rewards
- **Reinforcement Learning from Static Quality Metrics (RLSQM)**: Using static analysis-based quality metrics as reward signals improved unit test quality

### 1.2 State Space Design by Agent Type

Based on OpenAI Gym best practices and QE domain analysis:

#### Core Testing Agents (6 agents)

**Test Generator Agent**
```python
class TestGeneratorState(BaseModel):
    # Code complexity metrics
    cyclomatic_complexity: int  # 1-100
    lines_of_code: int          # 0-10000
    num_functions: int          # 0-100
    num_branches: int           # 0-200

    # Coverage context
    current_coverage: float     # 0-100%
    target_coverage: float      # 0-100%
    coverage_gap: float         # target - current

    # Pattern context
    framework: str              # pytest, jest, mocha, etc.
    test_type: str             # unit, integration, e2e
    language: str              # python, javascript, etc.

    # Historical performance
    previous_attempts: int      # 0-10
    avg_success_rate: float    # 0-1.0

    def to_discrete_state(self) -> tuple:
        """Convert to discrete state for Q-table lookup"""
        return (
            min(self.cyclomatic_complexity // 10, 10),  # Bins: 0-10
            min(self.lines_of_code // 100, 100),        # Bins: 0-100
            min(self.coverage_gap // 10, 10),            # Bins: 0-10
            self.framework,
            self.test_type
        )
```

**Test Executor Agent**
```python
class TestExecutorState(BaseModel):
    # Test suite characteristics
    num_tests: int              # 0-10000
    total_duration_estimate: float  # 0-3600 seconds
    test_complexity: str        # simple, moderate, complex

    # Execution context
    parallel_workers: int       # 1-16
    available_memory_mb: int    # 0-16384
    ci_environment: bool        # True/False

    # Historical performance
    avg_execution_time: float   # seconds
    flaky_test_rate: float     # 0-1.0
    previous_failures: int      # 0-100

    def to_discrete_state(self) -> tuple:
        return (
            min(self.num_tests // 100, 100),
            self.test_complexity,
            min(self.parallel_workers, 16),
            self.ci_environment
        )
```

**Coverage Analyzer Agent**
```python
class CoverageAnalyzerState(BaseModel):
    # Coverage metrics
    line_coverage: float        # 0-100%
    branch_coverage: float      # 0-100%
    function_coverage: float    # 0-100%

    # Gap analysis
    uncovered_lines: int        # 0-10000
    uncovered_branches: int     # 0-1000
    critical_paths_uncovered: int  # 0-100

    # Code characteristics
    total_lines: int           # 0-100000
    code_complexity: str       # simple, moderate, complex

    # Historical context
    coverage_trend: str        # improving, stable, declining

    def to_discrete_state(self) -> tuple:
        return (
            int(self.line_coverage // 10),      # Bins: 0-10
            int(self.branch_coverage // 10),    # Bins: 0-10
            min(self.critical_paths_uncovered // 5, 20),  # Bins: 0-20
            self.code_complexity
        )
```

**Quality Gate Agent**
```python
class QualityGateState(BaseModel):
    # Quality metrics
    test_pass_rate: float       # 0-100%
    coverage_percentage: float  # 0-100%
    code_quality_score: float   # 0-100
    security_score: float       # 0-100

    # Thresholds
    min_coverage_threshold: float
    min_quality_threshold: float

    # Risk assessment
    blocker_issues: int         # 0-100
    critical_issues: int        # 0-500
    major_issues: int          # 0-2000

    # Build context
    is_release_build: bool
    build_environment: str      # dev, staging, prod

    def to_discrete_state(self) -> tuple:
        return (
            int(self.test_pass_rate // 10),
            int(self.coverage_percentage // 10),
            int(self.code_quality_score // 10),
            self.blocker_issues > 0,
            self.is_release_build
        )
```

#### Performance & Security Agents (2 agents)

**Performance Tester Agent**
```python
class PerformanceTesterState(BaseModel):
    # Load characteristics
    target_rps: int             # 0-100000 requests/sec
    duration_seconds: int       # 0-3600
    concurrent_users: int       # 0-100000

    # System metrics
    cpu_threshold: float        # 0-100%
    memory_threshold: float     # 0-100%
    latency_p95_ms: float      # 0-10000

    # Test type
    test_type: str             # load, stress, spike, soak

    # Historical performance
    baseline_rps: int
    baseline_latency_ms: float

    def to_discrete_state(self) -> tuple:
        return (
            min(self.target_rps // 1000, 100),
            min(self.concurrent_users // 100, 1000),
            self.test_type,
            int(self.latency_p95_ms // 100)
        )
```

**Security Scanner Agent**
```python
class SecurityScannerState(BaseModel):
    # Scan scope
    scan_type: str              # SAST, DAST, SCA, secrets
    num_files: int             # 0-100000
    codebase_size_mb: int      # 0-10000

    # Vulnerability context
    known_vulnerabilities: int  # 0-10000
    critical_vulns: int        # 0-100
    high_vulns: int            # 0-500

    # Compliance requirements
    compliance_standard: str    # OWASP, PCI-DSS, SOC2, etc.

    # Historical findings
    false_positive_rate: float  # 0-1.0
    avg_scan_time: float       # seconds

    def to_discrete_state(self) -> tuple:
        return (
            self.scan_type,
            min(self.num_files // 1000, 100),
            self.critical_vulns > 0,
            self.compliance_standard
        )
```

#### Advanced Testing Agents (4 agents)

**Flaky Test Hunter Agent**
```python
class FlakyTestHunterState(BaseModel):
    # Test characteristics
    test_failure_rate: float    # 0-1.0
    failure_pattern: str        # intermittent, environmental, timing
    num_executions: int         # 0-1000

    # Timing metrics
    execution_variance_ms: float  # 0-10000
    avg_execution_time_ms: float  # 0-60000

    # Environmental factors
    depends_on_network: bool
    depends_on_external_service: bool
    has_timing_dependency: bool

    # Statistical significance
    confidence_level: float     # 0-1.0

    def to_discrete_state(self) -> tuple:
        return (
            int(self.test_failure_rate * 10),  # Bins: 0-10
            self.failure_pattern,
            self.depends_on_network or self.depends_on_external_service,
            int(self.confidence_level * 10)
        )
```

### 1.3 Action Space Design

#### Core Testing Agents

**Test Generator Actions**
```python
class TestGeneratorAction(str, Enum):
    # Pattern selection
    USE_PROPERTY_BASED = "use_property_based"      # Use hypothesis/fast-check
    USE_EXAMPLE_BASED = "use_example_based"        # Traditional example tests
    USE_MUTATION_TESTING = "use_mutation_testing"  # Generate mutation tests
    USE_FUZZING = "use_fuzzing"                    # Fuzzing-based tests

    # Coverage strategy
    PRIORITIZE_BRANCHES = "prioritize_branches"    # Focus on branch coverage
    PRIORITIZE_LINES = "prioritize_lines"          # Focus on line coverage
    PRIORITIZE_EDGE_CASES = "prioritize_edge_cases"  # Focus on edge cases

    # Test complexity
    GENERATE_SIMPLE = "generate_simple"            # Simple unit tests
    GENERATE_COMPREHENSIVE = "generate_comprehensive"  # Full test suite
    GENERATE_INTEGRATION = "generate_integration"  # Integration tests

    # Learning actions
    REUSE_PATTERN = "reuse_pattern"                # Reuse learned pattern
    CREATE_NEW_PATTERN = "create_new_pattern"      # Create new pattern
```

**Test Executor Actions**
```python
class TestExecutorAction(str, Enum):
    # Parallelization strategy
    EXECUTE_SEQUENTIAL = "execute_sequential"      # Run tests sequentially
    EXECUTE_PARALLEL_2 = "execute_parallel_2"      # 2 workers
    EXECUTE_PARALLEL_4 = "execute_parallel_4"      # 4 workers
    EXECUTE_PARALLEL_8 = "execute_parallel_8"      # 8 workers
    EXECUTE_PARALLEL_16 = "execute_parallel_16"    # 16 workers

    # Test selection
    RUN_ALL_TESTS = "run_all_tests"               # Run entire suite
    RUN_CHANGED_ONLY = "run_changed_only"         # Only changed files
    RUN_FAILED_FIRST = "run_failed_first"         # Failed tests first
    RUN_FAST_FIRST = "run_fast_first"             # Fast tests first

    # Retry strategy
    NO_RETRY = "no_retry"                          # No retries
    RETRY_FAILED_1X = "retry_failed_1x"           # Retry failed once
    RETRY_FAILED_3X = "retry_failed_3x"           # Retry failed 3x
```

**Coverage Analyzer Actions**
```python
class CoverageAnalyzerAction(str, Enum):
    # Analysis depth
    QUICK_SCAN = "quick_scan"                      # Fast coverage check
    DETAILED_ANALYSIS = "detailed_analysis"        # Deep analysis
    GAP_PRIORITIZATION = "gap_prioritization"      # Prioritize gaps

    # Algorithm selection
    USE_LINEAR_SCAN = "use_linear_scan"            # O(n) analysis
    USE_BINARY_SEARCH = "use_binary_search"        # O(log n) analysis
    USE_GRAPH_ALGORITHM = "use_graph_algorithm"    # Graph-based analysis

    # Reporting
    REPORT_SUMMARY = "report_summary"              # High-level summary
    REPORT_DETAILED = "report_detailed"            # Detailed gaps
    REPORT_ACTIONABLE = "report_actionable"        # Action items
```

### 1.4 Reward Function Design

Based on research showing reward augmentation is critical for testing systems:

#### Multi-Objective Reward Function

```python
class QERewardCalculator:
    """Calculate rewards for QE agent actions"""

    def __init__(self):
        # Weights for different objectives
        self.weights = {
            "coverage_gain": 0.30,
            "bugs_found": 0.25,
            "execution_speed": 0.15,
            "cost_efficiency": 0.10,
            "quality_improvement": 0.10,
            "pattern_reusability": 0.10
        }

    def calculate_reward(
        self,
        state_before: Dict,
        action: str,
        state_after: Dict,
        metadata: Dict
    ) -> float:
        """Calculate composite reward"""

        # 1. Coverage gain reward (0-100 points)
        coverage_before = state_before.get("coverage_percentage", 0)
        coverage_after = state_after.get("coverage_percentage", 0)
        coverage_gain = coverage_after - coverage_before
        coverage_reward = coverage_gain * 10  # 1% gain = 10 points

        # 2. Bugs found reward (0-100 points)
        bugs_found = metadata.get("bugs_found", 0)
        critical_bugs = metadata.get("critical_bugs", 0)
        bug_reward = bugs_found * 5 + critical_bugs * 20

        # 3. Execution speed reward (-50 to +50 points)
        expected_time = metadata.get("expected_time_seconds", 60)
        actual_time = metadata.get("actual_time_seconds", 60)
        time_ratio = expected_time / max(actual_time, 1)
        speed_reward = (time_ratio - 1) * 50  # Faster = positive, slower = negative

        # 4. Cost efficiency reward (0-50 points)
        estimated_cost = metadata.get("estimated_cost", 0.01)
        actual_cost = metadata.get("actual_cost", 0.01)
        cost_ratio = estimated_cost / max(actual_cost, 0.0001)
        cost_reward = (cost_ratio - 1) * 50

        # 5. Quality improvement reward (0-50 points)
        quality_before = state_before.get("quality_score", 50)
        quality_after = state_after.get("quality_score", 50)
        quality_reward = (quality_after - quality_before) * 2

        # 6. Pattern reusability reward (0-30 points)
        pattern_reused = metadata.get("pattern_reused", False)
        pattern_success = metadata.get("pattern_success", False)
        reusability_reward = 0
        if pattern_reused and pattern_success:
            reusability_reward = 30
        elif pattern_reused and not pattern_success:
            reusability_reward = -10

        # Weighted sum
        total_reward = (
            self.weights["coverage_gain"] * coverage_reward +
            self.weights["bugs_found"] * bug_reward +
            self.weights["execution_speed"] * speed_reward +
            self.weights["cost_efficiency"] * cost_reward +
            self.weights["quality_improvement"] * quality_reward +
            self.weights["pattern_reusability"] * reusability_reward
        )

        # Penalty for failures
        if metadata.get("task_failed", False):
            total_reward -= 50

        # Bonus for exceeding expectations
        if coverage_after >= 90:
            total_reward += 20

        return total_reward
```

#### Agent-Specific Reward Functions

**Test Generator Reward**
```python
def test_generator_reward(state_before, action, state_after, metadata) -> float:
    base_reward = QERewardCalculator().calculate_reward(
        state_before, action, state_after, metadata
    )

    # Additional test generator specific rewards
    edge_cases_covered = metadata.get("edge_cases_covered", 0)
    tests_generated = metadata.get("tests_generated", 0)

    # Reward edge case coverage
    edge_case_bonus = edge_cases_covered * 5

    # Reward efficient test generation (not too many, not too few)
    optimal_test_count = metadata.get("optimal_test_count", 10)
    efficiency_penalty = abs(tests_generated - optimal_test_count) * -2

    return base_reward + edge_case_bonus + efficiency_penalty
```

**Flaky Test Hunter Reward**
```python
def flaky_test_hunter_reward(state_before, action, state_after, metadata) -> float:
    # Reward for correctly identifying flaky tests
    true_positives = metadata.get("true_positives", 0)  # Correctly identified flaky
    false_positives = metadata.get("false_positives", 0)  # Incorrectly flagged
    true_negatives = metadata.get("true_negatives", 0)  # Correctly ignored stable
    false_negatives = metadata.get("false_negatives", 0)  # Missed flaky tests

    # F1-score based reward (0-100 points)
    precision = true_positives / max(true_positives + false_positives, 1)
    recall = true_positives / max(true_positives + false_negatives, 1)
    f1_score = 2 * (precision * recall) / max(precision + recall, 0.01)

    # Reward correct identification
    reward = f1_score * 100

    # Penalty for missed flaky tests (high cost)
    reward -= false_negatives * 20

    # Small penalty for false positives (lower cost)
    reward -= false_positives * 5

    return reward
```

---

## 2. Multi-Agent Q-Learning Strategy

### 2.1 Research Findings

Recent research (2024-2025) on multi-agent Q-learning shows:

**Shared vs Separate Q-Tables:**
- When agents are homogeneous and have equal experience, shared Q-tables provide minimal benefit
- When agents have different experience levels, Q-value sharing improves performance
- Conflicts in shared Q-tables can be resolved via random retention or weighted averaging
- Joint Q-tables outperform separate tables in convergence speed for cooperative tasks

**Hierarchical Aggregation:**
- QA-learning aggregates worker Q-tables into tutor agent repositories, then into consultant Q-tables
- This hierarchical approach improves coordination in multi-level agent systems

**Experience Sharing:**
- Selective experience sharing (only most relevant experiences) improves learning
- Parallel Hindsight Experience Replay (PHER) increases data utilization efficiency

### 2.2 Recommended Strategy: Hybrid Hierarchical Q-Tables

For the LionAGI QE Fleet with 18 heterogeneous agents, we recommend:

```
┌─────────────────────────────────────────────────┐
│         Fleet Commander Q-Table                  │
│  (Aggregated high-level coordination policies)  │
└─────────────────────────────────────────────────┘
                     ▲
                     │ Aggregates
        ┌────────────┼────────────┬────────────┐
        ▼            ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ Core    │  │ Perf &  │  │Advanced │  │Special- │
   │ Testing │  │ Security│  │ Testing │  │ ized    │
   │Q-Table  │  │Q-Table  │  │Q-Table  │  │Q-Table  │
   └─────────┘  └─────────┘  └─────────┘  └─────────┘
        ▲            ▲            ▲            ▲
        │            │            │            │
   Aggregates   Aggregates   Aggregates   Aggregates
        │            │            │            │
   ┌────┴───┬───┐   │       ┌────┴───┬───┐   │
   ▼        ▼   ▼   ▼       ▼        ▼   ▼   ▼
 Agent   Agent  ... ...   Agent   Agent  ... ...
 Q-Table Q-Table          Q-Table Q-Table
```

**Why Hybrid?**
1. **Agent Heterogeneity**: 18 different agent types have different state/action spaces
2. **Transfer Learning**: Similar agents (e.g., test-generator and test-data-architect) can share patterns
3. **Hierarchical Coordination**: Fleet commander benefits from aggregated knowledge
4. **Scalability**: Adding new agents doesn't require retraining all agents

### 2.3 Implementation Architecture

```python
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
import numpy as np
from enum import Enum

class QTableScope(str, Enum):
    INDIVIDUAL = "individual"      # Agent's own Q-table
    CATEGORY = "category"          # Category Q-table (e.g., core-testing)
    FLEET = "fleet"               # Fleet commander Q-table

@dataclass
class QTableConfig:
    """Configuration for Q-table"""
    agent_id: str
    scope: QTableScope
    state_dimensions: List[str]
    action_space: List[str]
    learning_rate: float = 0.1
    discount_factor: float = 0.95

class HierarchicalQTableManager:
    """Manage hierarchical Q-tables for multi-agent learning"""

    def __init__(self, postgres_url: str):
        self.postgres_url = postgres_url
        self.individual_tables: Dict[str, QTable] = {}
        self.category_tables: Dict[str, QTable] = {}
        self.fleet_table: Optional[QTable] = None

        # Agent category mapping
        self.agent_categories = {
            "test-generator": "core-testing",
            "test-executor": "core-testing",
            "coverage-analyzer": "core-testing",
            "quality-gate": "core-testing",
            "quality-analyzer": "core-testing",
            "code-complexity": "core-testing",
            "performance-tester": "performance-security",
            "security-scanner": "performance-security",
            "regression-risk-analyzer": "advanced-testing",
            "test-data-architect": "advanced-testing",
            "api-contract-validator": "advanced-testing",
            "flaky-test-hunter": "advanced-testing",
            "deployment-readiness": "specialized",
            "visual-tester": "specialized",
            "chaos-engineer": "specialized",
            "requirements-validator": "strategic",
            "production-intelligence": "strategic",
            "fleet-commander": "fleet",
        }

    async def get_q_value(
        self,
        agent_id: str,
        state: Tuple,
        action: str
    ) -> float:
        """Get Q-value with hierarchical fallback"""

        # 1. Try individual Q-table first (highest priority)
        if agent_id in self.individual_tables:
            q_value = await self.individual_tables[agent_id].get(state, action)
            if q_value is not None:
                return q_value

        # 2. Fall back to category Q-table (transfer learning)
        category = self.agent_categories.get(agent_id)
        if category and category in self.category_tables:
            q_value = await self.category_tables[category].get(state, action)
            if q_value is not None:
                return q_value * 0.7  # Discount transferred knowledge

        # 3. Fall back to fleet Q-table (general patterns)
        if self.fleet_table:
            q_value = await self.fleet_table.get(state, action)
            if q_value is not None:
                return q_value * 0.5  # Further discount general knowledge

        # 4. Default initialization
        return 0.0

    async def update_q_value(
        self,
        agent_id: str,
        state: Tuple,
        action: str,
        reward: float,
        next_state: Tuple,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95
    ):
        """Update Q-value across all hierarchical levels"""

        # 1. Update individual Q-table
        current_q = await self.get_q_value(agent_id, state, action)
        max_next_q = await self.get_max_q_value(agent_id, next_state)

        # Q-learning update rule
        new_q = current_q + learning_rate * (
            reward + discount_factor * max_next_q - current_q
        )

        # Store in individual table
        await self.individual_tables[agent_id].set(state, action, new_q)

        # 2. Propagate to category Q-table (weighted average)
        category = self.agent_categories.get(agent_id)
        if category:
            await self.update_category_table(category, state, action, new_q)

        # 3. Propagate to fleet Q-table (with lower weight)
        if self.fleet_table:
            await self.update_fleet_table(state, action, new_q)

    async def update_category_table(
        self,
        category: str,
        state: Tuple,
        action: str,
        new_q: float
    ):
        """Update category Q-table using exponential moving average"""
        if category not in self.category_tables:
            return

        current_category_q = await self.category_tables[category].get(state, action) or 0.0

        # Exponential moving average (α = 0.1)
        updated_q = 0.9 * current_category_q + 0.1 * new_q

        await self.category_tables[category].set(state, action, updated_q)

    async def update_fleet_table(
        self,
        state: Tuple,
        action: str,
        new_q: float
    ):
        """Update fleet Q-table using exponential moving average"""
        if not self.fleet_table:
            return

        current_fleet_q = await self.fleet_table.get(state, action) or 0.0

        # Exponential moving average (α = 0.05, slower updates for stability)
        updated_q = 0.95 * current_fleet_q + 0.05 * new_q

        await self.fleet_table.set(state, action, updated_q)

    async def get_max_q_value(self, agent_id: str, state: Tuple) -> float:
        """Get maximum Q-value for a state across all actions"""
        action_space = self.get_action_space(agent_id)

        q_values = [
            await self.get_q_value(agent_id, state, action)
            for action in action_space
        ]

        return max(q_values) if q_values else 0.0

    def get_action_space(self, agent_id: str) -> List[str]:
        """Get action space for an agent"""
        # Return agent-specific action space
        # This would be defined per agent type
        pass
```

### 2.4 Transfer Learning Between Similar Agents

Agents with similar tasks can share learned patterns:

```python
class TransferLearningManager:
    """Manage knowledge transfer between similar agents"""

    # Define agent similarity groups
    SIMILARITY_GROUPS = {
        "test-generation": ["test-generator", "test-data-architect"],
        "test-execution": ["test-executor", "regression-risk-analyzer"],
        "coverage-analysis": ["coverage-analyzer", "quality-gate"],
        "security": ["security-scanner", "chaos-engineer"],
    }

    async def transfer_knowledge(
        self,
        source_agent: str,
        target_agent: str,
        min_confidence: float = 0.7
    ):
        """Transfer high-confidence Q-values from source to target"""

        # Only transfer between similar agents
        if not self.are_similar(source_agent, target_agent):
            return

        # Get high-confidence Q-values from source
        source_table = await self.get_q_table(source_agent)
        high_confidence_entries = await source_table.get_entries_above_threshold(
            min_value=min_confidence
        )

        # Transfer to target with decay
        target_table = await self.get_q_table(target_agent)
        for entry in high_confidence_entries:
            # Transfer with 0.8 multiplier (slight degradation)
            await target_table.initialize_if_missing(
                state=entry.state,
                action=entry.action,
                value=entry.q_value * 0.8
            )

    def are_similar(self, agent1: str, agent2: str) -> bool:
        """Check if two agents are in the same similarity group"""
        for group in self.SIMILARITY_GROUPS.values():
            if agent1 in group and agent2 in group:
                return True
        return False
```

---

## 3. PostgreSQL Schema for Q-Learning

### 3.1 Research Findings

PostgreSQL best practices for concurrent updates:

- **MVCC (Multiversion Concurrency Control)**: Reading never blocks writing, writing never blocks reading
- **Row-level locking**: Use `SELECT ... FOR UPDATE` for concurrent updates
- **Read Committed isolation**: Second client forced to redo computation when concurrent updates occur
- **High scalability**: PostgreSQL production clusters manage terabytes of data with high concurrency

### 3.2 Recommended Schema

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Q-Tables (one per agent + category + fleet)
CREATE TABLE q_tables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL,
    scope VARCHAR(20) NOT NULL CHECK (scope IN ('individual', 'category', 'fleet')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Metadata
    state_dimensions JSONB NOT NULL,
    action_space JSONB NOT NULL,
    learning_rate FLOAT DEFAULT 0.1,
    discount_factor FLOAT DEFAULT 0.95,

    -- Statistics
    total_updates INTEGER DEFAULT 0,
    avg_reward FLOAT DEFAULT 0.0,

    UNIQUE(agent_id, scope)
);

-- Q-Values (state-action pairs)
CREATE TABLE q_values (
    id BIGSERIAL PRIMARY KEY,
    q_table_id UUID NOT NULL REFERENCES q_tables(id) ON DELETE CASCADE,

    -- State representation (discrete)
    state_hash VARCHAR(64) NOT NULL,  -- Hash of state tuple for fast lookup
    state_data JSONB NOT NULL,         -- Full state data for debugging

    -- Action
    action VARCHAR(100) NOT NULL,

    -- Q-value
    q_value FLOAT NOT NULL DEFAULT 0.0,

    -- Learning metadata
    visit_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),

    -- Confidence metrics
    confidence_score FLOAT DEFAULT 0.0,  -- Based on visit count and variance
    value_variance FLOAT DEFAULT 0.0,     -- Track value stability

    -- Version for optimistic locking
    version INTEGER DEFAULT 1,

    CONSTRAINT unique_state_action UNIQUE(q_table_id, state_hash, action)
);

-- Learning experiences (for experience replay)
CREATE TABLE learning_experiences (
    id BIGSERIAL PRIMARY KEY,
    q_table_id UUID NOT NULL REFERENCES q_tables(id) ON DELETE CASCADE,

    -- Experience tuple (s, a, r, s')
    state_hash VARCHAR(64) NOT NULL,
    state_data JSONB NOT NULL,
    action VARCHAR(100) NOT NULL,
    reward FLOAT NOT NULL,
    next_state_hash VARCHAR(64) NOT NULL,
    next_state_data JSONB NOT NULL,

    -- Metadata
    timestamp TIMESTAMP DEFAULT NOW(),
    episode_id UUID,  -- Group experiences by episode

    -- Priority for prioritized experience replay
    priority FLOAT DEFAULT 1.0,
    sample_count INTEGER DEFAULT 0,

    -- TTL for experience cleanup
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '30 days'
);

-- Learning statistics (for monitoring convergence)
CREATE TABLE learning_stats (
    id BIGSERIAL PRIMARY KEY,
    q_table_id UUID NOT NULL REFERENCES q_tables(id) ON DELETE CASCADE,

    -- Time window
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,

    -- Metrics
    episodes_completed INTEGER DEFAULT 0,
    avg_episode_reward FLOAT,
    std_episode_reward FLOAT,
    avg_q_value_change FLOAT,  -- Track convergence
    exploration_rate FLOAT,

    -- Performance metrics
    avg_task_duration_seconds FLOAT,
    success_rate FLOAT,

    CONSTRAINT unique_window UNIQUE(q_table_id, window_start, window_end)
);

-- Indexes for performance

-- Fast Q-value lookup (most frequent operation)
CREATE INDEX idx_q_values_lookup ON q_values(q_table_id, state_hash, action);

-- Fast Q-value updates with locking
CREATE INDEX idx_q_values_update ON q_values(q_table_id, state_hash)
WHERE q_value > 0;  -- Partial index for learned values

-- Experience replay sampling
CREATE INDEX idx_experiences_priority ON learning_experiences(q_table_id, priority DESC, timestamp DESC);

-- Cleanup expired experiences
CREATE INDEX idx_experiences_expiry ON learning_experiences(expires_at)
WHERE expires_at < NOW();

-- Convergence monitoring
CREATE INDEX idx_stats_time ON learning_stats(q_table_id, window_start DESC);

-- Composite index for hierarchical lookup
CREATE INDEX idx_q_tables_scope ON q_tables(agent_id, scope);
```

### 3.3 Optimistic Locking for Concurrent Updates

```python
import asyncpg
from typing import Tuple, Optional

class QTablePostgres:
    """PostgreSQL-backed Q-table with optimistic locking"""

    def __init__(self, pool: asyncpg.Pool, q_table_id: str):
        self.pool = pool
        self.q_table_id = q_table_id

    async def get(self, state: Tuple, action: str) -> Optional[float]:
        """Get Q-value (no locking needed for reads)"""
        state_hash = self._hash_state(state)

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT q_value
                FROM q_values
                WHERE q_table_id = $1 AND state_hash = $2 AND action = $3
                """,
                self.q_table_id, state_hash, action
            )

            return row['q_value'] if row else None

    async def update(
        self,
        state: Tuple,
        action: str,
        new_q_value: float,
        max_retries: int = 3
    ) -> bool:
        """Update Q-value with optimistic locking and retry"""
        state_hash = self._hash_state(state)
        state_data = self._serialize_state(state)

        for attempt in range(max_retries):
            try:
                async with self.pool.acquire() as conn:
                    # Start transaction
                    async with conn.transaction():
                        # Get current value and version
                        row = await conn.fetchrow(
                            """
                            SELECT q_value, version, visit_count, value_variance
                            FROM q_values
                            WHERE q_table_id = $1 AND state_hash = $2 AND action = $3
                            FOR UPDATE  -- Lock the row
                            """,
                            self.q_table_id, state_hash, action
                        )

                        if row:
                            # Update existing entry
                            current_version = row['version']
                            visit_count = row['visit_count']

                            # Update variance for confidence tracking
                            old_q = row['q_value']
                            old_variance = row['value_variance']
                            new_variance = self._update_variance(
                                old_variance, old_q, new_q_value, visit_count
                            )

                            result = await conn.execute(
                                """
                                UPDATE q_values
                                SET
                                    q_value = $1,
                                    version = version + 1,
                                    visit_count = visit_count + 1,
                                    value_variance = $2,
                                    confidence_score = $3,
                                    last_updated = NOW()
                                WHERE
                                    q_table_id = $4
                                    AND state_hash = $5
                                    AND action = $6
                                    AND version = $7  -- Optimistic lock check
                                """,
                                new_q_value,
                                new_variance,
                                self._calculate_confidence(visit_count + 1, new_variance),
                                self.q_table_id,
                                state_hash,
                                action,
                                current_version
                            )

                            # Check if update succeeded (optimistic lock)
                            if result == "UPDATE 0":
                                raise OptimisticLockError("Concurrent update detected")

                        else:
                            # Insert new entry
                            await conn.execute(
                                """
                                INSERT INTO q_values (
                                    q_table_id, state_hash, state_data, action,
                                    q_value, visit_count, confidence_score
                                )
                                VALUES ($1, $2, $3, $4, $5, 1, 0.1)
                                """,
                                self.q_table_id, state_hash, state_data,
                                action, new_q_value
                            )

                        # Update table statistics
                        await conn.execute(
                            """
                            UPDATE q_tables
                            SET total_updates = total_updates + 1,
                                updated_at = NOW()
                            WHERE id = $1
                            """,
                            self.q_table_id
                        )

                return True  # Success

            except OptimisticLockError:
                if attempt < max_retries - 1:
                    # Retry with exponential backoff
                    await asyncio.sleep(0.1 * (2 ** attempt))
                    continue
                else:
                    return False  # Failed after retries

    async def store_experience(
        self,
        state: Tuple,
        action: str,
        reward: float,
        next_state: Tuple,
        episode_id: str,
        priority: float = 1.0
    ):
        """Store experience for replay buffer"""
        state_hash = self._hash_state(state)
        state_data = self._serialize_state(state)
        next_state_hash = self._hash_state(next_state)
        next_state_data = self._serialize_state(next_state)

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO learning_experiences (
                    q_table_id, state_hash, state_data, action, reward,
                    next_state_hash, next_state_data, episode_id, priority
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                self.q_table_id, state_hash, state_data, action, reward,
                next_state_hash, next_state_data, episode_id, priority
            )

    async def sample_experiences(
        self,
        batch_size: int = 32,
        prioritized: bool = True
    ) -> List[Dict]:
        """Sample experiences for replay"""
        async with self.pool.acquire() as conn:
            if prioritized:
                # Prioritized experience replay
                rows = await conn.fetch(
                    """
                    SELECT state_data, action, reward, next_state_data
                    FROM learning_experiences
                    WHERE q_table_id = $1 AND expires_at > NOW()
                    ORDER BY priority DESC, RANDOM()
                    LIMIT $2
                    """,
                    self.q_table_id, batch_size
                )
            else:
                # Uniform sampling
                rows = await conn.fetch(
                    """
                    SELECT state_data, action, reward, next_state_data
                    FROM learning_experiences
                    WHERE q_table_id = $1 AND expires_at > NOW()
                    ORDER BY RANDOM()
                    LIMIT $2
                    """,
                    self.q_table_id, batch_size
                )

            return [dict(row) for row in rows]

    def _hash_state(self, state: Tuple) -> str:
        """Hash state tuple for fast lookup"""
        import hashlib
        state_str = str(sorted(state))  # Sort for consistency
        return hashlib.sha256(state_str.encode()).hexdigest()[:64]

    def _serialize_state(self, state: Tuple) -> Dict:
        """Serialize state to JSON"""
        import json
        return json.dumps(state)

    def _update_variance(
        self,
        old_variance: float,
        old_value: float,
        new_value: float,
        n: int
    ) -> float:
        """Update variance using Welford's online algorithm"""
        if n == 0:
            return 0.0
        delta = new_value - old_value
        return old_variance + delta * delta / (n + 1)

    def _calculate_confidence(self, visit_count: int, variance: float) -> float:
        """Calculate confidence score (0-1) based on visits and variance"""
        # More visits = higher confidence
        # Lower variance = higher confidence
        visit_confidence = min(visit_count / 100, 1.0)  # Cap at 100 visits
        variance_confidence = 1.0 / (1.0 + variance)    # Lower variance = higher

        return (visit_confidence + variance_confidence) / 2

class OptimisticLockError(Exception):
    """Raised when optimistic lock check fails"""
    pass
```

### 3.4 Performance Optimization

```sql
-- Partitioning for large Q-tables (horizontal scaling)
CREATE TABLE q_values_partitioned (
    LIKE q_values INCLUDING ALL
) PARTITION BY HASH (q_table_id);

-- Create 8 partitions
CREATE TABLE q_values_p0 PARTITION OF q_values_partitioned
    FOR VALUES WITH (MODULUS 8, REMAINDER 0);
CREATE TABLE q_values_p1 PARTITION OF q_values_partitioned
    FOR VALUES WITH (MODULUS 8, REMAINDER 1);
-- ... repeat for p2-p7

-- Materialized view for convergence dashboard
CREATE MATERIALIZED VIEW convergence_summary AS
SELECT
    qt.agent_id,
    qt.scope,
    COUNT(DISTINCT qv.state_hash) as unique_states,
    COUNT(*) as total_state_actions,
    AVG(qv.q_value) as avg_q_value,
    AVG(qv.confidence_score) as avg_confidence,
    MAX(qv.last_updated) as last_update,
    qt.total_updates
FROM q_tables qt
LEFT JOIN q_values qv ON qt.id = qv.q_table_id
GROUP BY qt.id, qt.agent_id, qt.scope, qt.total_updates;

-- Refresh every 5 minutes
CREATE INDEX idx_convergence_agent ON convergence_summary(agent_id);
```

---

## 4. Production Considerations

### 4.1 Monitoring Q-Learning Convergence

Based on research showing production RL requires careful monitoring:

```python
class QLearningMonitor:
    """Monitor Q-learning convergence and performance"""

    def __init__(self, postgres_pool: asyncpg.Pool):
        self.pool = postgres_pool

    async def check_convergence(
        self,
        agent_id: str,
        window_hours: int = 24
    ) -> Dict[str, Any]:
        """Check if Q-learning has converged"""

        async with self.pool.acquire() as conn:
            # Get recent statistics
            stats = await conn.fetch(
                """
                SELECT
                    window_start,
                    avg_q_value_change,
                    std_episode_reward,
                    success_rate,
                    exploration_rate
                FROM learning_stats
                WHERE
                    q_table_id = (
                        SELECT id FROM q_tables
                        WHERE agent_id = $1 AND scope = 'individual'
                    )
                    AND window_start >= NOW() - INTERVAL '%s hours'
                ORDER BY window_start DESC
                """,
                agent_id, window_hours
            )

            if not stats or len(stats) < 10:
                return {
                    "converged": False,
                    "reason": "Insufficient data",
                    "recommendation": "Continue learning"
                }

            # Convergence criteria
            recent_changes = [s['avg_q_value_change'] for s in stats[:10]]
            avg_change = np.mean(recent_changes)

            # Criteria 1: Q-value changes are small
            q_value_stable = avg_change < 0.01

            # Criteria 2: Reward variance is low
            reward_variances = [s['std_episode_reward'] for s in stats[:10]]
            avg_variance = np.mean(reward_variances)
            reward_stable = avg_variance < 5.0

            # Criteria 3: Success rate is high
            success_rates = [s['success_rate'] for s in stats[:10]]
            avg_success = np.mean(success_rates)
            performance_good = avg_success > 0.85

            # Criteria 4: Exploration has decreased
            exploration_rate = stats[0]['exploration_rate']
            exploration_low = exploration_rate < 0.05

            converged = all([
                q_value_stable,
                reward_stable,
                performance_good,
                exploration_low
            ])

            return {
                "converged": converged,
                "metrics": {
                    "avg_q_change": avg_change,
                    "avg_reward_variance": avg_variance,
                    "avg_success_rate": avg_success,
                    "current_exploration": exploration_rate
                },
                "criteria": {
                    "q_value_stable": q_value_stable,
                    "reward_stable": reward_stable,
                    "performance_good": performance_good,
                    "exploration_low": exploration_low
                },
                "recommendation": self._get_recommendation(
                    q_value_stable, reward_stable, performance_good, exploration_low
                )
            }

    def _get_recommendation(
        self,
        q_stable: bool,
        reward_stable: bool,
        perf_good: bool,
        explore_low: bool
    ) -> str:
        """Get recommendation based on convergence criteria"""
        if all([q_stable, reward_stable, perf_good, explore_low]):
            return "Learning converged. Ready for production deployment."
        elif not perf_good:
            return "Performance not meeting target. Review reward function."
        elif not explore_low:
            return "Still exploring. Decrease epsilon faster."
        elif not reward_stable:
            return "Reward variance high. Check environment stability."
        else:
            return "Continue learning. Near convergence."

    async def get_convergence_dashboard(self) -> Dict[str, Any]:
        """Get convergence dashboard for all agents"""

        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM convergence_summary
                ORDER BY agent_id
            """)

            return {
                agent['agent_id']: {
                    "scope": agent['scope'],
                    "unique_states": agent['unique_states'],
                    "total_updates": agent['total_updates'],
                    "avg_q_value": agent['avg_q_value'],
                    "avg_confidence": agent['avg_confidence'],
                    "last_update": agent['last_update']
                }
                for agent in rows
            }
```

### 4.2 Epsilon Decay Strategy

Based on research showing reward-based epsilon decay (RBED) outperforms exponential decay:

```python
class EpsilonDecayStrategy:
    """Manage exploration-exploitation tradeoff"""

    def __init__(
        self,
        initial_epsilon: float = 0.2,
        min_epsilon: float = 0.01,
        decay_mode: str = "reward_based"
    ):
        self.initial_epsilon = initial_epsilon
        self.min_epsilon = min_epsilon
        self.decay_mode = decay_mode

        # Exponential decay parameters
        self.decay_rate = 0.995

        # Reward-based decay parameters
        self.reward_window = []
        self.window_size = 100
        self.target_reward = 50.0

    def get_epsilon(
        self,
        episode: int,
        recent_reward: Optional[float] = None
    ) -> float:
        """Get current epsilon value"""

        if self.decay_mode == "exponential":
            return self._exponential_decay(episode)
        elif self.decay_mode == "reward_based":
            return self._reward_based_decay(recent_reward)
        elif self.decay_mode == "step":
            return self._step_decay(episode)
        else:
            raise ValueError(f"Unknown decay mode: {self.decay_mode}")

    def _exponential_decay(self, episode: int) -> float:
        """Exponential decay: ε = max(ε_min, ε_initial * decay_rate^episode)"""
        epsilon = self.initial_epsilon * (self.decay_rate ** episode)
        return max(self.min_epsilon, epsilon)

    def _reward_based_decay(self, recent_reward: Optional[float]) -> float:
        """Reward-Based Epsilon Decay (RBED)

        Decay epsilon faster when rewards are consistently high,
        slower when rewards are low (more exploration needed).
        """
        if recent_reward is None:
            return self.initial_epsilon

        # Update reward window
        self.reward_window.append(recent_reward)
        if len(self.reward_window) > self.window_size:
            self.reward_window.pop(0)

        # Calculate performance ratio
        if len(self.reward_window) < 10:
            return self.initial_epsilon

        avg_reward = np.mean(self.reward_window)
        performance_ratio = avg_reward / self.target_reward

        # Decay faster when performing well
        if performance_ratio > 1.0:
            # Performing above target - decay faster
            decay_multiplier = 0.99
        elif performance_ratio > 0.7:
            # Performing reasonably - normal decay
            decay_multiplier = 0.995
        else:
            # Performing poorly - slower decay (more exploration)
            decay_multiplier = 0.998

        # Apply decay
        current_epsilon = self.reward_window[-1] if hasattr(self, '_last_epsilon') else self.initial_epsilon
        new_epsilon = current_epsilon * decay_multiplier

        self._last_epsilon = new_epsilon
        return max(self.min_epsilon, new_epsilon)

    def _step_decay(self, episode: int) -> float:
        """Step decay at specific milestones"""
        if episode < 100:
            return 0.2
        elif episode < 500:
            return 0.1
        elif episode < 1000:
            return 0.05
        else:
            return 0.01
```

### 4.3 A/B Testing Framework

Based on research showing A/B testing is critical for production RL:

```python
from dataclasses import dataclass
from typing import List, Dict, Any
import numpy as np
from scipy import stats

@dataclass
class ABTestConfig:
    """Configuration for A/B test"""
    test_id: str
    variant_a: str  # "baseline" or "learned_policy"
    variant_b: str  # "learned_policy" or "new_policy"
    traffic_split: float = 0.5  # 50/50 split
    min_samples: int = 100
    confidence_level: float = 0.95

class ABTestingFramework:
    """A/B test learned policies vs baseline"""

    def __init__(self, postgres_pool: asyncpg.Pool):
        self.pool = postgres_pool
        self.active_tests: Dict[str, ABTestConfig] = {}

    async def start_test(
        self,
        agent_id: str,
        baseline_policy: str = "random",
        learned_policy: str = "q_learning",
        duration_hours: int = 24
    ) -> str:
        """Start A/B test comparing policies"""

        test_id = f"ab_{agent_id}_{int(time.time())}"

        config = ABTestConfig(
            test_id=test_id,
            variant_a=baseline_policy,
            variant_b=learned_policy,
            traffic_split=0.5
        )

        self.active_tests[test_id] = config

        # Store test config in database
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ab_tests (
                    test_id, agent_id, variant_a, variant_b,
                    traffic_split, start_time, end_time
                )
                VALUES ($1, $2, $3, $4, $5, NOW(), NOW() + INTERVAL '%s hours')
                """,
                test_id, agent_id, baseline_policy, learned_policy,
                0.5, duration_hours
            )

        return test_id

    async def assign_variant(self, test_id: str) -> str:
        """Assign user to A or B variant"""
        config = self.active_tests[test_id]

        # Random assignment based on traffic split
        return config.variant_a if np.random.random() < config.traffic_split else config.variant_b

    async def record_result(
        self,
        test_id: str,
        variant: str,
        metric_value: float,
        metadata: Dict[str, Any]
    ):
        """Record test result"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ab_test_results (
                    test_id, variant, metric_value, metadata, timestamp
                )
                VALUES ($1, $2, $3, $4, NOW())
                """,
                test_id, variant, metric_value, json.dumps(metadata)
            )

    async def analyze_test(self, test_id: str) -> Dict[str, Any]:
        """Analyze A/B test results"""

        async with self.pool.acquire() as conn:
            # Get results for both variants
            results_a = await conn.fetch(
                """
                SELECT metric_value FROM ab_test_results
                WHERE test_id = $1 AND variant = (
                    SELECT variant_a FROM ab_tests WHERE test_id = $1
                )
                """,
                test_id
            )

            results_b = await conn.fetch(
                """
                SELECT metric_value FROM ab_test_results
                WHERE test_id = $1 AND variant = (
                    SELECT variant_b FROM ab_tests WHERE test_id = $1
                )
                """,
                test_id
            )

        if len(results_a) < 30 or len(results_b) < 30:
            return {
                "status": "insufficient_data",
                "samples_a": len(results_a),
                "samples_b": len(results_b),
                "recommendation": "Continue test"
            }

        # Extract metric values
        values_a = [r['metric_value'] for r in results_a]
        values_b = [r['metric_value'] for r in results_b]

        # Statistical analysis
        mean_a = np.mean(values_a)
        mean_b = np.mean(values_b)
        std_a = np.std(values_a)
        std_b = np.std(values_b)

        # Two-sample t-test
        t_stat, p_value = stats.ttest_ind(values_a, values_b)

        # Effect size (Cohen's d)
        pooled_std = np.sqrt((std_a**2 + std_b**2) / 2)
        cohens_d = (mean_b - mean_a) / pooled_std

        # Statistical significance
        significant = p_value < 0.05

        # Practical significance (effect size > 0.2)
        practical = abs(cohens_d) > 0.2

        # Determine winner
        if significant and practical:
            if mean_b > mean_a:
                winner = "variant_b"
                improvement = ((mean_b - mean_a) / mean_a) * 100
            else:
                winner = "variant_a"
                improvement = ((mean_a - mean_b) / mean_b) * 100
        else:
            winner = "no_clear_winner"
            improvement = 0

        return {
            "status": "complete",
            "samples_a": len(values_a),
            "samples_b": len(values_b),
            "mean_a": mean_a,
            "mean_b": mean_b,
            "std_a": std_a,
            "std_b": std_b,
            "t_statistic": t_stat,
            "p_value": p_value,
            "cohens_d": cohens_d,
            "statistically_significant": significant,
            "practically_significant": practical,
            "winner": winner,
            "improvement_percent": improvement,
            "recommendation": self._get_recommendation(winner, improvement, significant, practical)
        }

    def _get_recommendation(
        self,
        winner: str,
        improvement: float,
        significant: bool,
        practical: bool
    ) -> str:
        """Get deployment recommendation"""
        if winner == "variant_b" and significant and practical:
            return f"Deploy variant B. {improvement:.1f}% improvement with statistical and practical significance."
        elif winner == "variant_a":
            return "Keep baseline. Learned policy did not improve performance."
        else:
            return "No clear winner. Consider longer test or different metrics."
```

### 4.4 Rollback Strategy

```python
class PolicyRollbackManager:
    """Manage policy rollbacks if performance degrades"""

    def __init__(self, postgres_pool: asyncpg.Pool):
        self.pool = postgres_pool

    async def snapshot_policy(self, agent_id: str) -> str:
        """Create snapshot of current Q-table"""
        snapshot_id = f"snapshot_{agent_id}_{int(time.time())}"

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Copy Q-table
                await conn.execute(
                    """
                    INSERT INTO q_table_snapshots (snapshot_id, agent_id, q_table_data)
                    SELECT $1, agent_id, jsonb_agg(row_to_json(qv.*))
                    FROM q_values qv
                    WHERE q_table_id = (
                        SELECT id FROM q_tables
                        WHERE agent_id = $2 AND scope = 'individual'
                    )
                    """,
                    snapshot_id, agent_id
                )

        return snapshot_id

    async def monitor_performance(
        self,
        agent_id: str,
        window_hours: int = 1
    ) -> Dict[str, Any]:
        """Monitor performance and detect degradation"""

        async with self.pool.acquire() as conn:
            # Get recent performance
            recent_stats = await conn.fetchrow(
                """
                SELECT AVG(success_rate) as avg_success, AVG(avg_episode_reward) as avg_reward
                FROM learning_stats
                WHERE
                    q_table_id = (SELECT id FROM q_tables WHERE agent_id = $1 AND scope = 'individual')
                    AND window_start >= NOW() - INTERVAL '%s hours'
                """,
                agent_id, window_hours
            )

            # Get baseline performance (last 24 hours before deployment)
            baseline_stats = await conn.fetchrow(
                """
                SELECT AVG(success_rate) as avg_success, AVG(avg_episode_reward) as avg_reward
                FROM learning_stats
                WHERE
                    q_table_id = (SELECT id FROM q_tables WHERE agent_id = $1 AND scope = 'individual')
                    AND window_start BETWEEN NOW() - INTERVAL '48 hours' AND NOW() - INTERVAL '24 hours'
                """,
                agent_id
            )

        if not recent_stats or not baseline_stats:
            return {"degradation_detected": False, "reason": "insufficient_data"}

        # Calculate degradation
        success_degradation = baseline_stats['avg_success'] - recent_stats['avg_success']
        reward_degradation = baseline_stats['avg_reward'] - recent_stats['avg_reward']

        # Thresholds for rollback
        ROLLBACK_THRESHOLD_SUCCESS = 0.10  # 10% drop in success rate
        ROLLBACK_THRESHOLD_REWARD = 15.0   # 15 point drop in reward

        degradation_detected = (
            success_degradation > ROLLBACK_THRESHOLD_SUCCESS or
            reward_degradation > ROLLBACK_THRESHOLD_REWARD
        )

        return {
            "degradation_detected": degradation_detected,
            "metrics": {
                "recent_success": recent_stats['avg_success'],
                "baseline_success": baseline_stats['avg_success'],
                "success_drop": success_degradation,
                "recent_reward": recent_stats['avg_reward'],
                "baseline_reward": baseline_stats['avg_reward'],
                "reward_drop": reward_degradation
            },
            "recommendation": "ROLLBACK IMMEDIATELY" if degradation_detected else "Continue monitoring"
        }

    async def rollback(self, agent_id: str, snapshot_id: str):
        """Rollback to previous snapshot"""

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Get Q-table ID
                q_table_id = await conn.fetchval(
                    "SELECT id FROM q_tables WHERE agent_id = $1 AND scope = 'individual'",
                    agent_id
                )

                # Delete current Q-values
                await conn.execute(
                    "DELETE FROM q_values WHERE q_table_id = $1",
                    q_table_id
                )

                # Restore from snapshot
                await conn.execute(
                    """
                    INSERT INTO q_values (q_table_id, state_hash, state_data, action, q_value, visit_count)
                    SELECT
                        $1,
                        (value->>'state_hash')::varchar,
                        (value->>'state_data')::jsonb,
                        (value->>'action')::varchar,
                        (value->>'q_value')::float,
                        (value->>'visit_count')::integer
                    FROM q_table_snapshots, jsonb_array_elements(q_table_data) AS value
                    WHERE snapshot_id = $2
                    """,
                    q_table_id, snapshot_id
                )

                # Log rollback event
                await conn.execute(
                    """
                    INSERT INTO rollback_events (agent_id, snapshot_id, timestamp, reason)
                    VALUES ($1, $2, NOW(), 'Performance degradation detected')
                    """,
                    agent_id, snapshot_id
                )
```

---

## 5. Team-Wide Learning Coordination

### 5.1 Centralized Q-Table Sharing

```python
class TeamLearningCoordinator:
    """Coordinate learning across team members and CI runs"""

    def __init__(self, postgres_pool: asyncpg.Pool):
        self.pool = postgres_pool

    async def sync_from_central(
        self,
        agent_id: str,
        developer_id: Optional[str] = None
    ) -> int:
        """Sync Q-values from central repository to local"""

        async with self.pool.acquire() as conn:
            # Get central Q-values that are high-confidence
            central_values = await conn.fetch(
                """
                SELECT state_hash, action, q_value, confidence_score
                FROM q_values
                WHERE
                    q_table_id = (SELECT id FROM q_tables WHERE agent_id = $1 AND scope = 'fleet')
                    AND confidence_score > 0.7
                """,
                agent_id
            )

            # Upsert into individual Q-table
            local_q_table_id = await conn.fetchval(
                "SELECT id FROM q_tables WHERE agent_id = $1 AND scope = 'individual'",
                agent_id
            )

            synced_count = 0
            for row in central_values:
                # Only sync if local doesn't have this state-action or has lower confidence
                local_q = await conn.fetchrow(
                    """
                    SELECT q_value, confidence_score FROM q_values
                    WHERE q_table_id = $1 AND state_hash = $2 AND action = $3
                    """,
                    local_q_table_id, row['state_hash'], row['action']
                )

                if not local_q or local_q['confidence_score'] < row['confidence_score']:
                    # Sync this value
                    await conn.execute(
                        """
                        INSERT INTO q_values (q_table_id, state_hash, action, q_value, confidence_score)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (q_table_id, state_hash, action)
                        DO UPDATE SET
                            q_value = EXCLUDED.q_value,
                            confidence_score = EXCLUDED.confidence_score,
                            last_updated = NOW()
                        """,
                        local_q_table_id, row['state_hash'], row['action'],
                        row['q_value'], row['confidence_score']
                    )
                    synced_count += 1

            return synced_count

    async def push_to_central(
        self,
        agent_id: str,
        developer_id: Optional[str] = None
    ) -> int:
        """Push high-confidence local Q-values to central repository"""

        async with self.pool.acquire() as conn:
            # Get local Q-values with high confidence
            local_values = await conn.fetch(
                """
                SELECT state_hash, state_data, action, q_value, confidence_score, visit_count
                FROM q_values
                WHERE
                    q_table_id = (SELECT id FROM q_tables WHERE agent_id = $1 AND scope = 'individual')
                    AND confidence_score > 0.7
                    AND visit_count >= 5
                """,
                agent_id
            )

            # Get fleet Q-table ID
            fleet_q_table_id = await conn.fetchval(
                "SELECT id FROM q_tables WHERE agent_id = $1 AND scope = 'fleet'",
                agent_id
            )

            pushed_count = 0
            for row in local_values:
                # Check if central has this state-action
                central_q = await conn.fetchrow(
                    """
                    SELECT q_value, confidence_score, visit_count FROM q_values
                    WHERE q_table_id = $1 AND state_hash = $2 AND action = $3
                    """,
                    fleet_q_table_id, row['state_hash'], row['action']
                )

                if not central_q:
                    # Insert new entry
                    await conn.execute(
                        """
                        INSERT INTO q_values (
                            q_table_id, state_hash, state_data, action,
                            q_value, confidence_score, visit_count
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        fleet_q_table_id, row['state_hash'], row['state_data'],
                        row['action'], row['q_value'], row['confidence_score'], row['visit_count']
                    )
                    pushed_count += 1
                else:
                    # Merge using weighted average based on confidence
                    local_weight = row['confidence_score']
                    central_weight = central_q['confidence_score']
                    total_weight = local_weight + central_weight

                    merged_q_value = (
                        (row['q_value'] * local_weight + central_q['q_value'] * central_weight)
                        / total_weight
                    )
                    merged_confidence = (local_weight + central_weight) / 2
                    merged_visits = row['visit_count'] + central_q['visit_count']

                    await conn.execute(
                        """
                        UPDATE q_values
                        SET
                            q_value = $1,
                            confidence_score = $2,
                            visit_count = $3,
                            last_updated = NOW()
                        WHERE q_table_id = $4 AND state_hash = $5 AND action = $6
                        """,
                        merged_q_value, merged_confidence, merged_visits,
                        fleet_q_table_id, row['state_hash'], row['action']
                    )
                    pushed_count += 1

            return pushed_count

    async def resolve_conflicts(self, agent_id: str):
        """Resolve conflicts when multiple developers update same state-action"""

        async with self.pool.acquire() as conn:
            # Find state-actions updated by multiple sources recently
            conflicts = await conn.fetch(
                """
                SELECT state_hash, action,
                       array_agg(q_value) as q_values,
                       array_agg(confidence_score) as confidence_scores
                FROM q_values
                WHERE
                    q_table_id = (SELECT id FROM q_tables WHERE agent_id = $1 AND scope = 'fleet')
                    AND last_updated >= NOW() - INTERVAL '1 hour'
                GROUP BY state_hash, action
                HAVING COUNT(*) > 1
                """,
                agent_id
            )

            for conflict in conflicts:
                # Resolve using highest confidence value
                q_values = conflict['q_values']
                confidences = conflict['confidence_scores']

                best_idx = np.argmax(confidences)
                best_q_value = q_values[best_idx]
                best_confidence = confidences[best_idx]

                # Update to best value
                await conn.execute(
                    """
                    UPDATE q_values
                    SET q_value = $1, confidence_score = $2
                    WHERE
                        q_table_id = (SELECT id FROM q_tables WHERE agent_id = $3 AND scope = 'fleet')
                        AND state_hash = $4
                        AND action = $5
                    """,
                    best_q_value, best_confidence, agent_id,
                    conflict['state_hash'], conflict['action']
                )
```

### 5.2 Privacy Considerations

```python
class PrivacyManager:
    """Manage privacy for Q-learning data sharing"""

    def __init__(self):
        self.sensitive_fields = ['developer_id', 'project_path', 'file_content']

    def anonymize_state(self, state: Dict) -> Dict:
        """Anonymize state before sharing"""
        anonymized = state.copy()

        # Remove sensitive fields
        for field in self.sensitive_fields:
            if field in anonymized:
                anonymized[field] = self._hash_value(anonymized[field])

        return anonymized

    def _hash_value(self, value: str) -> str:
        """Hash sensitive value"""
        import hashlib
        return hashlib.sha256(value.encode()).hexdigest()[:16]

    async def apply_differential_privacy(
        self,
        q_value: float,
        epsilon: float = 1.0
    ) -> float:
        """Apply differential privacy noise to Q-value"""
        # Laplace mechanism
        sensitivity = 1.0  # Maximum change in Q-value
        scale = sensitivity / epsilon
        noise = np.random.laplace(0, scale)

        return q_value + noise
```

---

## 6. Code Examples and Pseudocode

### 6.1 Complete Q-Learning Loop

```python
import asyncio
from typing import Tuple, Dict, Any
import numpy as np

class QEAgentQLearning:
    """Q-Learning integration for QE agents"""

    def __init__(
        self,
        agent_id: str,
        q_table_manager: HierarchicalQTableManager,
        reward_calculator: QERewardCalculator,
        epsilon_strategy: EpsilonDecayStrategy
    ):
        self.agent_id = agent_id
        self.q_table_manager = q_table_manager
        self.reward_calculator = reward_calculator
        self.epsilon_strategy = epsilon_strategy

        # Hyperparameters
        self.learning_rate = 0.1
        self.discount_factor = 0.95

        # Episode tracking
        self.episode_count = 0
        self.total_reward = 0.0

    async def select_action(
        self,
        state: Tuple,
        action_space: List[str]
    ) -> str:
        """Select action using epsilon-greedy policy"""

        # Get current epsilon
        epsilon = self.epsilon_strategy.get_epsilon(
            episode=self.episode_count,
            recent_reward=self.total_reward / max(self.episode_count, 1)
        )

        # Epsilon-greedy selection
        if np.random.random() < epsilon:
            # Explore: random action
            action = np.random.choice(action_space)
        else:
            # Exploit: best action from Q-table
            q_values = {}
            for action in action_space:
                q_values[action] = await self.q_table_manager.get_q_value(
                    self.agent_id, state, action
                )

            # Select action with highest Q-value
            action = max(q_values, key=q_values.get)

        return action

    async def execute_episode(
        self,
        task: QETask,
        max_steps: int = 10
    ) -> Dict[str, Any]:
        """Execute one learning episode"""

        episode_id = f"episode_{self.agent_id}_{self.episode_count}"
        episode_reward = 0.0
        episode_steps = []

        # Get initial state from task
        state = self._extract_state(task)

        for step in range(max_steps):
            # Select action
            action_space = self._get_action_space(task)
            action = await self.select_action(state, action_space)

            # Execute action (run agent's execute method)
            result = await self._execute_action(task, action)

            # Get next state
            next_state = self._extract_state_from_result(result)

            # Calculate reward
            reward = self.reward_calculator.calculate_reward(
                state_before=self._state_to_dict(state),
                action=action,
                state_after=self._state_to_dict(next_state),
                metadata=result
            )

            # Update Q-value
            await self.q_table_manager.update_q_value(
                agent_id=self.agent_id,
                state=state,
                action=action,
                reward=reward,
                next_state=next_state,
                learning_rate=self.learning_rate,
                discount_factor=self.discount_factor
            )

            # Store experience for replay
            await self._store_experience(
                state=state,
                action=action,
                reward=reward,
                next_state=next_state,
                episode_id=episode_id
            )

            # Track episode
            episode_reward += reward
            episode_steps.append({
                "step": step,
                "state": state,
                "action": action,
                "reward": reward,
                "next_state": next_state
            })

            # Check if episode is done
            if result.get("done", False):
                break

            # Move to next state
            state = next_state

        # Update episode tracking
        self.episode_count += 1
        self.total_reward += episode_reward

        return {
            "episode_id": episode_id,
            "steps": len(episode_steps),
            "total_reward": episode_reward,
            "avg_reward_per_step": episode_reward / len(episode_steps),
            "episode_details": episode_steps
        }

    async def train_with_experience_replay(
        self,
        num_batches: int = 10,
        batch_size: int = 32
    ):
        """Train using experience replay"""

        for _ in range(num_batches):
            # Sample experiences from buffer
            experiences = await self._sample_experiences(batch_size)

            for exp in experiences:
                state = exp['state_data']
                action = exp['action']
                reward = exp['reward']
                next_state = exp['next_state_data']

                # Replay Q-learning update
                await self.q_table_manager.update_q_value(
                    agent_id=self.agent_id,
                    state=state,
                    action=action,
                    reward=reward,
                    next_state=next_state,
                    learning_rate=self.learning_rate * 0.5,  # Lower LR for replay
                    discount_factor=self.discount_factor
                )

    def _extract_state(self, task: QETask) -> Tuple:
        """Extract state from task (agent-specific)"""
        # This would be implemented by each agent type
        pass

    def _get_action_space(self, task: QETask) -> List[str]:
        """Get available actions for current task"""
        # This would be implemented by each agent type
        pass

    async def _execute_action(self, task: QETask, action: str) -> Dict[str, Any]:
        """Execute action and get result"""
        # This would call the agent's execute method
        pass

    def _extract_state_from_result(self, result: Dict) -> Tuple:
        """Extract next state from action result"""
        pass

    def _state_to_dict(self, state: Tuple) -> Dict:
        """Convert state tuple to dictionary"""
        pass

    async def _store_experience(
        self,
        state: Tuple,
        action: str,
        reward: float,
        next_state: Tuple,
        episode_id: str
    ):
        """Store experience in replay buffer"""
        pass

    async def _sample_experiences(self, batch_size: int) -> List[Dict]:
        """Sample experiences from replay buffer"""
        pass
```

### 6.2 Integration with Existing BaseQEAgent

```python
# Modify existing BaseQEAgent to include Q-learning

class BaseQEAgent(ABC):
    """Base class for all QE agents with Q-learning"""

    def __init__(
        self,
        agent_id: str,
        model: iModel,
        memory: QEMemory,
        skills: Optional[List[str]] = None,
        enable_learning: bool = True,  # Enable by default
        q_table_manager: Optional[HierarchicalQTableManager] = None
    ):
        self.agent_id = agent_id
        self.model = model
        self.memory = memory
        self.skills = skills or []
        self.enable_learning = enable_learning

        # Initialize LionAGI branch
        self.branch = Branch(
            system=self.get_system_prompt(),
            chat_model=model,
            name=agent_id
        )

        # Setup logging
        self.logger = logging.getLogger(f"lionagi_qe.{agent_id}")

        # Q-learning integration
        if enable_learning and q_table_manager:
            self.q_learning = QEAgentQLearning(
                agent_id=agent_id,
                q_table_manager=q_table_manager,
                reward_calculator=QERewardCalculator(),
                epsilon_strategy=EpsilonDecayStrategy(decay_mode="reward_based")
            )
        else:
            self.q_learning = None

        # Metrics
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_cost": 0.0,
            "patterns_learned": 0,
            "avg_reward": 0.0
        }

    async def execute_with_learning(self, task: QETask) -> Dict[str, Any]:
        """Execute task with Q-learning"""

        if not self.enable_learning or not self.q_learning:
            # Fall back to regular execution
            return await self.execute(task)

        # Execute learning episode
        episode_result = await self.q_learning.execute_episode(task)

        # Update metrics
        self.metrics["avg_reward"] = (
            self.metrics["avg_reward"] * self.metrics["tasks_completed"] +
            episode_result["total_reward"]
        ) / (self.metrics["tasks_completed"] + 1)

        return episode_result
```

---

## 7. References

### Academic Papers

1. **Reinforcement Learning from Automatic Feedback for High-Quality Unit Test Generation** (2024)
   - IEEE Conference Publication
   - Introduces RLSQM (RL from Static Quality Metrics)
   - https://ieeexplore.ieee.org/document/11026897/

2. **Reward Augmentation in Reinforcement Learning for Testing Distributed Systems** (2024)
   - arXiv:2409.02137
   - Shows importance of reward augmentation for sparse rewards in testing
   - Evaluated on RedisRaft, Etcd, RSL
   - https://arxiv.org/abs/2409.02137

3. **Reinforcement learning for online testing of autonomous driving systems** (2024)
   - Empirical Software Engineering, Springer
   - DQN outperforms Q-learning in 2/3 scenarios
   - https://link.springer.com/article/10.1007/s10664-024-10562-5

4. **Cooperative multi-agent target searching: deep RL with parallel hindsight experience replay** (2023)
   - Complex & Intelligent Systems
   - PHER-MADDPG algorithm
   - https://link.springer.com/article/10.1007/s40747-023-00985-w

5. **RBED: Reward Based Epsilon Decay** (2019)
   - arXiv:1910.13701
   - Adaptive epsilon decay based on reward feedback
   - https://arxiv.org/abs/1910.13701

6. **A Survey on Transfer Learning for Multiagent Reinforcement Learning** (2019)
   - JAIR (Journal of AI Research)
   - Transfer learning strategies for MARL
   - https://www.jair.org/index.php/jair/article/download/11396/26482/21167

### Production RL Systems

7. **Deploying reinforcement learning in production using Ray and Amazon SageMaker** (2024)
   - AWS Machine Learning Blog
   - A/B testing, Model Monitor, rollback strategies
   - https://aws.amazon.com/blogs/machine-learning/deploying-reinforcement-learning-in-production-using-ray-and-amazon-sagemaker/

8. **Business process improvement with AB testing and reinforcement learning** (2024)
   - Software and Systems Modeling, Springer
   - AB-BPM for production RL systems
   - https://link.springer.com/article/10.1007/s10270-024-01229-2

### Technical Resources

9. **OpenAI Gym Documentation**
   - State and action space design
   - https://gymnasium.farama.org/api/env/

10. **PostgreSQL Concurrency Control Documentation**
    - MVCC, locking strategies
    - https://www.postgresql.org/docs/current/mvcc.html

11. **Multi-Agent Experience Replay Buffer - AgileRL**
    - Implementation example for multi-agent replay buffers
    - https://docs.agilerl.com/en/latest/api/components/multi_agent_replay_buffer.html

### Existing Implementations

12. **LionAGI Framework**
    - Python async-first agent orchestration
    - https://github.com/lion-agi/lionagi

13. **Gymnasium (OpenAI Gym Fork)**
    - Standard RL environment API
    - https://github.com/Farama-Foundation/Gymnasium

14. **Stable-Baselines3**
    - Reference implementations of RL algorithms
    - https://stable-baselines3.readthedocs.io/

---

## 8. Appendices

### Appendix A: Database Schema SQL

See Section 3.2 for complete PostgreSQL schema.

### Appendix B: Configuration Files

**learning.json** (existing):
```json
{
  "enabled": true,
  "learningRate": 0.1,
  "discountFactor": 0.95,
  "explorationRate": 0.2,
  "explorationDecay": 0.995,
  "minExplorationRate": 0.01,
  "targetImprovement": 0.2,
  "maxMemorySize": 104857600,
  "batchSize": 32,
  "updateFrequency": 10,
  "replayBufferSize": 10000
}
```

**Recommended additions**:
```json
{
  "enabled": true,
  "qLearning": {
    "learningRate": 0.1,
    "discountFactor": 0.95,
    "epsilonStrategy": "reward_based",
    "initialEpsilon": 0.2,
    "minEpsilon": 0.01,
    "epsilonDecay": 0.995,
    "targetReward": 50.0
  },
  "experienceReplay": {
    "enabled": true,
    "bufferSize": 10000,
    "batchSize": 32,
    "prioritized": true,
    "alpha": 0.6,
    "beta": 0.4,
    "betaIncrement": 0.001
  },
  "hierarchicalLearning": {
    "enabled": true,
    "individualWeight": 1.0,
    "categoryWeight": 0.7,
    "fleetWeight": 0.5,
    "aggregationInterval": 300
  },
  "transferLearning": {
    "enabled": true,
    "minConfidence": 0.7,
    "decayFactor": 0.8
  },
  "convergence": {
    "checkInterval": 3600,
    "qValueChangeThreshold": 0.01,
    "rewardVarianceThreshold": 5.0,
    "minSuccessRate": 0.85,
    "minExplorationRate": 0.05
  },
  "production": {
    "abTesting": true,
    "trafficSplit": 0.5,
    "minSamples": 100,
    "confidenceLevel": 0.95,
    "snapshotInterval": 3600,
    "rollbackThreshold": 0.10
  },
  "teamLearning": {
    "enabled": true,
    "syncInterval": 3600,
    "pushThreshold": 0.7,
    "conflictResolution": "highest_confidence",
    "privacyMode": "differential",
    "dpEpsilon": 1.0
  }
}
```

### Appendix C: Deployment Checklist

**Pre-Production**:
- [ ] Initialize PostgreSQL schema
- [ ] Create Q-tables for all 18 agents
- [ ] Load baseline Q-values (if available)
- [ ] Configure epsilon decay strategy
- [ ] Set up monitoring dashboards
- [ ] Create policy snapshots for rollback
- [ ] Configure A/B testing framework

**Production Rollout**:
- [ ] Start with 10% traffic to learned policies
- [ ] Monitor convergence metrics hourly
- [ ] Check for performance degradation
- [ ] Gradually increase traffic to 50%
- [ ] Run A/B test for 24-48 hours
- [ ] Analyze statistical significance
- [ ] Decision: full rollout or rollback

**Post-Production**:
- [ ] Continue monitoring convergence
- [ ] Sync local Q-tables to central repository
- [ ] Export learned patterns for transfer learning
- [ ] Document successful strategies
- [ ] Update team on learned best practices

---

## Conclusion

This research report provides comprehensive, research-backed recommendations for implementing Q-learning across the LionAGI QE Fleet's 18 specialized agents. Key takeaways:

1. **Hybrid Hierarchical Q-Tables**: Individual agent Q-tables with category and fleet-level aggregation for knowledge sharing and transfer learning

2. **Agent-Specific State/Action/Reward Design**: Tailored state spaces, action sets, and multi-objective reward functions for each agent type

3. **PostgreSQL with Optimistic Locking**: Efficient concurrent Q-value updates using MVCC and row-level locking

4. **Production-Ready Monitoring**: Real-time convergence tracking, A/B testing, and automated rollback capabilities

5. **Team-Wide Learning**: Centralized Q-table repository with conflict resolution and privacy-preserving synchronization

The implementation should follow an iterative approach:
- **Phase 1**: Core infrastructure (database schema, Q-table manager, reward calculator)
- **Phase 2**: Single agent pilot (test-generator) with full learning loop
- **Phase 3**: Expand to 5 core agents with hierarchical aggregation
- **Phase 4**: Production deployment with A/B testing and monitoring
- **Phase 5**: All 18 agents with team-wide learning coordination

By following these research-backed best practices, the QE Fleet can achieve continuous improvement through reinforcement learning while maintaining production stability and enabling knowledge sharing across the development team.
