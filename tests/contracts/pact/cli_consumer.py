"""
CLI Consumer Contract Tests

Consumer-driven contract tests for the AQE CLI tool integrating
with the LionAGI QE Fleet MCP API.
"""

import pytest
from pact import Consumer, Provider, Like, EachLike, Term
import os


PACT_BROKER_URL = os.getenv("PACT_BROKER_URL", "http://localhost:9292")
PACT_BROKER_TOKEN = os.getenv("PACT_BROKER_TOKEN", "")

pact = Consumer("aqe-cli-tool").has_pact_with(
    Provider("lionagi-qe-mcp-api"),
    pact_dir="./pacts",
    publish_to_broker=True if PACT_BROKER_URL else False,
    broker_base_url=PACT_BROKER_URL,
    broker_token=PACT_BROKER_TOKEN,
    version="1.0.0"
)


class TestCLIConsumerContracts:
    """Contract tests for AQE CLI tool"""

    def setup_method(self):
        pact.start_service()

    def teardown_method(self):
        pact.stop_service()

    @pytest.fixture
    def mock_api_client(self):
        class MockAPIClient:
            def __init__(self, base_url):
                self.base_url = base_url

            async def get_fleet_status(self):
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.base_url}/tools/fleet_status"
                    ) as resp:
                        return await resp.json()

            async def flaky_test_hunt(self, test_path, iterations=10):
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/tools/flaky_test_hunt",
                        json={"test_path": test_path, "iterations": iterations}
                    ) as resp:
                        return await resp.json()

            async def regression_risk_analyze(self, changes, test_suite):
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/tools/regression_risk_analyze",
                        json={"changes": changes, "test_suite": test_suite}
                    ) as resp:
                        return await resp.json()

        return MockAPIClient(pact.uri)

    @pytest.mark.asyncio
    async def test_contract_fleet_status(self, mock_api_client):
        """
        Contract: CLI retrieves fleet status

        Scenario: User runs `aqe status` command
        Expected: API returns comprehensive fleet information
        """
        expected_response = {
            "initialized": True,
            "agents": EachLike({
                "agent_id": Like("test-generator"),
                "type": Like("TestGeneratorAgent"),
                "status": Term(r"(idle|busy|error)", "idle"),
                "tasks_completed": Like(42)
            }),
            "memory_stats": {
                "total_keys": Like(128),
                "size_mb": Like(45.2)
            },
            "routing_stats": {
                "enabled": Like(True),
                "total_calls": Like(1024),
                "cost_saved": Like(125.50)
            },
            "performance_metrics": {
                "avg_response_time_ms": Like(250.5),
                "success_rate": Like(98.5)
            }
        }

        (pact
         .given("fleet is initialized")
         .upon_receiving("a request to get fleet status")
         .with_request(
             method="GET",
             path="/tools/fleet_status"
         )
         .will_respond_with(200, body=expected_response))

        with pact:
            result = await mock_api_client.get_fleet_status()

            assert result["initialized"] is True
            assert "agents" in result
            assert "memory_stats" in result
            assert "performance_metrics" in result

    @pytest.mark.asyncio
    async def test_contract_flaky_test_hunt(self, mock_api_client):
        """
        Contract: CLI hunts for flaky tests

        Scenario: User runs `aqe flaky-hunt ./tests`
        Expected: API returns list of flaky tests with stability scores
        """
        expected_response = {
            "flaky_tests": EachLike("tests/test_integration.py::test_api_call"),
            "stability_scores": {
                "tests/test_integration.py::test_api_call": Like(0.85)
            },
            "root_causes": EachLike("Race condition in database access"),
            "fixes": EachLike("Add database transaction isolation")
        }

        (pact
         .given("flaky test hunter agent is available")
         .upon_receiving("a request to detect flaky tests")
         .with_request(
             method="POST",
             path="/tools/flaky_test_hunt",
             headers={"Content-Type": "application/json"},
             body={
                 "test_path": Like("./tests"),
                 "iterations": 10,
                 "detect_threshold": 0.1
             }
         )
         .will_respond_with(200, body=expected_response))

        with pact:
            result = await mock_api_client.flaky_test_hunt(
                test_path="./tests",
                iterations=10
            )

            assert "flaky_tests" in result
            assert "stability_scores" in result
            assert "root_causes" in result
            assert "fixes" in result

    @pytest.mark.asyncio
    async def test_contract_regression_risk_analyze(self, mock_api_client):
        """
        Contract: CLI analyzes regression risk

        Scenario: User runs `aqe regression-risk --changes src/utils.py`
        Expected: API returns prioritized test list based on risk
        """
        expected_response = {
            "high_risk_tests": EachLike("tests/test_utils.py::test_calculate"),
            "medium_risk_tests": EachLike("tests/test_models.py::test_validation"),
            "low_risk_tests": EachLike("tests/test_views.py::test_render"),
            "risk_scores": {
                "tests/test_utils.py::test_calculate": Like(0.95)
            },
            "estimated_time_saved": Like(240.5)
        }

        (pact
         .given("regression risk analyzer agent is available")
         .upon_receiving("a request to analyze regression risk")
         .with_request(
             method="POST",
             path="/tools/regression_risk_analyze",
             headers={"Content-Type": "application/json"},
             body={
                 "changes": ["src/utils.py", "src/models.py"],
                 "test_suite": Like("./tests"),
                 "ml_enabled": True
             }
         )
         .will_respond_with(200, body=expected_response))

        with pact:
            result = await mock_api_client.regression_risk_analyze(
                changes=["src/utils.py", "src/models.py"],
                test_suite="./tests"
            )

            assert "high_risk_tests" in result
            assert "medium_risk_tests" in result
            assert "estimated_time_saved" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--pact-publish-version=1.0.0"])
