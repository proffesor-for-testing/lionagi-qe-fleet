#!/usr/bin/env python3
"""
Seed Data Cleanup Script

Cleans up generated seed data according to retention policies.
Run this script after tests to remove expired test data.

Usage:
    python -m tests.fixtures.cicd_phase1.cleanup_seeds
    python -m tests.fixtures.cicd_phase1.cleanup_seeds --archive
    python -m tests.fixtures.cicd_phase1.cleanup_seeds --force
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

from compliance.retention_policy import RetentionPolicyManager


def main():
    parser = argparse.ArgumentParser(description="Cleanup CI/CD Phase 1 seed data")
    parser.add_argument(
        "--seeds-dir",
        default="seeds",
        help="Seed data directory",
    )
    parser.add_argument(
        "--archive",
        action="store_true",
        help="Archive data before deletion",
    )
    parser.add_argument(
        "--archive-dir",
        default="archives",
        help="Archive directory",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force cleanup without confirmation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting",
    )

    args = parser.parse_args()

    # Setup paths
    base_dir = Path(__file__).parent
    seeds_dir = base_dir / args.seeds_dir
    archive_dir = base_dir / args.archive_dir if args.archive else None

    if not seeds_dir.exists():
        print(f"No seed data found at {seeds_dir}")
        return

    # Initialize retention manager
    retention = RetentionPolicyManager()

    # Register all seed files
    print("📊 Scanning seed data...")
    seed_files = list(seeds_dir.rglob("*.json"))
    for seed_file in seed_files:
        # Determine category from path
        category = seed_file.parent.name if seed_file.parent != seeds_dir else "general"

        # Register with retention policy
        retention.register_data(
            record_id=str(seed_file.relative_to(seeds_dir)),
            data=seed_file,
            category=category,
        )

    # Get expired records
    expired = retention.get_expired_records()
    print(f"Found {len(expired)} expired seed files")

    if not expired:
        print("✅ No cleanup needed")
        return

    # Show what will be deleted
    print("\n📋 Files to be deleted:")
    for record in expired:
        print(f"   - {record.record_id}")

    if args.dry_run:
        print("\n🔍 Dry run - no files deleted")
        return

    # Confirm deletion
    if not args.force:
        response = input("\n❓ Proceed with cleanup? [y/N]: ")
        if response.lower() != "y":
            print("❌ Cleanup cancelled")
            return

    # Cleanup
    print("\n🧹 Cleaning up...")
    cleanup_report = retention.cleanup_expired_data(
        archive_path=archive_dir if args.archive else None
    )

    # Delete actual files
    deleted_count = 0
    for record in expired:
        file_path = seeds_dir / record.record_id
        if file_path.exists():
            file_path.unlink()
            deleted_count += 1

    print(f"\n✅ Cleanup complete!")
    print(f"   Expired: {cleanup_report['expired_count']}")
    if args.archive:
        print(f"   Archived: {cleanup_report['archived_count']} to {archive_dir}")
    print(f"   Deleted: {deleted_count}")

    # Generate cleanup report
    report_file = base_dir / "cleanup_report.json"
    with open(report_file, "w") as f:
        json.dump(
            {
                **cleanup_report,
                "deleted_files": deleted_count,
                "archived": args.archive,
            },
            f,
            indent=2,
        )
    print(f"\n📄 Report: {report_file}")


if __name__ == "__main__":
    main()
