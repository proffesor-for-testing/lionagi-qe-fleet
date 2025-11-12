"""Tests for artifact query API."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from lionagi_qe.storage.backends.local import LocalStorage
from lionagi_qe.storage.models.storage_config import LocalStorageConfig, RetentionPolicy
from lionagi_qe.storage.models.artifact import ArtifactType
from lionagi_qe.storage.query import ArtifactQuery


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
async def query_api(temp_storage_dir):
    """Create query API with populated storage."""
    config = LocalStorageConfig(path=temp_storage_dir, create_if_missing=True)
    retention = RetentionPolicy(default_ttl_days=30, keep_latest_n=10)
    storage = LocalStorage(
        config=config,
        retention_policy=retention,
        compression_enabled=True,
        compression_level=6,
    )

    # Populate with test data
    for i in range(10):
        await storage.store(
            job_id=f"job-{i}",
            artifact_type=ArtifactType.TEST_RESULTS,
            data=f"Test data {i}".encode() * 100,
            tags={"env": "test", "iteration": str(i)},
        )

    for i in range(5):
        await storage.store(
            job_id=f"job-cov-{i}",
            artifact_type=ArtifactType.COVERAGE_REPORT,
            data=f"Coverage {i}".encode() * 200,
            tags={"env": "prod"},
        )

    return ArtifactQuery(storage)


@pytest.mark.asyncio
class TestArtifactQuery:
    """Test artifact query API."""

    async def test_get_latest(self, query_api):
        """Test getting latest artifact."""
        artifact = await query_api.get_latest("job-5", ArtifactType.TEST_RESULTS)

        assert artifact is not None
        assert artifact.metadata.job_id == "job-5"
        assert artifact.metadata.artifact_type == ArtifactType.TEST_RESULTS

    async def test_get_latest_nonexistent(self, query_api):
        """Test getting nonexistent artifact."""
        artifact = await query_api.get_latest("nonexistent", ArtifactType.TEST_RESULTS)
        assert artifact is None

    async def test_get_latest_n(self, query_api):
        """Test getting N latest artifacts."""
        artifacts = await query_api.get_latest_n(ArtifactType.TEST_RESULTS, n=5)

        assert len(artifacts) == 5
        # Should be sorted by timestamp (newest first)
        for i in range(len(artifacts) - 1):
            assert artifacts[i].timestamp >= artifacts[i + 1].timestamp

    async def test_get_by_date_range(self, query_api):
        """Test getting artifacts by date range."""
        now = datetime.utcnow()
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)

        artifacts = await query_api.get_by_date_range(
            ArtifactType.TEST_RESULTS, start, end
        )

        assert len(artifacts) > 0
        for artifact in artifacts:
            assert start <= artifact.timestamp <= end

    async def test_get_by_tags(self, query_api):
        """Test getting artifacts by tags."""
        artifacts = await query_api.get_by_tags({"env": "test"})

        assert len(artifacts) > 0
        for artifact in artifacts:
            assert artifact.tags.get("env") == "test"

    async def test_get_last_24_hours(self, query_api):
        """Test getting artifacts from last 24 hours."""
        artifacts = await query_api.get_last_24_hours(ArtifactType.TEST_RESULTS)

        assert len(artifacts) > 0
        cutoff = datetime.utcnow() - timedelta(hours=24)
        for artifact in artifacts:
            assert artifact.timestamp >= cutoff

    async def test_get_last_week(self, query_api):
        """Test getting artifacts from last week."""
        artifacts = await query_api.get_last_week(ArtifactType.COVERAGE_REPORT)

        assert len(artifacts) > 0
        cutoff = datetime.utcnow() - timedelta(days=7)
        for artifact in artifacts:
            assert artifact.timestamp >= cutoff

    async def test_compare_with_baseline(self, query_api):
        """Test comparing artifacts."""
        comparison = await query_api.compare_with_baseline(
            current_job_id="job-9",
            baseline_job_id="job-0",
            artifact_type=ArtifactType.TEST_RESULTS,
        )

        assert comparison["current"].job_id == "job-9"
        assert comparison["baseline"].job_id == "job-0"
        assert "size_diff_bytes" in comparison
        assert "size_diff_percent" in comparison
        assert "size_increased" in comparison
        assert "time_diff_seconds" in comparison

    async def test_compare_with_missing_baseline(self, query_api):
        """Test comparing with nonexistent baseline."""
        with pytest.raises(ValueError, match="Baseline artifact not found"):
            await query_api.compare_with_baseline(
                current_job_id="job-0",
                baseline_job_id="nonexistent",
                artifact_type=ArtifactType.TEST_RESULTS,
            )

    async def test_get_size_trend(self, query_api):
        """Test getting size trend."""
        trend = await query_api.get_size_trend(ArtifactType.TEST_RESULTS, days=30)

        assert len(trend) > 0
        for point in trend:
            assert "timestamp" in point
            assert "job_id" in point
            assert "size_bytes" in point
            assert "compressed_size_bytes" in point
            assert "compression_ratio" in point

    async def test_get_compression_stats(self, query_api):
        """Test getting compression statistics."""
        stats = await query_api.get_compression_stats(ArtifactType.TEST_RESULTS)

        assert "avg_compression_ratio" in stats
        assert "avg_savings_percent" in stats
        assert "total_size_bytes" in stats
        assert "total_compressed_bytes" in stats
        assert "total_savings_bytes" in stats
        assert "total_savings_mb" in stats

        assert stats["avg_compression_ratio"] < 1.0
        assert stats["avg_savings_percent"] > 0
        assert stats["total_size_bytes"] > stats["total_compressed_bytes"]

    async def test_search_basic(self, query_api):
        """Test basic search."""
        results = await query_api.search(
            artifact_type=ArtifactType.TEST_RESULTS, limit=5
        )

        assert len(results) <= 5
        for result in results:
            assert result.artifact_type == ArtifactType.TEST_RESULTS

    async def test_search_by_job_pattern(self, query_api):
        """Test search with job ID pattern."""
        results = await query_api.search(job_id_pattern="job-[0-5]")

        assert len(results) > 0
        for result in results:
            assert result.job_id in [f"job-{i}" for i in range(6)]

    async def test_search_by_size(self, query_api):
        """Test search by size range."""
        results = await query_api.search(
            artifact_type=ArtifactType.TEST_RESULTS,
            min_size_mb=0.001,
            max_size_mb=1.0,
        )

        assert len(results) > 0
        for result in results:
            size_mb = result.size_bytes / (1024 * 1024)
            assert 0.001 <= size_mb <= 1.0

    async def test_search_by_days_ago(self, query_api):
        """Test search by days ago."""
        results = await query_api.search(days_ago=1)

        assert len(results) > 0
        cutoff = datetime.utcnow() - timedelta(days=1)
        for result in results:
            assert result.timestamp >= cutoff

    async def test_search_combined_filters(self, query_api):
        """Test search with multiple filters."""
        results = await query_api.search(
            artifact_type=ArtifactType.TEST_RESULTS,
            tags={"env": "test"},
            min_size_mb=0.001,
            days_ago=1,
            limit=5,
        )

        assert len(results) <= 5
        for result in results:
            assert result.artifact_type == ArtifactType.TEST_RESULTS
            assert result.tags.get("env") == "test"
