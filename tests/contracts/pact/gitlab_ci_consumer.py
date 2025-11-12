"""
GitLab CI Consumer Contract Tests

Consumer-driven contract tests for GitLab CI pipelines integrating
with the LionAGI QE Fleet MCP API.
"""

import pytest
from pact import Consumer, Provider, Like, EachLike, Term
import os


PACT_BROKER_URL = os.getenv("PACT_BROKER_URL", "http://localhost:9292")
PACT_BROKER_TOKEN = os.getenv("PACT_BROKER_TOKEN", "")

pact = Consumer("gitlab-ci-pipeline").has_pact_with(
    Provider("lionagi-qe-mcp-api"),
    pact_dir="./pacts",
    publish_to_broker=True if PACT_BROKER_URL else False,
    broker_base_url=PACT_BROKER_URL,
    broker_token=PACT_BROKER_TOKEN,
    version="1.0.0"
)


class TestGitLabCIContracts:
    """Contract tests for GitLab CI/CD pipelines"""

    def setup_method(self):
        pact.start_service()

    def teardown_method(self):
        pact.stop_service()

    @pytest.fixture
    def mock_api_client(self):
        class MockAPIClient:
            def __init__(self, base_url):
                self.base_url = base_url

            async def security_scan(self, path, scan_type="comprehensive"):
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/tools/security_scan",
                        json={"path": path, "scan_type": scan_type}
                    ) as resp:
                        return await resp.json()

            async def deployment_readiness(self, version, environment="production"):
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/tools/deployment_readiness",
                        json={"version": version, "environment": environment}
                    ) as resp:
                        return await resp.json()

            async def performance_test(self, endpoint, duration=60, users=10):
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/tools/performance_test",
                        json={
                            "endpoint": endpoint,
                            "duration": duration,
                            "users": users,
                            "tool": "k6"
                        }
                    ) as resp:
                        return await resp.json()

        return MockAPIClient(pact.uri)

    @pytest.mark.asyncio
    async def test_contract_security_scan(self, mock_api_client):
        """
        Contract: GitLab CI runs security scan

        Scenario: Pipeline executes SAST/DAST security scanning
        Expected: API returns vulnerability report with severity counts
        """
        expected_response = {
            "vulnerabilities": EachLike({
                "id": Like("CVE-2024-1234"),
                "title": Like("SQL Injection vulnerability"),
                "severity": Term(r"(low|medium|high|critical)", "high"),
                "description": Like("Unsanitized SQL query"),
                "file": Like("src/database.py"),
                "line": Like(42)
            }),
            "severity_counts": {
                "low": Like(3),
                "medium": Like(5),
                "high": Like(2),
                "critical": Like(0)
            },
            "risk_score": Like(65.5),
            "recommendations": EachLike("Use parameterized queries"),
            "compliance_status": {
                "OWASP_Top_10": Like(True),
                "CWE": Like(True)
            }
        }

        (pact
         .given("security scanner agent is available")
         .upon_receiving("a request to perform security scan")
         .with_request(
             method="POST",
             path="/tools/security_scan",
             headers={"Content-Type": "application/json"},
             body={
                 "path": Like("./src"),
                 "scan_type": "comprehensive",
                 "severity_threshold": "medium"
             }
         )
         .will_respond_with(200, body=expected_response))

        with pact:
            result = await mock_api_client.security_scan(
                path="./src",
                scan_type="comprehensive"
            )

            assert "vulnerabilities" in result
            assert "severity_counts" in result
            assert "risk_score" in result
            assert "compliance_status" in result

    @pytest.mark.asyncio
    async def test_contract_deployment_readiness(self, mock_api_client):
        """
        Contract: GitLab CI checks deployment readiness

        Scenario: Pipeline validates if version is ready for production
        Expected: API returns readiness status with risk assessment
        """
        expected_response = {
            "ready": Like(True),
            "risk_level": Term(r"(low|medium|high|critical)", "low"),
            "factors": {
                "test_coverage": Like({"score": 87.5, "passed": True}),
                "security_scan": Like({"score": 95.0, "passed": True}),
                "performance": Like({"score": 92.0, "passed": True}),
                "code_quality": Like({"score": 88.5, "passed": True})
            },
            "blockers": [],
            "recommendations": EachLike("Monitor performance metrics post-deployment")
        }

        (pact
         .given("deployment readiness agent is available")
         .upon_receiving("a request to assess deployment readiness")
         .with_request(
             method="POST",
             path="/tools/deployment_readiness",
             headers={"Content-Type": "application/json"},
             body={
                 "version": Like("v1.4.3"),
                 "environment": "production"
             }
         )
         .will_respond_with(200, body=expected_response))

        with pact:
            result = await mock_api_client.deployment_readiness(
                version="v1.4.3",
                environment="production"
            )

            assert "ready" in result
            assert "risk_level" in result
            assert "factors" in result
            assert "blockers" in result

    @pytest.mark.asyncio
    async def test_contract_performance_test(self, mock_api_client):
        """
        Contract: GitLab CI runs performance tests

        Scenario: Pipeline executes load testing
        Expected: API returns performance metrics with percentiles
        """
        expected_response = {
            "requests_per_second": Like(1250.5),
            "response_time_p50": Like(45.2),
            "response_time_p95": Like(120.5),
            "response_time_p99": Like(250.8),
            "error_rate": Like(0.5),
            "total_requests": Like(75030)
        }

        (pact
         .given("performance tester agent is available")
         .upon_receiving("a request to run performance tests")
         .with_request(
             method="POST",
             path="/tools/performance_test",
             headers={"Content-Type": "application/json"},
             body={
                 "endpoint": Like("https://api.example.com/users"),
                 "duration": 60,
                 "users": 10,
                 "ramp_up": 5,
                 "tool": "k6"
             }
         )
         .will_respond_with(200, body=expected_response))

        with pact:
            result = await mock_api_client.performance_test(
                endpoint="https://api.example.com/users",
                duration=60,
                users=10
            )

            assert "requests_per_second" in result
            assert "response_time_p95" in result
            assert "error_rate" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--pact-publish-version=1.0.0"])
