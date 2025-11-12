# Chaos Engineering & Resilience Testing - Phase 1

## Overview

This directory contains comprehensive chaos engineering and resilience testing for the LionAGI QE Fleet Phase 1 infrastructure components:

- **Redis** - In-memory cache and session storage
- **PostgreSQL** - Persistent database for Q-learning and memory
- **Storage Backends** - S3 and local filesystem
- **Network** - Connectivity and latency
- **Resources** - CPU, memory, disk, handles

## Directory Structure

```
tests/chaos/
├── chaostoolkit/          # Chaos Toolkit experiments
│   ├── redis-failure-experiment.json
│   ├── postgres-failure-experiment.json
│   └── storage-failure-experiment.json
├── toxiproxy/             # Toxiproxy network chaos
│   ├── toxiproxy-config.json
│   └── scenarios/
├── resilience/            # Python pytest resilience tests
│   ├── test_redis_resilience.py
│   ├── test_postgres_resilience.py
│   ├── test_storage_resilience.py
│   ├── test_network_resilience.py
│   ├── test_resource_exhaustion.py
│   └── test_observability.py
├── scenarios/             # Chaos scenarios and playbooks
└── README.md              # This file
```

## Prerequisites

### Install Dependencies

```bash
# Python dependencies
pip install chaostoolkit chaostoolkit-kubernetes toxiproxy-py pytest pytest-asyncio pytest-mock psutil

# Chaos Toolkit
pip install chaostoolkit-lib>=1.24.2

# Toxiproxy (for network chaos)
# Download from: https://github.com/Shopify/toxiproxy/releases
# Or via Docker:
docker run -d --name toxiproxy -p 8474:8474 -p 26379:26379 -p 25432:25432 ghcr.io/shopify/toxiproxy
```

### System Requirements

- **Python 3.9+**
- **Redis 6.0+** (for Redis chaos tests)
- **PostgreSQL 14+** (for database chaos tests)
- **Toxiproxy** (for network chaos)
- **Root/sudo access** (for some network chaos scenarios)

## Quick Start

### 1. Run Chaos Toolkit Experiments

```bash
# Redis failure experiment
chaos run tests/chaos/chaostoolkit/redis-failure-experiment.json

# PostgreSQL pool exhaustion
chaos run tests/chaos/chaostoolkit/postgres-failure-experiment.json

# Storage backend failures
chaos run tests/chaos/chaostoolkit/storage-failure-experiment.json
```

### 2. Run Toxiproxy Network Chaos

```bash
# Start Toxiproxy
toxiproxy-server &

# Load configuration
toxiproxy-cli create redis --listen=127.0.0.1:26379 --upstream=localhost:6379
toxiproxy-cli create postgres --listen=127.0.0.1:25432 --upstream=localhost:5432

# Inject latency
toxiproxy-cli toxic add redis --type=latency --toxicName=redis_latency --attribute=latency=500

# Check status
toxiproxy-cli list
```

### 3. Run Python Resilience Tests

```bash
# Run all resilience tests
pytest tests/chaos/resilience/ -v --tb=short

# Run specific test categories
pytest tests/chaos/resilience/test_redis_resilience.py -v
pytest tests/chaos/resilience/test_postgres_resilience.py -v
pytest tests/chaos/resilience/test_storage_resilience.py -v

# Run with chaos marker
pytest tests/chaos/resilience/ -m chaos -v
```

## Chaos Scenarios

### 1. Redis Connection Failures

**Hypothesis:** System maintains functionality when Redis becomes unavailable by falling back to Session.context.

**Test Cases:**
- Connection refused
- Connection timeout
- Pool exhaustion
- Network partition

**Expected Behavior:**
- Automatic fallback to Session.context (in-memory)
- Circuit breaker opens after 5 failures
- Recovery within 30 seconds
- Zero data loss

**Run:**
```bash
chaos run tests/chaos/chaostoolkit/redis-failure-experiment.json
pytest tests/chaos/resilience/test_redis_resilience.py -v
```

### 2. PostgreSQL Connection Pool Exhaustion

**Hypothesis:** System degrades gracefully when database connection pool is exhausted, using queue-based buffering and circuit breakers.

**Test Cases:**
- Gradual pool exhaustion
- Connection acquisition timeout
- Query timeout
- Transaction rollback

**Expected Behavior:**
- Request queuing when pool full
- Circuit breaker prevents cascade
- Graceful degradation to read-only
- Recovery after connection release

**Run:**
```bash
chaos run tests/chaos/chaostoolkit/postgres-failure-experiment.json
pytest tests/chaos/resilience/test_postgres_resilience.py -v
```

### 3. Storage Backend Failures

**Hypothesis:** System handles S3 and filesystem failures with fallback mechanisms and no data loss.

**Test Cases:**
- S3 network partition
- Filesystem permission denial
- Disk space exhaustion
- I/O errors

**Expected Behavior:**
- Automatic fallback between backends
- Retry with exponential backoff
- No partial writes
- Data consistency maintained

**Run:**
```bash
chaos run tests/chaos/chaostoolkit/storage-failure-experiment.json
pytest tests/chaos/resilience/test_storage_resilience.py -v
```

### 4. Network Chaos (Toxiproxy)

**Scenarios:**

**A. Latency Injection**
```bash
# 500ms latency to Redis
toxiproxy-cli toxic add redis --type=latency --toxicName=redis_latency --attribute=latency=500 --attribute=jitter=100
```

**B. Packet Loss**
```bash
# 10% packet loss to PostgreSQL
toxiproxy-cli toxic add postgres --type=slicer --toxicName=pg_packet_loss --toxicity=0.1
```

**C. Bandwidth Limit**
```bash
# Limit Redis bandwidth to 100KB/s
toxiproxy-cli toxic add redis --type=bandwidth --toxicName=redis_bandwidth --attribute=rate=100
```

**D. Complete Outage**
```bash
# Simulate complete network partition
toxiproxy-cli toxic add redis --type=reset_peer --toxicName=redis_reset --toxicity=1.0
```

### 5. Resource Exhaustion

**Test Cases:**
- CPU stress (90-95% usage)
- Memory pressure (85% usage)
- Disk space exhaustion (95% usage)
- File handle exhaustion

**Expected Behavior:**
- Graceful degradation
- Load shedding for non-critical requests
- Resource monitoring and alerts
- Recovery after resource release

**Run:**
```bash
pytest tests/chaos/resilience/test_resource_exhaustion.py -v
```

## Safety Mechanisms

### Pre-Flight Checks

Before running chaos experiments:

1. **Verify environment** - Ensure running in staging/test, not production
2. **Check system health** - Verify baseline steady state
3. **Validate blast radius limits** - Confirm maximum impact constraints
4. **Prepare rollback plan** - Automated rollback procedures ready
5. **Alert on-call team** - Ensure team available during experiment

### Blast Radius Limits

| Constraint | Limit | Auto-Rollback |
|------------|-------|---------------|
| Max Affected Services | 1 | Yes |
| Max Affected Users | 100 | Yes |
| Max Duration | 5 minutes | Yes |
| Max Error Rate | 5% | Yes |
| Max P99 Latency | 5000ms | Yes |

### Auto-Rollback Triggers

Experiments automatically rollback if:

- Error rate exceeds 5% for 1 minute
- P99 latency exceeds 5000ms for 1 minute
- Cascading failures detected
- Blast radius limit breached
- Manual emergency stop signal

## Observability

### Metrics Collected

During chaos experiments, the following metrics are collected:

**System Metrics:**
- CPU utilization (%)
- Memory utilization (%)
- Disk usage (%)
- Network throughput (bytes/s)

**Application Metrics:**
- Request rate (req/s)
- Error rate (%)
- Latency percentiles (p50, p95, p99)
- Throughput (ops/s)

**Chaos-Specific Metrics:**
- Circuit breaker state (open/closed/half-open)
- Retry count
- Fallback activation count
- Recovery time (seconds)

### Logging

All chaos events are logged with structured JSON:

```json
{
  "timestamp": "2025-01-01T00:00:00Z",
  "level": "ERROR",
  "component": "RedisMemory",
  "operation": "store",
  "error_type": "ConnectionError",
  "error_message": "Connection refused",
  "chaos_experiment": "redis-failure-experiment",
  "retry_attempt": 1,
  "circuit_breaker_state": "open"
}
```

### Distributed Tracing

Chaos events appear as spans in distributed traces:

```
trace_id: abc123
├─ span: http_request (200ms)
├─ span: chaos_redis_latency (500ms) ← Chaos event
├─ span: redis_store_retry (250ms)
└─ span: fallback_session_context (50ms)
```

## Resilience Patterns Tested

### 1. Circuit Breaker Pattern

- Opens after 5 consecutive failures
- Half-open after 30-second timeout
- Closes after successful request
- Prevents cascading failures

### 2. Retry with Exponential Backoff

- Initial delay: 1 second
- Backoff factor: 2x
- Max attempts: 3
- Jitter: ±200ms (prevent thundering herd)

### 3. Fallback Mechanisms

- Redis → Session.context (in-memory)
- S3 → Local filesystem
- PostgreSQL → Read-only mode

### 4. Graceful Degradation

- Disable non-critical features under pressure
- Prioritize critical requests
- Load shedding (503 responses)
- Maintain core functionality

## Best Practices

### Running Chaos Experiments

1. **Start small** - Begin with staging environment
2. **Gradual intensity** - Increase chaos gradually
3. **Monitor continuously** - Watch metrics in real-time
4. **Document outcomes** - Record results and insights
5. **Iterate improvements** - Fix issues and retest

### Game Days

Schedule regular "Game Day" exercises:

- **Frequency:** Monthly
- **Duration:** 2-3 hours
- **Team:** Dev, QE, SRE
- **Format:** Facilitated chaos scenarios
- **Goals:** Build confidence, improve runbooks

### Continuous Chaos

Consider running low-intensity chaos continuously in production:

- **Intensity:** 5-10% of requests
- **Types:** Small latency injection, occasional timeouts
- **Benefits:** Build confidence, catch regressions early

## Troubleshooting

### Experiment Fails to Start

```bash
# Check Chaos Toolkit installation
chaos --version

# Verify Python dependencies
pip list | grep chaos

# Check experiment syntax
chaos validate tests/chaos/chaostoolkit/redis-failure-experiment.json
```

### Toxiproxy Not Working

```bash
# Check Toxiproxy running
curl http://localhost:8474/version

# List proxies
toxiproxy-cli list

# Reset all toxics
toxiproxy-cli reset
```

### Tests Hanging or Timing Out

- Check system resources (CPU, memory, disk)
- Verify services are running (Redis, PostgreSQL)
- Increase test timeouts in pytest.ini
- Check for deadlocks in logs

### Auto-Rollback Not Triggering

- Verify rollback triggers configured
- Check monitoring thresholds
- Review experiment logs
- Ensure rollback scripts have execute permissions

## Contributing

When adding new chaos experiments:

1. **Follow naming convention:** `{component}-{failure-type}-experiment.json`
2. **Include documentation:** Hypothesis, expected behavior, rollback
3. **Add tests:** Python test coverage for scenarios
4. **Update this README:** Add scenario to Quick Start
5. **Test thoroughly:** Run in staging before production

## References

- [Chaos Toolkit Documentation](https://chaostoolkit.org/)
- [Toxiproxy Documentation](https://github.com/Shopify/toxiproxy)
- [Principles of Chaos Engineering](https://principlesofchaos.org/)
- [Google SRE Book - Testing for Reliability](https://sre.google/sre-book/testing-reliability/)

## Support

For questions or issues:

- **Team:** Agentic QE Fleet
- **Agent:** qe-chaos-engineer
- **Skills:** chaos-engineering-resilience, shift-right-testing
