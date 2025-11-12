# Webhook API Integration Guide

**REST API integration for advanced CI/CD workflows**

---

## Overview

The QE Fleet Webhook API provides HTTP/WebSocket endpoints for programmatic access to all QE agents. Perfect for custom integrations, advanced workflows, and real-time updates.

**Key Features**:
- ✅ REST API with 17 endpoints (one per agent)
- ✅ WebSocket streaming for real-time progress
- ✅ Authentication via API keys
- ✅ Rate limiting and usage tracking
- ✅ OpenAPI/Swagger documentation

---

## Quick Start

### 1. Generate API Key

```bash
# Generate API key (stores in ~/.qe-fleet/api-key)
aqe auth create-key

# Output:
# API Key: qe_key_abc123def456...
# Store this securely - it won't be shown again
```

### 2. Basic Request

```bash
curl -X POST https://api.example.com/api/v1/qe/generate \
  -H "Authorization: Bearer qe_key_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def add(a, b): return a + b",
    "framework": "pytest",
    "test_type": "unit"
  }'
```

### 3. Parse Response

```json
{
  "status": "success",
  "request_id": "req_abc123",
  "data": {
    "test_code": "def test_add():\n    assert add(1, 2) == 3",
    "test_name": "test_add",
    "coverage_estimate": 100.0
  },
  "usage": {
    "tokens": 1234,
    "cost": 0.0012,
    "model": "gpt-4o-mini"
  }
}
```

---

## API Endpoints

### Base URL

```
https://api.example.com/api/v1/qe
```

### Authentication

All requests require Bearer token authentication:

```bash
Authorization: Bearer qe_key_...
```

---

## Core Endpoints

### 1. Test Generation

**POST** `/generate`

Generate comprehensive test suites.

**Request**:
```json
{
  "code": "string",
  "framework": "pytest|jest|mocha",
  "test_type": "unit|integration|e2e",
  "coverage_target": 80.0,
  "include_edge_cases": true
}
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "test_code": "string",
    "test_name": "string",
    "assertions": ["assertion1", "assertion2"],
    "edge_cases": ["edge1", "edge2"],
    "coverage_estimate": 87.5
  }
}
```

**cURL Example**:
```bash
curl -X POST https://api.example.com/api/v1/qe/generate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "code": "def multiply(a, b): return a * b",
  "framework": "pytest",
  "test_type": "unit",
  "coverage_target": 90.0
}
EOF
```

---

### 2. Test Execution

**POST** `/execute`

Execute test suites with coverage tracking.

**Request**:
```json
{
  "test_path": "tests/",
  "framework": "pytest",
  "parallel": true,
  "coverage": true,
  "timeout": 300
}
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "tests_run": 156,
    "passed": 154,
    "failed": 2,
    "duration": 45.3,
    "coverage": {
      "line_rate": 87.5,
      "branch_rate": 82.3
    }
  }
}
```

---

### 3. Coverage Analysis

**POST** `/coverage/analyze`

Analyze test coverage and identify gaps.

**Request**:
```json
{
  "test_path": "tests/",
  "code_path": "src/",
  "threshold": 80.0
}
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "coverage": 87.5,
    "gaps": [
      {
        "file": "src/user.py",
        "line_start": 42,
        "line_end": 45,
        "reason": "Exception handling not covered"
      }
    ]
  }
}
```

---

### 4. Security Scanning

**POST** `/security/scan`

Comprehensive security vulnerability scanning.

**Request**:
```json
{
  "path": "src/",
  "scan_type": "comprehensive",
  "severity": "medium"
}
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "vulnerabilities": [
      {
        "severity": "high",
        "type": "SQL Injection",
        "file": "src/db.py",
        "line": 89,
        "description": "Unsanitized user input in SQL query"
      }
    ],
    "summary": {
      "critical": 0,
      "high": 1,
      "medium": 3,
      "low": 7
    }
  }
}
```

---

### 5. Quality Gate

**POST** `/quality/gate`

Validate code quality against thresholds.

**Request**:
```json
{
  "coverage_threshold": 80.0,
  "quality_threshold": 85.0,
  "security_threshold": 90.0
}
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "passed": false,
    "results": {
      "coverage": {"actual": 75.3, "threshold": 80.0, "passed": false},
      "quality": {"actual": 92.0, "threshold": 85.0, "passed": true},
      "security": {"actual": 95.0, "threshold": 90.0, "passed": true}
    },
    "message": "Quality gate failed: Coverage below threshold"
  }
}
```

---

## WebSocket Streaming

For real-time progress updates during long-running operations.

### Connection

```javascript
const ws = new WebSocket('wss://api.example.com/api/v1/qe/stream');

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'subscribe',
    endpoint: 'generate',
    token: 'qe_key_...',
    params: {
      code: '...',
      framework: 'pytest'
    }
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

### Event Types

```json
// Progress update
{
  "type": "progress",
  "percent": 45.2,
  "message": "Generating test for function: calculate_total"
}

// Result
{
  "type": "result",
  "data": {
    "test_code": "...",
    "coverage_estimate": 87.5
  }
}

// Error
{
  "type": "error",
  "error": {
    "code": "GENERATION_FAILED",
    "message": "Failed to generate tests"
  }
}
```

---

## Authentication

### API Key Management

**Create Key**:
```bash
aqe auth create-key --name "CI Pipeline"
```

**List Keys**:
```bash
aqe auth list-keys
```

**Revoke Key**:
```bash
aqe auth revoke-key qe_key_abc123...
```

**Rotate Key**:
```bash
aqe auth rotate-key qe_key_abc123...
```

### Security Best Practices

1. **Store securely** - Use CI secrets/vault
2. **Rotate regularly** - Every 90 days
3. **Limit scope** - Use separate keys per environment
4. **Monitor usage** - Track API calls
5. **Revoke on breach** - Immediately revoke compromised keys

---

## Rate Limiting

Default limits (configurable):

| Tier | Requests/Hour | Requests/Day | Concurrent |
|------|---------------|--------------|------------|
| **Free** | 100 | 1,000 | 5 |
| **Pro** | 1,000 | 10,000 | 20 |
| **Enterprise** | Unlimited | Unlimited | 100 |

**Rate Limit Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699564800
```

**429 Too Many Requests**:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 3600 seconds.",
    "retry_after": 3600
  }
}
```

---

## CI Platform Examples

### GitHub Actions

```yaml
- name: Generate Tests via API
  run: |
    RESPONSE=$(curl -X POST https://api.example.com/api/v1/qe/generate \
      -H "Authorization: Bearer ${{ secrets.QE_API_KEY }}" \
      -H "Content-Type: application/json" \
      -d '{"code": "$(cat src/user.py)", "framework": "pytest"}')

    echo "$RESPONSE" | jq '.data.test_code' > tests/test_user.py
```

### GitLab CI

```yaml
generate_tests:
  script:
    - |
      curl -X POST https://api.example.com/api/v1/qe/generate \
        -H "Authorization: Bearer $QE_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"code": "'"$(cat src/user.py)"'", "framework": "pytest"}' \
        | jq '.data.test_code' > tests/test_user.py
```

### Jenkins

```groovy
stage('Generate Tests') {
    steps {
        script {
            def response = sh(
                script: """
                    curl -X POST https://api.example.com/api/v1/qe/generate \\
                      -H "Authorization: Bearer ${QE_API_KEY}" \\
                      -H "Content-Type: application/json" \\
                      -d '{"code": "$(cat src/user.py)", "framework": "pytest"}'
                """,
                returnStdout: true
            )
            def json = readJSON text: response
            writeFile file: 'tests/test_user.py', text: json.data.test_code
        }
    }
}
```

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {
      "field": "Additional context"
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description | Action |
|------|-------------|-------------|--------|
| `INVALID_REQUEST` | 400 | Invalid request parameters | Fix request |
| `UNAUTHORIZED` | 401 | Invalid/missing API key | Check key |
| `FORBIDDEN` | 403 | Insufficient permissions | Upgrade plan |
| `NOT_FOUND` | 404 | Endpoint not found | Check URL |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests | Wait & retry |
| `INTERNAL_ERROR` | 500 | Server error | Retry later |
| `API_ERROR` | 502 | Upstream API error | Retry |
| `TIMEOUT` | 504 | Request timeout | Increase timeout |

---

## Best Practices

1. **Use WebSocket for long operations** - Real-time progress
2. **Implement retry logic** - Handle transient errors
3. **Cache responses** - Reduce API calls
4. **Batch requests** - Combine multiple operations
5. **Monitor usage** - Track costs and rate limits
6. **Use request IDs** - For debugging and tracing
7. **Set timeouts** - Prevent hanging requests
8. **Validate responses** - Check status codes
9. **Store credentials securely** - Use secrets management
10. **Log API calls** - For audit and debugging

---

## OpenAPI Documentation

Interactive API documentation available at:

```
https://api.example.com/docs
```

Features:
- ✅ Try API calls directly in browser
- ✅ Request/response examples
- ✅ Schema definitions
- ✅ Authentication testing
- ✅ Download OpenAPI spec

---

## Next Steps

- [Artifact Storage](./artifact-storage.md) - Store API results
- [Badge Generation](./badges.md) - Display metrics
- [CLI Usage](./cli-ci.md) - Command-line alternative
- [Troubleshooting](./troubleshooting.md) - Common API issues

---

**Last Updated**: 2025-11-12
**Version**: 1.0.0
