"""Tests for local filesystem storage backend."""

import asyncio
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from lionagi_qe.storage.backends.local import LocalStorage
from lionagi_qe.storage.models.storage_config import LocalStorageConfig, RetentionPolicy
from lionagi_qe.storage.models.artifact import ArtifactType


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage(temp_storage_dir):
    """Create local storage instance."""
    config = LocalStorageConfig(path=temp_storage_dir, create_if_missing=True)
    retention = RetentionPolicy(default_ttl_days=30, keep_latest_n=10)
    return LocalStorage(
        config=config,
        retention_policy=retention,
        compression_enabled=True,
        compression_level=6,
    )


@pytest.mark.asyncio
class TestLocalStorage:
    """Test local storage backend."""

    async def test_store_artifact(self, storage):
        """Test storing an artifact."""
        # Use larger data that actually compresses well
        data = b"Test data for artifact" * 100
        metadata = await storage.store(
            job_id="job-123",
            artifact_type=ArtifactType.TEST_RESULTS,
            data=data,
            tags={"env": "test", "branch": "main"},
        )

        assert metadata.job_id == "job-123"
        assert metadata.artifact_type == ArtifactType.TEST_RESULTS
        assert metadata.size_bytes == len(data)
        assert metadata.compressed_size_bytes < len(data)  # Should be compressed
        assert metadata.compression_ratio < 1.0
        assert metadata.tags["env"] == "test"
        assert Path(metadata.storage_path).exists()

    async def test_retrieve_artifact(self, storage):
        """Test retrieving an artifact."""
        data = b"Test retrieval"
        await storage.store(
            job_id="job-456", artifact_type=ArtifactType.COVERAGE_REPORT, data=data
        )

        artifact = await storage.retrieve("job-456", ArtifactType.COVERAGE_REPORT)

        assert artifact is not None
        assert artifact.metadata.job_id == "job-456"
        assert artifact.metadata.artifact_type == ArtifactType.COVERAGE_REPORT

        # Decompress and verify
        decompressed = storage.decompress_artifact(artifact)
        assert decompressed == data

    async def test_retrieve_nonexistent(self, storage):
        """Test retrieving nonexistent artifact."""
        artifact = await storage.retrieve(
            "nonexistent", ArtifactType.TEST_RESULTS
        )
        assert artifact is None

    async def test_list_artifacts(self, storage):
        """Test listing artifacts."""
        # Store multiple artifacts
        for i in range(5):
            await storage.store(
                job_id=f"job-{i}",
                artifact_type=ArtifactType.TEST_RESULTS,
                data=f"Data {i}".encode(),
            )

        # List all
        artifacts = await storage.list(limit=10)
        assert len(artifacts) == 5

        # List with type filter
        artifacts = await storage.list(
            artifact_type=ArtifactType.TEST_RESULTS, limit=10
        )
        assert len(artifacts) == 5

    async def test_list_with_date_filter(self, storage):
        """Test listing with date filters."""
        # Store artifact
        await storage.store(
            job_id="job-date",
            artifact_type=ArtifactType.TEST_RESULTS,
            data=b"Date test",
        )

        # List with date range
        now = datetime.utcnow()
        artifacts = await storage.list(
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1),
        )
        assert len(artifacts) >= 1

    async def test_list_with_tags(self, storage):
        """Test listing with tag filters."""
        await storage.store(
            job_id="job-tagged",
            artifact_type=ArtifactType.TEST_RESULTS,
            data=b"Tagged",
            tags={"env": "prod", "region": "us-east"},
        )

        artifacts = await storage.list(tags={"env": "prod"})
        assert len(artifacts) >= 1
        assert all(a.tags.get("env") == "prod" for a in artifacts)

    async def test_delete_artifact(self, storage):
        """Test deleting an artifact."""
        await storage.store(
            job_id="job-delete", artifact_type=ArtifactType.TEST_RESULTS, data=b"Delete me"
        )

        # Verify exists
        exists = await storage.exists("job-delete", ArtifactType.TEST_RESULTS)
        assert exists

        # Delete
        deleted = await storage.delete("job-delete", ArtifactType.TEST_RESULTS)
        assert deleted

        # Verify deleted
        exists = await storage.exists("job-delete", ArtifactType.TEST_RESULTS)
        assert not exists

    async def test_delete_nonexistent(self, storage):
        """Test deleting nonexistent artifact."""
        deleted = await storage.delete("nonexistent", ArtifactType.TEST_RESULTS)
        assert not deleted

    async def test_exists(self, storage):
        """Test checking artifact existence."""
        exists = await storage.exists("job-check", ArtifactType.TEST_RESULTS)
        assert not exists

        await storage.store(
            job_id="job-check",
            artifact_type=ArtifactType.TEST_RESULTS,
            data=b"Exists",
        )

        exists = await storage.exists("job-check", ArtifactType.TEST_RESULTS)
        assert exists

    async def test_cleanup_expired(self, storage, temp_storage_dir):
        """Test cleaning up expired artifacts."""
        # Store artifact with short TTL and custom expiration
        from datetime import datetime, timedelta

        config = LocalStorageConfig(path=temp_storage_dir)
        retention = RetentionPolicy(default_ttl_days=1, keep_latest_n=0)
        short_ttl_storage = LocalStorage(
            config=config, retention_policy=retention, compression_enabled=True
        )

        # Store artifact and manually set expiration to past
        metadata = await short_ttl_storage.store(
            job_id="job-expire",
            artifact_type=ArtifactType.TEST_RESULTS,
            data=b"Expire me",
        )

        # Manually update metadata to be expired
        metadata.expires_at = datetime.utcnow() - timedelta(days=1)
        await asyncio.to_thread(short_ttl_storage.index.add, metadata)

        # Run cleanup
        deleted_count = await short_ttl_storage.cleanup_expired()
        assert deleted_count >= 1

    async def test_get_storage_stats(self, storage):
        """Test getting storage statistics."""
        # Store some artifacts
        for i in range(3):
            await storage.store(
                job_id=f"job-stats-{i}",
                artifact_type=ArtifactType.TEST_RESULTS,
                data=f"Stats {i}".encode() * 100,
            )

        stats = await storage.get_storage_stats()

        assert stats["total_artifacts"] >= 3
        assert stats["total_size_bytes"] > 0
        assert stats["total_compressed_size_bytes"] > 0
        assert "test-results" in stats["artifacts_by_type"]

    async def test_large_artifact(self, storage):
        """Test storing large artifact."""
        # Create 10MB artifact
        large_data = b"X" * (10 * 1024 * 1024)

        metadata = await storage.store(
            job_id="job-large",
            artifact_type=ArtifactType.BUILD_LOGS,
            data=large_data,
        )

        # Should compress well (repeated data)
        assert metadata.compression_ratio < 0.1
        assert metadata.compressed_size_bytes < metadata.size_bytes * 0.1

        # Retrieve and verify
        artifact = await storage.retrieve("job-large", ArtifactType.BUILD_LOGS)
        decompressed = storage.decompress_artifact(artifact)
        assert len(decompressed) == len(large_data)

    async def test_multiple_artifact_types(self, storage):
        """Test storing multiple artifact types for same job."""
        job_id = "job-multi"

        await storage.store(
            job_id=job_id, artifact_type=ArtifactType.TEST_RESULTS, data=b"Tests"
        )
        await storage.store(
            job_id=job_id, artifact_type=ArtifactType.COVERAGE_REPORT, data=b"Coverage"
        )
        await storage.store(
            job_id=job_id,
            artifact_type=ArtifactType.SECURITY_FINDINGS,
            data=b"Security",
        )

        # Verify all exist
        assert await storage.exists(job_id, ArtifactType.TEST_RESULTS)
        assert await storage.exists(job_id, ArtifactType.COVERAGE_REPORT)
        assert await storage.exists(job_id, ArtifactType.SECURITY_FINDINGS)

    async def test_compression_disabled(self, temp_storage_dir):
        """Test storage with compression disabled."""
        config = LocalStorageConfig(path=temp_storage_dir)
        retention = RetentionPolicy()
        storage_no_compress = LocalStorage(
            config=config,
            retention_policy=retention,
            compression_enabled=False,
        )

        data = b"Uncompressed data"
        metadata = await storage_no_compress.store(
            job_id="job-nocompress",
            artifact_type=ArtifactType.TEST_RESULTS,
            data=data,
        )

        # Compression ratio should be 1.0 (no compression)
        assert metadata.compression_ratio == 1.0
        assert metadata.size_bytes == metadata.compressed_size_bytes
