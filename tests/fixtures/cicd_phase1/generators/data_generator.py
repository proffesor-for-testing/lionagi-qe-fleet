"""
Test Data Generator

Main orchestrator for generating comprehensive test datasets
with versioning, tagging, and export capabilities.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..factories.api_factory import APIRequestFactory, EdgeCaseAPIFactory
from ..factories.artifact_factory import (
    JSONArtifactFactory,
    XMLArtifactFactory,
    BinaryArtifactFactory,
    EdgeCaseArtifactFactory,
)
from ..factories.auth_factory import (
    JWTTokenFactory,
    OAuth2TokenFactory,
    APIKeyFactory,
    EdgeCaseTokenFactory,
)
from ..factories.rate_limit_factory import (
    RateLimitFactory,
    BurstScenarioFactory,
    ThrottleScenarioFactory,
)


class TestDataGenerator:
    """Main test data generator orchestrator"""

    def __init__(self, version: str = "1.0.0"):
        self.version = version
        self.generated_datasets: List[Dict[str, Any]] = []

    def generate_complete_dataset(
        self,
        name: str,
        categories: Optional[List[str]] = None,
        include_edge_cases: bool = True,
    ) -> Dict[str, Any]:
        """Generate complete test dataset"""
        categories = categories or ["happy_path", "boundary", "invalid", "edge_cases"]

        dataset = {
            "name": name,
            "version": self.version,
            "generated_at": datetime.utcnow().isoformat(),
            "categories": {},
        }

        if "happy_path" in categories:
            dataset["categories"]["happy_path"] = self._generate_happy_path_data()

        if "boundary" in categories:
            dataset["categories"]["boundary"] = self._generate_boundary_data()

        if "invalid" in categories:
            dataset["categories"]["invalid"] = self._generate_invalid_data()

        if "edge_cases" in categories and include_edge_cases:
            dataset["categories"]["edge_cases"] = self._generate_edge_case_data()

        self.generated_datasets.append(dataset)
        return dataset

    def _generate_happy_path_data(self) -> Dict[str, Any]:
        """Generate happy path test data"""
        return {
            "api_requests": {
                "webhooks": APIRequestFactory.create_batch(10, "webhook"),
                "artifacts": APIRequestFactory.create_batch(5, "artifact"),
                "tests": APIRequestFactory.create_batch(5, "test"),
            },
            "artifacts": {
                "test_results": [
                    JSONArtifactFactory.create_test_results() for _ in range(3)
                ],
                "coverage_reports": [
                    JSONArtifactFactory.create_coverage_report() for _ in range(3)
                ],
                "build_manifests": [
                    JSONArtifactFactory.create_build_manifest() for _ in range(2)
                ],
            },
            "authentication": {
                "jwt_tokens": [
                    JWTTokenFactory.create_valid_token() for _ in range(5)
                ],
                "oauth2_tokens": [
                    OAuth2TokenFactory.create_access_token() for _ in range(5)
                ],
                "api_keys": [
                    APIKeyFactory.create_api_key() for _ in range(5)
                ],
            },
        }

    def _generate_boundary_data(self) -> Dict[str, Any]:
        """Generate boundary value test data"""
        return {
            "api_requests": [
                EdgeCaseAPIFactory.create_boundary_values(),
            ],
            "rate_limits": {
                "at_limit": RateLimitFactory.create_normal_traffic(
                    duration_seconds=60,
                    requests_per_second=10,  # Exactly at limit
                ),
                "just_under_limit": RateLimitFactory.create_normal_traffic(
                    duration_seconds=60,
                    requests_per_second=9,
                ),
                "just_over_limit": RateLimitFactory.create_normal_traffic(
                    duration_seconds=60,
                    requests_per_second=11,
                ),
            },
            "artifacts": {
                "minimum_size": JSONArtifactFactory.create_test_results(total_tests=1),
                "maximum_size": EdgeCaseArtifactFactory.create_oversized_artifact(10.0),
            },
        }

    def _generate_invalid_data(self) -> Dict[str, Any]:
        """Generate invalid test data"""
        return {
            "api_requests": {
                "empty": EdgeCaseAPIFactory.create_empty_payload(),
                "null_values": EdgeCaseAPIFactory.create_null_values_payload(),
                "malformed_json": EdgeCaseAPIFactory.create_malformed_json(),
                "special_chars": EdgeCaseAPIFactory.create_special_characters_payload(),
            },
            "authentication": {
                "expired": JWTTokenFactory.create_expired_token(),
                "invalid": JWTTokenFactory.create_invalid_token(),
                "malformed": JWTTokenFactory.create_malformed_token(),
                "empty": EdgeCaseTokenFactory.create_empty_token(),
            },
            "artifacts": {
                "corrupted_json": EdgeCaseArtifactFactory.create_corrupted_json(),
                "empty_json": EdgeCaseArtifactFactory.create_empty_json(),
            },
        }

    def _generate_edge_case_data(self) -> Dict[str, Any]:
        """Generate edge case test data"""
        return {
            "api_requests": {
                "oversized": EdgeCaseAPIFactory.create_oversized_payload(50.0),
                "special_characters": EdgeCaseAPIFactory.create_special_characters_payload(),
            },
            "artifacts": {
                "deeply_nested": EdgeCaseArtifactFactory.create_nested_artifact(100),
                "unicode": EdgeCaseArtifactFactory.create_unicode_artifact(),
            },
            "authentication": {
                "sql_injection": EdgeCaseTokenFactory.create_sql_injection_token(),
                "xss": EdgeCaseTokenFactory.create_xss_token(),
                "path_traversal": EdgeCaseTokenFactory.create_path_traversal_token(),
                "unicode": EdgeCaseTokenFactory.create_unicode_token(),
            },
            "rate_limits": {
                "burst": BurstScenarioFactory.create_webhook_flood(1000),
                "spike": RateLimitFactory.create_spike_pattern(
                    duration_seconds=120,
                    spike_count=5,
                ),
            },
        }

    def export_dataset(
        self,
        dataset: Dict[str, Any],
        output_path: Path,
        format: str = "json",
    ):
        """Export dataset to file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(output_path, "w") as f:
                json.dump(dataset, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def generate_version_metadata(self) -> Dict[str, Any]:
        """Generate version metadata for dataset"""
        return {
            "version": self.version,
            "generated_at": datetime.utcnow().isoformat(),
            "datasets_count": len(self.generated_datasets),
            "dataset_names": [d["name"] for d in self.generated_datasets],
        }
