"""
Pydantic models for API request/response validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class JobStatus(str, Enum):
    """Job execution status."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Framework(str, Enum):
    """Supported testing frameworks."""

    JEST = "jest"
    PYTEST = "pytest"
    MOCHA = "mocha"
    VITEST = "vitest"


class TestType(str, Enum):
    """Test generation types."""

    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    API = "api"
    PERFORMANCE = "performance"


class Priority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Request Models


class TestGenerationRequest(BaseModel):
    """Request model for test generation."""

    target: str = Field(..., description="Target file/directory to generate tests for")
    framework: Framework = Field(
        default=Framework.JEST, description="Testing framework to use"
    )
    test_type: TestType = Field(
        default=TestType.UNIT, description="Type of tests to generate"
    )
    coverage_target: Optional[float] = Field(
        default=80.0, ge=0.0, le=100.0, description="Target coverage percentage"
    )
    priority: Priority = Field(default=Priority.MEDIUM, description="Job priority")
    callback_url: Optional[str] = Field(
        default=None, description="Webhook URL for completion notification"
    )

    @field_validator("target")
    @classmethod
    def validate_target(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Target cannot be empty")
        return v.strip()


class TestExecutionRequest(BaseModel):
    """Request model for test execution."""

    test_path: str = Field(..., description="Path to tests to execute")
    framework: Framework = Field(
        default=Framework.JEST, description="Testing framework to use"
    )
    parallel: bool = Field(
        default=True, description="Enable parallel test execution"
    )
    coverage: bool = Field(default=True, description="Enable coverage reporting")
    timeout: Optional[int] = Field(
        default=300, ge=1, le=3600, description="Timeout in seconds"
    )
    env_vars: Optional[Dict[str, str]] = Field(
        default=None, description="Environment variables for test execution"
    )
    priority: Priority = Field(default=Priority.MEDIUM, description="Job priority")
    callback_url: Optional[str] = Field(
        default=None, description="Webhook URL for completion notification"
    )


class CoverageAnalysisRequest(BaseModel):
    """Request model for coverage analysis."""

    source_path: str = Field(..., description="Path to source code")
    test_path: Optional[str] = Field(
        default=None, description="Path to test files (optional)"
    )
    min_coverage: float = Field(
        default=80.0, ge=0.0, le=100.0, description="Minimum coverage threshold"
    )
    include_gaps: bool = Field(
        default=True, description="Include uncovered code gaps in response"
    )
    priority: Priority = Field(default=Priority.MEDIUM, description="Job priority")
    callback_url: Optional[str] = Field(
        default=None, description="Webhook URL for completion notification"
    )


class QualityGateRequest(BaseModel):
    """Request model for quality gate validation."""

    project_path: str = Field(..., description="Path to project root")
    min_coverage: float = Field(
        default=80.0, ge=0.0, le=100.0, description="Minimum coverage threshold"
    )
    max_complexity: int = Field(
        default=10, ge=1, description="Maximum cyclomatic complexity"
    )
    max_duplicates: float = Field(
        default=3.0, ge=0.0, le=100.0, description="Maximum code duplication percentage"
    )
    security_checks: bool = Field(
        default=True, description="Run security vulnerability checks"
    )
    priority: Priority = Field(default=Priority.HIGH, description="Job priority")
    callback_url: Optional[str] = Field(
        default=None, description="Webhook URL for completion notification"
    )


class SecurityScanRequest(BaseModel):
    """Request model for security scanning."""

    target: str = Field(..., description="Target directory to scan")
    scan_dependencies: bool = Field(
        default=True, description="Scan dependencies for vulnerabilities"
    )
    scan_code: bool = Field(default=True, description="Perform SAST code analysis")
    severity_threshold: str = Field(
        default="medium",
        description="Minimum severity to report (low, medium, high, critical)",
    )
    priority: Priority = Field(default=Priority.HIGH, description="Job priority")
    callback_url: Optional[str] = Field(
        default=None, description="Webhook URL for completion notification"
    )

    @field_validator("severity_threshold")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        valid = ["low", "medium", "high", "critical"]
        if v.lower() not in valid:
            raise ValueError(f"Severity must be one of: {', '.join(valid)}")
        return v.lower()


class PerformanceTestRequest(BaseModel):
    """Request model for performance testing."""

    target_url: str = Field(..., description="Target URL/endpoint to test")
    duration_seconds: int = Field(
        default=60, ge=1, le=3600, description="Test duration in seconds"
    )
    virtual_users: int = Field(
        default=10, ge=1, le=1000, description="Number of concurrent virtual users"
    )
    ramp_up_seconds: int = Field(
        default=10, ge=0, le=300, description="Ramp-up time in seconds"
    )
    think_time_ms: int = Field(
        default=1000, ge=0, le=60000, description="Think time between requests (ms)"
    )
    priority: Priority = Field(default=Priority.MEDIUM, description="Job priority")
    callback_url: Optional[str] = Field(
        default=None, description="Webhook URL for completion notification"
    )


class FleetStatusRequest(BaseModel):
    """Request model for fleet status check."""

    verbose: bool = Field(
        default=False, description="Include detailed agent information"
    )
    include_metrics: bool = Field(
        default=True, description="Include performance metrics"
    )


# Response Models


class JobResponse(BaseModel):
    """Response model for job creation."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    estimated_completion: Optional[datetime] = Field(
        default=None, description="Estimated completion time"
    )
    stream_url: Optional[str] = Field(
        default=None, description="WebSocket URL for real-time updates"
    )


class JobStatusResponse(BaseModel):
    """Response model for job status query."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(
        default=None, description="Job start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Job completion timestamp"
    )
    progress: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Progress percentage"
    )
    current_step: Optional[str] = Field(
        default=None, description="Current execution step"
    )
    result: Optional[Dict[str, Any]] = Field(
        default=None, description="Job result (only when completed)"
    )
    error: Optional[str] = Field(default=None, description="Error message (if failed)")


class FleetStatusResponse(BaseModel):
    """Response model for fleet status."""

    total_agents: int = Field(..., description="Total number of agents")
    active_agents: int = Field(..., description="Number of active agents")
    idle_agents: int = Field(..., description="Number of idle agents")
    busy_agents: int = Field(..., description="Number of busy agents")
    total_jobs: int = Field(..., description="Total jobs processed")
    queued_jobs: int = Field(..., description="Jobs in queue")
    running_jobs: int = Field(..., description="Currently running jobs")
    agents: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Detailed agent information (if verbose=true)"
    )
    metrics: Optional[Dict[str, Any]] = Field(
        default=None, description="Performance metrics (if include_metrics=true)"
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
