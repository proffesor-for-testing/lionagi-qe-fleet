"""Storage configuration models."""

from enum import Enum
from pathlib import Path
from typing import Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


class StorageBackend(str, Enum):
    """Available storage backends."""

    LOCAL = "local"
    S3 = "s3"
    MINIO = "minio"
    GITHUB_ACTIONS = "github-actions"
    GITLAB_CI = "gitlab-ci"


class LocalStorageConfig(BaseModel):
    """Configuration for local filesystem storage."""

    path: Path = Field(
        default=Path(".artifacts"), description="Directory to store artifacts"
    )
    create_if_missing: bool = Field(
        default=True, description="Create directory if it doesn't exist"
    )


class S3StorageConfig(BaseModel):
    """Configuration for S3-compatible storage."""

    bucket: str = Field(..., description="S3 bucket name")
    region: str = Field(default="us-east-1", description="AWS region")
    endpoint_url: Optional[str] = Field(
        None, description="Custom endpoint URL (for MinIO)"
    )
    access_key: Optional[str] = Field(
        None, description="AWS access key (or use IAM role)"
    )
    secret_key: Optional[str] = Field(
        None, description="AWS secret key (or use IAM role)"
    )
    prefix: str = Field(
        default="qe-fleet/", description="Key prefix for all artifacts"
    )
    use_ssl: bool = Field(default=True, description="Use SSL for connections")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")


class CIStorageConfig(BaseModel):
    """Configuration for CI-native artifact storage."""

    platform: Literal["github-actions", "gitlab-ci"] = Field(
        ..., description="CI platform"
    )
    artifact_name_prefix: str = Field(
        default="qe-fleet-", description="Prefix for artifact names"
    )
    retention_days: int = Field(
        default=30, description="Days to retain artifacts in CI"
    )


class RetentionPolicy(BaseModel):
    """Configuration for artifact retention."""

    default_ttl_days: int = Field(
        default=30, description="Default time-to-live in days"
    )
    keep_latest_n: int = Field(
        default=10, description="Always keep N most recent artifacts"
    )
    cleanup_schedule_cron: str = Field(
        default="0 2 * * *", description="Cron schedule for cleanup (2 AM daily)"
    )
    enabled: bool = Field(default=True, description="Enable automatic cleanup")

    @field_validator("default_ttl_days")
    @classmethod
    def validate_ttl(cls, v: int) -> int:
        if v < 1:
            raise ValueError("TTL must be at least 1 day")
        return v

    @field_validator("keep_latest_n")
    @classmethod
    def validate_keep_latest(cls, v: int) -> int:
        if v < 0:
            raise ValueError("keep_latest_n must be non-negative")
        return v


class StorageConfig(BaseModel):
    """Complete storage system configuration."""

    backend: StorageBackend = Field(
        default=StorageBackend.LOCAL, description="Storage backend to use"
    )
    local: LocalStorageConfig = Field(
        default_factory=LocalStorageConfig, description="Local storage config"
    )
    s3: Optional[S3StorageConfig] = Field(
        None, description="S3 storage config (required if backend is s3/minio)"
    )
    ci: Optional[CIStorageConfig] = Field(
        None, description="CI storage config (required if backend is github/gitlab)"
    )
    retention: RetentionPolicy = Field(
        default_factory=RetentionPolicy, description="Retention policy"
    )
    compression_enabled: bool = Field(
        default=True, description="Enable gzip compression"
    )
    compression_level: int = Field(
        default=6, ge=1, le=9, description="Gzip compression level (1-9)"
    )
    max_artifact_size_mb: int = Field(
        default=100, description="Maximum artifact size in MB"
    )

    @field_validator("backend")
    @classmethod
    def validate_backend_config(cls, v: StorageBackend, info) -> StorageBackend:
        """Validate that required config is present for chosen backend."""
        # Note: This runs before other fields are set, so we can't check dependencies here
        # Validation is done in __init__ or a separate method
        return v

    def validate_configuration(self) -> None:
        """Validate that required configuration is present for chosen backend."""
        if self.backend in (StorageBackend.S3, StorageBackend.MINIO):
            if self.s3 is None:
                raise ValueError(f"S3 config required for backend: {self.backend}")
        elif self.backend in (StorageBackend.GITHUB_ACTIONS, StorageBackend.GITLAB_CI):
            if self.ci is None:
                raise ValueError(f"CI config required for backend: {self.backend}")
