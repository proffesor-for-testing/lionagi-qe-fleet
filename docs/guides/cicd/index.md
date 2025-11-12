# CI/CD Integration Guide

**Version**: 1.2.1
**Status**: Production Ready
**Last Updated**: 2025-11-12

---

## Overview

Integrate LionAGI QE Fleet into your CI/CD pipeline to automate test generation, execution, coverage analysis, security scanning, and quality gates.

**Quick Links**:
- [5-Minute Quickstart](./quickstart.md) - Get running in 5 minutes
- [Example Workflows](./examples/) - Copy-paste examples for all major platforms
- [Troubleshooting](./troubleshooting.md) - Common issues and solutions
- [FAQ](./faq.md) - Frequently asked questions

---

## What You Can Automate

### ✅ Test Generation
- Automatically generate tests for new code in PRs
- AI-powered edge case detection
- Framework-agnostic (pytest, Jest, Mocha, Cypress, etc.)

### ✅ Test Execution
- Parallel test execution
- Real-time coverage analysis
- Cross-framework support

### ✅ Security Scanning
- SAST, DAST, dependency scanning
- Secrets detection
- Vulnerability reporting

### ✅ Quality Gates
- Automated quality gate validation
- Configurable thresholds
- PR blocking capabilities

### ✅ Coverage Analysis
- Real-time coverage tracking
- Gap detection with O(log n) algorithms
- Historical comparison

### ✅ Badge Generation
- Coverage, quality, security, and test count badges
- Shields.io compatible SVG
- Auto-updating via API

---

## Integration Methods

### 1. Command-Line Interface (CLI)

**Best for**: Quick setup, any CI platform, simple workflows

```bash
# Install
pip install lionagi-qe-fleet

# Run in CI
aqe generate src/ --ci-mode --json
aqe execute tests/ --parallel --coverage
```

[→ CLI Usage Guide](./cli-ci.md)

---

### 2. Webhook API (Generic)

**Best for**: Advanced workflows, custom integrations, any CI platform

```bash
# Trigger via HTTP
curl -X POST https://api.example.com/qe/generate \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"code_path": "src/", "framework": "pytest"}'
```

[→ Webhook API Guide](./webhook-integration.md)

---

### 3. Platform-Specific Plugins

**Best for**: Deep integration, platform-native features

- **GitHub Actions** - [Examples](./examples/github-actions/)
- **GitLab CI** - [Examples](./examples/gitlab-ci/)
- **Jenkins** - [Examples](./examples/jenkins/)
- **CircleCI** - [Examples](./examples/circleci/)

---

## Supported Platforms

| Platform | Support Level | Native Plugin | Webhook API | CLI |
|----------|---------------|---------------|-------------|-----|
| **GitHub Actions** | ✅ Full | Coming Soon | ✅ | ✅ |
| **GitLab CI** | ✅ Full | Coming Soon | ✅ | ✅ |
| **Jenkins** | ✅ Full | Coming Soon | ✅ | ✅ |
| **CircleCI** | ✅ Full | N/A | ✅ | ✅ |
| **Azure Pipelines** | ✅ Full | N/A | ✅ | ✅ |
| **Buildkite** | ✅ Full | N/A | ✅ | ✅ |
| **Travis CI** | ✅ Full | N/A | ✅ | ✅ |
| **TeamCity** | ✅ Full | N/A | ✅ | ✅ |

All platforms work via CLI or Webhook API. Native plugins are in development for GitHub Actions, GitLab CI, and Jenkins.

---

## Core Guides

### Getting Started
1. [**Quickstart**](./quickstart.md) - 5-minute setup
2. [**Best Practices**](./best-practices.md) - Recommended patterns

### Integration Methods
3. [**CLI Usage in CI**](./cli-ci.md) - Flags, exit codes, scripting
4. [**Webhook API**](./webhook-integration.md) - REST API integration
5. [**Artifact Storage**](./artifact-storage.md) - Store and query test results
6. [**Badge Generation**](./badges.md) - Display metrics in README

### Platform-Specific
7. [**GitHub Actions**](./examples/github-actions/) - Native workflows
8. [**GitLab CI**](./examples/gitlab-ci/) - .gitlab-ci.yml examples
9. [**Jenkins**](./examples/jenkins/) - Jenkinsfile examples
10. [**CircleCI**](./examples/circleci/) - .circleci/config.yml examples

### Advanced
11. [**Overview**](./overview.md) - Architecture and design
12. [**Troubleshooting**](./troubleshooting.md) - Common issues
13. [**FAQ**](./faq.md) - Frequently asked questions

---

## Quick Examples

### GitHub Actions

```yaml
name: QE Fleet
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install QE Fleet
        run: pip install lionagi-qe-fleet

      - name: Generate & Run Tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          aqe generate src/ --ci-mode --json > results.json
          aqe execute tests/ --parallel --coverage

      - name: Quality Gate
        run: aqe quality-gate --threshold 80
```

[→ More GitHub Actions Examples](./examples/github-actions/)

---

### GitLab CI

```yaml
test_generation:
  stage: test
  image: python:3.11
  before_script:
    - pip install lionagi-qe-fleet
  script:
    - aqe generate src/ --ci-mode --json
    - aqe execute tests/ --parallel --coverage
    - aqe quality-gate --threshold 80
  coverage: '/Coverage: \d+.\d+%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

[→ More GitLab CI Examples](./examples/gitlab-ci/)

---

## Features by Integration Method

| Feature | CLI | Webhook API | Native Plugin |
|---------|-----|-------------|---------------|
| **Test Generation** | ✅ | ✅ | ✅ (planned) |
| **Test Execution** | ✅ | ✅ | ✅ (planned) |
| **Coverage Analysis** | ✅ | ✅ | ✅ (planned) |
| **Security Scanning** | ✅ | ✅ | ✅ (planned) |
| **Quality Gates** | ✅ | ✅ | ✅ (planned) |
| **Badge Generation** | ⚠️ Via API | ✅ | ✅ (planned) |
| **Artifact Storage** | ✅ | ✅ | ✅ (planned) |
| **PR Comments** | ❌ | ✅ | ✅ (planned) |
| **Real-time Streaming** | ⚠️ Limited | ✅ | ✅ (planned) |
| **Cost Optimization** | ✅ | ✅ | ✅ (planned) |

---

## Next Steps

### First Time Users
1. Complete the [Quickstart](./quickstart.md) (5 minutes)
2. Review [Best Practices](./best-practices.md)
3. Try an [Example Workflow](./examples/) for your platform

### Advanced Users
1. Set up [Artifact Storage](./artifact-storage.md) for historical data
2. Integrate [Badge Generation](./badges.md) for README
3. Configure [Webhook API](./webhook-integration.md) for custom workflows

### Need Help?
- [Troubleshooting Guide](./troubleshooting.md)
- [FAQ](./faq.md)
- [GitHub Issues](https://github.com/lionagi/lionagi-qe-fleet/issues)
- [GitHub Discussions](https://github.com/lionagi/lionagi-qe-fleet/discussions)

---

## Version History

- **v1.2.1** (Current) - Production ready with MCP, storage, badges
- **v1.2.0** - Added AgentDB integration, Q-learning
- **v1.1.0** - Streaming progress, multi-model routing
- **v1.0.0** - Initial release with 19 agents

[→ Full Changelog](../../../CHANGELOG.md)

---

**Documentation Version**: 1.0.0
**Last Updated**: 2025-11-12
**Maintained by**: LionAGI QE Fleet Core Team
