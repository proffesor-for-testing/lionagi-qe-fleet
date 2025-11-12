# Artifact Storage Guide

**Store and query test results, coverage reports, and security findings**

---

## Overview

The Artifact Storage system provides pluggable backends for persisting QE Fleet results with compression, retention policies, and historical querying.

**Supported Backends**:
- **Local** - Filesystem storage (development)
- **S3** - AWS S3/MinIO (production)
- **CI-Native** - Platform artifact storage (GitHub Actions, GitLab CI)

---

## Quick Start

### 1. Configure Storage Backend

```python
# config/storage.json
{
  "backend": "s3",
  "s3": {
    "bucket": "my-qe-artifacts",
    "region": "us-east-1",
    "prefix": "qe-fleet/"
  },
  "retention": {
    "default_days": 90,
    "test_results": 30,
    "coverage_reports": 90,
    "security_findings": 365
  },
  "compression": {
    "enabled": true,
    "algorithm": "gzip",
    "level": 6
  }
}
```

### 2. Store Artifacts via CLI

```bash
# Automatically stores results
aqe generate src/ --output tests/generated/ --store-artifacts

# Explicit storage
aqe execute tests/ --store-artifacts --artifact-key "build-$CI_COMMIT_SHA"
```

### 3. Query Historical Data

```bash
# List recent artifacts
aqe artifacts list --limit 10

# Get specific artifact
aqe artifacts get build-abc123

# Compare runs
aqe artifacts compare build-abc123 build-def456
```

---

## Storage Backends

### Local Storage

**Best for**: Development, testing

**Configuration**:
```python
{
  "backend": "local",
  "local": {
    "base_path": ".qe-artifacts/",
    "create_dirs": true
  }
}
```

**Pros**:
- ✅ Zero setup
- ✅ Fast access
- ✅ No external dependencies

**Cons**:
- ⚠️ Not shared across CI runs
- ⚠️ Limited by disk space
- ⚠️ No automatic cleanup

---

### S3 Storage (Recommended)

**Best for**: Production, team collaboration

**Configuration**:
```python
{
  "backend": "s3",
  "s3": {
    "bucket": "my-qe-artifacts",
    "region": "us-east-1",
    "access_key_id": "${AWS_ACCESS_KEY_ID}",
    "secret_access_key": "${AWS_SECRET_ACCESS_KEY}",
    "endpoint_url": null,  # For MinIO: "https://minio.example.com"
    "prefix": "qe-fleet/",
    "use_ssl": true
  }
}
```

**Setup AWS S3**:
```bash
# Create bucket
aws s3 mb s3://my-qe-artifacts

# Set lifecycle policy
aws s3api put-bucket-lifecycle-configuration \
  --bucket my-qe-artifacts \
  --lifecycle-configuration file://lifecycle.json
```

**Pros**:
- ✅ Unlimited storage
- ✅ Automatic retention
- ✅ Shared across team
- ✅ Historical querying

---

### CI-Native Storage

**Best for**: Platform-specific features, no external setup

**GitHub Actions**:
```yaml
- name: Store Artifacts
  uses: actions/upload-artifact@v4
  with:
    name: qe-results
    path: |
      coverage.xml
      tests/generated/
      security-report.json
    retention-days: 90
```

**GitLab CI**:
```yaml
artifacts:
  paths:
    - coverage.xml
    - tests/generated/
  reports:
    coverage_report:
      coverage_format: cobertura
      path: coverage.xml
  expire_in: 90 days
```

---

## Artifact Types

### Test Results

Stores execution results, pass/fail status, duration.

```json
{
  "type": "test_results",
  "timestamp": "2025-11-12T10:00:00Z",
  "data": {
    "tests_run": 156,
    "passed": 154,
    "failed": 2,
    "duration": 45.3,
    "failures": [...]
  }
}
```

### Coverage Reports

Stores coverage metrics and uncovered code.

```json
{
  "type": "coverage",
  "timestamp": "2025-11-12T10:00:00Z",
  "data": {
    "line_rate": 87.5,
    "branch_rate": 82.3,
    "files": {...}
  }
}
```

### Security Findings

Stores vulnerability scan results.

```json
{
  "type": "security",
  "timestamp": "2025-11-12T10:00:00Z",
  "data": {
    "vulnerabilities": [...],
    "summary": {
      "critical": 0,
      "high": 1,
      "medium": 3
    }
  }
}
```

---

## Querying Artifacts

### List Artifacts

```bash
# Recent artifacts
aqe artifacts list --limit 10

# Filter by type
aqe artifacts list --type coverage --limit 5

# Date range
aqe artifacts list --since 2025-11-01 --until 2025-11-12
```

### Get Specific Artifact

```bash
# By key
aqe artifacts get build-abc123

# By commit SHA
aqe artifacts get --commit abc123def456

# Latest for branch
aqe artifacts get --branch main --latest
```

### Compare Artifacts

```bash
# Compare two runs
aqe artifacts compare build-abc123 build-def456

# Compare against baseline
aqe artifacts compare build-abc123 --baseline main

# Show only changes
aqe artifacts compare build-abc123 build-def456 --diff-only
```

**Output**:
```json
{
  "comparison": {
    "coverage": {
      "before": 85.3,
      "after": 87.5,
      "change": +2.2
    },
    "tests": {
      "before": 154,
      "after": 156,
      "change": +2
    }
  }
}
```

---

## Retention Policies

### Automatic Cleanup

Configure retention by artifact type:

```python
{
  "retention": {
    "default_days": 90,
    "test_results": 30,
    "coverage_reports": 90,
    "security_findings": 365,
    "keep_latest_n": 100  # Keep last 100 regardless of age
  }
}
```

### Manual Cleanup

```bash
# Delete old artifacts
aqe artifacts cleanup --older-than 90d

# Delete by key
aqe artifacts delete build-abc123

# Delete all for branch
aqe artifacts delete --branch feature-x --all
```

---

## CI Integration Examples

### GitHub Actions with S3

```yaml
- name: Run Tests & Store Results
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  run: |
    aqe execute tests/ --store-artifacts \
      --artifact-key "build-${{ github.sha }}" \
      --metadata '{"branch": "${{ github.ref_name }}", "pr": "${{ github.event.number }}"}'
```

### GitLab CI with Artifacts

```yaml
test:
  script:
    - aqe execute tests/ --coverage
  artifacts:
    paths:
      - coverage.xml
      - tests/generated/
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    expire_in: 90 days
```

---

## Best Practices

1. **Use S3 for production** - Reliable, scalable
2. **Set retention policies** - Control costs
3. **Tag artifacts** - For easy querying
4. **Compress large artifacts** - Reduce storage costs
5. **Keep historical baselines** - For trend analysis
6. **Clean up feature branches** - After merge
7. **Monitor storage usage** - Track costs
8. **Use lifecycle policies** - Automatic cleanup

---

## Next Steps

- [Badge Generation](./badges.md) - Display metrics from artifacts
- [Webhook API](./webhook-integration.md) - Programmatic access
- [Troubleshooting](./troubleshooting.md) - Storage issues

---

**Last Updated**: 2025-11-12
