# Chaos Engineering & Resilience Testing Strategy - Phase 1

**Version:** 1.0.0
**Date:** 2025-11-12
**Agent:** qe-chaos-engineer
**Status:** ✅ Ready for Execution

## Executive Summary

This document outlines the comprehensive chaos engineering and resilience testing strategy for LionAGI QE Fleet Phase 1. The strategy validates system resilience through controlled fault injection across critical infrastructure components: Redis, PostgreSQL, storage backends (S3/filesystem), network connectivity, and resource management.

**Key Outcomes:**
- ✅ 3 Chaos Toolkit experiments (Redis, PostgreSQL, Storage)
- ✅ 10+ Toxiproxy network chaos scenarios
- ✅ 6 Python resilience test suites (100+ test cases)
- ✅ Circuit breaker, retry, and fallback pattern validation
- ✅ Observability validation (logging, metrics, tracing, alerting)
- ✅ Runbooks and playbooks for common failure scenarios
- ✅ Automated chaos testing pipeline

## Scope

### In Scope - Phase 1 Components

1. **Redis (RedisMemory)**
   - Connection failures and timeouts
   - Connection pool exhaustion
   - Network partitions
   - Latency injection

2. **PostgreSQL (PostgresMemory)**
   - Connection pool exhaustion
   - Query timeouts
   - Transaction failures
   - Network partitions

3. **Storage Backends**
   - S3 connectivity failures
   - Filesystem permission errors
   - Disk space exhaustion
   - I/O errors

4. **Network Layer**
   - Latency injection (500ms - 5s)
   - Packet loss (5-20%)
   - Network partitions
   - Bandwidth limits

5. **Resource Management**
   - CPU exhaustion (90-95%)
   - Memory pressure (85%)
   - Disk exhaustion (95%)
   - File handle exhaustion

6. **Observability**
   - Error logging validation
   - Metrics collection (error rate, latency, throughput)
   - Distributed tracing
   - Alerting mechanisms

### Out of Scope - Future Phases

- Celery worker failures (Phase 2)
- Kubernetes orchestration chaos (Phase 2)
- Multi-region failover (Phase 3)
- Advanced chaos automation (Phase 3)

## Fault Injection Scenarios

### 1. Redis Connection Failures

**Hypothesis:** System maintains functionality when Redis becomes unavailable by falling back to Session.context.

**Fault Types:**
```bash
# Connection refused
iptables -A OUTPUT -p tcp --dport 6379 -j DROP

# Latency injection (Toxiproxy)
toxiproxy-cli toxic add redis --type=latency --attribute=latency=500

# Packet loss
toxiproxy-cli toxic add redis --type=slicer --toxicity=0.1

# Bandwidth limit
toxiproxy-cli toxic add redis --type=bandwidth --attribute=rate=100
```

**Expected Behavior:**
- ✅ Automatic fallback to Session.context (in-memory)
- ✅ Circuit breaker opens after 5 failures
- ✅ Retry with exponential backoff (1s, 2s, 4s)
- ✅ Recovery within 30 seconds
- ✅ Zero data loss

**Test Files:**
- `tests/chaos/chaostoolkit/redis-failure-experiment.json`
- `tests/chaos/resilience/test_redis_resilience.py`
- `tests/chaos/scenarios/redis-chaos-playbook.md`

### 2. PostgreSQL Connection Pool Exhaustion

**Hypothesis:** System degrades gracefully when database connection pool is exhausted, using queue-based buffering.

**Fault Injection:**
```python
# Exhaust connection pool (gradual)
async def exhaust_pool_gradually(max_connections=10, ramp_up_time=60):
    for i in range(max_connections * 2):
        await asyncio.sleep(ramp_up_time / (max_connections * 2))
        # Acquire connection and hold
```

**Expected Behavior:**
- ✅ Request queuing when pool full
- ✅ Circuit breaker prevents cascading failures
- ✅ Graceful degradation to read-only mode
- ✅ Error rate < 15% during exhaustion
- ✅ Recovery after connection release

**Test Files:**
- `tests/chaos/chaostoolkit/postgres-failure-experiment.json`
- `tests/chaos/resilience/test_postgres_resilience.py`

### 3. Storage Backend Failures

**Hypothesis:** System handles S3 and filesystem failures with automatic fallback and no data loss.

**Fault Types:**
```bash
# Block S3 endpoints
iptables -A OUTPUT -d s3.amazonaws.com -j DROP

# Filesystem permission denial
chmod 000 /tmp/lionagi_storage

# Disk space exhaustion
dd if=/dev/zero of=/tmp/fill_disk bs=1M count=10000
```

**Expected Behavior:**
- ✅ Automatic fallback: S3 → Local filesystem
- ✅ Retry with exponential backoff (max 3 attempts)
- ✅ No partial writes (atomic operations)
- ✅ Checksum verification for data integrity
- ✅ Circuit breaker per backend (independent)

**Test Files:**
- `tests/chaos/chaostoolkit/storage-failure-experiment.json`
- `tests/chaos/resilience/test_storage_resilience.py`

### 4. Network Latency & Packet Loss

**Hypothesis:** System tolerates network latency up to 1 second and 10% packet loss without significant impact.

**Toxiproxy Scenarios:**
```json
{
  "latency_500ms": {
    "type": "latency",
    "attributes": {"latency": 500, "jitter": 100}
  },
  "packet_loss_10pct": {
    "type": "slicer",
    "toxicity": 0.1
  },
  "bandwidth_100kb": {
    "type": "bandwidth",
    "attributes": {"rate": 100}
  }
}
```

**Expected Behavior:**
- ✅ P99 latency < 2 seconds
- ✅ Timeout mechanisms prevent indefinite waits
- ✅ Retransmission for packet loss
- ✅ No cascading failures

**Test Files:**
- `tests/chaos/toxiproxy/toxiproxy-config.json`
- `tests/chaos/resilience/test_network_resilience.py`

### 5. Resource Exhaustion

**Hypothesis:** System degrades gracefully under resource pressure with load shedding and prioritization.

**Fault Injection:**
```python
# CPU stress
def stress_cpu(target_percent=90, duration=300):
    # CPU-intensive loops to reach target

# Memory pressure
def allocate_memory(target_percent=85):
    # Allocate memory until threshold

# Disk exhaustion
dd if=/dev/zero of=/tmp/fill_disk bs=1M count=10000
```

**Expected Behavior:**
- ✅ Load shedding for non-critical requests (503 responses)
- ✅ Request prioritization (critical requests first)
- ✅ Cache eviction under memory pressure
- ✅ Log rotation under disk pressure
- ✅ Graceful degradation (features disabled)

**Test Files:**
- `tests/chaos/resilience/test_resource_exhaustion.py`

## Recovery Testing

### Automatic Recovery Mechanisms

1. **Circuit Breaker Pattern**
   - **Threshold:** 5 consecutive failures
   - **Timeout:** 30 seconds (half-open probe)
   - **Recovery:** Close after successful request

2. **Retry with Exponential Backoff**
   - **Initial delay:** 1 second
   - **Backoff factor:** 2x
   - **Max attempts:** 3
   - **Jitter:** ±200ms (prevent thundering herd)

3. **Fallback Mechanisms**
   - Redis → Session.context (in-memory)
   - S3 → Local filesystem
   - PostgreSQL → Read-only mode
   - Network → Cached responses

4. **Graceful Degradation**
   - Disable analytics under pressure
   - Disable background jobs
   - Prioritize critical requests
   - Load shedding (503 responses)

### Recovery Time SLAs

| Component | Recovery Target | Auto-Rollback Trigger |
|-----------|----------------|----------------------|
| Redis | < 30 seconds | Error rate > 5% |
| PostgreSQL | < 60 seconds | Error rate > 15% |
| Storage | < 30 seconds | Circuit breaker open |
| Network | < 30 seconds | Latency > 5s |
| Resources | < 60 seconds | OOM imminent |

## Blast Radius Control

### Safety Constraints

| Constraint | Limit | Enforcement |
|------------|-------|-------------|
| **Max Affected Services** | 1 | Automatic isolation |
| **Max Affected Users** | 100 | Auto-rollback |
| **Max Duration** | 5 minutes | Auto-rollback |
| **Max Error Rate** | 5% | Auto-rollback |
| **Max P99 Latency** | 5000ms | Auto-rollback |

### Auto-Rollback Triggers

Experiments automatically rollback if:

1. **Error rate** exceeds 5% for 1 minute
2. **P99 latency** exceeds 5000ms for 1 minute
3. **Cascading failures** detected (2+ services affected)
4. **Blast radius limit** breached
5. **Manual emergency stop** signal

### Rollback Procedures

**Redis Failure:**
```bash
# Restore connectivity
iptables -D OUTPUT -p tcp --dport 6379 -j DROP

# Verify reconnection
redis-cli ping

# Monitor recovery
curl http://localhost:8000/health | jq .
```

**PostgreSQL Failure:**
```bash
# Release connections
python -c "from app import db; db.release_all_connections()"

# Verify pool health
curl http://localhost:8000/metrics | grep db_pool_available
```

**Storage Failure:**
```bash
# Restore permissions
chmod 755 /tmp/lionagi_storage

# Restore S3 connectivity
iptables -D OUTPUT -d s3.amazonaws.com -j DROP
```

## Chaos Experiments

### Experiment Execution Flow

```
┌─────────────────────────────────────────────────────┐
│  Phase 1: Pre-Flight Checks (2 minutes)             │
│  - Verify environment (staging/test)                │
│  - Check system health (steady state)               │
│  - Validate blast radius limits                     │
│  - Prepare rollback plan                            │
│  - Alert on-call team                               │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  Phase 2: Baseline Collection (1 minute)            │
│  - Collect error rate, latency, throughput          │
│  - Establish steady-state metrics                   │
│  - Verify monitoring dashboards active              │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  Phase 3: Fault Injection (3-5 minutes)             │
│  - Execute fault (gradual or immediate)             │
│  - Monitor blast radius every 10 seconds            │
│  - Track steady-state deviations                    │
│  - Check auto-rollback triggers                     │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  Phase 4: Observability (during fault)              │
│  - Collect system metrics (CPU, memory, disk)       │
│  - Collect application metrics (errors, latency)    │
│  - Capture distributed traces                       │
│  - Monitor for cascading failures                   │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  Phase 5: Rollback (1-2 minutes)                    │
│  - Execute rollback procedure                       │
│  - Verify service recovery                          │
│  - Measure recovery time                            │
│  - Confirm steady state restored                    │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  Phase 6: Post-Mortem (5-10 minutes)                │
│  - Analyze metrics and logs                         │
│  - Validate hypothesis (pass/fail)                  │
│  - Generate insights and recommendations            │
│  - Calculate resilience score                       │
│  - Update runbooks                                  │
└─────────────────────────────────────────────────────┘
```

### Progressive Chaos Testing

**Week 1: Isolated Component Testing**
- Day 1: Redis connection failures
- Day 2: PostgreSQL pool exhaustion
- Day 3: Storage backend failures

**Week 2: Network Chaos**
- Day 1: Latency injection (500ms)
- Day 2: Packet loss (10%)
- Day 3: Network partitions

**Week 3: Resource Exhaustion**
- Day 1: CPU stress (90%)
- Day 2: Memory pressure (85%)
- Day 3: Disk exhaustion (95%)

**Week 4: Combined Scenarios**
- Day 1: Redis + network latency
- Day 2: PostgreSQL + CPU stress
- Day 3: Full system chaos (all components)

## Observability Integration

### Metrics Collection

**System Metrics:**
```python
system_metrics = {
    "cpu_utilization_percent": psutil.cpu_percent(),
    "memory_utilization_percent": psutil.virtual_memory().percent,
    "disk_usage_percent": psutil.disk_usage('/').percent,
    "network_rx_bytes": psutil.net_io_counters().bytes_recv,
    "network_tx_bytes": psutil.net_io_counters().bytes_sent
}
```

**Application Metrics:**
```python
application_metrics = {
    "request_rate_rps": count_requests_per_second(),
    "error_rate_percent": calculate_error_rate(),
    "latency_p50_ms": calculate_percentile(50),
    "latency_p95_ms": calculate_percentile(95),
    "latency_p99_ms": calculate_percentile(99),
    "throughput_ops_per_sec": calculate_throughput()
}
```

**Chaos-Specific Metrics:**
```python
chaos_metrics = {
    "circuit_breaker_state": get_circuit_breaker_state(),  # open/closed/half-open
    "circuit_open_count": count_circuit_opens(),
    "retry_count_total": count_retries(),
    "retry_success_rate": calculate_retry_success_rate(),
    "fallback_activation_count": count_fallback_activations(),
    "recovery_time_seconds": measure_recovery_time()
}
```

### Structured Logging

All chaos events logged in JSON format:

```json
{
  "timestamp": "2025-11-12T10:00:00.000Z",
  "level": "ERROR",
  "component": "RedisMemory",
  "operation": "store",
  "error_type": "ConnectionError",
  "error_message": "Connection refused",
  "chaos_experiment": "redis-failure-experiment",
  "experiment_phase": "fault_injection",
  "retry_attempt": 1,
  "circuit_breaker_state": "open",
  "fallback_activated": true,
  "fallback_backend": "session_context",
  "blast_radius": {
    "affected_users": 47,
    "affected_services": ["cache"]
  },
  "context": {
    "key": "aqe/test-plan/results",
    "partition": "coordination",
    "operation_id": "op-12345"
  }
}
```

### Distributed Tracing

Chaos events as trace spans:

```
trace_id: abc123def456
├─ span: http_request (200ms)
│  ├─ tags: {endpoint: "/api/test", method: "POST"}
│  └─ status: OK
├─ span: chaos_redis_latency (500ms) ← Chaos event
│  ├─ tags: {chaos.type: "latency", chaos.target: "redis", chaos.latency_ms: 500}
│  └─ status: OK
├─ span: redis_store_retry (250ms)
│  ├─ tags: {retry_attempt: 1, backoff_ms: 1000}
│  └─ status: ERROR (connection refused)
├─ span: circuit_breaker_open (5ms)
│  ├─ tags: {component: "redis", state: "open"}
│  └─ status: OK
└─ span: fallback_session_context (50ms)
   ├─ tags: {fallback_from: "redis", fallback_to: "session_context"}
   └─ status: OK
```

### Alerting Rules

**Critical Alerts:**
```yaml
- alert: HighErrorRate
  expr: error_rate > 0.05
  for: 1m
  severity: critical
  message: "Error rate {{$value}}% exceeds 5% threshold"

- alert: HighLatency
  expr: latency_p99_ms > 5000
  for: 1m
  severity: critical
  message: "P99 latency {{$value}}ms exceeds 5000ms threshold"

- alert: CascadingFailure
  expr: affected_services_count > 1
  severity: critical
  message: "Cascading failure detected across {{$value}} services"

- alert: BlastRadiusBreach
  expr: affected_users > 100
  severity: critical
  message: "Blast radius breached: {{$value}} users affected (max 100)"
```

**Warning Alerts:**
```yaml
- alert: ElevatedErrorRate
  expr: error_rate > 0.02
  for: 2m
  severity: warning
  message: "Error rate {{$value}}% elevated above 2%"

- alert: CircuitBreakerOpen
  expr: circuit_breaker_state == "open"
  for: 30s
  severity: warning
  message: "Circuit breaker open for {{$labels.component}}"

- alert: FallbackActivated
  expr: fallback_activation_count > 0
  severity: warning
  message: "Fallback activated for {{$labels.component}}"
```

## Resilience Scoring

### Scoring Formula

```
Resilience Score (0-100) =
  Availability (40%) +
  Recovery Time (30%) +
  Blast Radius Control (20%) +
  Graceful Degradation (10%)
```

### Component Scoring

**Availability (40%):**
- 100%: Zero downtime during chaos
- 90-99%: Degraded but operational
- < 90%: Service disruption

**Recovery Time (30%):**
- < 10s: Excellent (100 points)
- 10-30s: Good (80 points)
- 30-60s: Acceptable (60 points)
- > 60s: Needs improvement (40 points)

**Blast Radius Control (20%):**
- Fully contained: 100 points
- 1 service affected: 80 points
- 2 services affected: 50 points
- > 2 services: 20 points

**Graceful Degradation (10%):**
- Partial functionality maintained: 100 points
- Critical features working: 80 points
- Minimal functionality: 50 points
- Complete failure: 0 points

### Target Scores

| Component | Target Score | Current Score | Status |
|-----------|-------------|---------------|--------|
| Redis | 85+ | TBD | 🔄 Testing |
| PostgreSQL | 85+ | TBD | 🔄 Testing |
| Storage | 80+ | TBD | 🔄 Testing |
| Network | 80+ | TBD | 🔄 Testing |
| Resources | 75+ | TBD | 🔄 Testing |

## Deliverables

### 1. Chaos Toolkit Experiments (3)
✅ `/tests/chaos/chaostoolkit/redis-failure-experiment.json`
✅ `/tests/chaos/chaostoolkit/postgres-failure-experiment.json`
✅ `/tests/chaos/chaostoolkit/storage-failure-experiment.json`

### 2. Toxiproxy Network Chaos
✅ `/tests/chaos/toxiproxy/toxiproxy-config.json` (10+ scenarios)

### 3. Python Resilience Tests (6 suites, 100+ tests)
✅ `/tests/chaos/resilience/test_redis_resilience.py`
✅ `/tests/chaos/resilience/test_postgres_resilience.py`
✅ `/tests/chaos/resilience/test_storage_resilience.py`
✅ `/tests/chaos/resilience/test_network_resilience.py`
✅ `/tests/chaos/resilience/test_resource_exhaustion.py`
✅ `/tests/chaos/resilience/test_observability.py`

### 4. Documentation & Runbooks
✅ `/tests/chaos/README.md` - Comprehensive guide
✅ `/tests/chaos/scenarios/redis-chaos-playbook.md` - Runbook

### 5. Automation Scripts
✅ `/tests/chaos/scenarios/run_chaos_suite.sh` - Automated test runner

## Execution Timeline

### Phase 1: Setup (Week 1)
- Day 1-2: Install dependencies (Chaos Toolkit, Toxiproxy)
- Day 3-4: Configure environments (staging, test)
- Day 5: Verify pre-flight checks

### Phase 2: Isolated Testing (Week 2-3)
- Week 2: Component-level chaos (Redis, PostgreSQL, Storage)
- Week 3: Network chaos (latency, packet loss, partitions)

### Phase 3: Combined Testing (Week 4)
- Day 1: Resource exhaustion scenarios
- Day 2: Multi-component chaos
- Day 3: Full system resilience validation

### Phase 4: Continuous Chaos (Week 5+)
- Integrate chaos into CI/CD pipeline
- Scheduled game days (monthly)
- Low-intensity continuous chaos in production

## Success Criteria

### Must Have (P0)
- ✅ All Chaos Toolkit experiments pass
- ✅ All pytest resilience tests pass
- ✅ Auto-rollback triggers work correctly
- ✅ Recovery time meets SLAs
- ✅ Zero data loss in all scenarios
- ✅ Blast radius limits enforced

### Should Have (P1)
- ✅ Resilience scores > 80 for all components
- ✅ Observability dashboards functional
- ✅ Runbooks complete and tested
- ✅ Team trained on chaos procedures

### Nice to Have (P2)
- 🔄 Continuous chaos in production (low intensity)
- 🔄 Automated chaos scheduling
- 🔄 Machine learning for anomaly detection
- 🔄 Chaos experiment recommendations

## References

- **Chaos Toolkit:** https://chaostoolkit.org/
- **Toxiproxy:** https://github.com/Shopify/toxiproxy
- **Principles of Chaos Engineering:** https://principlesofchaos.org/
- **Google SRE Book:** https://sre.google/sre-book/testing-reliability/
- **Netflix Chaos Engineering:** https://netflixtechblog.com/tagged/chaos-engineering

## Contact

**Agent:** qe-chaos-engineer
**Skills:** chaos-engineering-resilience, shift-right-testing, risk-based-testing
**Memory Namespace:** aqe/chaos/*

---

**Generated by:** Agentic QE Fleet v1.4.3
**Strategy Version:** 1.0.0
**Date:** 2025-11-12
