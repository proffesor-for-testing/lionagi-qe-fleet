# AQE Fleet API - cURL Examples

Complete examples for all API endpoints using cURL.

## Authentication

All endpoints require an API key in the Authorization header:

```bash
export API_KEY="aqe_your_api_key_here"
export API_URL="http://localhost:8080"
```

## Health Check

```bash
curl -X GET "${API_URL}/health"
```

**Response:**
```json
{
  "status": "healthy",
  "service": "agentic-qe-fleet-api",
  "version": "1.0.0"
}
```

## Test Generation

### Generate Unit Tests

```bash
curl -X POST "${API_URL}/api/v1/test/generate" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "src/services/user.service.ts",
    "framework": "jest",
    "test_type": "unit",
    "coverage_target": 90.0,
    "priority": "high"
  }'
```

### Generate Integration Tests

```bash
curl -X POST "${API_URL}/api/v1/test/generate" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "src/api/",
    "framework": "pytest",
    "test_type": "integration",
    "coverage_target": 85.0,
    "priority": "medium",
    "callback_url": "https://your-ci-server.com/webhook"
  }'
```

## Test Execution

### Execute Tests with Coverage

```bash
curl -X POST "${API_URL}/api/v1/test/execute" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "test_path": "tests/",
    "framework": "jest",
    "parallel": true,
    "coverage": true,
    "timeout": 300
  }'
```

### Execute Tests with Environment Variables

```bash
curl -X POST "${API_URL}/api/v1/test/execute" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "test_path": "tests/integration/",
    "framework": "pytest",
    "parallel": true,
    "coverage": true,
    "env_vars": {
      "DATABASE_URL": "postgresql://test:test@localhost/testdb",
      "API_KEY": "test-key-123"
    }
  }'
```

## Coverage Analysis

### Analyze Coverage with Gap Detection

```bash
curl -X POST "${API_URL}/api/v1/coverage/analyze" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "src/",
    "test_path": "tests/",
    "min_coverage": 80.0,
    "include_gaps": true
  }'
```

## Quality Gate Validation

### Validate Quality Gates

```bash
curl -X POST "${API_URL}/api/v1/quality/gate" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": ".",
    "min_coverage": 80.0,
    "max_complexity": 10,
    "max_duplicates": 3.0,
    "security_checks": true,
    "priority": "high"
  }'
```

## Security Scanning

### Full Security Scan

```bash
curl -X POST "${API_URL}/api/v1/security/scan" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "target": ".",
    "scan_dependencies": true,
    "scan_code": true,
    "severity_threshold": "medium",
    "priority": "high"
  }'
```

### Quick Dependency Scan

```bash
curl -X POST "${API_URL}/api/v1/security/scan" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "target": ".",
    "scan_dependencies": true,
    "scan_code": false,
    "severity_threshold": "high"
  }'
```

## Performance Testing

### Run Load Test

```bash
curl -X POST "${API_URL}/api/v1/performance/test" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://api.example.com/users",
    "duration_seconds": 60,
    "virtual_users": 50,
    "ramp_up_seconds": 10,
    "think_time_ms": 1000
  }'
```

## Fleet Status

### Get Fleet Status

```bash
curl -X POST "${API_URL}/api/v1/fleet/status" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "verbose": true,
    "include_metrics": true
  }'
```

## Job Management

### Get Job Status

```bash
# Save job ID from creation response
JOB_ID="test-gen-123abc"

curl -X GET "${API_URL}/api/v1/job/${JOB_ID}/status" \
  -H "Authorization: Bearer ${API_KEY}"
```

### Get Job Result

```bash
curl -X GET "${API_URL}/api/v1/job/${JOB_ID}/result" \
  -H "Authorization: Bearer ${API_KEY}"
```

### Stream Job Progress (WebSocket - using websocat)

```bash
# Install websocat: cargo install websocat
websocat "ws://localhost:8080/api/v1/job/${JOB_ID}/stream"
```

## CI/CD Integration Examples

### GitHub Actions

```yaml
name: QE Fleet Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Generate Tests
        run: |
          RESPONSE=$(curl -X POST "${{ secrets.AQE_API_URL }}/api/v1/test/generate" \
            -H "Authorization: Bearer ${{ secrets.AQE_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "target": "src/",
              "framework": "jest",
              "test_type": "unit",
              "coverage_target": 80.0
            }')

          JOB_ID=$(echo $RESPONSE | jq -r '.job_id')
          echo "JOB_ID=$JOB_ID" >> $GITHUB_ENV

      - name: Wait for Completion
        run: |
          while true; do
            STATUS=$(curl -X GET "${{ secrets.AQE_API_URL }}/api/v1/job/$JOB_ID/status" \
              -H "Authorization: Bearer ${{ secrets.AQE_API_KEY }}" \
              | jq -r '.status')

            if [ "$STATUS" = "completed" ]; then
              echo "Job completed successfully"
              break
            elif [ "$STATUS" = "failed" ]; then
              echo "Job failed"
              exit 1
            fi

            sleep 5
          done
```

### GitLab CI

```yaml
qe-tests:
  stage: test
  script:
    - |
      RESPONSE=$(curl -X POST "${AQE_API_URL}/api/v1/test/execute" \
        -H "Authorization: Bearer ${AQE_API_KEY}" \
        -H "Content-Type: application/json" \
        -d '{
          "test_path": "tests/",
          "framework": "pytest",
          "parallel": true,
          "coverage": true
        }')

      JOB_ID=$(echo $RESPONSE | jq -r '.job_id')

      # Wait for completion
      while true; do
        STATUS=$(curl -X GET "${AQE_API_URL}/api/v1/job/${JOB_ID}/status" \
          -H "Authorization: Bearer ${AQE_API_KEY}" \
          | jq -r '.status')

        [ "$STATUS" = "completed" ] && break
        [ "$STATUS" = "failed" ] && exit 1
        sleep 5
      done
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any

    environment {
        AQE_API_URL = credentials('aqe-api-url')
        AQE_API_KEY = credentials('aqe-api-key')
    }

    stages {
        stage('Quality Gate') {
            steps {
                script {
                    def response = sh(
                        script: """
                            curl -X POST "\${AQE_API_URL}/api/v1/quality/gate" \
                              -H "Authorization: Bearer \${AQE_API_KEY}" \
                              -H "Content-Type: application/json" \
                              -d '{
                                "project_path": ".",
                                "min_coverage": 80.0,
                                "max_complexity": 10,
                                "security_checks": true
                              }'
                        """,
                        returnStdout: true
                    ).trim()

                    def job = readJSON text: response
                    def jobId = job.job_id

                    // Wait for completion
                    waitUntil {
                        def status = sh(
                            script: """
                                curl -X GET "\${AQE_API_URL}/api/v1/job/\${jobId}/status" \
                                  -H "Authorization: Bearer \${AQE_API_KEY}" \
                                | jq -r '.status'
                            """,
                            returnStdout: true
                        ).trim()

                        return status == 'completed' || status == 'failed'
                    }
                }
            }
        }
    }
}
```

## Rate Limit Handling

```bash
# Check rate limit headers
curl -X GET "${API_URL}/api/v1/fleet/status" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"verbose": false, "include_metrics": false}' \
  -i | grep -i "x-ratelimit"

# Expected headers:
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 95
# X-RateLimit-Reset: 1673524800
```

## Error Handling

```bash
# Handle 429 (Rate Limit Exceeded)
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}/api/v1/test/generate" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"target": "src/", "framework": "jest"}')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "429" ]; then
  RETRY_AFTER=$(echo "$BODY" | jq -r '.details.reset')
  echo "Rate limit exceeded. Retry after: $RETRY_AFTER"
  exit 1
fi

# Handle 401 (Unauthorized)
if [ "$HTTP_CODE" = "401" ]; then
  echo "Authentication failed. Check API key."
  exit 1
fi
```
