"""Abstract base class for storage backends."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, Any
from datetime import datetime

from ..models.artifact import Artifact, ArtifactType, ArtifactMetadata


class ArtifactStorage(ABC):
    """Abstract base class for artifact storage backends."""

    @abstractmethod
    async def store(
        self,
        job_id: str,
        artifact_type: ArtifactType,
        data: bytes,
        tags: Optional[dict[str, str]] = None,
    ) -> ArtifactMetadata:
        """
        Store an artifact.

        Args:
            job_id: Job ID that created this artifact
            artifact_type: Type of artifact
            data: Raw artifact data (will be compressed if enabled)
            tags: Optional tags for filtering

        Returns:
            Metadata for the stored artifact

        Raises:
            StorageError: If storage operation fails
        """
        pass

    @abstractmethod
    async def retrieve(
        self, job_id: str, artifact_type: ArtifactType
    ) -> Optional[Artifact]:
        """
        Retrieve an artifact.

        Args:
            job_id: Job ID that created the artifact
            artifact_type: Type of artifact

        Returns:
            Complete artifact with metadata and content, or None if not found

        Raises:
            StorageError: If retrieval operation fails
        """
        pass

    @abstractmethod
    async def list(
        self,
        artifact_type: Optional[ArtifactType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tags: Optional[dict[str, str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ArtifactMetadata]:
        """
        List artifacts matching filters.

        Args:
            artifact_type: Filter by artifact type
            start_date: Filter by creation date (inclusive)
            end_date: Filter by creation date (inclusive)
            tags: Filter by tags (all must match)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of artifact metadata

        Raises:
            StorageError: If list operation fails
        """
        pass

    @abstractmethod
    async def delete(self, job_id: str, artifact_type: ArtifactType) -> bool:
        """
        Delete an artifact.

        Args:
            job_id: Job ID that created the artifact
            artifact_type: Type of artifact

        Returns:
            True if artifact was deleted, False if not found

        Raises:
            StorageError: If delete operation fails
        """
        pass

    @abstractmethod
    async def exists(self, job_id: str, artifact_type: ArtifactType) -> bool:
        """
        Check if an artifact exists.

        Args:
            job_id: Job ID that created the artifact
            artifact_type: Type of artifact

        Returns:
            True if artifact exists, False otherwise

        Raises:
            StorageError: If check operation fails
        """
        pass

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """
        Clean up expired artifacts based on retention policy.

        Returns:
            Number of artifacts deleted

        Raises:
            StorageError: If cleanup operation fails
        """
        pass

    @abstractmethod
    async def get_storage_stats(self) -> dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dictionary with stats:
            - total_artifacts: Total number of artifacts
            - total_size_bytes: Total size in bytes
            - total_compressed_size_bytes: Total compressed size
            - artifacts_by_type: Breakdown by artifact type
            - oldest_artifact: Timestamp of oldest artifact
            - newest_artifact: Timestamp of newest artifact

        Raises:
            StorageError: If stats operation fails
        """
        pass

    async def stream_list(
        self,
        artifact_type: Optional[ArtifactType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tags: Optional[dict[str, str]] = None,
        batch_size: int = 100,
    ) -> AsyncIterator[list[ArtifactMetadata]]:
        """
        Stream artifacts in batches.

        Args:
            artifact_type: Filter by artifact type
            start_date: Filter by creation date (inclusive)
            end_date: Filter by creation date (inclusive)
            tags: Filter by tags (all must match)
            batch_size: Size of each batch

        Yields:
            Batches of artifact metadata

        Raises:
            StorageError: If list operation fails
        """
        offset = 0
        while True:
            batch = await self.list(
                artifact_type=artifact_type,
                start_date=start_date,
                end_date=end_date,
                tags=tags,
                limit=batch_size,
                offset=offset,
            )
            if not batch:
                break
            yield batch
            offset += len(batch)
            if len(batch) < batch_size:
                break


class StorageError(Exception):
    """Base exception for storage operations."""

    pass
