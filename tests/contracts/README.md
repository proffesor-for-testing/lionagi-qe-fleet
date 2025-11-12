# API Contract Testing for LionAGI QE Fleet

This directory contains comprehensive API contract tests using consumer-driven contract testing (Pact) and breaking change detection.

## Directory Structure

```
tests/contracts/
├── pact/                          # Consumer contract tests
│   ├── github_actions_consumer.py # GitHub Actions CI/CD contracts
│   ├── gitlab_ci_consumer.py      # GitLab CI pipeline contracts
│   └── cli_consumer.py            # AQE CLI tool contracts
├── breaking_changes_test.py       # Breaking change detection
├── contract_test_strategy.md      # Comprehensive strategy document
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Quick Start

### 1. Install Dependencies

```bash
cd tests/contracts
pip install -r requirements.txt
```

### 2. Run Consumer Contracts

```bash
# Run all consumer contract tests
pytest pact/ -v

# Run specific consumer
pytest pact/github_actions_consumer.py -v
pytest pact/gitlab_ci_consumer.py -v
pytest pact/cli_consumer.py -v
```

### 3. Detect Breaking Changes

```bash
# Compare OpenAPI specs for breaking changes
pytest breaking_changes_test.py -v
```

### 4. Publish Contracts to Pact Broker

```bash
# Set environment variables
export PACT_BROKER_URL="http://pact-broker.example.com"
export PACT_BROKER_TOKEN="your-token"

# Run tests and publish
pytest pact/ -v --pact-publish-version=1.4.3
```

## Consumer Contracts

### GitHub Actions Consumer

**Contract**: `pact/github_actions_consumer.py`

Tests GitHub Actions workflow integration with the MCP API.

**Scenarios**:
- Generate unit tests for Python code
- Execute test suite with coverage
- Analyze coverage and identify gaps
- Validate quality gate (pass/fail deployment)

**Example**:
```python
pytest pact/github_actions_consumer.py::TestGitHubActionsContracts::test_contract_generate_unit_tests -v
```

### GitLab CI Consumer

**Contract**: `pact/gitlab_ci_consumer.py`

Tests GitLab CI pipeline integration with the MCP API.

**Scenarios**:
- Run comprehensive security scan
- Assess deployment readiness
- Execute performance/load testing

**Example**:
```python
pytest pact/gitlab_ci_consumer.py::TestGitLabCIContracts::test_contract_security_scan -v
```

### CLI Consumer

**Contract**: `pact/cli_consumer.py`

Tests AQE CLI tool integration with the MCP API.

**Scenarios**:
- Get fleet status
- Hunt for flaky tests
- Analyze regression risk

**Example**:
```python
pytest pact/cli_consumer.py::TestCLIConsumerContracts::test_contract_fleet_status -v
```

## Breaking Change Detection

**Test File**: `breaking_changes_test.py`

Automatically detects breaking changes between API versions by comparing OpenAPI specifications.

**Detected Changes**:
- 🔴 **CRITICAL**: Endpoint removal, method removal, required param removal
- 🟠 **HIGH**: Required param added, param type changed, response field removed
- 🟡 **MEDIUM**: Error code changes

**Example**:
```python
# Test endpoint removal detection
pytest breaking_changes_test.py::TestBreakingChangeDetection::test_detect_endpoint_removal -v

# Test type change detection
pytest breaking_changes_test.py::TestBreakingChangeDetection::test_detect_type_change -v
```

## OpenAPI Specification

**Location**: `../../docs/api/openapi-spec.yaml`

The source of truth for all API contracts. Defines all 17 MCP tool endpoints with complete request/response schemas.

**Endpoints Covered**:
1. Core Testing (4): test_generate, test_execute, coverage_analyze, quality_gate
2. Performance & Security (2): performance_test, security_scan
3. Fleet Orchestration (2): fleet_orchestrate, fleet_status
4. Advanced Testing (8): requirements_validate, flaky_test_hunt, api_contract_validate, regression_risk_analyze, test_data_generate, visual_test, chaos_test, deployment_readiness
5. Streaming (1): test_execute_stream

## CI/CD Integration

### GitHub Actions

```yaml
name: Contract Tests

on: [pull_request]

jobs:
  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies
        run: |
          pip install -r tests/contracts/requirements.txt

      - name: Run consumer contracts
        run: |
          pytest tests/contracts/pact/ -v

      - name: Detect breaking changes
        run: |
          pytest tests/contracts/breaking_changes_test.py -v

      - name: Publish to Pact Broker
        if: github.ref == 'refs/heads/main'
        run: |
          pytest tests/contracts/pact/ -v --pact-publish-version=${{ github.sha }}
        env:
          PACT_BROKER_URL: ${{ secrets.PACT_BROKER_URL }}
          PACT_BROKER_TOKEN: ${{ secrets.PACT_BROKER_TOKEN }}
```

### GitLab CI

```yaml
contract_tests:
  stage: test
  image: python:3.11
  before_script:
    - pip install -r tests/contracts/requirements.txt
  script:
    - pytest tests/contracts/pact/ -v
    - pytest tests/contracts/breaking_changes_test.py -v
  artifacts:
    paths:
      - pacts/
    reports:
      junit: test-results.xml
```

## Pact Broker Setup

### Using Docker

```bash
# Start Pact Broker
docker run -d \
  --name pact-broker \
  -p 9292:9292 \
  -e PACT_BROKER_DATABASE_URL=postgres://user:pass@db:5432/pact \
  pactfoundation/pact-broker:latest

# Publish contracts
pytest pact/ -v --pact-publish-version=1.4.3
```

### Using Docker Compose

```yaml
# docker-compose.yml
version: '3'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: pact
      POSTGRES_USER: pact
      POSTGRES_PASSWORD: pact
    volumes:
      - pact-db:/var/lib/postgresql/data

  pact-broker:
    image: pactfoundation/pact-broker:latest
    ports:
      - "9292:9292"
    environment:
      PACT_BROKER_DATABASE_URL: postgres://pact:pact@postgres:5432/pact
    depends_on:
      - postgres

volumes:
  pact-db:
```

```bash
# Start services
docker-compose up -d

# View Pact Broker UI
open http://localhost:9292
```

## Contract Testing Workflow

### 1. Write Consumer Contract

```python
# tests/contracts/pact/my_consumer.py
from pact import Consumer, Provider, Like

pact = Consumer("my-consumer").has_pact_with(
    Provider("lionagi-qe-mcp-api"),
    pact_dir="./pacts"
)

def test_my_contract():
    (pact
     .given("test generator is available")
     .upon_receiving("a request to generate tests")
     .with_request(method="POST", path="/tools/test_generate")
     .will_respond_with(200, body={"test_code": Like("def test_...")}))

    with pact:
        # Make actual API call
        result = api_client.test_generate(code="def foo(): pass")
        assert "test_code" in result
```

### 2. Run Consumer Tests

```bash
pytest pact/my_consumer.py -v
```

This generates a pact file in `pacts/` directory.

### 3. Publish to Pact Broker

```bash
pytest pact/my_consumer.py -v --pact-publish-version=1.0.0
```

### 4. Provider Verification

```python
# tests/contracts/provider_verification.py
from pact import Verifier

def test_verify_contracts():
    verifier = Verifier(
        provider="lionagi-qe-mcp-api",
        broker_url="http://localhost:9292"
    )

    verifier.verify_with_broker(
        provider_base_url="http://localhost:8080",
        publish_version="1.4.3",
        publish_verification_results=True
    )
```

### 5. Detect Breaking Changes

```bash
pytest breaking_changes_test.py -v
```

## Best Practices

### 1. Contract-First Development

Write contracts BEFORE implementing features:

```python
# 1. Write consumer contract
def test_new_feature_contract():
    # Define expected behavior
    pass

# 2. Implement provider to honor contract
# 3. Verify provider honors all contracts
```

### 2. Version Compatibility

Test backward compatibility across versions:

```python
def test_v1_4_2_client_with_v1_4_3_api():
    """Ensure patch versions are compatible"""
    old_client = APIClient(version="1.4.2")
    result = old_client.test_generate(code="...")
    assert result is not None  # Should work
```

### 3. Breaking Change Prevention

Always run breaking change detection in CI:

```yaml
- name: Block on breaking changes
  run: |
    pytest breaking_changes_test.py -v
    if [ $? -ne 0 ]; then
      echo "❌ Breaking changes detected!"
      exit 1
    fi
```

### 4. Consumer Collaboration

Share contracts with all consumers:

```bash
# Publish to Pact Broker
pytest pact/ --pact-publish-version=$VERSION

# Consumers can verify against published contracts
```

## Troubleshooting

### Pact Tests Failing

```bash
# Check Pact Broker connection
curl http://localhost:9292/health

# Verify OpenAPI spec is valid
python -c "import yaml; yaml.safe_load(open('../../docs/api/openapi-spec.yaml'))"

# Run tests with verbose output
pytest pact/ -vv --log-cli-level=DEBUG
```

### Breaking Changes Detected

```bash
# Compare specs manually
diff <(yq . docs/api/openapi-spec-v1.4.2.yaml) \
     <(yq . docs/api/openapi-spec-v1.4.3.yaml)

# Generate detailed report
pytest breaking_changes_test.py::test_generate_breaking_change_report -v
```

### Contract Mismatch

```bash
# Re-record contracts
rm -rf pacts/
pytest pact/ -v

# Verify provider honors contracts
pytest tests/contracts/provider_verification.py -v
```

## Resources

- [Pact Documentation](https://docs.pact.io/)
- [OpenAPI Specification](https://spec.openapis.org/oas/v3.0.3)
- [Consumer-Driven Contracts](https://martinfowler.com/articles/consumerDrivenContracts.html)
- [API Versioning Best Practices](https://www.baeldung.com/rest-versioning)
- [Contract Testing Strategy](./contract_test_strategy.md)

## Support

For questions or issues:
- **Email**: aqe-fleet@lionagi.com
- **Issues**: https://github.com/lionagi/qe-fleet/issues
- **Slack**: #aqe-contract-testing

---

**Last Updated**: 2025-11-12
**Version**: 1.0.0
