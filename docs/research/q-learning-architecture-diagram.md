# Q-Learning Architecture Diagrams

Visual representations of the Q-Learning implementation for multi-agent QE systems.

---

## 1. Hierarchical Q-Table Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Fleet Commander Q-Table                       │
│                                                                   │
│  Aggregated coordination policies across all agent categories   │
│  • Task decomposition strategies                                │
│  • Agent assignment patterns                                    │
│  • Resource allocation decisions                                │
│                                                                   │
│  State: (task_complexity, available_agents, deadline, ...)      │
│  Actions: [sequential, parallel, hierarchical, hybrid]          │
│  Updates: Weighted average from categories (α = 0.05)           │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Aggregates (weighted)
        ┌─────────────────────┼─────────────────────┬─────────────┐
        │                     │                     │             │
        ▼                     ▼                     ▼             ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Core Testing │    │ Performance  │    │  Advanced    │    │ Specialized  │
│   Q-Table    │    │  & Security  │    │   Testing    │    │   Q-Table    │
│              │    │   Q-Table    │    │   Q-Table    │    │              │
│ 6 agents     │    │ 2 agents     │    │ 4 agents     │    │ 3 agents     │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
        ▲                     ▲                     ▲             ▲
        │                     │                     │             │
   Aggregates (α=0.1)    Aggregates           Aggregates     Aggregates
        │                     │                     │             │
┌───────┴────┬────┬───┐      │          ┌──────────┴───┬────┐   │
│            │    │   │      │          │              │    │   │
▼            ▼    ▼   ▼      ▼          ▼              ▼    ▼   ▼
Agent1-Q  Agent2-Q ... ...  Agent-Q   Agent-Q       Agent-Q ... Agent-Q
test-gen  test-exec     ...  perf      regress-risk  deploy      visual
```

**Legend**:
- **Fleet Q-Table**: High-level coordination patterns
- **Category Q-Tables**: Shared patterns within agent groups
- **Individual Q-Tables**: Agent-specific learned policies
- **α (alpha)**: Weight for exponential moving average updates

---

## 2. Q-Learning Loop Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    START: New Task Arrives                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Extract State  │
                    │                 │
                    │ • Code metrics  │
                    │ • Coverage gaps │
                    │ • Context info  │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Get ε (epsilon) │
                    │                 │
                    │ Reward-based    │
                    │ decay strategy  │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Select Action  │
                    │                 │
                    │ If rand < ε:    │
                    │   → Explore     │◄──────┐
                    │ Else:           │       │
                    │   → Exploit     │       │
                    └─────────────────┘       │
                              │               │
                              ▼               │
                    ┌─────────────────┐       │
                    │ Execute Action  │       │
                    │                 │       │
                    │ Run agent logic │       │
                    │ Get result      │       │
                    └─────────────────┘       │
                              │               │
                              ▼               │
                    ┌─────────────────┐       │
                    │  Get Next State │       │
                    │                 │       │
                    │ Extract from    │       │
                    │ action result   │       │
                    └─────────────────┘       │
                              │               │
                              ▼               │
                    ┌─────────────────┐       │
                    │ Calculate Reward│       │
                    │                 │       │
                    │ • Coverage gain │       │
                    │ • Bugs found    │       │
                    │ • Speed/cost    │       │
                    └─────────────────┘       │
                              │               │
                              ▼               │
                    ┌─────────────────┐       │
                    │  Update Q-Value │       │
                    │                 │       │
                    │ Q(s,a) ← Q(s,a) │       │
                    │  + α[r + γ·max  │       │
                    │     Q(s',a')-Q] │       │
                    └─────────────────┘       │
                              │               │
                              ▼               │
                    ┌─────────────────┐       │
                    │Store Experience │       │
                    │                 │       │
                    │ Replay buffer   │       │
                    │ (s,a,r,s')      │       │
                    └─────────────────┘       │
                              │               │
                              ▼               │
                    ┌─────────────────┐       │
                    │ Episode Done?   │       │
                    └─────────────────┘       │
                          │       │           │
                       No │       │ Yes       │
                          └───────┘           │
                                              │
                              ┌───────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Return Result  │
                    │                 │
                    │ • Episode stats │
                    │ • Total reward  │
                    │ • Learning data │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Background:    │
                    │ Experience      │
                    │ Replay Training │
                    └─────────────────┘
```

---

## 3. PostgreSQL Schema Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         PostgreSQL Database                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐                                            │
│  │    q_tables     │  Metadata for Q-tables                     │
│  ├─────────────────┤                                            │
│  │ id (PK)         │  UUID                                       │
│  │ agent_id        │  "test-generator", "coverage-analyzer"...  │
│  │ scope           │  'individual', 'category', 'fleet'         │
│  │ state_dims      │  JSONB - state dimensions                  │
│  │ action_space    │  JSONB - available actions                 │
│  │ total_updates   │  Integer - update counter                  │
│  └─────────────────┘                                            │
│           │                                                       │
│           │ 1:N relationship                                     │
│           ▼                                                       │
│  ┌─────────────────┐                                            │
│  │    q_values     │  State-action-value pairs                  │
│  ├─────────────────┤                                            │
│  │ id (PK)         │  BIGSERIAL                                 │
│  │ q_table_id (FK) │  → q_tables.id                             │
│  │ state_hash      │  SHA256 for fast lookup                    │
│  │ state_data      │  JSONB - full state                        │
│  │ action          │  VARCHAR - action name                     │
│  │ q_value         │  FLOAT - learned Q-value                   │
│  │ visit_count     │  INTEGER - times visited                   │
│  │ confidence      │  FLOAT - confidence score                  │
│  │ version         │  INTEGER - optimistic lock                 │
│  └─────────────────┘                                            │
│       │                                                           │
│       │ Indexed by (q_table_id, state_hash, action)             │
│       │                                                           │
│  ┌─────────────────────────┐                                    │
│  │ learning_experiences    │  Experience replay buffer          │
│  ├─────────────────────────┤                                    │
│  │ id (PK)                 │  BIGSERIAL                         │
│  │ q_table_id (FK)         │  → q_tables.id                     │
│  │ state_hash              │  SHA256                            │
│  │ state_data              │  JSONB                             │
│  │ action                  │  VARCHAR                           │
│  │ reward                  │  FLOAT                             │
│  │ next_state_hash         │  SHA256                            │
│  │ next_state_data         │  JSONB                             │
│  │ priority                │  FLOAT - for prioritized replay    │
│  │ expires_at              │  TIMESTAMP - TTL                   │
│  └─────────────────────────┘                                    │
│       │                                                           │
│       │ Indexed by (q_table_id, priority DESC, timestamp DESC)  │
│       │                                                           │
│  ┌─────────────────┐                                            │
│  │ learning_stats  │  Convergence monitoring                    │
│  ├─────────────────┤                                            │
│  │ id (PK)         │  BIGSERIAL                                 │
│  │ q_table_id (FK) │  → q_tables.id                             │
│  │ window_start    │  TIMESTAMP                                 │
│  │ window_end      │  TIMESTAMP                                 │
│  │ avg_reward      │  FLOAT                                     │
│  │ std_reward      │  FLOAT                                     │
│  │ avg_q_change    │  FLOAT - convergence metric                │
│  │ success_rate    │  FLOAT                                     │
│  │ exploration_rate│  FLOAT                                     │
│  └─────────────────┘                                            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Concurrent Update Flow (Optimistic Locking)

```
Agent 1                          PostgreSQL                        Agent 2
   │                                 │                                 │
   │  SELECT ... FOR UPDATE          │                                 │
   ├────────────────────────────────►│                                 │
   │                                 │                                 │
   │  ◄─ Row locked (version=5)     │                                 │
   │                                 │                                 │
   │                                 │  SELECT ... FOR UPDATE          │
   │                                 │◄────────────────────────────────┤
   │                                 │                                 │
   │                                 │  ⏸ WAITING (row locked)         │
   │                                 │                                 │
   │  UPDATE ... WHERE version=5     │                                 │
   ├────────────────────────────────►│                                 │
   │                                 │                                 │
   │  ◄─ SUCCESS (version→6)         │                                 │
   │                                 │                                 │
   │  COMMIT                         │                                 │
   ├────────────────────────────────►│                                 │
   │                                 │                                 │
   │                                 │  ▶ RESUME                       │
   │                                 │                                 │
   │                                 │  ◄─ Row locked (version=6)      │
   │                                 │                                 │
   │                                 │  UPDATE ... WHERE version=6     │
   │                                 │◄────────────────────────────────┤
   │                                 │                                 │
   │                                 │  ─► SUCCESS (version→7)         │
   │                                 │                                 │
   │                                 │  COMMIT                         │
   │                                 │◄────────────────────────────────┤
   │                                 │                                 │
```

**Benefits**:
- No lost updates (optimistic lock prevents)
- High concurrency (MVCC allows parallel reads)
- Automatic retry on conflict
- Version tracking for debugging

---

## 5. Team-Wide Learning Flow

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  Developer 1 │         │  Developer 2 │         │  CI Pipeline │
│              │         │              │         │              │
│  Local Q-    │         │  Local Q-    │         │  Local Q-    │
│  Table       │         │  Table       │         │  Table       │
└──────┬───────┘         └──────┬───────┘         └──────┬───────┘
       │                        │                        │
       │ Push high-confidence   │                        │
       │ Q-values (conf > 0.7)  │                        │
       │                        │                        │
       ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Central PostgreSQL Repository                  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Fleet Q-Table (Shared Knowledge)              │ │
│  │                                                            │ │
│  │  State-Action pairs with:                                 │ │
│  │  • Q-value (weighted average from contributors)           │ │
│  │  • Confidence score (combined from all sources)           │ │
│  │  • Visit count (total across all agents)                  │ │
│  │  • Last updated timestamp                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Conflict Resolution:                                            │
│  • Multiple updates → Use highest confidence value              │
│  • Similar confidence → Weighted average                        │
│  • Track contributor metadata                                   │
└─────────────────────────────────────────────────────────────────┘
       │                        │                        │
       │ Pull updates (hourly)  │                        │
       │                        │                        │
       ▼                        ▼                        ▼
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  Developer 1 │         │  Developer 2 │         │  CI Pipeline │
│              │         │              │         │              │
│  Synced Q-   │         │  Synced Q-   │         │  Synced Q-   │
│  Table       │         │  Table       │         │  Table       │
└──────────────┘         └──────────────┘         └──────────────┘
```

**Privacy Protection**:
- State anonymization (hash sensitive fields)
- Differential privacy (ε = 1.0 Laplace noise)
- Optional local-only mode
- Audit logs for all sync operations

---

## 6. A/B Testing and Rollback

```
                    ┌──────────────────────────┐
                    │  New Task Arrives        │
                    └──────────────────────────┘
                                │
                                ▼
                    ┌──────────────────────────┐
                    │  A/B Test Active?        │
                    └──────────────────────────┘
                          │           │
                       No │           │ Yes
                          │           │
                          │           ▼
                          │   ┌──────────────────┐
                          │   │ Random Assignment│
                          │   │   50% / 50%      │
                          │   └──────────────────┘
                          │           │
                          │      ┌────┴────┐
                          │      │         │
                          ▼      ▼         ▼
                    ┌──────────────┐  ┌──────────────┐
                    │  Variant A   │  │  Variant B   │
                    │  (Baseline)  │  │  (Learned)   │
                    │              │  │              │
                    │ • Random     │  │ • Q-Learning │
                    │ • Rule-based │  │ • Optimized  │
                    └──────────────┘  └──────────────┘
                          │                  │
                          │                  │
                          ▼                  ▼
                    ┌──────────────────────────┐
                    │  Record Metrics          │
                    │                          │
                    │ • Success rate           │
                    │ • Coverage improvement   │
                    │ • Execution time         │
                    │ • Bug detection          │
                    └──────────────────────────┘
                                │
                                ▼
                    ┌──────────────────────────┐
                    │  Sufficient Data?        │
                    │  (N >= 100 per variant)  │
                    └──────────────────────────┘
                          │           │
                       No │           │ Yes
                          │           │
                          │           ▼
                          │   ┌──────────────────────┐
                          │   │ Statistical Analysis │
                          │   │                      │
                          │   │ • T-test (p < 0.05)  │
                          │   │ • Cohen's d > 0.2    │
                          │   │ • Effect size        │
                          │   └──────────────────────┘
                          │           │
                          │           ▼
                          │   ┌──────────────────────┐
                          │   │  Winner?             │
                          │   └──────────────────────┘
                          │       │         │
                          │    B wins    No winner
                          │       │         │
                          │       ▼         ▼
                          │   Deploy B   Keep A
                          │
                          ▼
                    Continue Test
                          │
                          │
      ┌───────────────────┴────────────────────┐
      │  Performance Monitoring                │
      │                                         │
      │  If degradation detected:               │
      │  • Success rate drops > 10%            │
      │  • Reward drops > 15 points            │
      │                                         │
      │        ▼                                │
      │  ┌──────────────────────┐              │
      │  │  ROLLBACK TRIGGERED  │              │
      │  └──────────────────────┘              │
      │        │                                │
      │        ▼                                │
      │  ┌──────────────────────┐              │
      │  │ Restore from Snapshot│              │
      │  │ (Created hourly)     │              │
      │  └──────────────────────┘              │
      │        │                                │
      │        ▼                                │
      │  ┌──────────────────────┐              │
      │  │ Notify Team          │              │
      │  │ Log Rollback Event   │              │
      │  └──────────────────────┘              │
      └─────────────────────────────────────────┘
```

---

## 7. Convergence Monitoring Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│                     Q-Learning Dashboard                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Agent: test-generator                     Status: ✓ Converged   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                                                   │
│  Convergence Criteria:                                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Q-Value Stability    [████████████████] ✓ < 0.01 change   │  │
│  │ Reward Variance      [████████████████] ✓ < 5.0 std       │  │
│  │ Success Rate         [███████████████ ] ✓ > 85%           │  │
│  │ Exploration Rate     [████████████████] ✓ < 0.05          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Learning Progress:                                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Episodes:          1,243                                   │  │
│  │ Total Updates:     45,892                                  │  │
│  │ Avg Reward:        67.3                                    │  │
│  │ Current Epsilon:   0.03                                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Q-Value Distribution:                                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │     │                                                       │  │
│  │ 100 │                              ▄▄▄▄                    │  │
│  │  80 │                          ▄▄▄▄████▄▄                  │  │
│  │  60 │                      ▄▄▄▄████████████                │  │
│  │  40 │                  ▄▄▄▄████████████████▄▄              │  │
│  │  20 │              ▄▄▄▄████████████████████████            │  │
│  │   0 └─────────────────────────────────────────────►        │  │
│  │      -50  -25    0   25   50   75  100  125  150          │  │
│  │                     Q-Value Range                          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Recent Performance (Last 24 hours):                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Reward Trend:                                              │  │
│  │  80 │                                            ▄▄▄       │  │
│  │  60 │                                    ▄▄▄▄▄▄▄███       │  │
│  │  40 │                        ▄▄▄▄▄▄▄▄▄▄▄███████████       │  │
│  │  20 │            ▄▄▄▄▄▄▄▄▄▄▄▄███████████████████████       │  │
│  │   0 └──────────────────────────────────────────────►      │  │
│  │      0h   4h   8h  12h  16h  20h  24h                      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  [Snapshot Policy] [Export Q-Table] [View Details] [Settings]   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Transfer Learning Between Similar Agents

```
┌─────────────────────────────────────────────────────────────────┐
│                    Transfer Learning Groups                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Group 1: Test Generation                                        │
│  ┌────────────────────┐              ┌────────────────────┐     │
│  │  test-generator    │◄────────────►│ test-data-architect│     │
│  │                    │  Knowledge   │                    │     │
│  │ Q-Table (5K pairs) │  Transfer    │ Q-Table (3K pairs) │     │
│  └────────────────────┘              └────────────────────┘     │
│                                                                   │
│  Shared Patterns:                                                │
│  • Property-based test strategies                                │
│  • Edge case detection heuristics                                │
│  • Test data generation approaches                               │
│                                                                   │
│  Transfer Rate: 847 Q-values (confidence > 0.7)                  │
│  Success Rate: 92% of transferred patterns successful            │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Group 2: Test Execution                                         │
│  ┌────────────────────┐              ┌────────────────────┐     │
│  │  test-executor     │◄────────────►│regression-risk     │     │
│  │                    │  Knowledge   │   -analyzer        │     │
│  │ Q-Table (4K pairs) │  Transfer    │ Q-Table (2K pairs) │     │
│  └────────────────────┘              └────────────────────┘     │
│                                                                   │
│  Shared Patterns:                                                │
│  • Parallelization strategies                                    │
│  • Test selection heuristics                                     │
│  • Retry and timeout policies                                    │
│                                                                   │
│  Transfer Rate: 623 Q-values                                     │
│  Success Rate: 88%                                               │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Group 3: Coverage Analysis                                      │
│  ┌────────────────────┐              ┌────────────────────┐     │
│  │ coverage-analyzer  │◄────────────►│   quality-gate     │     │
│  │                    │  Knowledge   │                    │     │
│  │ Q-Table (3K pairs) │  Transfer    │ Q-Table (2K pairs) │     │
│  └────────────────────┘              └────────────────────┘     │
│                                                                   │
│  Shared Patterns:                                                │
│  • Gap prioritization algorithms                                 │
│  • Threshold adjustment strategies                               │
│  • Risk assessment methods                                       │
│                                                                   │
│  Transfer Rate: 456 Q-values                                     │
│  Success Rate: 90%                                               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Complete System Integration

```
┌───────────────────────────────────────────────────────────────────┐
│                      LionAGI QE Fleet System                       │
├───────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    User / CI Pipeline                        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                   Fleet Commander                            │  │
│  │                                                              │  │
│  │  • Task decomposition using Q-Learning                       │  │
│  │  • Agent assignment optimization                             │  │
│  │  • Workflow orchestration                                    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│                    ┌─────────┼─────────┐                          │
│                    ▼         ▼         ▼                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │  Core    │  │  Perf &  │  │ Advanced │  │Specialized│         │
│  │ Testing  │  │ Security │  │  Testing │  │          │         │
│  │          │  │          │  │          │  │          │         │
│  │ 6 agents │  │ 2 agents │  │ 4 agents │  │ 3 agents │         │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
│       │             │              │             │                │
│       │   Each agent has:          │             │                │
│       │   • Individual Q-table     │             │                │
│       │   • Learning loop          │             │                │
│       │   • Experience replay      │             │                │
│       │   • Epsilon-greedy policy  │             │                │
│       │                            │             │                │
│       └────────────┬───────────────┴─────────────┘                │
│                    │                                               │
│                    ▼                                               │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              Q-Learning Infrastructure                       │  │
│  │                                                              │  │
│  │  ┌─────────────────┐  ┌─────────────────┐                  │  │
│  │  │ Hierarchical    │  │ Reward          │                  │  │
│  │  │ Q-Table Manager │  │ Calculator      │                  │  │
│  │  └─────────────────┘  └─────────────────┘                  │  │
│  │                                                              │  │
│  │  ┌─────────────────┐  ┌─────────────────┐                  │  │
│  │  │ Experience      │  │ Epsilon Decay   │                  │  │
│  │  │ Replay Buffer   │  │ Strategy        │                  │  │
│  │  └─────────────────┘  └─────────────────┘                  │  │
│  │                                                              │  │
│  │  ┌─────────────────┐  ┌─────────────────┐                  │  │
│  │  │ Transfer        │  │ Team Learning   │                  │  │
│  │  │ Learning Mgr    │  │ Coordinator     │                  │  │
│  │  └─────────────────┘  └─────────────────┘                  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                    │                                               │
│                    ▼                                               │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                 PostgreSQL Storage                           │  │
│  │                                                              │  │
│  │  • q_tables          • learning_stats                       │  │
│  │  • q_values          • ab_tests                             │  │
│  │  • learning_experiences  • snapshots                        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                    │                                               │
│                    ▼                                               │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │               Production Monitoring                          │  │
│  │                                                              │  │
│  │  • Convergence Dashboard    • Performance Monitoring        │  │
│  │  • A/B Testing Framework    • Rollback Manager              │  │
│  │  • Cost Tracking            • Alert System                  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└───────────────────────────────────────────────────────────────────┘
```

---

## Key Takeaways

1. **Hierarchical Structure**: Individual → Category → Fleet Q-tables enable knowledge sharing while maintaining agent autonomy

2. **Optimistic Locking**: PostgreSQL MVCC + version field prevents lost updates with high concurrency

3. **Experience Replay**: Circular buffer stores (s, a, r, s') tuples for offline training

4. **Transfer Learning**: Similar agents share high-confidence Q-values with decay factor

5. **Production Safety**: A/B testing, monitoring, and automatic rollback protect against degradation

6. **Team Coordination**: Central repository enables knowledge sharing across developers and CI runs

7. **Privacy-Preserving**: Differential privacy and state anonymization protect sensitive information

---

**For Implementation Details**: See [q-learning-best-practices.md](./q-learning-best-practices.md)
**For Quick Reference**: See [q-learning-summary.md](./q-learning-summary.md)
