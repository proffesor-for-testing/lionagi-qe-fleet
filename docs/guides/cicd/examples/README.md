# CI/CD Example Workflows

**Ready-to-use workflow examples for major CI/CD platforms**

---

## Available Examples

### GitHub Actions

| Example | Description | File |
|---------|-------------|------|
| **Basic** | Simple test generation and quality gate | [basic.yml](./github-actions/basic.yml) |
| **Advanced** | Parallel jobs, caching, artifacts, PR comments | [advanced.yml](./github-actions/advanced.yml) |

**Setup**:
```bash
# Copy to your repository
mkdir -p .github/workflows
cp github-actions/basic.yml .github/workflows/qe-fleet.yml

# Add API key to secrets
# Settings → Secrets → Actions → New repository secret
# Name: ANTHROPIC_API_KEY
# Value: sk-ant-...
```

---

### GitLab CI

| Example | Description | File |
|---------|-------------|------|
| **Basic** | Simple CI configuration with coverage reporting | [basic.yml](./gitlab-ci/basic.yml) |

**Setup**:
```bash
# Copy to your repository
cp gitlab-ci/basic.yml .gitlab-ci.yml

# Add API key to CI/CD variables
# Settings → CI/CD → Variables → Add variable
# Key: ANTHROPIC_API_KEY
# Value: sk-ant-...
# Protected: Yes
# Masked: Yes
```

---

### Jenkins

| Example | Description | File |
|---------|-------------|------|
| **Basic** | Jenkinsfile with test generation and quality gates | [Jenkinsfile-basic](./jenkins/Jenkinsfile-basic) |

**Setup**:
```bash
# Copy to your repository
cp jenkins/Jenkinsfile-basic Jenkinsfile

# Add API key to credentials
# Manage Jenkins → Manage Credentials → Add Credentials
# Kind: Secret text
# Secret: sk-ant-...
# ID: anthropic-api-key
```

---

### CircleCI

| Example | Description | File |
|---------|-------------|------|
| **Basic** | CircleCI config with parallel jobs and artifacts | [config.yml](./circleci/config.yml) |

**Setup**:
```bash
# Copy to your repository
mkdir -p .circleci
cp circleci/config.yml .circleci/config.yml

# Add API key to project settings
# Project Settings → Environment Variables → Add Variable
# Name: ANTHROPIC_API_KEY
# Value: sk-ant-...
```

---

## Quick Customization

### Change Python Version

**GitHub Actions**:
```yaml
- uses: actions/setup-python@v4
  with:
    python-version: '3.12'  # Change from 3.11
```

**GitLab CI**:
```yaml
image: python:3.12-slim  # Change from 3.11-slim
```

**Jenkins**:
```groovy
environment {
    PYTHON_VERSION = '3.12'  // Change from '3.11'
}
```

---

### Change Coverage Threshold

All platforms:
```bash
# Change from 80 to 85
aqe quality-gate --coverage-threshold 85 --fail-on-error
```

---

### Add Security Scanning

All platforms:
```bash
# Add before quality gate
aqe security-scan src/ --scan-type comprehensive --ci-mode
```

---

### Store Artifacts in S3

All platforms:
```bash
# Set environment variables
export QE_STORAGE_BACKEND=s3
export QE_S3_BUCKET=my-qe-artifacts

# Commands automatically use S3
aqe execute tests/ --store-artifacts
```

---

## Platform Comparison

| Feature | GitHub Actions | GitLab CI | Jenkins | CircleCI |
|---------|----------------|-----------|---------|----------|
| **Parallel Jobs** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Caching** | ✅ Built-in | ✅ Built-in | ⚠️ Plugin | ✅ Built-in |
| **Artifacts** | ✅ Built-in | ✅ Built-in | ✅ Built-in | ✅ Built-in |
| **PR Comments** | ✅ Yes | ✅ Yes | ⚠️ Plugin | ⚠️ API |
| **Badges** | ✅ Built-in | ✅ Built-in | ⚠️ Plugin | ✅ Built-in |
| **Cost** | ✅ Free (public) | ✅ Free tier | ✅ Free (self-host) | ✅ Free tier |

---

## Common Modifications

### Run Only on Main Branch

**GitHub Actions**:
```yaml
on:
  push:
    branches: [main]  # Only main
```

**GitLab CI**:
```yaml
generate_tests:
  only:
    - main  # Only main
```

**Jenkins**:
```groovy
when {
    branch 'main'  // Only main
}
```

---

### Skip on Draft PRs

**GitHub Actions**:
```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]

jobs:
  qe:
    if: github.event.pull_request.draft == false
```

---

### Scheduled Runs

**GitHub Actions**:
```yaml
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
```

**GitLab CI**:
```yaml
# Use GitLab UI: CI/CD → Schedules
```

---

## Troubleshooting Examples

See [Troubleshooting Guide](../troubleshooting.md) for common issues.

### Example Not Working?

1. **Check API key**: Ensure it's set correctly in CI secrets
2. **Check Python version**: Must be 3.10+
3. **Check QE Fleet version**: Use `lionagi-qe-fleet==1.2.1`
4. **Check logs**: Look for error messages in CI output
5. **Enable debug mode**: Add `--verbose` flag

---

## Need More Examples?

- **Advanced Patterns**: [Best Practices](../best-practices.md)
- **Custom Workflows**: [API Reference](../webhook-integration.md)
- **Community Examples**: [GitHub Discussions](https://github.com/lionagi/lionagi-qe-fleet/discussions)

---

## Contributing Examples

Have a great workflow example? Share it!

1. Test your workflow thoroughly
2. Add clear comments
3. Submit PR to [lionagi-qe-fleet](https://github.com/lionagi/lionagi-qe-fleet)
4. Include description and screenshots

---

**Last Updated**: 2025-11-12
**Examples**: 6 workflows across 4 platforms
**Status**: Production Ready
