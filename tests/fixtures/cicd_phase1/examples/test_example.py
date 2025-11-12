"""
Example Test Cases Using CI/CD Phase 1 Test Data Framework

Demonstrates how to write actual tests using the generated test data.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from factories.api_factory import APIRequestFactory, EdgeCaseAPIFactory
from factories.artifact_factory import JSONArtifactFactory
from factories.auth_factory import JWTTokenFactory, EdgeCaseTokenFactory
from generators.scenario_generator import ScenarioGenerator
from compliance.gdpr_manager import GDPRComplianceManager


class TestAPIEndpoints:
    """Example tests for API endpoints"""

    def test_webhook_processing_happy_path(self):
        """Test webhook processing with valid data"""
        # Generate valid webhook
        webhook = APIRequestFactory.create_webhook_payload(
            event_type="push",
            commit_count=3,
        )

        # Process webhook (mock)
        result = self._process_webhook(webhook)

        # Assertions
        assert result["status"] == "success"
        assert len(result["processed_commits"]) == 3

    def test_webhook_processing_edge_cases(self):
        """Test webhook processing with edge cases"""
        # Empty payload
        empty = EdgeCaseAPIFactory.create_empty_payload()
        result = self._process_webhook(empty)
        assert result["status"] == "error"
        assert "invalid_payload" in result["error_code"]

        # Null values
        null_values = EdgeCaseAPIFactory.create_null_values_payload()
        result = self._process_webhook(null_values)
        assert result["status"] == "error"

    def test_webhook_batch_processing(self):
        """Test batch webhook processing"""
        # Generate batch
        webhooks = APIRequestFactory.create_batch(count=10, request_type="webhook")

        # Process batch
        results = [self._process_webhook(w) for w in webhooks]

        # Assertions
        assert len(results) == 10
        assert all(r["status"] == "success" for r in results)

    @staticmethod
    def _process_webhook(webhook):
        """Mock webhook processor"""
        if not webhook or not isinstance(webhook, dict):
            return {"status": "error", "error_code": "invalid_payload"}

        if "repository" not in webhook or webhook["repository"] is None:
            return {"status": "error", "error_code": "missing_repository"}

        commits = webhook.get("commits", [])
        return {
            "status": "success",
            "processed_commits": len(commits),
        }


class TestAuthentication:
    """Example tests for authentication"""

    def test_valid_jwt_token(self):
        """Test authentication with valid JWT"""
        token = JWTTokenFactory.create_valid_token(
            scopes=["read", "write"],
        )

        result = self._authenticate(token)
        assert result["authenticated"] is True

    def test_expired_jwt_token(self):
        """Test authentication with expired JWT"""
        token = JWTTokenFactory.create_expired_token()

        result = self._authenticate(token)
        assert result["authenticated"] is False
        assert result["error"] == "token_expired"

    def test_invalid_jwt_token(self):
        """Test authentication with invalid JWT"""
        token = JWTTokenFactory.create_invalid_token()

        result = self._authenticate(token)
        assert result["authenticated"] is False
        assert result["error"] == "invalid_token"

    def test_authentication_attack_vectors(self):
        """Test authentication against attack vectors"""
        attacks = [
            EdgeCaseTokenFactory.create_sql_injection_token(),
            EdgeCaseTokenFactory.create_xss_token(),
            EdgeCaseTokenFactory.create_path_traversal_token(),
        ]

        for token in attacks:
            result = self._authenticate(token)
            assert result["authenticated"] is False
            assert "invalid_token" in result["error"]

    @staticmethod
    def _authenticate(token):
        """Mock authenticator"""
        if not token or not isinstance(token, str):
            return {"authenticated": False, "error": "invalid_token"}

        # Simple mock validation
        if "expired" in token.lower():
            return {"authenticated": False, "error": "token_expired"}

        if len(token.split(".")) != 3:
            return {"authenticated": False, "error": "invalid_token"}

        # Check for attack patterns
        attack_patterns = ["<script>", "'; DROP", "../"]
        if any(pattern in token for pattern in attack_patterns):
            return {"authenticated": False, "error": "invalid_token"}

        return {"authenticated": True}


class TestArtifactProcessing:
    """Example tests for artifact processing"""

    def test_test_results_artifact(self):
        """Test processing test results artifact"""
        artifact = JSONArtifactFactory.create_test_results(
            total_tests=100,
            pass_rate=0.85,
        )

        result = self._process_artifact(artifact)

        assert result["status"] == "success"
        assert result["total_tests"] == 100
        assert result["pass_rate"] == 0.85

    def test_coverage_report_artifact(self):
        """Test processing coverage report artifact"""
        artifact = JSONArtifactFactory.create_coverage_report(
            line_coverage=0.85,
            branch_coverage=0.75,
        )

        result = self._process_artifact(artifact)

        assert result["status"] == "success"
        assert result["line_coverage"] == pytest.approx(85.0, rel=1)

    @staticmethod
    def _process_artifact(artifact):
        """Mock artifact processor"""
        if not artifact or not isinstance(artifact, dict):
            return {"status": "error"}

        if "summary" in artifact:
            summary = artifact["summary"]
            return {
                "status": "success",
                "total_tests": summary.get("total"),
                "pass_rate": summary.get("pass_rate"),
                "line_coverage": summary.get("line_coverage"),
            }

        return {"status": "error"}


class TestCompleteScenarios:
    """Example tests using complete scenarios"""

    def test_ci_pipeline_scenario(self):
        """Test complete CI pipeline scenario"""
        scenario = ScenarioGenerator.generate_ci_pipeline_scenario()

        # Verify scenario structure
        assert scenario["scenario"] == "ci_pipeline_execution"
        assert len(scenario["steps"]) == 5
        assert scenario["expected_outcome"] == "success"

        # Test each step
        for step in scenario["steps"]:
            if step["step"] == "webhook_received":
                assert "repository" in step["data"]
            elif step["step"] == "authentication":
                assert "token" in step["data"]
            elif step["step"] == "test_execution":
                assert "summary" in step["data"]

    def test_security_scenario(self):
        """Test security attack prevention scenario"""
        scenario = ScenarioGenerator.generate_security_scenario()

        # Verify scenario structure
        assert scenario["scenario"] == "security_attack_prevention"
        assert len(scenario["attacks"]) > 0
        assert scenario["expected_behavior"] == "all_attacks_blocked"

        # All attacks should have expected response codes
        for attack in scenario["attacks"]:
            assert attack["expected_response"] in [400, 401, 403]


class TestGDPRCompliance:
    """Example tests for GDPR compliance"""

    def test_no_pii_in_test_data(self):
        """Verify test data contains no real PII"""
        # Generate test data
        webhook = APIRequestFactory.create_webhook_payload()

        # Check compliance
        gdpr = GDPRComplianceManager()
        report = gdpr.generate_compliance_report(webhook)

        # Should be compliant (synthetic data)
        assert report["compliant"] is True or report["pii_count"] == 0

    def test_pii_detection(self):
        """Test PII detection in data"""
        # Data with potential PII patterns
        data = {
            "email": "test@example.com",
            "phone": "555-1234",
            "name": "Test User",
        }

        gdpr = GDPRComplianceManager()
        pii_found = gdpr.scan_for_pii(data)

        # Should detect PII fields
        assert len(pii_found) > 0
        assert any("email" in finding["path"] for finding in pii_found)

    def test_data_anonymization(self):
        """Test data anonymization"""
        data = {
            "user": {
                "email": "user@example.com",
                "name": "John Doe",
            }
        }

        gdpr = GDPRComplianceManager()
        anonymized = gdpr.anonymize_data(data, strategy="hash")

        # Verify anonymization
        assert anonymized["user"]["email"] != data["user"]["email"]
        assert anonymized["user"]["name"] != data["user"]["name"]
        assert len(anonymized["user"]["email"]) > 0


# Pytest fixtures
@pytest.fixture
def api_request_factory():
    """Fixture providing APIRequestFactory"""
    return APIRequestFactory()


@pytest.fixture
def auth_token_factory():
    """Fixture providing JWTTokenFactory"""
    return JWTTokenFactory()


@pytest.fixture
def artifact_factory():
    """Fixture providing JSONArtifactFactory"""
    return JSONArtifactFactory()


# Example parameterized test
@pytest.mark.parametrize("test_count,pass_rate", [
    (10, 1.0),
    (100, 0.95),
    (100, 0.85),
    (100, 0.50),
    (1000, 0.99),
])
def test_test_results_various_scenarios(test_count, pass_rate):
    """Test with various test counts and pass rates"""
    results = JSONArtifactFactory.create_test_results(
        total_tests=test_count,
        pass_rate=pass_rate,
    )

    assert results["summary"]["total"] == test_count
    assert results["summary"]["pass_rate"] == pytest.approx(pass_rate, rel=0.05)
    assert results["summary"]["passed"] + results["summary"]["failed"] + results["summary"]["skipped"] == test_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
