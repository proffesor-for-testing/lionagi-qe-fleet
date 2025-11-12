#!/usr/bin/env python3
"""
Seed Data Generation Script

Generates complete seed datasets for CI/CD testing.
Run this script to populate the seeds/ directory with test data.

Usage:
    python -m tests.fixtures.cicd_phase1.generate_seeds
    python -m tests.fixtures.cicd_phase1.generate_seeds --version 1.0.0
    python -m tests.fixtures.cicd_phase1.generate_seeds --categories happy_path,edge_cases
"""

import argparse
import json
from pathlib import Path

from generators.data_generator import TestDataGenerator
from compliance.gdpr_manager import GDPRComplianceManager


def main():
    parser = argparse.ArgumentParser(description="Generate CI/CD Phase 1 seed data")
    parser.add_argument(
        "--version",
        default="1.0.0",
        help="Version tag for generated data",
    )
    parser.add_argument(
        "--categories",
        default="happy_path,boundary,invalid,edge_cases",
        help="Comma-separated list of categories to generate",
    )
    parser.add_argument(
        "--output-dir",
        default="seeds",
        help="Output directory for seed data",
    )
    parser.add_argument(
        "--validate-gdpr",
        action="store_true",
        help="Validate GDPR compliance",
    )

    args = parser.parse_args()

    # Setup paths
    base_dir = Path(__file__).parent
    output_dir = base_dir / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize generator
    generator = TestDataGenerator(version=args.version)
    categories = [c.strip() for c in args.categories.split(",")]

    print(f"Generating test data for Phase 1...")
    print(f"Version: {args.version}")
    print(f"Categories: {', '.join(categories)}")

    # Generate complete dataset
    dataset = generator.generate_complete_dataset(
        name=f"phase1_v{args.version}",
        categories=categories,
        include_edge_cases="edge_cases" in categories,
    )

    # Export main dataset
    output_file = output_dir / f"phase1_v{args.version}.json"
    generator.export_dataset(dataset, output_file)
    print(f"✅ Generated: {output_file}")

    # Export by category
    for category, data in dataset["categories"].items():
        category_dir = output_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        # Export each subcategory
        for subcategory, subdata in data.items():
            subcategory_file = category_dir / f"{subcategory}.json"
            with open(subcategory_file, "w") as f:
                json.dump(subdata, f, indent=2, default=str)
            print(f"✅ Generated: {subcategory_file}")

    # GDPR validation
    if args.validate_gdpr:
        print("\n🔒 Validating GDPR compliance...")
        gdpr = GDPRComplianceManager()
        report = gdpr.generate_compliance_report(dataset)

        if report["compliant"]:
            print("✅ GDPR Compliant: No PII detected")
        else:
            print(f"⚠️  WARNING: {report['pii_count']} PII findings detected")
            for finding in report["pii_findings"]:
                print(f"   - {finding['path']}: {finding['reason']}")

    # Generate metadata
    metadata = generator.generate_version_metadata()
    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"\n✅ Metadata: {metadata_file}")

    print(f"\n🎉 Seed data generation complete!")
    print(f"📁 Output directory: {output_dir}")


if __name__ == "__main__":
    main()
