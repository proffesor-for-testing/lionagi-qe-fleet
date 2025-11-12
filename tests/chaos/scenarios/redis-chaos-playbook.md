# Redis Chaos Engineering Playbook

## Scenario 1: Redis Connection Failure

### Hypothesis
System maintains functionality when Redis becomes unavailable by automatically falling back to Session.context (in-memory storage).

### Prerequisites
- Redis running on localhost:6379
- System configured with fallback to Session.context
- Monitoring dashboard accessible
- Team available for 30-minute window

### Execution Steps

#### Phase 1: Baseline Collection (5 minutes)
```bash
# Collect baseline metrics
chaos run tests/chaos/chaostoolkit/redis-failure-experiment.json --dry

# Verify steady state
curl http://localhost:8000/health | jq .
# Expected: {"status": "healthy", "redis": "connected"}
```

#### Phase 2: Fault Injection (15 minutes)
```bash
# Block Redis port using iptables
sudo iptables -A OUTPUT -p tcp --dport 6379 -j DROP

# Verify Redis unreachable
redis-cli ping
# Expected: Error - Could not connect
```

#### Phase 3: Observability (during fault)
```bash
# Monitor application logs
tail -f logs/app.log | grep -i redis

# Check fallback activation
curl http://localhost:8000/metrics | grep fallback_active
# Expected: fallback_active{backend="session_context"} 1

# Monitor error rate
curl http://localhost:8000/metrics | grep error_rate
# Expected: error_rate < 0.05 (5%)
```

#### Phase 4: Rollback (2 minutes)
```bash
# Restore Redis connectivity
sudo iptables -D OUTPUT -p tcp --dport 6379 -j DROP

# Verify Redis reconnection
redis-cli ping
# Expected: PONG

# Monitor recovery
curl http://localhost:8000/health | jq .
# Expected: {"status": "healthy", "redis": "connected"}
```

#### Phase 5: Post-Mortem (8 minutes)
```bash
# Collect recovery metrics
chaos report last-experiment.json

# Measure recovery time
# Expected: < 30 seconds

# Verify zero data loss
# Check data consistency
```

### Success Criteria
- ✅ System continues processing requests (degraded performance acceptable)
- ✅ Automatic fallback to Session.context activates
- ✅ Error rate remains below 5%
- ✅ Recovery time < 30 seconds
- ✅ Zero data loss or corruption

### Failure Scenarios and Remediation

**Scenario:** System crashes when Redis becomes unavailable
- **Root Cause:** No fallback mechanism implemented
- **Remediation:** Implement Session.context fallback
- **Retest:** After fix deployed

**Scenario:** Recovery takes > 60 seconds
- **Root Cause:** Circuit breaker timeout too long
- **Remediation:** Reduce circuit breaker timeout to 30s
- **Retest:** After configuration change

## Scenario 2: Redis Connection Pool Exhaustion

### Hypothesis
System handles Redis connection pool exhaustion without cascading failures by queuing requests and using circuit breakers.

### Execution Steps

```bash
# Exhaust connection pool
python tests/chaos/scenarios/exhaust_redis_pool.py --connections=50 --duration=180

# Monitor circuit breaker
curl http://localhost:8000/metrics | grep circuit_breaker_state
# Expected: circuit_breaker_state{component="redis"} open

# Verify request queuing
curl http://localhost:8000/metrics | grep request_queue_size
# Expected: request_queue_size > 0
```

### Success Criteria
- ✅ Circuit breaker opens after threshold
- ✅ Requests queued (not dropped)
- ✅ No cascading service failures
- ✅ Graceful degradation to read-only mode

## Scenario 3: Redis Latency Injection (Toxiproxy)

### Hypothesis
System tolerates Redis latency up to 1 second without significant user impact.

### Execution Steps

```bash
# Start Toxiproxy
toxiproxy-server &

# Create Redis proxy
toxiproxy-cli create redis --listen=127.0.0.1:26379 --upstream=localhost:6379

# Update application config to use proxy
export REDIS_PORT=26379

# Inject 500ms latency
toxiproxy-cli toxic add redis --type=latency --toxicName=redis_latency \
  --attribute=latency=500 --attribute=jitter=100

# Monitor P99 latency
curl http://localhost:8000/metrics | grep latency_p99
# Expected: latency_p99 < 2000 (ms)
```

### Success Criteria
- ✅ P99 latency < 2 seconds
- ✅ Timeout mechanisms prevent indefinite waits
- ✅ User experience remains acceptable
- ✅ No request failures due to latency

## Scenario 4: Redis Data Consistency During Failure

### Hypothesis
No data corruption or loss occurs during Redis failures due to transaction rollback and atomic operations.

### Execution Steps

```bash
# Start continuous write workload
python tests/chaos/scenarios/redis_write_workload.py &

# Inject fault (connection failure)
sudo iptables -A OUTPUT -p tcp --dport 6379 -j DROP

# Wait 60 seconds
sleep 60

# Restore connectivity
sudo iptables -D OUTPUT -p tcp --dport 6379 -j DROP

# Verify data consistency
python tests/chaos/scenarios/verify_redis_consistency.py
# Expected: All checksums valid, no partial writes
```

### Success Criteria
- ✅ Zero data corruption
- ✅ No partial writes
- ✅ All committed data intact
- ✅ Checksums verify correctly

## Runbook: Redis Failure Response

### Detection
**Symptom:** Redis connection errors in application logs
**Alert:** `HighRedisErrorRate` fires in monitoring system

### Investigation
```bash
# Check Redis service status
systemctl status redis

# Check Redis logs
journalctl -u redis -f

# Test Redis connectivity
redis-cli ping

# Check connection pool metrics
curl http://localhost:8000/metrics | grep redis_pool
```

### Resolution

**Option 1: Restart Redis**
```bash
sudo systemctl restart redis
# Wait 10 seconds
redis-cli ping
```

**Option 2: Clear stuck connections**
```bash
# List connections
redis-cli CLIENT LIST

# Kill specific connection
redis-cli CLIENT KILL ADDR 127.0.0.1:12345
```

**Option 3: Failover to fallback**
```bash
# Verify fallback active
curl http://localhost:8000/health | jq .fallback_active
# Expected: true

# Monitor until Redis recovers
watch -n 5 'curl -s http://localhost:8000/health | jq .'
```

### Post-Incident
1. Collect metrics and logs
2. Perform root cause analysis
3. Update runbook with learnings
4. Schedule chaos experiment to test fix

## Metrics Dashboard

### Key Metrics to Monitor

**Availability:**
- `redis_connection_success_rate`
- `redis_operation_success_rate`
- `fallback_activation_count`

**Performance:**
- `redis_operation_latency_p99`
- `redis_connection_pool_wait_time`
- `request_queue_size`

**Resilience:**
- `circuit_breaker_state` (open/closed/half-open)
- `retry_count_total`
- `fallback_hits_total`
- `recovery_time_seconds`

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Error Rate | > 2% | > 5% |
| P99 Latency | > 1000ms | > 5000ms |
| Pool Exhaustion | > 80% | > 95% |
| Circuit Breaker Open | - | Alert |
| Recovery Time | > 30s | > 60s |
