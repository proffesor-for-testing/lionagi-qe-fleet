"""Storage factory for creating backend instances."""

from pathlib import Path

from ..backends.base import ArtifactStorage
from ..backends.local import LocalStorage
from ..backends.s3 import S3Storage
from ..backends.ci import CIStorage
from ..models.storage_config import StorageConfig, StorageBackend


class StorageFactory:
    """Factory for creating storage backend instances."""

    @staticmethod
    def create(config: StorageConfig) -> ArtifactStorage:
        """
        Create a storage backend instance based on configuration.

        Args:
            config: Storage configuration

        Returns:
            Storage backend instance

        Raises:
            ValueError: If backend type is invalid or config is missing
        """
        # Validate configuration
        config.validate_configuration()

        if config.backend == StorageBackend.LOCAL:
            return LocalStorage(
                config=config.local,
                retention_policy=config.retention,
                compression_enabled=config.compression_enabled,
                compression_level=config.compression_level,
            )

        elif config.backend in (StorageBackend.S3, StorageBackend.MINIO):
            if config.s3 is None:
                raise ValueError(f"S3 config required for backend: {config.backend}")

            return S3Storage(
                config=config.s3,
                retention_policy=config.retention,
                compression_enabled=config.compression_enabled,
                compression_level=config.compression_level,
            )

        elif config.backend in (
            StorageBackend.GITHUB_ACTIONS,
            StorageBackend.GITLAB_CI,
        ):
            if config.ci is None:
                raise ValueError(f"CI config required for backend: {config.backend}")

            return CIStorage(
                config=config.ci,
                retention_policy=config.retention,
                compression_enabled=config.compression_enabled,
                compression_level=config.compression_level,
                fallback_path=config.local.path,
            )

        else:
            raise ValueError(f"Unsupported storage backend: {config.backend}")

    @staticmethod
    def create_from_env() -> ArtifactStorage:
        """
        Create storage backend from environment variables.

        Environment variables:
        - QE_STORAGE_BACKEND: Backend type (local, s3, minio, github-actions, gitlab-ci)
        - QE_STORAGE_PATH: Local storage path (for local backend)
        - QE_S3_BUCKET: S3 bucket name
        - QE_S3_REGION: S3 region
        - QE_S3_ENDPOINT: S3 endpoint URL (for MinIO)
        - QE_S3_ACCESS_KEY: S3 access key
        - QE_S3_SECRET_KEY: S3 secret key
        - QE_RETENTION_TTL_DAYS: Default TTL in days
        - QE_RETENTION_KEEP_LATEST: Number of latest artifacts to keep

        Returns:
            Storage backend instance
        """
        import os
        from ..models.storage_config import (
            StorageConfig,
            LocalStorageConfig,
            S3StorageConfig,
            CIStorageConfig,
            RetentionPolicy,
            StorageBackend,
        )

        backend_str = os.getenv("QE_STORAGE_BACKEND", "local")
        backend = StorageBackend(backend_str)

        # Build config based on backend
        config = StorageConfig(backend=backend)

        # Local config
        if backend == StorageBackend.LOCAL:
            path_str = os.getenv("QE_STORAGE_PATH", ".artifacts")
            config.local = LocalStorageConfig(path=Path(path_str))

        # S3 config
        elif backend in (StorageBackend.S3, StorageBackend.MINIO):
            bucket = os.getenv("QE_S3_BUCKET")
            if not bucket:
                raise ValueError("QE_S3_BUCKET environment variable required")

            config.s3 = S3StorageConfig(
                bucket=bucket,
                region=os.getenv("QE_S3_REGION", "us-east-1"),
                endpoint_url=os.getenv("QE_S3_ENDPOINT"),
                access_key=os.getenv("QE_S3_ACCESS_KEY"),
                secret_key=os.getenv("QE_S3_SECRET_KEY"),
            )

        # CI config
        elif backend in (StorageBackend.GITHUB_ACTIONS, StorageBackend.GITLAB_CI):
            config.ci = CIStorageConfig(platform=backend)

        # Retention policy
        ttl_days = int(os.getenv("QE_RETENTION_TTL_DAYS", "30"))
        keep_latest = int(os.getenv("QE_RETENTION_KEEP_LATEST", "10"))
        config.retention = RetentionPolicy(
            default_ttl_days=ttl_days, keep_latest_n=keep_latest
        )

        return StorageFactory.create(config)
