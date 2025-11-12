"""
Artifact Storage System for QE Fleet

Provides pluggable storage backends for test results, coverage reports,
security findings, and other artifacts with compression and retention policies.
"""

from .models.artifact import Artifact, ArtifactType, ArtifactMetadata
from .models.storage_config import (
    StorageConfig,
    LocalStorageConfig,
    S3StorageConfig,
    CIStorageConfig,
    RetentionPolicy,
)
from .backends.base import ArtifactStorage
from .backends.local import LocalStorage
from .backends.s3 import S3Storage
from .backends.ci import CIStorage
from .backends.factory import StorageFactory
from .utils.compression import CompressionUtil
from .utils.retention import RetentionManager
from .query import ArtifactQuery

__all__ = [
    # Models
    "Artifact",
    "ArtifactType",
    "ArtifactMetadata",
    # Config
    "StorageConfig",
    "LocalStorageConfig",
    "S3StorageConfig",
    "CIStorageConfig",
    "RetentionPolicy",
    # Backends
    "ArtifactStorage",
    "LocalStorage",
    "S3Storage",
    "CIStorage",
    "StorageFactory",
    # Utils
    "CompressionUtil",
    "RetentionManager",
    # Query
    "ArtifactQuery",
]
