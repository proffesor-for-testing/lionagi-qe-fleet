#!/usr/bin/env python3
"""
Example usage of the QE Fleet artifact storage system.

This example demonstrates:
1. Creating a storage backend
2. Storing test results, coverage reports, and security findings
3. Retrieving and querying artifacts
4. Comparing with baselines
5. Cleanup and maintenance
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

from lionagi_qe.storage import (
    StorageConfig,
    LocalStorageConfig,
    RetentionPolicy,
    StorageFactory,
    ArtifactType,
    ArtifactQuery,
)


async def main():
    """Main example function."""
    print("=" * 60)
    print("QE Fleet Artifact Storage Example")
    print("=" * 60)

    # 1. Create storage configuration
    print("\n1. Creating storage configuration...")
    config = StorageConfig(
        backend="local",
        local=LocalStorageConfig(path=Path(".artifacts-demo")),
        retention=RetentionPolicy(default_ttl_days=30, keep_latest_n=10),
        compression_enabled=True,
        compression_level=6,
    )
    print(f"   Backend: {config.backend}")
    print(f"   Path: {config.local.path}")
    print(f"   Compression: {config.compression_enabled}")

    # 2. Create storage backend
    print("\n2. Creating storage backend...")
    storage = StorageFactory.create(config)
    print(f"   Storage type: {type(storage).__name__}")

    # 3. Store test results
    print("\n3. Storing test results...")
    test_results = {
        "total_tests": 150,
        "passed": 145,
        "failed": 3,
        "skipped": 2,
        "duration_seconds": 45.2,
        "timestamp": datetime.utcnow().isoformat(),
    }
    test_results_data = json.dumps(test_results, indent=2).encode()

    metadata = await storage.store(
        job_id="build-12345",
        artifact_type=ArtifactType.TEST_RESULTS,
        data=test_results_data,
        tags={"env": "ci", "branch": "main", "build": "12345"},
    )
    print(f"   Stored: {metadata.storage_path}")
    print(f"   Size: {metadata.size_bytes} bytes")
    print(f"   Compressed: {metadata.compressed_size_bytes} bytes")
    compression_savings = (1 - metadata.compression_ratio) * 100
    print(f"   Compression: {compression_savings:.1f}% savings")

    # 4. Store coverage report
    print("\n4. Storing coverage report...")
    coverage_report = {
        "coverage_percent": 87.5,
        "lines_covered": 3500,
        "lines_total": 4000,
        "branches_covered": 450,
        "branches_total": 500,
        "timestamp": datetime.utcnow().isoformat(),
    }
    coverage_data = json.dumps(coverage_report, indent=2).encode()

    await storage.store(
        job_id="build-12345",
        artifact_type=ArtifactType.COVERAGE_REPORT,
        data=coverage_data,
        tags={"env": "ci", "branch": "main"},
    )
    print("   Coverage report stored successfully")

    # 5. Store security findings
    print("\n5. Storing security findings...")
    security_findings = {
        "total_issues": 5,
        "high": 0,
        "medium": 2,
        "low": 3,
        "issues": [
            {"severity": "medium", "title": "Outdated dependency", "fixed": False},
            {"severity": "medium", "title": "Weak cipher suite", "fixed": False},
            {"severity": "low", "title": "Missing security header", "fixed": True},
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }
    security_data = json.dumps(security_findings, indent=2).encode()

    await storage.store(
        job_id="build-12345",
        artifact_type=ArtifactType.SECURITY_FINDINGS,
        data=security_data,
        tags={"env": "ci", "scanner": "bandit"},
    )
    print("   Security findings stored successfully")

    # 6. Retrieve artifacts
    print("\n6. Retrieving artifacts...")
    artifact = await storage.retrieve("build-12345", ArtifactType.TEST_RESULTS)
    if artifact:
        # Decompress
        if hasattr(storage, "decompress_artifact"):
            decompressed = storage.decompress_artifact(artifact)
            data = json.loads(decompressed)
            print(f"   Retrieved test results:")
            print(f"   - Total tests: {data['total_tests']}")
            print(f"   - Passed: {data['passed']}")
            print(f"   - Failed: {data['failed']}")

    # 7. Query API
    print("\n7. Using query API...")
    query = ArtifactQuery(storage)

    # Get latest artifacts
    latest = await query.get_latest_n(ArtifactType.TEST_RESULTS, n=5)
    print(f"   Found {len(latest)} recent test results")

    # Get artifacts by tags
    ci_artifacts = await query.get_by_tags({"env": "ci"})
    print(f"   Found {len(ci_artifacts)} CI artifacts")

    # 8. Storage statistics
    print("\n8. Storage statistics...")
    stats = await storage.get_storage_stats()
    print(f"   Total artifacts: {stats['total_artifacts']}")
    print(f"   Total size: {stats['total_size_bytes']:,} bytes")
    print(
        f"   Compressed size: {stats['total_compressed_size_bytes']:,} bytes"
    )
    print(f"   Artifacts by type:")
    for artifact_type, count in stats["artifacts_by_type"].items():
        print(f"     - {artifact_type}: {count}")

    # 9. Compression statistics
    print("\n9. Compression statistics...")
    compression_stats = await query.get_compression_stats()
    print(
        f"   Average compression ratio: {compression_stats['avg_compression_ratio']:.2f}"
    )
    print(
        f"   Average savings: {compression_stats['avg_savings_percent']:.1f}%"
    )
    print(
        f"   Total space saved: {compression_stats['total_savings_mb']:.2f} MB"
    )

    # 10. Store baseline for comparison
    print("\n10. Storing baseline build...")
    baseline_results = {
        "total_tests": 140,
        "passed": 138,
        "failed": 2,
        "skipped": 0,
        "duration_seconds": 42.0,
    }
    await storage.store(
        job_id="baseline-build",
        artifact_type=ArtifactType.TEST_RESULTS,
        data=json.dumps(baseline_results).encode(),
    )

    # 11. Compare with baseline
    print("\n11. Comparing with baseline...")
    try:
        comparison = await query.compare_with_baseline(
            current_job_id="build-12345",
            baseline_job_id="baseline-build",
            artifact_type=ArtifactType.TEST_RESULTS,
        )
        print(f"   Size difference: {comparison['size_diff_bytes']} bytes")
        print(
            f"   Size change: {comparison['size_diff_percent']:.1f}%"
        )
        print(
            f"   Size {'increased' if comparison['size_increased'] else 'decreased'}"
        )
    except Exception as e:
        print(f"   Could not compare: {e}")

    # 12. Cleanup (optional - usually run on schedule)
    print("\n12. Checking for expired artifacts...")
    # Note: With default 30-day retention, nothing will be expired yet
    expired_count = await storage.cleanup_expired()
    print(f"   Cleaned up {expired_count} expired artifacts")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print(f"Artifacts stored in: {config.local.path}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
