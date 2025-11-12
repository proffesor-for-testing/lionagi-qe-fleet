# Artifact Storage System

The QE Fleet artifact storage system provides pluggable storage backends for test results, coverage reports, security findings, and other artifacts with compression and retention policies.

## Features

- **Multiple Storage Backends**: Local filesystem, AWS S3, MinIO, GitHub Actions, GitLab CI
- **Automatic Compression**: gzip compression with ~70% space savings
- **Retention Policies**: Configurable TTL with automatic cleanup
- **Metadata Index**: SQLite-based index for fast querying
- **Query API**: High-level API for artifact retrieval and comparison
- **Performance**: Store/retrieve in <1s, supports files up to 100MB

## Quick Start

### Installation

The storage system is included in lionagi-qe-fleet. For S3 support, install boto3:

```bash
pip install lionagi-qe-fleet[persistence]  # Includes storage dependencies
# or for S3 support:
pip install boto3
```

### Basic Usage

```python
import asyncio
from pathlib import Path
from lionagi_qe.storage import (
    StorageConfig,
    LocalStorageConfig,
    RetentionPolicy,
    StorageFactory,
    ArtifactType,
)

async def main():
    # Create configuration
    config = StorageConfig(
        backend="local",
        local=LocalStorageConfig(path=Path(".artifacts")),
        retention=RetentionPolicy(default_ttl_days=30, keep_latest_n=10),
    )

    # Create storage backend
    storage = StorageFactory.create(config)

    # Store artifact
    metadata = await storage.store(
        job_id="build-123",
        artifact_type=ArtifactType.TEST_RESULTS,
        data=b"Test results data...",
        tags={"env": "ci", "branch": "main"},
    )

    # Retrieve artifact
    artifact = await storage.retrieve("build-123", ArtifactType.TEST_RESULTS)

    # Decompress
    decompressed = storage.decompress_artifact(artifact)

asyncio.run(main())
```

## Storage Backends

### Local Filesystem

Default backend, stores artifacts in `.artifacts/` directory:

```python
config = StorageConfig(
    backend="local",
    local=LocalStorageConfig(
        path=Path(".artifacts"),
        create_if_missing=True
    )
)
```

### AWS S3

Store artifacts in S3 bucket:

```python
from lionagi_qe.storage.models.storage_config import S3StorageConfig

config = StorageConfig(
    backend="s3",
    s3=S3StorageConfig(
        bucket="my-artifacts",
        region="us-east-1",
        access_key=os.getenv("AWS_ACCESS_KEY"),
        secret_key=os.getenv("AWS_SECRET_KEY"),
    )
)
```

### MinIO (Self-Hosted S3)

Use MinIO for self-hosted S3-compatible storage:

```python
config = StorageConfig(
    backend="minio",
    s3=S3StorageConfig(
        bucket="qe-artifacts",
        endpoint_url="http://localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        use_ssl=False,
    )
)
```

### GitHub Actions

Automatically detects GitHub Actions and uses native artifacts:

```python
config = StorageConfig(
    backend="github-actions",
    ci=CIStorageConfig(
        platform="github-actions",
        artifact_name_prefix="qe-fleet-",
        retention_days=30,
    )
)
```

## Configuration

### YAML Configuration

```yaml
# .qe-fleet-storage.yml
storage:
  backend: local
  local:
    path: .artifacts/

retention:
  default_ttl_days: 30
  keep_latest_n: 10
  cleanup_schedule_cron: "0 2 * * *"
  enabled: true

compression_enabled: true
compression_level: 6
max_artifact_size_mb: 100
```

### Environment Variables

```bash
export QE_STORAGE_BACKEND=local
export QE_STORAGE_PATH=.artifacts
export QE_RETENTION_TTL_DAYS=30
export QE_RETENTION_KEEP_LATEST=10

# For S3:
export QE_S3_BUCKET=my-artifacts
export QE_S3_REGION=us-east-1
export QE_S3_ACCESS_KEY=xxx
export QE_S3_SECRET_KEY=yyy
```

Create storage from environment:

```python
storage = StorageFactory.create_from_env()
```

## Query API

High-level API for querying artifacts:

```python
from lionagi_qe.storage.query import ArtifactQuery

query = ArtifactQuery(storage)

# Get latest artifacts
latest = await query.get_latest_n(ArtifactType.TEST_RESULTS, n=10)

# Get by date range
artifacts = await query.get_by_date_range(
    artifact_type=ArtifactType.COVERAGE_REPORT,
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now()
)

# Get by tags
tagged = await query.get_by_tags({"env": "prod", "region": "us-east"})

# Compare with baseline
comparison = await query.compare_with_baseline(
    current_job_id="build-456",
    baseline_job_id="build-123",
    artifact_type=ArtifactType.TEST_RESULTS
)

# Get size trend
trend = await query.get_size_trend(ArtifactType.TEST_RESULTS, days=30)

# Search with filters
results = await query.search(
    job_id_pattern="build-*",
    artifact_type=ArtifactType.TEST_RESULTS,
    tags={"env": "ci"},
    min_size_mb=0.1,
    max_size_mb=10.0,
    days_ago=7
)
```

## Artifact Types

Supported artifact types:

- `TEST_RESULTS` - Test execution results
- `COVERAGE_REPORT` - Code coverage reports
- `SECURITY_FINDINGS` - Security scan results
- `PERFORMANCE_METRICS` - Performance test metrics
- `BUILD_LOGS` - Build logs
- `STATIC_ANALYSIS` - Static analysis results
- `API_DOCS` - API documentation
- `SCREENSHOTS` - UI screenshots
- `VIDEOS` - Test execution videos
- `CUSTOM` - Custom artifact types

## Retention Policies

Configure automatic cleanup:

```python
retention = RetentionPolicy(
    default_ttl_days=30,      # Delete after 30 days
    keep_latest_n=10,         # Always keep 10 most recent
    cleanup_schedule_cron="0 2 * * *",  # Run at 2 AM daily
    enabled=True
)
```

Manual cleanup:

```python
deleted_count = await storage.cleanup_expired()
print(f"Cleaned up {deleted_count} artifacts")
```

## Compression

Automatic gzip compression with configurable levels:

```python
config = StorageConfig(
    compression_enabled=True,
    compression_level=6,  # 1-9 (higher = better compression, slower)
)
```

Typical compression ratios:
- JSON/XML: 80-90% savings
- Text logs: 70-80% savings
- HTML reports: 75-85% savings
- Binary data: 10-30% savings

## Storage Statistics

Get storage statistics:

```python
stats = await storage.get_storage_stats()
print(f"Total artifacts: {stats['total_artifacts']}")
print(f"Total size: {stats['total_size_bytes']:,} bytes")
print(f"Compressed: {stats['total_compressed_size_bytes']:,} bytes")
print(f"By type: {stats['artifacts_by_type']}")
```

## Performance

- **Store operation**: <100ms for 1MB artifact
- **Retrieve operation**: <100ms for 1MB artifact
- **List operation**: <50ms for 1000 artifacts
- **Compression**: ~70% space savings
- **Max artifact size**: 100MB (configurable)

## Integration Examples

### Store Test Results

```python
import json

test_results = {
    "total": 150,
    "passed": 145,
    "failed": 3,
    "skipped": 2,
    "duration": 45.2
}

metadata = await storage.store(
    job_id="build-123",
    artifact_type=ArtifactType.TEST_RESULTS,
    data=json.dumps(test_results).encode(),
    tags={"env": "ci", "branch": "main"}
)
```

### Store Coverage Report

```python
coverage_html = "<html>...</html>"

await storage.store(
    job_id="build-123",
    artifact_type=ArtifactType.COVERAGE_REPORT,
    data=coverage_html.encode(),
    tags={"coverage": "87.5"}
)
```

### Compare Builds

```python
comparison = await query.compare_with_baseline(
    current_job_id="build-456",
    baseline_job_id="build-123",
    artifact_type=ArtifactType.TEST_RESULTS
)

if comparison["size_increased"]:
    print(f"⚠️  Size increased by {comparison['size_diff_percent']:.1f}%")
```

## See Also

- [API Reference](./api-reference.md)
- [Configuration Guide](./configuration.md)
- [Storage Backends](./backends.md)
- [Examples](../../examples/storage_usage_example.py)
