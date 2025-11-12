# Agentic QE Fleet REST API

Complete REST API for triggering QE agents from external CI/CD systems.

## Overview

The AQE Fleet API provides 9 primary endpoints for comprehensive quality engineering automation:

- **Test Generation**: AI-powered test creation with sublinear optimization
- **Test Execution**: Multi-framework parallel test execution
- **Coverage Analysis**: Real-time gap detection with O(log n) algorithms
- **Quality Gates**: Intelligent validation with risk assessment
- **Security Scanning**: Multi-layer SAST/DAST vulnerability detection
- **Performance Testing**: Load testing with configurable virtual users
- **Fleet Status**: Real-time agent and job monitoring
- **Job Management**: Status tracking and WebSocket streaming

## Quick Start

### Installation

```bash
# Install API dependencies
pip install "lionagi-qe-fleet[api]"

# Or install all features
pip install "lionagi-qe-fleet[all]"
```

### Start Server

```bash
# Using CLI (recommended)
aqe serve --port 8080

# Using Python
python -m lionagi_qe.api.server

# Using uvicorn directly
uvicorn lionagi_qe.api.server:app --host 0.0.0.0 --port 8080
```

### Generate API Key

```bash
# Generate API key via CLI
aqe api generate-key --name "ci-cd-integration"

# Output:
# Generated API key: aqe_abc123def456...
# Store this key securely - it won't be shown again
```

### Make First Request

```bash
export API_KEY="aqe_your_api_key_here"

curl -X POST http://localhost:8080/api/v1/test/generate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "src/services/user.service.ts",
    "framework": "jest",
    "coverage_target": 90.0
  }'
```

## API Endpoints

### 1. Test Generation

**POST** `/api/v1/test/generate`

Generate tests for specified target using AI-powered test generation agent.

**Request:**
```json
{
  "target": "src/services/user.service.ts",
  "framework": "jest",
  "test_type": "unit",
  "coverage_target": 90.0,
  "priority": "high",
  "callback_url": "https://your-ci.com/webhook"
}
```

**Response:**
```json
{
  "job_id": "test-gen-123abc",
  "status": "queued",
  "created_at": "2025-01-12T10:30:00Z",
  "stream_url": "/api/v1/job/test-gen-123abc/stream"
}
```

### 2. Test Execution

**POST** `/api/v1/test/execute`

Execute tests with specified framework and configuration.

**Request:**
```json
{
  "test_path": "tests/",
  "framework": "jest",
  "parallel": true,
  "coverage": true,
  "timeout": 300,
  "env_vars": {
    "DATABASE_URL": "postgresql://localhost/testdb"
  }
}
```

### 3. Coverage Analysis

**POST** `/api/v1/coverage/analyze`

Analyze code coverage and identify gaps using O(log n) algorithms.

**Request:**
```json
{
  "source_path": "src/",
  "test_path": "tests/",
  "min_coverage": 80.0,
  "include_gaps": true
}
```

### 4. Quality Gate Validation

**POST** `/api/v1/quality/gate`

Validate project quality against configured thresholds.

**Request:**
```json
{
  "project_path": ".",
  "min_coverage": 80.0,
  "max_complexity": 10,
  "max_duplicates": 3.0,
  "security_checks": true
}
```

### 5. Security Scanning

**POST** `/api/v1/security/scan`

Perform security vulnerability scanning with SAST/DAST analysis.

**Request:**
```json
{
  "target": ".",
  "scan_dependencies": true,
  "scan_code": true,
  "severity_threshold": "medium"
}
```

### 6. Performance Testing

**POST** `/api/v1/performance/test`

Execute performance/load testing with configurable virtual users.

**Request:**
```json
{
  "target_url": "https://api.example.com/users",
  "duration_seconds": 60,
  "virtual_users": 50,
  "ramp_up_seconds": 10,
  "think_time_ms": 1000
}
```

### 7. Fleet Status

**POST** `/api/v1/fleet/status`

Get current status of the Agentic QE Fleet.

**Request:**
```json
{
  "verbose": true,
  "include_metrics": true
}
```

### 8. Job Status

**GET** `/api/v1/job/{job_id}/status`

Get current status and progress of a job.

**Response:**
```json
{
  "job_id": "test-gen-123abc",
  "status": "running",
  "progress": 45.2,
  "current_step": "Analyzing code structure...",
  "created_at": "2025-01-12T10:30:00Z",
  "started_at": "2025-01-12T10:30:02Z"
}
```

### 9. WebSocket Streaming

**WS** `/api/v1/job/{job_id}/stream`

Stream real-time job progress via WebSocket.

**Messages:**
```json
{
  "type": "progress",
  "progress": 45.2,
  "message": "Analyzing code structure...",
  "timestamp": "2025-01-12T10:30:15Z"
}
```

## Authentication

All endpoints (except `/health`) require authentication using API keys or JWT tokens.

### API Key Format

```
Authorization: Bearer aqe_<32-char-token>
```

### JWT Token Format

```
Authorization: Bearer <jwt-token>
```

### Generating API Keys

```bash
# CLI method
aqe api generate-key --name "production-ci"

# Python SDK method
from lionagi_qe.api.auth import generate_api_key
api_key = generate_api_key("production-ci")
```

## Rate Limiting

- **Default Limit**: 100 requests per minute per API key
- **Algorithm**: Sliding window
- **Headers**: All responses include rate limit information

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1673524800
```

### Handling Rate Limits

```python
import time

response = requests.post(url, headers=headers, json=data)

if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 60))
    print(f"Rate limited. Retry after {retry_after} seconds")
    time.sleep(retry_after)
```

## Python SDK

### Installation

```bash
pip install lionagi-qe-fleet[api]
```

### Basic Usage

```python
from lionagi_qe.api.sdk import AQEClient

async with AQEClient(api_key="aqe_your_key") as client:
    # Generate tests
    job = await client.generate_tests(
        target="src/services/user.service.ts",
        framework="jest",
        coverage_target=90.0
    )

    # Stream progress
    async for update in client.stream_job_progress(job["job_id"]):
        print(f"{update['progress']}%: {update['message']}")
```

### Advanced Usage

```python
# Parallel job execution
jobs = await asyncio.gather(
    client.generate_tests(target="src/services/"),
    client.analyze_coverage(source_path="src/"),
    client.validate_quality_gate(project_path="."),
    client.scan_security(target=".")
)

# Wait for all jobs
for job in jobs:
    status = await client.get_job_status(job["job_id"])
    print(f"Job {job['job_id']}: {status['status']}")
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run QE Tests
  env:
    AQE_API_KEY: ${{ secrets.AQE_API_KEY }}
  run: |
    python -c "
    import asyncio
    from lionagi_qe.api.sdk import AQEClient

    async def main():
        async with AQEClient(api_key='$AQE_API_KEY') as client:
            job = await client.generate_tests(target='src/')
            async for update in client.stream_job_progress(job['job_id']):
                print(f\"{update['progress']}%\")

    asyncio.run(main())
    "
```

### GitLab CI

```yaml
test:
  script:
    - pip install lionagi-qe-fleet[api]
    - python scripts/run_aqe_tests.py
```

### Jenkins

```groovy
stage('QE Tests') {
    steps {
        withCredentials([string(credentialsId: 'aqe-api-key', variable: 'API_KEY')]) {
            sh 'python scripts/run_aqe_tests.py'
        }
    }
}
```

## Performance

### Response Times (p95)

- API request handling: **< 200ms**
- WebSocket connection: **< 50ms**
- Job enqueue: **< 100ms**

### Throughput

- **1000 concurrent requests** supported
- **99.9% uptime** target
- Automatic retry with exponential backoff

### Scalability

- Horizontal scaling via load balancer
- Redis-backed job queue (production)
- Stateless API design

## Error Handling

### Standard Error Response

```json
{
  "error": "validation_error",
  "message": "Invalid target path",
  "details": {
    "field": "target",
    "issue": "Path does not exist"
  },
  "timestamp": "2025-01-12T10:30:00Z"
}
```

### Common Error Codes

- **400**: Bad Request (validation error)
- **401**: Unauthorized (invalid API key)
- **404**: Not Found (job/resource not found)
- **429**: Too Many Requests (rate limit exceeded)
- **500**: Internal Server Error

## WebSocket Protocol

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8080/api/v1/job/test-gen-123/stream');
```

### Message Types

1. **Progress Update**
   ```json
   {"type": "progress", "progress": 45.2, "message": "Processing..."}
   ```

2. **Completion**
   ```json
   {"type": "complete", "progress": 100.0, "result": {...}}
   ```

3. **Error**
   ```json
   {"type": "error", "error": "Processing failed"}
   ```

### Handling Disconnections

```javascript
ws.onclose = () => {
    // Reconnect with exponential backoff
    setTimeout(() => reconnect(), 1000);
};
```

## Monitoring

### Health Check

```bash
curl http://localhost:8080/health
```

### Metrics Endpoint

```bash
curl -X POST http://localhost:8080/api/v1/fleet/status \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"include_metrics": true}'
```

## Security

### Best Practices

1. **Store API keys securely** (environment variables, secrets manager)
2. **Use HTTPS in production**
3. **Rotate API keys regularly**
4. **Monitor for unusual activity**
5. **Implement IP whitelisting** (if needed)

### Security Headers

All responses include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`

## Documentation

- **Interactive API Docs**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI Spec**: http://localhost:8080/openapi.json

## Support

- **GitHub Issues**: https://github.com/lionagi/lionagi-qe-fleet/issues
- **Documentation**: https://github.com/lionagi/lionagi-qe-fleet/tree/main/docs

## Version

Current API Version: **1.0.0**

Built with:
- FastAPI 0.109+
- Python 3.10+
- WebSockets 12.0+
