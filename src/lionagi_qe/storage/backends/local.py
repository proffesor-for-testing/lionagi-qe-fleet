"""Local filesystem storage backend."""

from __future__ import annotations
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from ..backends.base import ArtifactStorage, StorageError
from ..models.artifact import Artifact, ArtifactType, ArtifactMetadata
from ..models.storage_config import LocalStorageConfig, RetentionPolicy
from ..utils.compression import CompressionUtil
from ..utils.retention import RetentionManager
from ..utils.index import MetadataIndex


class LocalStorage(ArtifactStorage):
    """Local filesystem storage backend."""

    def __init__(
        self,
        config: LocalStorageConfig,
        retention_policy: RetentionPolicy,
        compression_enabled: bool = True,
        compression_level: int = 6,
    ):
        """
        Initialize local storage.

        Args:
            config: Local storage configuration
            retention_policy: Retention policy
            compression_enabled: Enable compression
            compression_level: Gzip compression level (1-9)
        """
        self.config = config
        self.retention_policy = retention_policy
        self.compression_enabled = compression_enabled
        self.compression_level = compression_level

        # Create storage directory
        if config.create_if_missing:
            config.path.mkdir(parents=True, exist_ok=True)

        # Initialize metadata index
        index_path = config.path / "index.sqlite"
        self.index = MetadataIndex(index_path)

        # Initialize retention manager
        self.retention_manager = RetentionManager(retention_policy)

    def _get_artifact_path(self, job_id: str, artifact_type: ArtifactType) -> Path:
        """Get filesystem path for an artifact."""
        job_dir = self.config.path / job_id
        filename = f"{artifact_type.value}.bin.gz"
        return job_dir / filename

    async def store(
        self,
        job_id: str,
        artifact_type: ArtifactType,
        data: bytes,
        tags: Optional[dict[str, str]] = None,
    ) -> ArtifactMetadata:
        """Store an artifact."""
        try:
            # Compress data if enabled
            if self.compression_enabled:
                compressed_data, compression_ratio, checksum = CompressionUtil.compress(
                    data, self.compression_level
                )
            else:
                compressed_data = data
                compression_ratio = 1.0
                checksum = CompressionUtil.compress(data, 1)[2]  # Get checksum only

            # Create job directory
            artifact_path = self._get_artifact_path(job_id, artifact_type)
            artifact_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to disk
            await asyncio.to_thread(artifact_path.write_bytes, compressed_data)

            # Create metadata
            timestamp = datetime.utcnow()
            metadata = ArtifactMetadata(
                job_id=job_id,
                artifact_type=artifact_type,
                timestamp=timestamp,
                size_bytes=len(data),
                compressed_size_bytes=len(compressed_data),
                compression_ratio=compression_ratio,
                storage_path=str(artifact_path),
                checksum=checksum,
                tags=tags or {},
                retention_days=self.retention_policy.default_ttl_days,
                expires_at=self.retention_manager.calculate_expiry(timestamp),
            )

            # Add to index
            await asyncio.to_thread(self.index.add, metadata)

            return metadata

        except Exception as e:
            raise StorageError(f"Failed to store artifact: {e}")

    async def retrieve(
        self, job_id: str, artifact_type: ArtifactType
    ) -> Optional[Artifact]:
        """Retrieve an artifact."""
        try:
            # Get metadata from index
            metadata = await asyncio.to_thread(
                self.index.get, job_id, artifact_type
            )
            if metadata is None:
                return None

            # Read from disk
            artifact_path = Path(metadata.storage_path)
            if not artifact_path.exists():
                # Artifact missing from disk, remove from index
                await asyncio.to_thread(self.index.delete, job_id, artifact_type)
                return None

            compressed_data = await asyncio.to_thread(artifact_path.read_bytes)

            return Artifact(metadata=metadata, content=compressed_data)

        except Exception as e:
            raise StorageError(f"Failed to retrieve artifact: {e}")

    async def list(
        self,
        artifact_type: Optional[ArtifactType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tags: Optional[dict[str, str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ArtifactMetadata]:
        """List artifacts matching filters."""
        try:
            return await asyncio.to_thread(
                self.index.list,
                artifact_type=artifact_type,
                start_date=start_date,
                end_date=end_date,
                tags=tags,
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            raise StorageError(f"Failed to list artifacts: {e}")

    async def delete(self, job_id: str, artifact_type: ArtifactType) -> bool:
        """Delete an artifact."""
        try:
            # Get metadata
            metadata = await asyncio.to_thread(
                self.index.get, job_id, artifact_type
            )
            if metadata is None:
                return False

            # Delete from disk
            artifact_path = Path(metadata.storage_path)
            if artifact_path.exists():
                await asyncio.to_thread(artifact_path.unlink)

            # Delete from index
            await asyncio.to_thread(self.index.delete, job_id, artifact_type)

            return True

        except Exception as e:
            raise StorageError(f"Failed to delete artifact: {e}")

    async def exists(self, job_id: str, artifact_type: ArtifactType) -> bool:
        """Check if an artifact exists."""
        try:
            metadata = await asyncio.to_thread(
                self.index.get, job_id, artifact_type
            )
            if metadata is None:
                return False

            # Verify file exists on disk
            artifact_path = Path(metadata.storage_path)
            return artifact_path.exists()

        except Exception as e:
            raise StorageError(f"Failed to check artifact existence: {e}")

    async def cleanup_expired(self) -> int:
        """Clean up expired artifacts."""
        try:
            # Get all artifacts
            all_artifacts = await asyncio.to_thread(
                self.index.list, limit=1000000
            )

            # Find expired artifacts
            expired = self.retention_manager.get_expired_artifacts(all_artifacts)

            # Delete each expired artifact
            deleted_count = 0
            for artifact in expired:
                success = await self.delete(artifact.job_id, artifact.artifact_type)
                if success:
                    deleted_count += 1

            return deleted_count

        except Exception as e:
            raise StorageError(f"Failed to cleanup expired artifacts: {e}")

    async def get_storage_stats(self) -> dict[str, Any]:
        """Get storage statistics."""
        try:
            return await asyncio.to_thread(self.index.get_stats)
        except Exception as e:
            raise StorageError(f"Failed to get storage stats: {e}")

    def decompress_artifact(self, artifact: Artifact) -> bytes:
        """
        Decompress artifact content.

        Args:
            artifact: Artifact with compressed content

        Returns:
            Decompressed content

        Raises:
            StorageError: If decompression fails
        """
        try:
            if self.compression_enabled:
                return CompressionUtil.decompress(artifact.content)
            return artifact.content
        except Exception as e:
            raise StorageError(f"Failed to decompress artifact: {e}")
