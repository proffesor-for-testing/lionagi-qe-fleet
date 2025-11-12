"""
Example Usage of CI/CD Phase 1 Test Data Framework

This file demonstrates how to use the test data management framework
in various scenarios.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from factories.api_factory import APIRequestFactory, APIResponseFactory, EdgeCaseAPIFactory
from factories.artifact_factory import JSONArtifactFactory, XMLArtifactFactory, BinaryArtifactFactory
from factories.auth_factory import JWTTokenFactory, OAuth2TokenFactory, APIKeyFactory
from factories.rate_limit_factory import RateLimitFactory, BurstScenarioFactory
from generators.scenario_generator import ScenarioGenerator
from generators.data_generator import TestDataGenerator
from generators.edge_case_generator import EdgeCaseGenerator
from compliance.gdpr_manager import GDPRComplianceManager
from compliance.data_anonymizer import DataAnonymizer
from compliance.retention_policy import RetentionPolicyManager


def example_1_basic_factories():
    """Example 1: Basic factory usage"""
    print("=" * 80)
    print("Example 1: Basic Factory Usage")
    print("=" * 80)

    # Generate webhook payload
    webhook = APIRequestFactory.create_webhook_payload(
        event_type="push",
        repository="my-project",
        branch="main",
        commit_count=3,
    )
    print(f"\n1. Webhook Payload:")
    print(f"   Repository: {webhook['repository']['name']}")
    print(f"   Branch: {webhook['ref']}")
    print(f"   Commits: {len(webhook['commits'])}")

    # Generate test results
    test_results = JSONArtifactFactory.create_test_results(
        total_tests=100,
        pass_rate=0.85,
    )
    print(f"\n2. Test Results:")
    print(f"   Total: {test_results['summary']['total']}")
    print(f"   Passed: {test_results['summary']['passed']}")
    print(f"   Failed: {test_results['summary']['failed']}")
    print(f"   Pass Rate: {test_results['summary']['pass_rate']:.2%}")

    # Generate JWT token
    token = JWTTokenFactory.create_valid_token(
        expiry_hours=24,
        scopes=["ci:read", "ci:write"],
    )
    print(f"\n3. JWT Token:")
    print(f"   Token: {token[:50]}...")


def example_2_batch_generation():
    """Example 2: Batch data generation"""
    print("\n" + "=" * 80)
    print("Example 2: Batch Data Generation")
    print("=" * 80)

    # Generate batch of webhooks
    webhooks = APIRequestFactory.create_batch(count=10, request_type="webhook")
    print(f"\n1. Generated {len(webhooks)} webhook payloads")

    # Generate multiple test results
    test_results_batch = [
        JSONArtifactFactory.create_test_results() for _ in range(5)
    ]
    print(f"\n2. Generated {len(test_results_batch)} test result artifacts")

    # Generate rate limit scenarios
    burst = RateLimitFactory.create_burst_traffic(burst_count=100)
    print(f"\n3. Generated burst traffic scenario with {len(burst)} events")


def example_3_edge_cases():
    """Example 3: Edge case generation"""
    print("\n" + "=" * 80)
    print("Example 3: Edge Case Generation")
    print("=" * 80)

    # String edge cases
    strings = EdgeCaseGenerator.generate_string_edge_cases()
    print(f"\n1. String Edge Cases: {len(strings)} cases")
    print(f"   Examples: Empty='', Single='a', Unicode='日本語', XSS='<script>...'")

    # Numeric edge cases
    numbers = EdgeCaseGenerator.generate_numeric_edge_cases()
    print(f"\n2. Numeric Edge Cases: {len(numbers)} cases")
    print(f"   Examples: Zero, Min/Max int, Infinity, NaN")

    # Comprehensive edge cases
    all_edge_cases = EdgeCaseGenerator.generate_comprehensive_edge_cases()
    print(f"\n3. Comprehensive Edge Cases:")
    for category, cases in all_edge_cases.items():
        print(f"   {category}: {len(cases)} cases")


def example_4_complete_scenarios():
    """Example 4: Complete scenario generation"""
    print("\n" + "=" * 80)
    print("Example 4: Complete Scenario Generation")
    print("=" * 80)

    # CI pipeline scenario
    ci_scenario = ScenarioGenerator.generate_ci_pipeline_scenario()
    print(f"\n1. CI Pipeline Scenario:")
    print(f"   Steps: {len(ci_scenario['steps'])}")
    for i, step in enumerate(ci_scenario["steps"], 1):
        print(f"   {i}. {step['step']}")

    # Rate limit scenario
    rate_scenario = ScenarioGenerator.generate_rate_limit_scenario()
    print(f"\n2. Rate Limit Scenario:")
    print(f"   Phases: {len(rate_scenario['phases'])}")
    for phase in rate_scenario["phases"]:
        print(f"   - {phase['phase']}: {len(phase['events'])} events")

    # Security scenario
    security_scenario = ScenarioGenerator.generate_security_scenario()
    print(f"\n3. Security Scenario:")
    print(f"   Attacks to test: {len(security_scenario['attacks'])}")
    for attack in security_scenario["attacks"]:
        print(f"   - {attack['attack_type']}")


def example_5_gdpr_compliance():
    """Example 5: GDPR compliance checking"""
    print("\n" + "=" * 80)
    print("Example 5: GDPR Compliance")
    print("=" * 80)

    # Create test data with PII
    test_data = {
        "user": {
            "email": "user@example.com",
            "name": "John Doe",
            "phone": "555-1234",
        },
        "metadata": {
            "timestamp": "2025-01-01T00:00:00Z",
        },
    }

    # Initialize GDPR manager
    gdpr = GDPRComplianceManager()

    # Scan for PII
    pii_found = gdpr.scan_for_pii(test_data)
    print(f"\n1. PII Scan Results:")
    print(f"   Found {len(pii_found)} PII fields:")
    for finding in pii_found:
        print(f"   - {finding['path']}: {finding['reason']}")

    # Anonymize data
    anonymized = gdpr.anonymize_data(test_data, strategy="hash")
    print(f"\n2. Anonymized Data:")
    print(f"   Original email: {test_data['user']['email']}")
    print(f"   Anonymized: {anonymized['user']['email']}")

    # Generate compliance report
    report = gdpr.generate_compliance_report(test_data)
    print(f"\n3. Compliance Report:")
    print(f"   Compliant: {report['compliant']}")
    print(f"   PII Count: {report['pii_count']}")
    print(f"   Recommendations: {len(report['recommendations'])}")


def example_6_data_anonymization():
    """Example 6: Data anonymization techniques"""
    print("\n" + "=" * 80)
    print("Example 6: Data Anonymization Techniques")
    print("=" * 80)

    anonymizer = DataAnonymizer(seed=42)  # Deterministic for demo

    value = "sensitive_data_12345"

    # Different anonymization strategies
    print(f"\n1. Original Value: {value}")
    print(f"\n2. Anonymization Strategies:")
    print(f"   Pseudonymize: {anonymizer.pseudonymize(value)}")
    print(f"   Anonymize: {anonymizer.anonymize(value)}")
    print(f"   Mask: {anonymizer.data_masking(value, show_chars=3)}")

    # Generalization
    print(f"\n3. Generalization:")
    print(f"   Number 12345 → {anonymizer.generalize_number(12345, precision=100)}")
    print(f"   Date 2025-01-15 → {anonymizer.generalize_date('2025-01-15')}")


def example_7_retention_policies():
    """Example 7: Data retention management"""
    print("\n" + "=" * 80)
    print("Example 7: Data Retention Management")
    print("=" * 80)

    # Initialize retention manager
    retention = RetentionPolicyManager()

    # Register test data
    retention.register_data(
        record_id="test_001",
        data={"test": "data"},
        category="test_data",
        policy_name="test_results",
    )

    retention.register_data(
        record_id="artifact_001",
        data={"artifact": "data"},
        category="build_artifacts",
        policy_name="ci_artifacts",
    )

    # Generate report
    report = retention.generate_retention_report()
    print(f"\n1. Retention Report:")
    print(f"   Total Records: {report['total_records']}")
    print(f"\n2. Policy Statistics:")
    for policy_name, stats in report["policies"].items():
        print(f"   {policy_name}:")
        print(f"      Total: {stats['total_records']}")
        print(f"      Expired: {stats['expired_records']}")
        print(f"      Retention: {stats['retention_days']} days")


def example_8_complete_dataset():
    """Example 8: Generate complete dataset"""
    print("\n" + "=" * 80)
    print("Example 8: Complete Dataset Generation")
    print("=" * 80)

    # Initialize generator
    generator = TestDataGenerator(version="1.0.0")

    # Generate complete dataset
    dataset = generator.generate_complete_dataset(
        name="example_dataset",
        categories=["happy_path", "boundary", "invalid", "edge_cases"],
    )

    print(f"\n1. Dataset Generated:")
    print(f"   Name: {dataset['name']}")
    print(f"   Version: {dataset['version']}")
    print(f"   Generated: {dataset['generated_at']}")
    print(f"\n2. Categories:")
    for category, data in dataset["categories"].items():
        print(f"   {category}:")
        for subcategory, subdata in data.items():
            if isinstance(subdata, list):
                print(f"      {subcategory}: {len(subdata)} items")
            elif isinstance(subdata, dict):
                print(f"      {subcategory}: {len(subdata)} keys")

    # Export dataset
    output_path = Path(__file__).parent / "example_dataset.json"
    generator.export_dataset(dataset, output_path)
    print(f"\n3. Exported to: {output_path}")


def main():
    """Run all examples"""
    print("\n")
    print("*" * 80)
    print("CI/CD Phase 1 Test Data Framework - Usage Examples")
    print("*" * 80)

    example_1_basic_factories()
    example_2_batch_generation()
    example_3_edge_cases()
    example_4_complete_scenarios()
    example_5_gdpr_compliance()
    example_6_data_anonymization()
    example_7_retention_policies()
    example_8_complete_dataset()

    print("\n" + "*" * 80)
    print("All examples completed successfully!")
    print("*" * 80 + "\n")


if __name__ == "__main__":
    main()
