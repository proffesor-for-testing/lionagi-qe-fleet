# Phase 1 Test Architecture Diagram

## Test Pyramid Structure

```
                    ┌───────────────────────────┐
                    │   Performance Tests       │
                    │   (5 scenarios)           │
                    │   Load: locust, k6        │
                    │   60s duration            │
                    └───────────────────────────┘
                              ▲
                              │
          ┌───────────────────┴───────────────────┐
          │     Integration Tests (30)            │
          │     API → Storage, Queue, WebSocket   │
          │     2-5 min execution time            │
          └───────────────────────────────────────┘
                          ▲
                          │
      ┌───────────────────┴───────────────────────────┐
      │         API Tests (40)                        │
      │         Endpoint + Contract Testing           │
      │         <1 min execution, 100% coverage       │
      └───────────────────────────────────────────────┘
                          ▲
                          │
┌─────────────────────────┴─────────────────────────────────┐
│              Unit Tests (150)                             │
│   MCP Server | MCP Tools | Storage | Base Agent          │
│   <30s execution, 85-95% coverage per module             │
└───────────────────────────────────────────────────────────┘
```

## Test Layer Details

### Layer 1: Unit Tests (Foundation)
```
┌─────────────────────────────────────────────────────────┐
│ Unit Tests (150 tests, <30s)                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ MCP Server   │  │  MCP Tools   │  │   Storage    │ │
│  │  (25 tests)  │  │  (40 tests)  │  │  (45 tests)  │ │
│  │   95% cov    │  │   90% cov    │  │   85% cov    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │ Base Agent   │  │     Core     │                    │
│  │  (30 tests)  │  │  (10 tests)  │                    │
│  │   95% cov    │  │   90% cov    │                    │
│  └──────────────┘  └──────────────┘                    │
│                                                         │
│  Characteristics:                                       │
│  • Fast execution (<30s total)                          │
│  • Isolated (no external dependencies)                  │
│  • High coverage (85-95%)                               │
│  • Mock all external services                           │
└─────────────────────────────────────────────────────────┘
```

### Layer 2: API Tests
```
┌─────────────────────────────────────────────────────────┐
│ API Tests (40 tests, <1 min)                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Endpoint Tests (32)                              │  │
│  │ • POST /tools/test_generate                      │  │
│  │ • POST /tools/test_execute                       │  │
│  │ • POST /tools/coverage_analyze                   │  │
│  │ • POST /tools/quality_gate                       │  │
│  │ • POST /tools/performance_test                   │  │
│  │ • POST /tools/security_scan                      │  │
│  │ • POST /tools/fleet_orchestrate                  │  │
│  │ • GET  /tools/get_fleet_status                   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Contract Tests (10)                              │  │
│  │ • test_generate contract (Pact)                  │  │
│  │ • test_execute contract                          │  │
│  │ • coverage_analyze contract                      │  │
│  │ • quality_gate contract                          │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Characteristics:                                       │
│  • 100% endpoint coverage                               │
│  • Request/response validation                          │
│  • Authentication testing                               │
│  • Consumer-driven contracts                            │
└─────────────────────────────────────────────────────────┘
```

### Layer 3: Integration Tests
```
┌─────────────────────────────────────────────────────────┐
│ Integration Tests (30 tests, 2-5 min)                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ MCP Server Integration (10 tests)                 │ │
│  │ • Full lifecycle (start → execute → stop)         │ │
│  │ • Tool execution end-to-end                       │ │
│  │ • Fleet coordination via MCP                      │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ API → Storage Integration (8 tests)               │ │
│  │ • Test generation → Redis storage                 │ │
│  │ • Coverage analysis → PostgreSQL storage          │ │
│  │ • Cross-agent memory sharing                      │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Queue Integration (6 tests)                       │ │
│  │ • Celery + Redis broker                           │ │
│  │ • Async task processing                           │ │
│  │ • Task retry on failure                           │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ WebSocket Streaming (4 tests)                     │ │
│  │ • Test execution real-time streaming              │ │
│  │ • Coverage analysis real-time streaming           │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  Characteristics:                                       │
│  • Real backend integration                             │
│  • Multi-component workflows                            │
│  • Critical path coverage: 100%                         │
│  • Requires: PostgreSQL, Redis, Celery                  │
└─────────────────────────────────────────────────────────┘
```

### Layer 4: Performance Tests
```
┌─────────────────────────────────────────────────────────┐
│ Performance Tests (5 scenarios, 60s each)              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Locust Tests (3 scenarios)                        │ │
│  │ • Test generation load                            │ │
│  │ • Coverage analysis load                          │ │
│  │ • Fleet orchestration load                        │ │
│  │                                                   │ │
│  │ Virtual Users: 10 → 50 → 100                      │ │
│  │ Duration: 60 seconds                              │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ k6 Tests (2 scenarios)                            │ │
│  │ • Test generation throughput                      │ │
│  │ • API endpoint latency                            │ │
│  │                                                   │ │
│  │ Virtual Users: 10 → 50 → 100                      │ │
│  │ Duration: 60 seconds                              │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  Thresholds:                                            │
│  • Response time P95: <500ms                            │
│  • Error rate: <1%                                      │
│  • Throughput: Meet baseline requirements               │
│                                                         │
│  Characteristics:                                       │
│  • Measure scalability                                  │
│  • Identify bottlenecks                                 │
│  • Validate performance requirements                    │
│  • Establish baseline metrics                           │
└─────────────────────────────────────────────────────────┘
```

## Test Data Flow

```
┌──────────────────────────────────────────────────────────┐
│                    Test Execution Flow                   │
└──────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │   pytest    │
    │   Runner    │
    └──────┬──────┘
           │
           ├─────────────────┐
           ▼                 ▼
    ┌─────────────┐   ┌─────────────┐
    │ Unit Tests  │   │Integration  │
    │  (Layer 1)  │   │    Tests    │
    └──────┬──────┘   │  (Layer 3)  │
           │          └──────┬──────┘
           │                 │
           │          ┌──────▼──────────────┐
           │          │  Real Backends:     │
           │          │  • PostgreSQL       │
           │          │  • Redis            │
           │          │  • Celery           │
           │          └─────────────────────┘
           │
           ├─────────────────┐
           ▼                 ▼
    ┌─────────────┐   ┌─────────────┐
    │  API Tests  │   │Performance  │
    │  (Layer 2)  │   │    Tests    │
    └──────┬──────┘   │  (Layer 4)  │
           │          └─────────────┘
           │
           ▼
    ┌─────────────┐
    │  Coverage   │
    │   Report    │
    │  (85%+)     │
    └─────────────┘
```

## Test Priority Matrix

```
┌──────────────────────────────────────────────────────────┐
│              Test Priority Matrix                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  HIGH IMPACT │  P0: MCP Server Init        │  P1: Tool  │
│              │      Fleet Setup            │      Error │
│              │      Tool Registration      │      Handle│
│  ────────────┼─────────────────────────────┼───────────│
│              │  P2: Streaming Tools        │  P1: Store │
│  LOW IMPACT  │      WebSocket Integration  │      Backend│
│              │      Advanced Tools         │      Tests │
│                                                          │
│              └─────────────┬─────────────────────────────┘
│                    LOW         HIGH
│                   FREQUENCY   FREQUENCY
└──────────────────────────────────────────────────────────┘

Priority Breakdown:
• P0 (Critical): 7 test categories - MUST PASS before release
• P1 (High): 7 test categories - Required for stability
• P2 (Medium): 6 test categories - Nice to have, lower risk
```

## Coverage Heatmap

```
┌─────────────────────────────────────────────────────────┐
│               Coverage Heatmap (Target vs Actual)        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Component          Target    Critical Paths           │
│  ─────────────────────────────────────────────────     │
│  MCP Server         ████████████████░ 95%    █ 100%    │
│  MCP Tools          █████████████░░░ 90%    █ 100%    │
│  Base Agent         ████████████████░ 95%    █ 100%    │
│  Storage (Redis)    ██████████████░░░ 85%    █ 100%    │
│  Storage (Postgres) ██████████████░░░ 85%    █ 100%    │
│  Test Generator     █████████████░░░░ 90%    █ 100%    │
│  Test Executor      █████████████░░░░ 90%    █ 100%    │
│  Coverage Analyzer  █████████████░░░░ 90%    █ 100%    │
│  Fleet Commander    ██████████████░░░ 85%    █ 100%    │
│  Authentication     █████████████████ 100%   █ 100%    │
│  API Endpoints      █████████████████ 100%   █ 100%    │
│                                                         │
│  Legend: █ Covered  ░ Not Covered                       │
│  Target: 85% overall, 100% critical paths               │
└─────────────────────────────────────────────────────────┘
```

## Test Execution Timeline

```
Week 1 (Foundation - P0)
┌─────────────────────────────────────────────────────────┐
│ Mon   Tue   Wed   Thu   Fri                             │
│ ├─────┼─────┼─────┼─────┼─────                          │
│ │MCP  │MCP  │Redis│Base │Review                         │
│ │Srv  │Tools│Mem  │Agent│& Fix                          │
│ │Init │Core │     │     │                               │
│ └─────┴─────┴─────┴─────┴─────                          │
│ Tests: 75 | Coverage: P0 critical paths                 │
└─────────────────────────────────────────────────────────┘

Week 2 (Core Functionality - P0-P1)
┌─────────────────────────────────────────────────────────┐
│ Mon   Tue   Wed   Thu   Fri                             │
│ ├─────┼─────┼─────┼─────┼─────                          │
│ │Test │Test │Cov  │API  │Review                         │
│ │Gen  │Exec │Analy│Store│& Fix                          │
│ │     │     │     │Integ│                               │
│ └─────┴─────┴─────┴─────┴─────                          │
│ Tests: 60 | Coverage: Core tools 100%                   │
└─────────────────────────────────────────────────────────┘

Week 3 (Advanced Features - P1-P2)
┌─────────────────────────────────────────────────────────┐
│ Mon   Tue   Wed   Thu   Fri                             │
│ ├─────┼─────┼─────┼─────┼─────                          │
│ │Stream│WS  │Queue│API  │Review                         │
│ │Tools │Integ│Integ│Tests│& Fix                          │
│ │     │     │     │     │                               │
│ └─────┴─────┴─────┴─────┴─────                          │
│ Tests: 50 | Coverage: Integration paths                 │
└─────────────────────────────────────────────────────────┘

Week 4 (Load & Contract - P2)
┌─────────────────────────────────────────────────────────┐
│ Mon   Tue   Wed   Thu   Fri                             │
│ ├─────┼─────┼─────┼─────┼─────                          │
│ │Locust│k6  │Pact │Mutat│Final                          │
│ │Load │Load │Contr│Test │Review                         │
│ │     │     │     │     │                               │
│ └─────┴─────┴─────┴─────┴─────                          │
│ Tests: 25 | Coverage: Performance & quality validation  │
└─────────────────────────────────────────────────────────┘
```

## Test Frameworks Integration

```
┌──────────────────────────────────────────────────────────┐
│              Test Framework Stack                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │              pytest Core                           │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │ │
│  │  │pytest-   │  │pytest-   │  │pytest-   │        │ │
│  │  │asyncio   │  │cov       │  │mock      │        │ │
│  │  └──────────┘  └──────────┘  └──────────┘        │ │
│  └────────────────────────────────────────────────────┘ │
│                        ▼                                 │
│  ┌────────────────────────────────────────────────────┐ │
│  │           Testing Extensions                       │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │ │
│  │  │hypothesis│  │coverage  │  │httpx     │        │ │
│  │  │(property)│  │(reports) │  │(API)     │        │ │
│  │  └──────────┘  └──────────┘  └──────────┘        │ │
│  └────────────────────────────────────────────────────┘ │
│                        ▼                                 │
│  ┌────────────────────────────────────────────────────┐ │
│  │        Performance & Contract Testing              │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │ │
│  │  │locust    │  │k6        │  │pact-     │        │ │
│  │  │(load)    │  │(load)    │  │python    │        │ │
│  │  └──────────┘  └──────────┘  └──────────┘        │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

**Diagram Version**: 1.0
**Generated**: 2025-11-12
**Purpose**: Visual reference for Phase 1 test architecture
