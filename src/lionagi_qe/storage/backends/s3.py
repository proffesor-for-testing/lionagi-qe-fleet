"""S3-compatible storage backend (AWS S3, MinIO)."""

from __future__ import annotations
import asyncio
import os
from datetime import datetime
from typing import Optional, Any

from ..backends.base import ArtifactStorage, StorageError
from ..models.artifact import Artifact, ArtifactType, ArtifactMetadata
from ..models.storage_config import S3StorageConfig, RetentionPolicy
from ..utils.compression import CompressionUtil
from ..utils.retention import RetentionManager


class S3Storage(ArtifactStorage):
    """
    S3-compatible storage backend.

    Supports both AWS S3 and MinIO (self-hosted S3-compatible storage).
    Requires boto3 to be installed: pip install boto3
    """

    def __init__(
        self,
        config: S3StorageConfig,
        retention_policy: RetentionPolicy,
        compression_enabled: bool = True,
        compression_level: int = 6,
    ):
        """
        Initialize S3 storage.

        Args:
            config: S3 storage configuration
            retention_policy: Retention policy
            compression_enabled: Enable compression
            compression_level: Gzip compression level (1-9)

        Raises:
            ImportError: If boto3 is not installed
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 storage. Install with: pip install boto3"
            )

        self.config = config
        self.retention_policy = retention_policy
        self.compression_enabled = compression_enabled
        self.compression_level = compression_level
        self.ClientError = ClientError

        # Initialize S3 client
        session_kwargs = {}
        if config.access_key and config.secret_key:
            session_kwargs["aws_access_key_id"] = config.access_key
            session_kwargs["aws_secret_access_key"] = config.secret_key

        client_kwargs = {
            "region_name": config.region,
            "use_ssl": config.use_ssl,
            "verify": config.verify_ssl,
        }
        if config.endpoint_url:
            client_kwargs["endpoint_url"] = config.endpoint_url

        self.s3_client = boto3.client("s3", **session_kwargs, **client_kwargs)
        self.retention_manager = RetentionManager(retention_policy)

        # In-memory metadata cache (in production, use Redis or similar)
        self._metadata_cache: dict[tuple[str, str], ArtifactMetadata] = {}

    def _get_s3_key(self, job_id: str, artifact_type: ArtifactType) -> str:
        """Get S3 key for an artifact."""
        return f"{self.config.prefix}{job_id}/{artifact_type.value}.bin.gz"

    def _get_metadata_key(self, job_id: str, artifact_type: ArtifactType) -> str:
        """Get S3 key for artifact metadata."""
        return f"{self.config.prefix}{job_id}/{artifact_type.value}.metadata.json"

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
                checksum = CompressionUtil.compress(data, 1)[2]

            # Upload to S3
            s3_key = self._get_s3_key(job_id, artifact_type)
            s3_tags = tags or {}
            s3_tags_str = "&".join([f"{k}={v}" for k, v in s3_tags.items()])

            await asyncio.to_thread(
                self.s3_client.put_object,
                Bucket=self.config.bucket,
                Key=s3_key,
                Body=compressed_data,
                ContentType="application/octet-stream",
                Tagging=s3_tags_str if s3_tags_str else None,
            )

            # Create metadata
            timestamp = datetime.utcnow()
            metadata = ArtifactMetadata(
                job_id=job_id,
                artifact_type=artifact_type,
                timestamp=timestamp,
                size_bytes=len(data),
                compressed_size_bytes=len(compressed_data),
                compression_ratio=compression_ratio,
                storage_path=s3_key,
                checksum=checksum,
                tags=s3_tags,
                retention_days=self.retention_policy.default_ttl_days,
                expires_at=self.retention_manager.calculate_expiry(timestamp),
            )

            # Store metadata
            metadata_key = self._get_metadata_key(job_id, artifact_type)
            await asyncio.to_thread(
                self.s3_client.put_object,
                Bucket=self.config.bucket,
                Key=metadata_key,
                Body=metadata.model_dump_json().encode(),
                ContentType="application/json",
            )

            # Cache metadata
            self._metadata_cache[(job_id, artifact_type.value)] = metadata

            return metadata

        except Exception as e:
            raise StorageError(f"Failed to store artifact in S3: {e}")

    async def retrieve(
        self, job_id: str, artifact_type: ArtifactType
    ) -> Optional[Artifact]:
        """Retrieve an artifact."""
        try:
            # Get metadata first
            metadata = await self._get_metadata(job_id, artifact_type)
            if metadata is None:
                return None

            # Download from S3
            s3_key = self._get_s3_key(job_id, artifact_type)
            response = await asyncio.to_thread(
                self.s3_client.get_object,
                Bucket=self.config.bucket,
                Key=s3_key,
            )
            compressed_data = response["Body"].read()

            return Artifact(metadata=metadata, content=compressed_data)

        except self.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise StorageError(f"Failed to retrieve artifact from S3: {e}")
        except Exception as e:
            raise StorageError(f"Failed to retrieve artifact from S3: {e}")

    async def _get_metadata(
        self, job_id: str, artifact_type: ArtifactType
    ) -> Optional[ArtifactMetadata]:
        """Get metadata for an artifact."""
        # Check cache first
        cache_key = (job_id, artifact_type.value)
        if cache_key in self._metadata_cache:
            return self._metadata_cache[cache_key]

        try:
            metadata_key = self._get_metadata_key(job_id, artifact_type)
            response = await asyncio.to_thread(
                self.s3_client.get_object,
                Bucket=self.config.bucket,
                Key=metadata_key,
            )
            metadata_json = response["Body"].read().decode()
            metadata = ArtifactMetadata.model_validate_json(metadata_json)
            self._metadata_cache[cache_key] = metadata
            return metadata

        except self.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise

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
            # List all metadata files
            prefix = f"{self.config.prefix}"
            response = await asyncio.to_thread(
                self.s3_client.list_objects_v2,
                Bucket=self.config.bucket,
                Prefix=prefix,
            )

            metadata_list = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    key = obj["Key"]
                    if key.endswith(".metadata.json"):
                        # Extract job_id and artifact_type from key
                        parts = key.replace(prefix, "").split("/")
                        if len(parts) >= 2:
                            job_id = parts[0]
                            artifact_file = parts[1].replace(".metadata.json", "")
                            try:
                                artifact_type_enum = ArtifactType(artifact_file)
                                metadata = await self._get_metadata(
                                    job_id, artifact_type_enum
                                )
                                if metadata:
                                    metadata_list.append(metadata)
                            except ValueError:
                                continue

            # Apply filters
            filtered = metadata_list
            if artifact_type:
                filtered = [m for m in filtered if m.artifact_type == artifact_type]
            if start_date:
                filtered = [m for m in filtered if m.timestamp >= start_date]
            if end_date:
                filtered = [m for m in filtered if m.timestamp <= end_date]
            if tags:
                filtered = [
                    m for m in filtered
                    if all(m.tags.get(k) == v for k, v in tags.items())
                ]

            # Sort by timestamp (newest first)
            filtered.sort(key=lambda m: m.timestamp, reverse=True)

            # Apply pagination
            return filtered[offset : offset + limit]

        except Exception as e:
            raise StorageError(f"Failed to list artifacts from S3: {e}")

    async def delete(self, job_id: str, artifact_type: ArtifactType) -> bool:
        """Delete an artifact."""
        try:
            # Delete both artifact and metadata
            s3_key = self._get_s3_key(job_id, artifact_type)
            metadata_key = self._get_metadata_key(job_id, artifact_type)

            # Check if exists
            metadata = await self._get_metadata(job_id, artifact_type)
            if metadata is None:
                return False

            # Delete from S3
            await asyncio.to_thread(
                self.s3_client.delete_objects,
                Bucket=self.config.bucket,
                Delete={"Objects": [{"Key": s3_key}, {"Key": metadata_key}]},
            )

            # Remove from cache
            cache_key = (job_id, artifact_type.value)
            self._metadata_cache.pop(cache_key, None)

            return True

        except Exception as e:
            raise StorageError(f"Failed to delete artifact from S3: {e}")

    async def exists(self, job_id: str, artifact_type: ArtifactType) -> bool:
        """Check if an artifact exists."""
        try:
            metadata = await self._get_metadata(job_id, artifact_type)
            return metadata is not None
        except Exception as e:
            raise StorageError(f"Failed to check artifact existence in S3: {e}")

    async def cleanup_expired(self) -> int:
        """Clean up expired artifacts."""
        try:
            all_artifacts = await self.list(limit=1000000)
            expired = self.retention_manager.get_expired_artifacts(all_artifacts)

            deleted_count = 0
            for artifact in expired:
                success = await self.delete(artifact.job_id, artifact.artifact_type)
                if success:
                    deleted_count += 1

            return deleted_count

        except Exception as e:
            raise StorageError(f"Failed to cleanup expired artifacts from S3: {e}")

    async def get_storage_stats(self) -> dict[str, Any]:
        """Get storage statistics."""
        try:
            all_artifacts = await self.list(limit=1000000)

            total_size = sum(m.size_bytes for m in all_artifacts)
            total_compressed = sum(m.compressed_size_bytes for m in all_artifacts)

            by_type = {}
            for artifact in all_artifacts:
                type_name = artifact.artifact_type.value
                by_type[type_name] = by_type.get(type_name, 0) + 1

            oldest = min((m.timestamp for m in all_artifacts), default=None)
            newest = max((m.timestamp for m in all_artifacts), default=None)

            return {
                "total_artifacts": len(all_artifacts),
                "total_size_bytes": total_size,
                "total_compressed_size_bytes": total_compressed,
                "artifacts_by_type": by_type,
                "oldest_artifact": oldest.isoformat() if oldest else None,
                "newest_artifact": newest.isoformat() if newest else None,
            }

        except Exception as e:
            raise StorageError(f"Failed to get storage stats from S3: {e}")

    def decompress_artifact(self, artifact: Artifact) -> bytes:
        """Decompress artifact content."""
        try:
            if self.compression_enabled:
                return CompressionUtil.decompress(artifact.content)
            return artifact.content
        except Exception as e:
            raise StorageError(f"Failed to decompress artifact: {e}")
