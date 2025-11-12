"""
Test generation and execution endpoints.
"""

from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from ..auth import APIKey, get_current_api_key
from ..models import (
    JobResponse,
    JobStatus,
    TestExecutionRequest,
    TestGenerationRequest,
)
from ..workers.tasks import enqueue_test_execution, enqueue_test_generation

router = APIRouter()


@router.post("/test/generate", response_model=JobResponse)
async def generate_tests(
    request: TestGenerationRequest,
    api_key: APIKey = Depends(get_current_api_key),
) -> JobResponse:
    """
    Generate tests for specified target using AI-powered test generation.

    This endpoint triggers the qe-test-generator agent with sublinear optimization.

    **Example:**
    ```bash
    curl -X POST http://localhost:8080/api/v1/test/generate \\
      -H "Authorization: Bearer $API_KEY" \\
      -H "Content-Type: application/json" \\
      -d '{
        "target": "src/services/user.service.ts",
        "framework": "jest",
        "test_type": "unit",
        "coverage_target": 90.0
      }'
    ```

    **Response:**
    ```json
    {
      "job_id": "test-gen-123abc",
      "status": "queued",
      "created_at": "2025-01-12T10:30:00Z",
      "stream_url": "ws://localhost:8080/api/v1/job/test-gen-123abc/stream"
    }
    ```
    """
    try:
        # Enqueue test generation job
        job_id = await enqueue_test_generation(
            target=request.target,
            framework=request.framework.value,
            test_type=request.test_type.value,
            coverage_target=request.coverage_target,
            priority=request.priority.value,
            callback_url=request.callback_url,
            api_key=api_key.key,
        )

        return JobResponse(
            job_id=job_id,
            status=JobStatus.QUEUED,
            created_at=datetime.utcnow(),
            stream_url=f"/api/v1/job/{job_id}/stream",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/execute", response_model=JobResponse)
async def execute_tests(
    request: TestExecutionRequest,
    api_key: APIKey = Depends(get_current_api_key),
) -> JobResponse:
    """
    Execute tests with specified framework and configuration.

    This endpoint triggers the qe-test-executor agent with parallel processing.

    **Example:**
    ```bash
    curl -X POST http://localhost:8080/api/v1/test/execute \\
      -H "Authorization: Bearer $API_KEY" \\
      -H "Content-Type: application/json" \\
      -d '{
        "test_path": "tests/",
        "framework": "jest",
        "parallel": true,
        "coverage": true
      }'
    ```

    **Response:**
    ```json
    {
      "job_id": "test-exec-456def",
      "status": "queued",
      "created_at": "2025-01-12T10:31:00Z",
      "stream_url": "ws://localhost:8080/api/v1/job/test-exec-456def/stream"
    }
    ```
    """
    try:
        # Enqueue test execution job
        job_id = await enqueue_test_execution(
            test_path=request.test_path,
            framework=request.framework.value,
            parallel=request.parallel,
            coverage=request.coverage,
            timeout=request.timeout,
            env_vars=request.env_vars or {},
            priority=request.priority.value,
            callback_url=request.callback_url,
            api_key=api_key.key,
        )

        return JobResponse(
            job_id=job_id,
            status=JobStatus.QUEUED,
            created_at=datetime.utcnow(),
            stream_url=f"/api/v1/job/{job_id}/stream",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
