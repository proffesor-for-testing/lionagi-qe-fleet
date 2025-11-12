"""Retention policy management."""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, Any

from ..models.artifact import ArtifactMetadata
from ..models.storage_config import RetentionPolicy


class RetentionManager:
    """Manages artifact retention policies."""

    def __init__(self, policy: RetentionPolicy):
        """
        Initialize retention manager.

        Args:
            policy: Retention policy configuration
        """
        self.policy = policy

    def should_keep(
        self, artifact: ArtifactMetadata, latest_n_artifacts: list[ArtifactMetadata]
    ) -> bool:
        """
        Determine if an artifact should be kept based on retention policy.

        Args:
            artifact: Artifact to check
            latest_n_artifacts: List of N most recent artifacts (for keep_latest_n)

        Returns:
            True if artifact should be kept, False if it should be deleted
        """
        # Always keep if in the latest N
        if artifact in latest_n_artifacts[: self.policy.keep_latest_n]:
            return True

        # Check if expired based on retention_days
        if artifact.retention_days is not None:
            expiry_date = artifact.timestamp + timedelta(days=artifact.retention_days)
            if datetime.utcnow() > expiry_date:
                return False

        # Check explicit expiration
        if artifact.expires_at is not None:
            if datetime.utcnow() > artifact.expires_at:
                return False

        # Apply default TTL if no explicit retention is set
        if artifact.retention_days is None and artifact.expires_at is None:
            default_expiry = artifact.timestamp + timedelta(
                days=self.policy.default_ttl_days
            )
            if datetime.utcnow() > default_expiry:
                return False

        return True

    def calculate_expiry(
        self, timestamp: datetime, retention_days: Optional[int] = None
    ) -> Optional[datetime]:
        """
        Calculate expiration timestamp for an artifact.

        Args:
            timestamp: Creation timestamp
            retention_days: Custom retention period, or None to use default

        Returns:
            Expiration timestamp, or None if artifact should be kept forever
        """
        days = retention_days if retention_days is not None else self.policy.default_ttl_days
        return timestamp + timedelta(days=days)

    def get_expired_artifacts(
        self, artifacts: list[ArtifactMetadata]
    ) -> list[ArtifactMetadata]:
        """
        Get list of expired artifacts that should be deleted.

        Args:
            artifacts: List of all artifacts

        Returns:
            List of artifacts that should be deleted
        """
        if not self.policy.enabled:
            return []

        # Sort by timestamp (newest first)
        sorted_artifacts = sorted(
            artifacts, key=lambda x: x.timestamp, reverse=True
        )

        expired = []
        for artifact in sorted_artifacts:
            if not self.should_keep(artifact, sorted_artifacts):
                expired.append(artifact)

        return expired

    def calculate_cleanup_stats(
        self, artifacts: list[ArtifactMetadata]
    ) -> dict[str, Any]:
        """
        Calculate statistics about what would be cleaned up.

        Args:
            artifacts: List of all artifacts

        Returns:
            Dictionary with cleanup stats:
            - total_artifacts: Total number of artifacts
            - artifacts_to_delete: Number that would be deleted
            - artifacts_to_keep: Number that would be kept
            - bytes_to_free: Bytes that would be freed
            - oldest_kept: Timestamp of oldest artifact that would be kept
        """
        expired = self.get_expired_artifacts(artifacts)
        kept = [a for a in artifacts if a not in expired]

        bytes_to_free = sum(a.compressed_size_bytes for a in expired)
        oldest_kept = min((a.timestamp for a in kept), default=None)

        return {
            "total_artifacts": len(artifacts),
            "artifacts_to_delete": len(expired),
            "artifacts_to_keep": len(kept),
            "bytes_to_free": bytes_to_free,
            "mb_to_free": bytes_to_free / (1024 * 1024),
            "oldest_kept": oldest_kept,
        }
