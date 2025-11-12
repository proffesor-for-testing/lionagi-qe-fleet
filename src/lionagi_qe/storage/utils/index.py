"""Metadata index using SQLite."""

from __future__ import annotations
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from ..models.artifact import ArtifactType, ArtifactMetadata


class MetadataIndex:
    """SQLite-based index for artifact metadata."""

    def __init__(self, db_path: Path):
        """
        Initialize metadata index.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self):
        """Ensure database schema exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    job_id TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    compressed_size_bytes INTEGER NOT NULL,
                    compression_ratio REAL NOT NULL,
                    storage_path TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    retention_days INTEGER,
                    expires_at TEXT,
                    PRIMARY KEY (job_id, artifact_type)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON artifacts(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_type ON artifacts(artifact_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expires ON artifacts(expires_at)"
            )
            conn.commit()
        finally:
            conn.close()

    def add(self, metadata: ArtifactMetadata) -> None:
        """
        Add or update artifact metadata.

        Args:
            metadata: Artifact metadata to store
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO artifacts
                (job_id, artifact_type, timestamp, size_bytes, compressed_size_bytes,
                 compression_ratio, storage_path, checksum, tags, retention_days, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metadata.job_id,
                    metadata.artifact_type.value,
                    metadata.timestamp.isoformat(),
                    metadata.size_bytes,
                    metadata.compressed_size_bytes,
                    metadata.compression_ratio,
                    metadata.storage_path,
                    metadata.checksum,
                    json.dumps(metadata.tags),
                    metadata.retention_days,
                    metadata.expires_at.isoformat() if metadata.expires_at else None,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get(
        self, job_id: str, artifact_type: ArtifactType
    ) -> Optional[ArtifactMetadata]:
        """
        Get metadata for a specific artifact.

        Args:
            job_id: Job ID
            artifact_type: Artifact type

        Returns:
            Artifact metadata, or None if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                "SELECT * FROM artifacts WHERE job_id = ? AND artifact_type = ?",
                (job_id, artifact_type.value),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return self._row_to_metadata(row)
        finally:
            conn.close()

    def list(
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
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row

        try:
            query = "SELECT * FROM artifacts WHERE 1=1"
            params = []

            if artifact_type:
                query += " AND artifact_type = ?"
                params.append(artifact_type.value)

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())

            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            results = [self._row_to_metadata(row) for row in rows]

            # Filter by tags in memory (SQLite doesn't support JSON queries easily)
            if tags:
                results = [
                    r for r in results if all(r.tags.get(k) == v for k, v in tags.items())
                ]

            return results
        finally:
            conn.close()

    def delete(self, job_id: str, artifact_type: ArtifactType) -> bool:
        """
        Delete artifact metadata.

        Args:
            job_id: Job ID
            artifact_type: Artifact type

        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.execute(
                "DELETE FROM artifacts WHERE job_id = ? AND artifact_type = ?",
                (job_id, artifact_type.value),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def count(
        self,
        artifact_type: Optional[ArtifactType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Count artifacts matching filters.

        Args:
            artifact_type: Filter by artifact type
            start_date: Filter by creation date (inclusive)
            end_date: Filter by creation date (inclusive)

        Returns:
            Number of matching artifacts
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            query = "SELECT COUNT(*) FROM artifacts WHERE 1=1"
            params = []

            if artifact_type:
                query += " AND artifact_type = ?"
                params.append(artifact_type.value)

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())

            cursor = conn.execute(query, params)
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_stats(self) -> dict[str, Any]:
        """
        Get index statistics.

        Returns:
            Dictionary with statistics
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            # Total count and sizes
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_artifacts,
                    SUM(size_bytes) as total_size_bytes,
                    SUM(compressed_size_bytes) as total_compressed_size_bytes,
                    MIN(timestamp) as oldest_artifact,
                    MAX(timestamp) as newest_artifact
                FROM artifacts
                """
            )
            row = cursor.fetchone()

            # Breakdown by type
            cursor = conn.execute(
                """
                SELECT artifact_type, COUNT(*) as count
                FROM artifacts
                GROUP BY artifact_type
                """
            )
            by_type = {row["artifact_type"]: row["count"] for row in cursor.fetchall()}

            return {
                "total_artifacts": row["total_artifacts"] or 0,
                "total_size_bytes": row["total_size_bytes"] or 0,
                "total_compressed_size_bytes": row["total_compressed_size_bytes"] or 0,
                "artifacts_by_type": by_type,
                "oldest_artifact": row["oldest_artifact"],
                "newest_artifact": row["newest_artifact"],
            }
        finally:
            conn.close()

    def _row_to_metadata(self, row: sqlite3.Row) -> ArtifactMetadata:
        """Convert database row to ArtifactMetadata."""
        return ArtifactMetadata(
            job_id=row["job_id"],
            artifact_type=ArtifactType(row["artifact_type"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            size_bytes=row["size_bytes"],
            compressed_size_bytes=row["compressed_size_bytes"],
            compression_ratio=row["compression_ratio"],
            storage_path=row["storage_path"],
            checksum=row["checksum"],
            tags=json.loads(row["tags"]),
            retention_days=row["retention_days"],
            expires_at=(
                datetime.fromisoformat(row["expires_at"])
                if row["expires_at"]
                else None
            ),
        )
