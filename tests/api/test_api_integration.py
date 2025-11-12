"""
Integration tests for AQE Fleet REST API.

Tests all API endpoints with authentication, rate limiting, and WebSocket streaming.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient

from lionagi_qe.api.server import app
from lionagi_qe.api.auth import generate_api_key


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def api_key():
    """Generate test API key."""
    return generate_api_key("test-key")


@pytest.fixture
def auth_headers(api_key):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {api_key}"}


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test health check without authentication."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "agentic-qe-fleet-api"
        assert data["version"] == "1.0.0"


class TestAuthentication:
    """Test authentication and authorization."""

    def test_missing_auth_header(self, client):
        """Test request without authentication fails."""
        response = client.post(
            "/api/v1/test/generate",
            json={"target": "src/", "framework": "jest"},
        )
        assert response.status_code == 401

    def test_invalid_api_key(self, client):
        """Test request with invalid API key fails."""
        response = client.post(
            "/api/v1/test/generate",
            json={"target": "src/", "framework": "jest"},
            headers={"Authorization": "Bearer invalid_key"},
        )
        assert response.status_code == 401

    def test_valid_api_key(self, client, auth_headers):
        """Test request with valid API key succeeds."""
        response = client.post(
            "/api/v1/test/generate",
            json={"target": "src/", "framework": "jest"},
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestRateLimiting:
    """Test rate limiting middleware."""

    def test_rate_limit_headers(self, client, auth_headers):
        """Test rate limit headers are included."""
        response = client.post(
            "/api/v1/test/generate",
            json={"target": "src/", "framework": "jest"},
            headers=auth_headers,
        )

        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_rate_limit_enforcement(self, client, auth_headers):
        """Test rate limit is enforced."""
        # Make requests until rate limit is hit
        # Note: This test may need adjustment based on actual rate limit
        responses = []
        for _ in range(105):  # Exceed 100 req/min limit
            response = client.post(
                "/api/v1/test/generate",
                json={"target": "src/", "framework": "jest"},
                headers=auth_headers,
            )
            responses.append(response)

        # At least one response should be 429
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Rate limit was not enforced"


class TestTestGeneration:
    """Test test generation endpoint."""

    def test_generate_tests_success(self, client, auth_headers):
        """Test successful test generation."""
        response = client.post(
            "/api/v1/test/generate",
            json={
                "target": "src/services/user.service.ts",
                "framework": "jest",
                "test_type": "unit",
                "coverage_target": 90.0,
                "priority": "high",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "job_id" in data
        assert data["status"] == "queued"
        assert "created_at" in data
        assert "stream_url" in data

    def test_generate_tests_validation(self, client, auth_headers):
        """Test request validation."""
        # Missing required field
        response = client.post(
            "/api/v1/test/generate",
            json={"framework": "jest"},
            headers=auth_headers,
        )
        assert response.status_code == 422  # Validation error


class TestTestExecution:
    """Test test execution endpoint."""

    def test_execute_tests_success(self, client, auth_headers):
        """Test successful test execution."""
        response = client.post(
            "/api/v1/test/execute",
            json={
                "test_path": "tests/",
                "framework": "jest",
                "parallel": True,
                "coverage": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data


class TestCoverageAnalysis:
    """Test coverage analysis endpoint."""

    def test_analyze_coverage_success(self, client, auth_headers):
        """Test successful coverage analysis."""
        response = client.post(
            "/api/v1/coverage/analyze",
            json={
                "source_path": "src/",
                "test_path": "tests/",
                "min_coverage": 80.0,
                "include_gaps": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data


class TestQualityGate:
    """Test quality gate endpoint."""

    def test_validate_quality_gate_success(self, client, auth_headers):
        """Test successful quality gate validation."""
        response = client.post(
            "/api/v1/quality/gate",
            json={
                "project_path": ".",
                "min_coverage": 80.0,
                "max_complexity": 10,
                "max_duplicates": 3.0,
                "security_checks": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data


class TestSecurityScan:
    """Test security scanning endpoint."""

    def test_security_scan_success(self, client, auth_headers):
        """Test successful security scan."""
        response = client.post(
            "/api/v1/security/scan",
            json={
                "target": ".",
                "scan_dependencies": True,
                "scan_code": True,
                "severity_threshold": "medium",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data


class TestPerformanceTest:
    """Test performance testing endpoint."""

    def test_performance_test_success(self, client, auth_headers):
        """Test successful performance test."""
        response = client.post(
            "/api/v1/performance/test",
            json={
                "target_url": "https://api.example.com/users",
                "duration_seconds": 60,
                "virtual_users": 10,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data


class TestFleetStatus:
    """Test fleet status endpoint."""

    def test_fleet_status_basic(self, client, auth_headers):
        """Test basic fleet status."""
        response = client.post(
            "/api/v1/fleet/status",
            json={"verbose": False, "include_metrics": False},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_agents" in data
        assert "active_agents" in data
        assert "queued_jobs" in data

    def test_fleet_status_verbose(self, client, auth_headers):
        """Test verbose fleet status."""
        response = client.post(
            "/api/v1/fleet/status",
            json={"verbose": True, "include_metrics": True},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "agents" in data
        assert "metrics" in data


class TestJobManagement:
    """Test job management endpoints."""

    def test_get_job_status(self, client, auth_headers):
        """Test getting job status."""
        # Create a job first
        create_response = client.post(
            "/api/v1/test/generate",
            json={"target": "src/", "framework": "jest"},
            headers=auth_headers,
        )
        job_id = create_response.json()["job_id"]

        # Get job status
        response = client.get(
            f"/api/v1/job/{job_id}/status", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["job_id"] == job_id
        assert "status" in data
        assert "progress" in data

    def test_get_nonexistent_job(self, client, auth_headers):
        """Test getting status of nonexistent job."""
        response = client.get(
            "/api/v1/job/nonexistent-job/status", headers=auth_headers
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestWebSocketStreaming:
    """Test WebSocket streaming functionality."""

    async def test_websocket_streaming(self, client, auth_headers):
        """Test WebSocket job progress streaming."""
        # Create a job first
        create_response = client.post(
            "/api/v1/test/generate",
            json={"target": "src/", "framework": "jest"},
            headers=auth_headers,
        )
        job_id = create_response.json()["job_id"]

        # Connect to WebSocket
        with client.websocket_connect(f"/api/v1/job/{job_id}/stream") as websocket:
            # Receive updates
            updates = []
            for _ in range(5):  # Receive a few updates
                data = websocket.receive_json()
                updates.append(data)

                if data.get("type") in ["complete", "error"]:
                    break

            # Verify updates
            assert len(updates) > 0
            assert all("type" in u for u in updates)


class TestOpenAPISpec:
    """Test OpenAPI documentation."""

    def test_openapi_endpoint(self, client):
        """Test OpenAPI spec is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        spec = response.json()
        assert "openapi" in spec
        assert "info" in spec
        assert spec["info"]["title"] == "Agentic QE Fleet API"

    def test_docs_endpoint(self, client):
        """Test Swagger UI is available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_endpoint(self, client):
        """Test ReDoc is available."""
        response = client.get("/redoc")
        assert response.status_code == 200
