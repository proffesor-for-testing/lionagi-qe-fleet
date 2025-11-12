"""Artifact data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    """Types of artifacts that can be stored."""

    TEST_RESULTS = "test-results"
    COVERAGE_REPORT = "coverage-report"
    SECURITY_FINDINGS = "security-findings"
    PERFORMANCE_METRICS = "performance-metrics"
    BUILD_LOGS = "build-logs"
    STATIC_ANALYSIS = "static-analysis"
    API_DOCS = "api-docs"
    SCREENSHOTS = "screenshots"
    VIDEOS = "videos"
    CUSTOM = "custom"


class ArtifactMetadata(BaseModel):
    """Metadata for an artifact."""

    job_id: str = Field(..., description="Job ID that created this artifact")
    artifact_type: ArtifactType = Field(..., description="Type of artifact")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    size_bytes: int = Field(..., description="Size in bytes (uncompressed)")
    compressed_size_bytes: int = Field(..., description="Size in bytes (compressed)")
    compression_ratio: float = Field(
        ..., description="Compression ratio (0-1, lower is better)"
    )
    storage_path: str = Field(..., description="Path in storage backend")
    checksum: str = Field(..., description="SHA-256 checksum of content")
    tags: dict[str, str] = Field(
        default_factory=dict, description="Custom tags for filtering"
    )
    retention_days: Optional[int] = Field(
        None, description="Days to retain (None = keep forever)"
    )
    expires_at: Optional[datetime] = Field(
        None, description="Expiration timestamp (None = no expiration)"
    )


class Artifact(BaseModel):
    """Complete artifact with metadata and content."""

    metadata: ArtifactMetadata = Field(..., description="Artifact metadata")
    content: bytes = Field(..., description="Artifact content (compressed)")

    def size_mb(self) -> float:
        """Return size in megabytes."""
        return self.metadata.size_bytes / (1024 * 1024)

    def compressed_size_mb(self) -> float:
        """Return compressed size in megabytes."""
        return self.metadata.compressed_size_bytes / (1024 * 1024)

    def compression_savings_percent(self) -> float:
        """Return compression savings as percentage."""
        return (1 - self.metadata.compression_ratio) * 100

    def is_expired(self) -> bool:
        """Check if artifact has expired."""
        if self.metadata.expires_at is None:
            return False
        return datetime.utcnow() > self.metadata.expires_at

    def days_until_expiry(self) -> Optional[int]:
        """Return days until expiry, or None if no expiration."""
        if self.metadata.expires_at is None:
            return None
        delta = self.metadata.expires_at - datetime.utcnow()
        return max(0, delta.days)
