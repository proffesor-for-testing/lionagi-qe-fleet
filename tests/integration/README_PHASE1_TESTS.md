# Phase 1 Integration Tests - Quick Reference

## Test Files

1. **`test_phase1_validation.py`** - Component validation tests (no server required)
2. **`test_phase1_cicd_integration.py`** - Full integration tests (requires server)
3. **`test_cicd_pipeline_scenario.py`** - End-to-end pipeline simulation
4. **`run_phase1_integration_tests.py`** - Test runner with reporting

## Running Tests

### Quick Validation (No Server Required)

```bash
# Activate virtual environment
source .venv/bin/activate

# Run component validation tests
pytest tests/integration/test_phase1_validation.py --noconftest -v -s

# Run specific test class
pytest tests/integration/test_phase1_validation.py::TestCLIEnhancementsValidation -v
pytest tests/integration/test_phase1_validation.py::TestArtifactStorageValidation -v
pytest tests/integration/test_phase1_validation.py::TestBadgeGenerationValidation -v
pytest tests/integration/test_phase1_validation.py::TestPerformanceValidation -v
```

### Full Integration Tests (Requires Server)

```bash
# 1. Start test infrastructure
docker-compose -f docker-compose-test.yml up -d

# 2. Start API server in separate terminal
source .venv/bin/activate
uvicorn lionagi_qe.api.server:app --reload --host 0.0.0.0 --port 8000

# 3. Run full integration tests
pytest tests/integration/test_phase1_cicd_integration.py -v -s

# 4. Run API-specific tests
pytest tests/integration/test_phase1_cicd_integration.py::TestWebhookAPI -v
```

### End-to-End Pipeline Simulation

```bash
# Requires running API server
pytest tests/integration/test_cicd_pipeline_scenario.py -v -s
```

## Current Test Status

### ✓ Tests Working (No Server)

- `TestCLIEnhancementsValidation` - CLI output, exit codes, modes
- `TestArtifactStorageValidation` - Real filesystem storage
- `TestBadgeGenerationValidation` - Real SVG generation
- `TestPerformanceValidation` - Throughput benchmarks

### ⚠️ Tests Requiring Server

- `TestWebhookAPI` - API endpoints, authentication, rate limiting
- `TestEndToEndWorkflows` - Complete CI/CD pipeline
- `test_complete_cicd_pipeline` - 9-stage pipeline simulation

## Test Results

```bash
# View test results
cat tests/integration/phase1_test_results.json

# View integration report
cat docs/guides/phase1-integration-test-report.md

# View executive summary
cat docs/guides/phase1-executive-summary.md
```

## API Corrections

Tests have been updated to match actual implementations:

### CLI Output
```python
# ✓ CORRECT
from lionagi_qe.cli import OutputFormatter, CLIOutput, ExitCode

formatter = OutputFormatter(json_format=True, quiet=False)
output = CLIOutput(success=True, data={}, exit_code=ExitCode.SUCCESS)
json_str = formatter.format_output(output)
```

### Artifact Storage
```python
# ✓ CORRECT
from lionagi_qe.storage import StorageFactory, LocalStorageConfig, Artifact

config = LocalStorageConfig(base_path="/tmp/storage")
storage = StorageFactory.create(config)

artifact = Artifact(id="test", type=ArtifactType.TEST_RESULTS, data={})
path = storage.store(artifact)
```

### Badge Generation
```python
# ✓ CORRECT
from lionagi_qe.badges import BadgeGenerator, BadgeCache

cache = BadgeCache(default_ttl=300)
generator = BadgeGenerator(cache=cache)

svg = generator.generate_coverage_badge(85.5)
```

## Performance Benchmarks

Run performance tests to validate throughput:

```bash
# Storage performance
pytest tests/integration/test_phase1_validation.py::TestPerformanceValidation::test_storage_write_throughput -v -s
pytest tests/integration/test_phase1_validation.py::TestPerformanceValidation::test_storage_read_throughput -v -s

# Badge generation performance
pytest tests/integration/test_phase1_validation.py::TestPerformanceValidation::test_badge_generation_performance -v -s
```

Expected results:
- Storage Write: >45/s (target: >20/s) ✓
- Storage Read: >78/s (target: >50/s) ✓
- Badge Generation: >67/s (target: >50/s) ✓

## Debugging Tests

### View detailed output
```bash
pytest tests/integration/test_phase1_validation.py -v -s --tb=long
```

### Run single test
```bash
pytest tests/integration/test_phase1_validation.py::TestCLIEnhancementsValidation::test_cli_output_formatter_json -v -s
```

### Check imports
```bash
python -c "from lionagi_qe.cli import OutputFormatter; print('CLI OK')"
python -c "from lionagi_qe.storage import StorageFactory; print('Storage OK')"
python -c "from lionagi_qe.badges import BadgeGenerator; print('Badges OK')"
```

## Next Steps

1. **Complete API Tests:**
   - Start API server
   - Run `TestWebhookAPI` tests
   - Validate all 17 endpoints

2. **Load Testing:**
   - Install locust: `pip install locust`
   - Create load test script
   - Test rate limiting (100 req/min)

3. **WebSocket Tests:**
   - Test streaming endpoints
   - Validate real-time updates
   - Test connection handling

## Contact

For issues or questions:
- See: `/workspaces/lionagi-qe-fleet/docs/guides/phase1-integration-test-report.md`
- Memory: `aqe/integration-test/phase1-results`
