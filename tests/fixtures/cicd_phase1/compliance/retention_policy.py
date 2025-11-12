"""
Retention Policy Manager

Manages data retention policies for test data in compliance with regulations.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RetentionPolicy:
    """Data retention policy definition"""

    name: str
    retention_days: int
    data_category: str
    auto_delete: bool = True
    archive_before_delete: bool = False
    compliance_standard: str = "GDPR"


@dataclass
class DataRecord:
    """Individual data record with metadata"""

    record_id: str
    data: Any
    created_at: float = field(default_factory=time.time)
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    retention_policy: Optional[str] = None


class RetentionPolicyManager:
    """Manages data retention policies"""

    DEFAULT_POLICIES = {
        "test_results": RetentionPolicy(
            name="test_results",
            retention_days=30,
            data_category="test_data",
            compliance_standard="GDPR",
        ),
        "ci_artifacts": RetentionPolicy(
            name="ci_artifacts",
            retention_days=90,
            data_category="build_artifacts",
            archive_before_delete=True,
            compliance_standard="GDPR",
        ),
        "auth_tokens": RetentionPolicy(
            name="auth_tokens",
            retention_days=1,
            data_category="authentication",
            compliance_standard="GDPR",
        ),
        "pii_data": RetentionPolicy(
            name="pii_data",
            retention_days=0,  # Immediate deletion
            data_category="personally_identifiable",
            compliance_standard="GDPR",
        ),
    }

    def __init__(self, policies: Optional[Dict[str, RetentionPolicy]] = None):
        self.policies = policies or self.DEFAULT_POLICIES.copy()
        self.records: Dict[str, DataRecord] = {}

    def add_policy(self, policy: RetentionPolicy):
        """Add retention policy"""
        self.policies[policy.name] = policy

    def register_data(
        self,
        record_id: str,
        data: Any,
        category: str = "general",
        policy_name: Optional[str] = None,
    ):
        """Register data with retention tracking"""
        record = DataRecord(
            record_id=record_id,
            data=data,
            category=category,
            retention_policy=policy_name,
        )
        self.records[record_id] = record

    def get_expired_records(self) -> List[DataRecord]:
        """Get records past retention period"""
        expired = []
        current_time = time.time()

        for record in self.records.values():
            policy_name = record.retention_policy
            if not policy_name:
                # Find policy by category
                policy_name = self._find_policy_by_category(record.category)

            if policy_name and policy_name in self.policies:
                policy = self.policies[policy_name]
                retention_seconds = policy.retention_days * 86400
                expiry_time = record.created_at + retention_seconds

                if current_time > expiry_time:
                    expired.append(record)

        return expired

    def cleanup_expired_data(self, archive_path: Optional[Path] = None) -> Dict[str, Any]:
        """Clean up expired data according to policies"""
        expired = self.get_expired_records()
        archived_count = 0
        deleted_count = 0

        for record in expired:
            policy = self.policies.get(record.retention_policy)

            if policy and policy.archive_before_delete and archive_path:
                self._archive_record(record, archive_path)
                archived_count += 1

            del self.records[record.record_id]
            deleted_count += 1

        return {
            "expired_count": len(expired),
            "archived_count": archived_count,
            "deleted_count": deleted_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _archive_record(self, record: DataRecord, archive_path: Path):
        """Archive record before deletion"""
        archive_path.mkdir(parents=True, exist_ok=True)

        archive_file = archive_path / f"{record.record_id}.json"
        with open(archive_file, "w") as f:
            json.dump(
                {
                    "record_id": record.record_id,
                    "category": record.category,
                    "created_at": record.created_at,
                    "archived_at": time.time(),
                    "data": record.data,
                },
                f,
                indent=2,
                default=str,
            )

    def _find_policy_by_category(self, category: str) -> Optional[str]:
        """Find policy by data category"""
        for name, policy in self.policies.items():
            if policy.data_category == category:
                return name
        return None

    def generate_retention_report(self) -> Dict[str, Any]:
        """Generate retention policy compliance report"""
        current_time = time.time()
        policy_stats = {}

        for policy_name, policy in self.policies.items():
            records_for_policy = [
                r for r in self.records.values()
                if r.retention_policy == policy_name
            ]

            expired = sum(
                1 for r in records_for_policy
                if current_time > (r.created_at + policy.retention_days * 86400)
            )

            policy_stats[policy_name] = {
                "total_records": len(records_for_policy),
                "expired_records": expired,
                "retention_days": policy.retention_days,
                "compliance_standard": policy.compliance_standard,
            }

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_records": len(self.records),
            "policies": policy_stats,
            "total_expired": sum(s["expired_records"] for s in policy_stats.values()),
        }
