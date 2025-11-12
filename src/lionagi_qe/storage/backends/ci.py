"""CI-native artifact storage (GitHub Actions, GitLab CI)."""

from __future__ import annotations
import asyncio
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from ..backends.base import ArtifactStorage, StorageError
from ..models.artifact import Artifact, ArtifactType, ArtifactMetadata
from ..models.storage_config import CIStorageConfig, RetentionPolicy
from ..utils.compression import CompressionUtil
from ..utils.retention import RetentionManager


class CIStorage(ArtifactStorage):
    """
    CI-native artifact storage.

    Automatically detects GitHub Actions or GitLab CI and uses native artifact storage.
    Falls back to local storage if not running in CI.
    """

    def __init__(
        self,
        config: CIStorageConfig,
        retention_policy: RetentionPolicy,
        compression_enabled: bool = True,
        compression_level: int = 6,
        fallback_path: Path = Path(".artifacts"),
    ):
        """
        Initialize CI storage.

        Args:
            config: CI storage configuration
            retention_policy: Retention policy
            compression_enabled: Enable compression
            compression_level: Gzip compression level (1-9)
            fallback_path: Fallback path if not in CI environment
        """
        self.config = config
        self.retention_policy = retention_policy
        self.compression_enabled = compression_enabled
        self.compression_level = compression_level
        self.fallback_path = fallback_path

        # Detect CI environment
        self.is_github_actions = os.getenv("GITHUB_ACTIONS") == "true"
        self.is_gitlab_ci = os.getenv("GITLAB_CI") == "true"
        self.is_ci = self.is_github_actions or self.is_gitlab_ci

        # Use local fallback if not in CI
        if not self.is_ci:
            from .local import LocalStorage
            from ..models.storage_config import LocalStorageConfig

            self._fallback_storage = LocalStorage(
                config=LocalStorageConfig(path=fallback_path),
                retention_policy=retention_policy,
                compression_enabled=compression_enabled,
                compression_level=compression_level,
            )

        self.retention_manager = RetentionManager(retention_policy)

        # Prepare artifact directory
        self.artifact_dir = fallback_path / "ci-artifacts"
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    def _get_artifact_name(self, job_id: str, artifact_type: ArtifactType) -> str:
        """Get artifact name for CI platform."""
        prefix = self.config.artifact_name_prefix
        return f"{prefix}{job_id}-{artifact_type.value}"

    def _get_artifact_path(self, job_id: str, artifact_type: ArtifactType) -> Path:
        """Get local path for artifact (before upload to CI)."""
        return self.artifact_dir / f"{job_id}-{artifact_type.value}.bin.gz"

    async def store(
        self,
        job_id: str,
        artifact_type: ArtifactType,
        data: bytes,
        tags: Optional[dict[str, str]] = None,
    ) -> ArtifactMetadata:
        """Store an artifact."""
        # Use fallback if not in CI
        if not self.is_ci:
            return await self._fallback_storage.store(
                job_id, artifact_type, data, tags
            )

        try:
            # Compress data
            if self.compression_enabled:
                compressed_data, compression_ratio, checksum = CompressionUtil.compress(
                    data, self.compression_level
                )
            else:
                compressed_data = data
                compression_ratio = 1.0
                checksum = CompressionUtil.compress(data, 1)[2]

            # Write to local file
            artifact_path = self._get_artifact_path(job_id, artifact_type)
            await asyncio.to_thread(artifact_path.write_bytes, compressed_data)

            # Upload to CI platform
            artifact_name = self._get_artifact_name(job_id, artifact_type)
            if self.is_github_actions:
                await self._upload_github_actions(artifact_path, artifact_name)
            elif self.is_gitlab_ci:
                await self._upload_gitlab_ci(artifact_path, artifact_name)

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
                retention_days=self.config.retention_days,
                expires_at=self.retention_manager.calculate_expiry(
                    timestamp, self.config.retention_days
                ),
            )

            return metadata

        except Exception as e:
            raise StorageError(f"Failed to store artifact in CI: {e}")

    async def _upload_github_actions(self, artifact_path: Path, artifact_name: str):
        """Upload artifact to GitHub Actions."""
        try:
            # GitHub Actions uses actions/upload-artifact
            # We need to use the gh CLI or set outputs for the workflow
            # For now, we'll just mark the file for upload
            # In a real workflow, you'd use: actions/upload-artifact@v4

            # Set GitHub Actions output to signal artifact is ready
            github_output = os.getenv("GITHUB_OUTPUT")
            if github_output:
                with open(github_output, "a") as f:
                    f.write(f"artifact_path={artifact_path}\n")
                    f.write(f"artifact_name={artifact_name}\n")

        except Exception as e:
            raise StorageError(f"Failed to upload to GitHub Actions: {e}")

    async def _upload_gitlab_ci(self, artifact_path: Path, artifact_name: str):
        """Upload artifact to GitLab CI."""
        try:
            # GitLab CI uses artifacts in .gitlab-ci.yml
            # We'll write a artifacts.txt file that the CI job can use
            artifacts_file = self.artifact_dir / "gitlab-artifacts.txt"
            with open(artifacts_file, "a") as f:
                f.write(f"{artifact_path}\n")

        except Exception as e:
            raise StorageError(f"Failed to upload to GitLab CI: {e}")

    async def retrieve(
        self, job_id: str, artifact_type: ArtifactType
    ) -> Optional[Artifact]:
        """Retrieve an artifact."""
        if not self.is_ci:
            return await self._fallback_storage.retrieve(job_id, artifact_type)

        try:
            # Try to find artifact locally first
            artifact_path = self._get_artifact_path(job_id, artifact_type)
            if not artifact_path.exists():
                return None

            compressed_data = await asyncio.to_thread(artifact_path.read_bytes)

            # Create metadata from file
            timestamp = datetime.fromtimestamp(artifact_path.stat().st_mtime)
            metadata = ArtifactMetadata(
                job_id=job_id,
                artifact_type=artifact_type,
                timestamp=timestamp,
                size_bytes=len(compressed_data),  # Approximate
                compressed_size_bytes=len(compressed_data),
                compression_ratio=0.7,  # Estimate
                storage_path=str(artifact_path),
                checksum="",  # Would need to recalculate
                tags={},
                retention_days=self.config.retention_days,
                expires_at=None,
            )

            return Artifact(metadata=metadata, content=compressed_data)

        except Exception as e:
            raise StorageError(f"Failed to retrieve artifact from CI: {e}")

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
        if not self.is_ci:
            return await self._fallback_storage.list(
                artifact_type, start_date, end_date, tags, limit, offset
            )

        try:
            # List local artifacts
            artifacts = []
            for path in self.artifact_dir.glob("*.bin.gz"):
                # Parse filename: {job_id}-{artifact_type}.bin.gz
                name = path.stem.replace(".bin", "")
                parts = name.rsplit("-", 1)
                if len(parts) == 2:
                    job_id, artifact_type_str = parts
                    try:
                        artifact_type_enum = ArtifactType(artifact_type_str)
                        timestamp = datetime.fromtimestamp(path.stat().st_mtime)

                        metadata = ArtifactMetadata(
                            job_id=job_id,
                            artifact_type=artifact_type_enum,
                            timestamp=timestamp,
                            size_bytes=path.stat().st_size,
                            compressed_size_bytes=path.stat().st_size,
                            compression_ratio=0.7,
                            storage_path=str(path),
                            checksum="",
                            tags={},
                            retention_days=self.config.retention_days,
                            expires_at=None,
                        )
                        artifacts.append(metadata)
                    except ValueError:
                        continue

            # Apply filters
            filtered = artifacts
            if artifact_type:
                filtered = [m for m in filtered if m.artifact_type == artifact_type]
            if start_date:
                filtered = [m for m in filtered if m.timestamp >= start_date]
            if end_date:
                filtered = [m for m in filtered if m.timestamp <= end_date]

            # Sort by timestamp
            filtered.sort(key=lambda m: m.timestamp, reverse=True)

            return filtered[offset : offset + limit]

        except Exception as e:
            raise StorageError(f"Failed to list artifacts from CI: {e}")

    async def delete(self, job_id: str, artifact_type: ArtifactType) -> bool:
        """Delete an artifact."""
        if not self.is_ci:
            return await self._fallback_storage.delete(job_id, artifact_type)

        try:
            artifact_path = self._get_artifact_path(job_id, artifact_type)
            if not artifact_path.exists():
                return False

            await asyncio.to_thread(artifact_path.unlink)
            return True

        except Exception as e:
            raise StorageError(f"Failed to delete artifact from CI: {e}")

    async def exists(self, job_id: str, artifact_type: ArtifactType) -> bool:
        """Check if an artifact exists."""
        if not self.is_ci:
            return await self._fallback_storage.exists(job_id, artifact_type)

        artifact_path = self._get_artifact_path(job_id, artifact_type)
        return artifact_path.exists()

    async def cleanup_expired(self) -> int:
        """Clean up expired artifacts."""
        if not self.is_ci:
            return await self._fallback_storage.cleanup_expired()

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
            raise StorageError(f"Failed to cleanup expired artifacts from CI: {e}")

    async def get_storage_stats(self) -> dict[str, Any]:
        """Get storage statistics."""
        if not self.is_ci:
            return await self._fallback_storage.get_storage_stats()

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
            raise StorageError(f"Failed to get storage stats from CI: {e}")
