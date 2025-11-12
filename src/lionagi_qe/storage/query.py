"""Query API for artifact retrieval and comparison."""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, Any

from .backends.base import ArtifactStorage
from .models.artifact import Artifact, ArtifactType, ArtifactMetadata


class ArtifactQuery:
    """High-level query API for artifacts."""

    def __init__(self, storage: ArtifactStorage):
        """
        Initialize query API.

        Args:
            storage: Storage backend to query
        """
        self.storage = storage

    async def get_latest(
        self, job_id: str, artifact_type: ArtifactType
    ) -> Optional[Artifact]:
        """
        Get latest artifact for a job and type.

        Args:
            job_id: Job ID
            artifact_type: Artifact type

        Returns:
            Latest artifact, or None if not found
        """
        return await self.storage.retrieve(job_id, artifact_type)

    async def get_latest_n(
        self, artifact_type: ArtifactType, n: int = 10
    ) -> list[ArtifactMetadata]:
        """
        Get N most recent artifacts of a type.

        Args:
            artifact_type: Artifact type to filter
            n: Number of artifacts to return

        Returns:
            List of artifact metadata (sorted newest first)
        """
        return await self.storage.list(artifact_type=artifact_type, limit=n)

    async def get_by_date_range(
        self,
        artifact_type: ArtifactType,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
    ) -> list[ArtifactMetadata]:
        """
        Get artifacts within a date range.

        Args:
            artifact_type: Artifact type to filter
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum results

        Returns:
            List of artifact metadata
        """
        return await self.storage.list(
            artifact_type=artifact_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

    async def get_by_tags(
        self, tags: dict[str, str], limit: int = 100
    ) -> list[ArtifactMetadata]:
        """
        Get artifacts matching tags.

        Args:
            tags: Tags to match (all must match)
            limit: Maximum results

        Returns:
            List of artifact metadata
        """
        return await self.storage.list(tags=tags, limit=limit)

    async def get_last_24_hours(
        self, artifact_type: Optional[ArtifactType] = None
    ) -> list[ArtifactMetadata]:
        """
        Get artifacts from last 24 hours.

        Args:
            artifact_type: Optional type filter

        Returns:
            List of artifact metadata
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=24)
        return await self.storage.list(
            artifact_type=artifact_type,
            start_date=start_date,
            end_date=end_date,
            limit=1000,
        )

    async def get_last_week(
        self, artifact_type: Optional[ArtifactType] = None
    ) -> list[ArtifactMetadata]:
        """
        Get artifacts from last week.

        Args:
            artifact_type: Optional type filter

        Returns:
            List of artifact metadata
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        return await self.storage.list(
            artifact_type=artifact_type,
            start_date=start_date,
            end_date=end_date,
            limit=1000,
        )

    async def compare_with_baseline(
        self, current_job_id: str, baseline_job_id: str, artifact_type: ArtifactType
    ) -> dict[str, Any]:
        """
        Compare current artifact with baseline.

        Args:
            current_job_id: Current job ID
            baseline_job_id: Baseline job ID
            artifact_type: Artifact type to compare

        Returns:
            Comparison results:
            - current: Current artifact metadata
            - baseline: Baseline artifact metadata
            - size_diff_bytes: Size difference
            - size_diff_percent: Size difference as percentage
            - time_diff_seconds: Time difference
        """
        current = await self.storage.retrieve(current_job_id, artifact_type)
        baseline = await self.storage.retrieve(baseline_job_id, artifact_type)

        if current is None:
            raise ValueError(f"Current artifact not found: {current_job_id}")
        if baseline is None:
            raise ValueError(f"Baseline artifact not found: {baseline_job_id}")

        size_diff = current.metadata.size_bytes - baseline.metadata.size_bytes
        size_diff_percent = (
            (size_diff / baseline.metadata.size_bytes * 100)
            if baseline.metadata.size_bytes > 0
            else 0
        )

        time_diff = (
            current.metadata.timestamp - baseline.metadata.timestamp
        ).total_seconds()

        return {
            "current": current.metadata,
            "baseline": baseline.metadata,
            "size_diff_bytes": size_diff,
            "size_diff_percent": size_diff_percent,
            "size_increased": size_diff > 0,
            "time_diff_seconds": time_diff,
        }

    async def get_size_trend(
        self, artifact_type: ArtifactType, days: int = 30
    ) -> list[dict[str, Any]]:
        """
        Get size trend over time for an artifact type.

        Args:
            artifact_type: Artifact type
            days: Number of days to look back

        Returns:
            List of data points: [{timestamp, size_bytes, compressed_size_bytes}]
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        artifacts = await self.storage.list(
            artifact_type=artifact_type,
            start_date=start_date,
            end_date=end_date,
            limit=1000,
        )

        return [
            {
                "timestamp": a.timestamp.isoformat(),
                "job_id": a.job_id,
                "size_bytes": a.size_bytes,
                "compressed_size_bytes": a.compressed_size_bytes,
                "compression_ratio": a.compression_ratio,
            }
            for a in artifacts
        ]

    async def get_compression_stats(
        self, artifact_type: Optional[ArtifactType] = None
    ) -> dict[str, Any]:
        """
        Get compression statistics.

        Args:
            artifact_type: Optional type filter

        Returns:
            Statistics:
            - avg_compression_ratio: Average compression ratio
            - avg_savings_percent: Average space savings
            - total_size_bytes: Total uncompressed size
            - total_compressed_bytes: Total compressed size
            - total_savings_bytes: Total bytes saved
        """
        artifacts = await self.storage.list(
            artifact_type=artifact_type, limit=1000000
        )

        if not artifacts:
            return {
                "avg_compression_ratio": 0,
                "avg_savings_percent": 0,
                "total_size_bytes": 0,
                "total_compressed_bytes": 0,
                "total_savings_bytes": 0,
            }

        total_size = sum(a.size_bytes for a in artifacts)
        total_compressed = sum(a.compressed_size_bytes for a in artifacts)
        total_savings = total_size - total_compressed

        avg_ratio = sum(a.compression_ratio for a in artifacts) / len(artifacts)
        avg_savings_percent = (1 - avg_ratio) * 100

        return {
            "avg_compression_ratio": avg_ratio,
            "avg_savings_percent": avg_savings_percent,
            "total_size_bytes": total_size,
            "total_compressed_bytes": total_compressed,
            "total_savings_bytes": total_savings,
            "total_savings_mb": total_savings / (1024 * 1024),
        }

    async def search(
        self,
        job_id_pattern: Optional[str] = None,
        artifact_type: Optional[ArtifactType] = None,
        tags: Optional[dict[str, str]] = None,
        min_size_mb: Optional[float] = None,
        max_size_mb: Optional[float] = None,
        days_ago: Optional[int] = None,
        limit: int = 100,
    ) -> list[ArtifactMetadata]:
        """
        Advanced search with multiple filters.

        Args:
            job_id_pattern: Job ID pattern (supports wildcards)
            artifact_type: Artifact type filter
            tags: Tags to match
            min_size_mb: Minimum size in MB
            max_size_mb: Maximum size in MB
            days_ago: Only include artifacts from N days ago
            limit: Maximum results

        Returns:
            List of matching artifact metadata
        """
        # Build date filter
        start_date = None
        if days_ago:
            start_date = datetime.utcnow() - timedelta(days=days_ago)

        # Get artifacts
        artifacts = await self.storage.list(
            artifact_type=artifact_type,
            start_date=start_date,
            tags=tags,
            limit=limit * 2,  # Get more to allow for filtering
        )

        # Apply additional filters
        filtered = artifacts

        if job_id_pattern:
            import fnmatch

            filtered = [
                a for a in filtered if fnmatch.fnmatch(a.job_id, job_id_pattern)
            ]

        if min_size_mb is not None:
            min_bytes = min_size_mb * 1024 * 1024
            filtered = [a for a in filtered if a.size_bytes >= min_bytes]

        if max_size_mb is not None:
            max_bytes = max_size_mb * 1024 * 1024
            filtered = [a for a in filtered if a.size_bytes <= max_bytes]

        return filtered[:limit]
