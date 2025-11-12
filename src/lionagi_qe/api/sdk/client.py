"""
Python client SDK for Agentic QE Fleet API.

Example usage:
    >>> from lionagi_qe.api.sdk import AQEClient
    >>>
    >>> client = AQEClient(api_key="aqe_your_api_key")
    >>>
    >>> # Generate tests
    >>> job = await client.generate_tests(
    ...     target="src/services/user.service.ts",
    ...     framework="jest",
    ...     coverage_target=90.0
    ... )
    >>>
    >>> # Check job status
    >>> status = await client.get_job_status(job.job_id)
    >>> print(f"Progress: {status.progress}%")
    >>>
    >>> # Stream progress
    >>> async for update in client.stream_job_progress(job.job_id):
    ...     print(f"{update['progress']}%: {update['message']}")
"""

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, Optional

import aiohttp

from .exceptions import (
    AQEAPIError,
    AQEAuthenticationError,
    AQEConnectionError,
    AQERateLimitError,
)


@dataclass
class AQEConfig:
    """Configuration for AQE API client."""

    base_url: str = "http://localhost:8080"
    api_key: str = ""
    timeout: int = 300
    max_retries: int = 3
    verify_ssl: bool = True


class AQEClient:
    """
    Python client for Agentic QE Fleet API.

    Provides async methods for all API endpoints with automatic retries
    and error handling.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8080",
        timeout: int = 300,
        max_retries: int = 3,
    ):
        """
        Initialize AQE API client.

        Args:
            api_key: API key for authentication
            base_url: Base URL of API server
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.config = AQEConfig(
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            )

    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            json: JSON request body
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            AQEAuthenticationError: If authentication fails
            AQERateLimitError: If rate limit exceeded
            AQEConnectionError: If connection fails
            AQEAPIError: For other API errors
        """
        await self._ensure_session()

        url = f"{self.config.base_url}{endpoint}"

        for attempt in range(self.config.max_retries):
            try:
                async with self._session.request(
                    method, url, json=json, params=params
                ) as response:
                    # Handle rate limiting
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        raise AQERateLimitError(
                            "Rate limit exceeded",
                            retry_after=retry_after,
                            limit=int(response.headers.get("X-RateLimit-Limit", 0)),
                            reset=int(response.headers.get("X-RateLimit-Reset", 0)),
                        )

                    # Handle authentication errors
                    if response.status == 401:
                        raise AQEAuthenticationError(
                            "Authentication failed - check API key", status_code=401
                        )

                    # Parse response
                    response_data = await response.json()

                    # Handle API errors
                    if response.status >= 400:
                        raise AQEAPIError(
                            response_data.get("message", "API error"),
                            status_code=response.status,
                            response=response_data,
                        )

                    return response_data

            except aiohttp.ClientError as e:
                if attempt == self.config.max_retries - 1:
                    raise AQEConnectionError(f"Connection failed: {e}")
                await asyncio.sleep(2**attempt)  # Exponential backoff

        raise AQEConnectionError("Max retries exceeded")

    # Test Generation

    async def generate_tests(
        self,
        target: str,
        framework: str = "jest",
        test_type: str = "unit",
        coverage_target: float = 80.0,
        priority: str = "medium",
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate tests for target code.

        Args:
            target: Target file/directory
            framework: Testing framework (jest, pytest, mocha, vitest)
            test_type: Type of tests (unit, integration, e2e, api, performance)
            coverage_target: Target coverage percentage
            priority: Job priority (low, medium, high, critical)
            callback_url: Optional webhook URL for completion notification

        Returns:
            Job response with job_id and status
        """
        return await self._request(
            "POST",
            "/api/v1/test/generate",
            json={
                "target": target,
                "framework": framework,
                "test_type": test_type,
                "coverage_target": coverage_target,
                "priority": priority,
                "callback_url": callback_url,
            },
        )

    # Test Execution

    async def execute_tests(
        self,
        test_path: str,
        framework: str = "jest",
        parallel: bool = True,
        coverage: bool = True,
        timeout: int = 300,
        env_vars: Optional[Dict[str, str]] = None,
        priority: str = "medium",
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute tests with specified configuration.

        Args:
            test_path: Path to tests
            framework: Testing framework
            parallel: Enable parallel execution
            coverage: Enable coverage reporting
            timeout: Execution timeout in seconds
            env_vars: Environment variables
            priority: Job priority
            callback_url: Optional webhook URL

        Returns:
            Job response with job_id and status
        """
        return await self._request(
            "POST",
            "/api/v1/test/execute",
            json={
                "test_path": test_path,
                "framework": framework,
                "parallel": parallel,
                "coverage": coverage,
                "timeout": timeout,
                "env_vars": env_vars or {},
                "priority": priority,
                "callback_url": callback_url,
            },
        )

    # Coverage Analysis

    async def analyze_coverage(
        self,
        source_path: str,
        test_path: Optional[str] = None,
        min_coverage: float = 80.0,
        include_gaps: bool = True,
        priority: str = "medium",
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze code coverage and identify gaps.

        Args:
            source_path: Path to source code
            test_path: Optional path to tests
            min_coverage: Minimum coverage threshold
            include_gaps: Include uncovered code gaps
            priority: Job priority
            callback_url: Optional webhook URL

        Returns:
            Job response with job_id and status
        """
        return await self._request(
            "POST",
            "/api/v1/coverage/analyze",
            json={
                "source_path": source_path,
                "test_path": test_path,
                "min_coverage": min_coverage,
                "include_gaps": include_gaps,
                "priority": priority,
                "callback_url": callback_url,
            },
        )

    # Quality Gate

    async def validate_quality_gate(
        self,
        project_path: str,
        min_coverage: float = 80.0,
        max_complexity: int = 10,
        max_duplicates: float = 3.0,
        security_checks: bool = True,
        priority: str = "high",
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate project quality gates.

        Args:
            project_path: Path to project
            min_coverage: Minimum coverage threshold
            max_complexity: Maximum cyclomatic complexity
            max_duplicates: Maximum code duplication percentage
            security_checks: Run security checks
            priority: Job priority
            callback_url: Optional webhook URL

        Returns:
            Job response with job_id and status
        """
        return await self._request(
            "POST",
            "/api/v1/quality/gate",
            json={
                "project_path": project_path,
                "min_coverage": min_coverage,
                "max_complexity": max_complexity,
                "max_duplicates": max_duplicates,
                "security_checks": security_checks,
                "priority": priority,
                "callback_url": callback_url,
            },
        )

    # Security Scan

    async def scan_security(
        self,
        target: str,
        scan_dependencies: bool = True,
        scan_code: bool = True,
        severity_threshold: str = "medium",
        priority: str = "high",
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform security vulnerability scanning.

        Args:
            target: Target directory
            scan_dependencies: Scan dependencies
            scan_code: Perform SAST analysis
            severity_threshold: Minimum severity (low, medium, high, critical)
            priority: Job priority
            callback_url: Optional webhook URL

        Returns:
            Job response with job_id and status
        """
        return await self._request(
            "POST",
            "/api/v1/security/scan",
            json={
                "target": target,
                "scan_dependencies": scan_dependencies,
                "scan_code": scan_code,
                "severity_threshold": severity_threshold,
                "priority": priority,
                "callback_url": callback_url,
            },
        )

    # Performance Test

    async def run_performance_test(
        self,
        target_url: str,
        duration_seconds: int = 60,
        virtual_users: int = 10,
        ramp_up_seconds: int = 10,
        think_time_ms: int = 1000,
        priority: str = "medium",
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run performance/load test.

        Args:
            target_url: Target URL to test
            duration_seconds: Test duration
            virtual_users: Concurrent users
            ramp_up_seconds: Ramp-up time
            think_time_ms: Think time between requests
            priority: Job priority
            callback_url: Optional webhook URL

        Returns:
            Job response with job_id and status
        """
        return await self._request(
            "POST",
            "/api/v1/performance/test",
            json={
                "target_url": target_url,
                "duration_seconds": duration_seconds,
                "virtual_users": virtual_users,
                "ramp_up_seconds": ramp_up_seconds,
                "think_time_ms": think_time_ms,
                "priority": priority,
                "callback_url": callback_url,
            },
        )

    # Fleet Status

    async def get_fleet_status(
        self, verbose: bool = False, include_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Get fleet status.

        Args:
            verbose: Include detailed agent information
            include_metrics: Include performance metrics

        Returns:
            Fleet status response
        """
        return await self._request(
            "POST",
            "/api/v1/fleet/status",
            json={"verbose": verbose, "include_metrics": include_metrics},
        )

    # Job Management

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get job status.

        Args:
            job_id: Job identifier

        Returns:
            Job status response
        """
        return await self._request("GET", f"/api/v1/job/{job_id}/status")

    async def get_job_result(self, job_id: str) -> Dict[str, Any]:
        """
        Get job result.

        Args:
            job_id: Job identifier

        Returns:
            Job result response
        """
        return await self._request("GET", f"/api/v1/job/{job_id}/result")

    async def stream_job_progress(
        self, job_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream job progress updates via WebSocket.

        Args:
            job_id: Job identifier

        Yields:
            Progress update dictionaries

        Example:
            >>> async for update in client.stream_job_progress(job_id):
            ...     print(f"{update['progress']}%: {update['message']}")
        """
        # Convert to WebSocket URL
        ws_url = self.config.base_url.replace("http://", "ws://").replace(
            "https://", "wss://"
        )
        ws_url = f"{ws_url}/api/v1/job/{job_id}/stream"

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        yield msg.json()
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        raise AQEConnectionError("WebSocket connection error")
