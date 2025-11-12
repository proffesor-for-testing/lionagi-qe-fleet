# CLI Usage in CI Environments

**Complete guide to using LionAGI QE Fleet CLI in CI/CD pipelines**

---

## Overview

The QE Fleet CLI is designed for CI/CD environments with:

- **Non-interactive mode** - No prompts or user input required
- **Standardized exit codes** - For CI workflow control
- **JSON output** - Machine-readable results
- **Quiet mode** - Minimal output for clean logs
- **CI mode** - Optimized settings for CI environments

---

## Installation in CI

### Using pip

```bash
pip install lionagi-qe-fleet
```

### Using pip with caching (faster)

```bash
pip install --cache-dir .pip-cache lionagi-qe-fleet
```

### Using uv (fastest)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install lionagi-qe-fleet
```

### Version pinning (recommended)

```bash
pip install lionagi-qe-fleet==1.2.1
```

---

## Global Flags for CI

All commands support these CI-optimized flags:

### `--ci-mode`

Enables CI-optimized settings:
- Non-interactive (no prompts)
- Structured logging
- Optimized timeouts
- Fail-fast behavior

```bash
aqe generate src/ --ci-mode
```

### `--json`

Output results in JSON format for programmatic parsing:

```bash
aqe generate src/ --json > results.json
```

**Output structure**:
```json
{
  "status": "success",
  "data": {
    "tests_generated": 42,
    "files_processed": 15,
    "coverage_estimate": 87.5
  },
  "timestamp": "2025-11-12T10:00:00Z"
}
```

### `--quiet` / `-q`

Suppress non-essential output:

```bash
aqe execute tests/ --quiet
```

**Output**: Only errors and final results

### `--non-interactive`

Disable all prompts (use defaults or fail):

```bash
aqe security-scan src/ --non-interactive
```

### `--output-format <format>`

Specify output format (json, xml, html, text):

```bash
aqe coverage-analyze tests/ --output-format xml
```

---

## Exit Codes

All commands use standardized exit codes for CI workflow control:

| Code | Meaning | CI Action |
|------|---------|-----------|
| `0` | Success | Continue workflow |
| `1` | General error | Fail workflow |
| `2` | Quality gate failed | Configurable (usually fail) |
| `3` | Configuration error | Fail workflow |
| `4` | API error (transient) | Retry recommended |
| `5` | Timeout | Fail or retry |

### Using Exit Codes in CI

**Fail on quality gate**:
```bash
aqe quality-gate --threshold 80
if [ $? -ne 0 ]; then
  echo "Quality gate failed!"
  exit 1
fi
```

**Retry on API errors**:
```bash
for i in {1..3}; do
  aqe generate src/ && break
  [ $? -eq 4 ] && sleep 10 || exit $?
done
```

**Continue on quality gate failure (warning only)**:
```bash
aqe quality-gate --threshold 80 || echo "⚠️ Quality gate failed (non-blocking)"
```

---

## Core Commands for CI

### 1. Test Generation

Generate tests for your codebase:

```bash
aqe generate <path> [options]
```

**Options**:
- `--framework <name>` - Test framework (pytest, jest, mocha, etc.)
- `--test-type <type>` - Test type (unit, integration, e2e)
- `--coverage-target <pct>` - Target coverage (0-100)
- `--output <dir>` - Output directory for generated tests
- `--parallel` - Generate tests in parallel
- `--ci-mode` - CI-optimized settings

**Examples**:

```bash
# Basic generation
aqe generate src/ --ci-mode

# With all options
aqe generate src/ \
  --framework pytest \
  --test-type unit \
  --coverage-target 85 \
  --output tests/generated/ \
  --parallel \
  --ci-mode \
  --json

# Multiple test types
aqe generate src/ --test-type unit,integration --ci-mode
```

**Output**:
```json
{
  "status": "success",
  "data": {
    "tests_generated": 42,
    "files_processed": 15,
    "coverage_estimate": 87.5,
    "test_files": [
      "tests/generated/test_user.py",
      "tests/generated/test_auth.py"
    ]
  },
  "timestamp": "2025-11-12T10:00:00Z"
}
```

---

### 2. Test Execution

Execute test suites with coverage:

```bash
aqe execute <path> [options]
```

**Options**:
- `--framework <name>` - Test framework
- `--parallel` - Parallel execution
- `--coverage` - Collect coverage metrics
- `--timeout <sec>` - Execution timeout
- `--format <fmt>` - Output format (json, xml, html)
- `--fail-fast` - Stop on first failure

**Examples**:

```bash
# Basic execution
aqe execute tests/ --ci-mode

# With coverage
aqe execute tests/ --parallel --coverage --ci-mode

# With timeout
aqe execute tests/ --timeout 300 --fail-fast --json

# Specific framework
aqe execute tests/ --framework pytest --coverage
```

**Output**:
```json
{
  "status": "success",
  "data": {
    "tests_run": 156,
    "passed": 154,
    "failed": 2,
    "skipped": 0,
    "duration": 45.3,
    "coverage": {
      "line_rate": 87.5,
      "branch_rate": 82.3,
      "lines_covered": 1234,
      "lines_total": 1410
    }
  }
}
```

---

### 3. Coverage Analysis

Analyze test coverage and find gaps:

```bash
aqe coverage-analyze <path> [options]
```

**Options**:
- `--threshold <pct>` - Minimum coverage threshold
- `--show-gaps` - Display uncovered code
- `--format <fmt>` - Output format

**Examples**:

```bash
# Basic analysis
aqe coverage-analyze tests/ --ci-mode

# With threshold
aqe coverage-analyze tests/ --threshold 80 --json

# Show gaps
aqe coverage-analyze tests/ --show-gaps --format json
```

---

### 4. Quality Gate

Validate code quality against thresholds:

```bash
aqe quality-gate [options]
```

**Options**:
- `--coverage-threshold <pct>` - Minimum coverage
- `--quality-threshold <score>` - Minimum quality score
- `--fail-on-error` - Exit 2 if thresholds not met
- `--rules <file>` - Custom quality rules (JSON)

**Examples**:

```bash
# Basic quality gate
aqe quality-gate --coverage-threshold 80 --fail-on-error

# With custom rules
aqe quality-gate --rules .qe-rules.json --ci-mode

# Multiple thresholds
aqe quality-gate \
  --coverage-threshold 80 \
  --quality-threshold 85 \
  --security-threshold 90 \
  --fail-on-error
```

**Output**:
```json
{
  "status": "failed",
  "data": {
    "coverage": {
      "actual": 75.3,
      "threshold": 80.0,
      "passed": false
    },
    "quality": {
      "actual": 92.0,
      "threshold": 85.0,
      "passed": true
    }
  },
  "message": "Quality gate failed: Coverage below threshold"
}
```

---

### 5. Security Scanning

Scan for security vulnerabilities:

```bash
aqe security-scan <path> [options]
```

**Options**:
- `--scan-type <type>` - Scan type (sast, dast, dependency, secrets, comprehensive)
- `--severity <level>` - Min severity to report (low, medium, high, critical)
- `--format <fmt>` - Output format

**Examples**:

```bash
# Comprehensive scan
aqe security-scan src/ --scan-type comprehensive --ci-mode

# Secrets only
aqe security-scan . --scan-type secrets --json

# High/Critical only
aqe security-scan src/ --severity high --format json
```

---

### 6. Performance Testing

Run performance/load tests:

```bash
aqe performance-test <path> [options]
```

**Options**:
- `--load <count>` - Concurrent users/requests
- `--duration <sec>` - Test duration
- `--rps <rate>` - Requests per second target

**Examples**:

```bash
# Basic load test
aqe performance-test tests/perf/ --load 100 --ci-mode

# With duration
aqe performance-test tests/perf/ --load 500 --duration 300 --json
```

---

## Piping and Scripting

### Capture Output

```bash
# Save JSON results
aqe generate src/ --json > results.json

# Parse with jq
aqe execute tests/ --json | jq '.data.coverage.line_rate'

# Check specific field
COVERAGE=$(aqe coverage-analyze --json | jq -r '.data.coverage')
if (( $(echo "$COVERAGE < 80" | bc -l) )); then
  echo "Coverage too low: $COVERAGE"
  exit 1
fi
```

### Conditional Execution

```bash
# Run tests only if generation succeeds
aqe generate src/ --ci-mode && aqe execute tests/ --ci-mode

# Quality gate or exit
aqe quality-gate --threshold 80 || exit 2

# Multiple stages with error handling
aqe generate src/ --ci-mode || exit 1
aqe execute tests/ --ci-mode || exit 1
aqe quality-gate --threshold 80 || exit 2
```

### Parallel Commands

```bash
# Run multiple scans in parallel
aqe security-scan src/ --scan-type sast --json > sast.json &
aqe security-scan src/ --scan-type dependency --json > deps.json &
wait

# Check all results
jq -s '.' sast.json deps.json > combined-security.json
```

---

## Environment Variables

Configure QE Fleet via environment variables:

### API Keys

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
```

### Configuration

```bash
# Storage backend
export QE_STORAGE_BACKEND="s3"
export QE_S3_BUCKET="my-qe-artifacts"

# Memory backend
export QE_MEMORY_BACKEND="postgres"
export QE_POSTGRES_URL="postgresql://user:pass@localhost:5432/qe"

# Logging
export QE_LOG_LEVEL="INFO"
export QE_LOG_FILE="/tmp/qe-fleet.log"

# Timeouts
export QE_EXECUTION_TIMEOUT="600"
export QE_GENERATION_TIMEOUT="300"

# Cost optimization
export QE_ROUTING_ENABLED="true"
```

---

## Platform-Specific Examples

### GitHub Actions

```yaml
- name: Generate Tests
  run: aqe generate src/ --ci-mode --json | tee results.json
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

- name: Parse Results
  id: results
  run: |
    COVERAGE=$(jq -r '.data.coverage_estimate' results.json)
    echo "coverage=$COVERAGE" >> $GITHUB_OUTPUT

- name: Quality Gate
  run: aqe quality-gate --coverage-threshold 80 --fail-on-error
```

### GitLab CI

```yaml
generate_tests:
  script:
    - aqe generate src/ --ci-mode --json > results.json
    - export COVERAGE=$(jq -r '.data.coverage_estimate' results.json)
    - echo "Coverage estimate: $COVERAGE%"
    - aqe quality-gate --coverage-threshold 80 --fail-on-error
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

### Jenkins

```groovy
stage('Quality Engineering') {
    steps {
        sh '''
            aqe generate src/ --ci-mode --json > results.json
            COVERAGE=$(jq -r '.data.coverage_estimate' results.json)
            echo "Coverage: $COVERAGE%"
            aqe quality-gate --coverage-threshold 80 --fail-on-error
        '''
    }
}
```

### CircleCI

```yaml
- run:
    name: Generate Tests
    command: |
      aqe generate src/ --ci-mode --json | tee results.json
      COVERAGE=$(jq -r '.data.coverage_estimate' results.json)
      echo "export COVERAGE=$COVERAGE" >> $BASH_ENV
```

---

## Troubleshooting

### Command Not Found

```bash
# Try full module path
python -m lionagi_qe generate src/ --ci-mode

# Check installation
pip show lionagi-qe-fleet

# Check PATH
which aqe
echo $PATH
```

### Timeout Issues

```bash
# Increase timeout
aqe generate src/ --timeout 600 --ci-mode

# Set via environment
export QE_GENERATION_TIMEOUT=600
aqe generate src/ --ci-mode
```

### API Rate Limits

```bash
# Add retry logic
for i in {1..3}; do
  aqe generate src/ --ci-mode && break
  [ $? -eq 4 ] && { echo "Retrying..."; sleep 30; } || exit $?
done
```

[→ Full Troubleshooting Guide](./troubleshooting.md)

---

## Best Practices

1. **Always use `--ci-mode`** - Optimized for CI environments
2. **Pin versions** - Use `lionagi-qe-fleet==1.2.1` not `latest`
3. **Cache dependencies** - Speed up CI runs
4. **Use JSON output** - For programmatic parsing
5. **Handle exit codes** - Don't ignore failures
6. **Set timeouts** - Prevent hanging jobs
7. **Use environment variables** - For configuration
8. **Store artifacts** - Save test results
9. **Enable parallel execution** - Faster CI runs
10. **Monitor costs** - Track AI API usage

[→ Best Practices Guide](./best-practices.md)

---

## Next Steps

- [Webhook API Guide](./webhook-integration.md) - For advanced integrations
- [Artifact Storage](./artifact-storage.md) - Store historical results
- [Badge Generation](./badges.md) - Display metrics
- [Example Workflows](./examples/) - Platform-specific examples

---

**Last Updated**: 2025-11-12
**Version**: 1.0.0
