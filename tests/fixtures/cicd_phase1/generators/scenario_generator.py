"""
Scenario Generator

Generates complete test scenarios combining multiple data types
for end-to-end integration testing.
"""

import random
from typing import Any, Dict, List

from ..factories.api_factory import APIRequestFactory, APIResponseFactory
from ..factories.artifact_factory import JSONArtifactFactory
from ..factories.auth_factory import JWTTokenFactory, OAuth2TokenFactory
from ..factories.rate_limit_factory import RateLimitFactory, BurstScenarioFactory


class ScenarioGenerator:
    """Generates complete test scenarios"""

    @staticmethod
    def generate_ci_pipeline_scenario() -> Dict[str, Any]:
        """Generate complete CI pipeline execution scenario"""
        # 1. Webhook triggers pipeline
        webhook = APIRequestFactory.create_webhook_payload(
            event_type="push",
            commit_count=random.randint(1, 5),
        )

        # 2. Pipeline authenticates
        auth_token = JWTTokenFactory.create_valid_token(
            user_id=webhook["pusher"]["email"],
            scopes=["ci:read", "ci:write", "artifacts:write"],
        )

        # 3. Tests run
        test_results = JSONArtifactFactory.create_test_results(
            total_tests=random.randint(50, 200),
            pass_rate=random.uniform(0.80, 0.95),
        )

        # 4. Coverage collected
        coverage_report = JSONArtifactFactory.create_coverage_report(
            line_coverage=random.uniform(0.75, 0.90),
            branch_coverage=random.uniform(0.65, 0.85),
        )

        # 5. Artifacts uploaded
        artifact_upload = APIRequestFactory.create_artifact_upload_request(
            artifact_type="test-results",
            size_mb=random.uniform(0.5, 5.0),
        )

        return {
            "scenario": "ci_pipeline_execution",
            "steps": [
                {"step": "webhook_received", "data": webhook},
                {"step": "authentication", "data": {"token": auth_token}},
                {"step": "test_execution", "data": test_results},
                {"step": "coverage_collection", "data": coverage_report},
                {"step": "artifact_upload", "data": artifact_upload},
            ],
            "expected_outcome": "success",
        }

    @staticmethod
    def generate_rate_limit_scenario() -> Dict[str, Any]:
        """Generate rate limiting scenario"""
        # Normal traffic
        normal_traffic = RateLimitFactory.create_normal_traffic(
            duration_seconds=30,
            requests_per_second=5,
        )

        # Burst traffic
        burst_traffic = RateLimitFactory.create_burst_traffic(
            burst_count=100,
            burst_duration_seconds=2.0,
        )

        # Recovery period
        recovery_traffic = RateLimitFactory.create_normal_traffic(
            duration_seconds=30,
            requests_per_second=3,
        )

        return {
            "scenario": "rate_limit_enforcement",
            "phases": [
                {"phase": "normal_traffic", "events": [e.__dict__ for e in normal_traffic]},
                {"phase": "burst_traffic", "events": [e.__dict__ for e in burst_traffic]},
                {"phase": "recovery", "events": [e.__dict__ for e in recovery_traffic]},
            ],
            "expected_rate_limits": {
                "normal_traffic": 0,  # No rate limits
                "burst_traffic": 80,  # Most requests rate limited
                "recovery": 0,  # Back to normal
            },
        }

    @staticmethod
    def generate_multi_user_scenario(user_count: int = 10) -> Dict[str, Any]:
        """Generate multi-user concurrent access scenario"""
        users = []
        for _ in range(user_count):
            user = {
                "user_id": JWTTokenFactory.create_valid_token(),
                "requests": APIRequestFactory.create_batch(
                    count=random.randint(5, 20),
                    request_type=random.choice(["webhook", "artifact", "test"]),
                ),
            }
            users.append(user)

        return {
            "scenario": "concurrent_multi_user_access",
            "users": users,
            "expected_behavior": "no_interference",
        }

    @staticmethod
    def generate_failure_recovery_scenario() -> Dict[str, Any]:
        """Generate failure and recovery scenario"""
        # Initial success
        initial_request = APIRequestFactory.create_test_execution_request(
            test_count=100,
        )
        initial_response = APIResponseFactory.create_success_response()

        # Failure occurs
        failure_request = APIRequestFactory.create_test_execution_request(
            test_count=100,
        )
        failure_response = APIResponseFactory.create_error_response(
            error_type="server_error",
            status_code=500,
        )

        # Retry with exponential backoff
        retry_requests = []
        for i in range(3):
            retry_requests.append({
                "attempt": i + 1,
                "backoff_seconds": 2 ** i,
                "request": APIRequestFactory.create_test_execution_request(),
            })

        # Eventually succeeds
        recovery_response = APIResponseFactory.create_success_response()

        return {
            "scenario": "failure_recovery_with_retries",
            "timeline": [
                {"event": "initial_request", "data": initial_request, "response": initial_response},
                {"event": "failure", "data": failure_request, "response": failure_response},
                {"event": "retries", "data": retry_requests},
                {"event": "recovery", "data": recovery_response},
            ],
            "expected_outcome": "eventual_success",
        }

    @staticmethod
    def generate_security_scenario() -> Dict[str, Any]:
        """Generate security testing scenario"""
        from ..factories.auth_factory import EdgeCaseTokenFactory

        # Valid authentication
        valid_token = JWTTokenFactory.create_valid_token()
        valid_request = APIRequestFactory.create_webhook_payload()

        # Attack attempts
        attacks = [
            {
                "attack_type": "sql_injection",
                "token": EdgeCaseTokenFactory.create_sql_injection_token(),
                "expected_response": 400,
            },
            {
                "attack_type": "xss",
                "token": EdgeCaseTokenFactory.create_xss_token(),
                "expected_response": 400,
            },
            {
                "attack_type": "path_traversal",
                "token": EdgeCaseTokenFactory.create_path_traversal_token(),
                "expected_response": 400,
            },
            {
                "attack_type": "expired_token",
                "token": JWTTokenFactory.create_expired_token(),
                "expected_response": 401,
            },
        ]

        return {
            "scenario": "security_attack_prevention",
            "valid_baseline": {
                "token": valid_token,
                "request": valid_request,
                "expected_response": 200,
            },
            "attacks": attacks,
            "expected_behavior": "all_attacks_blocked",
        }
