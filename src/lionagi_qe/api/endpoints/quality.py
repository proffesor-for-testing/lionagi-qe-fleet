"""
Quality gate validation endpoints.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from ..auth import APIKey, get_current_api_key
from ..models import JobResponse, JobStatus, QualityGateRequest
from ..workers.tasks import enqueue_quality_gate

router = APIRouter()


@router.post("/quality/gate", response_model=JobResponse)
async def validate_quality_gate(
    request: QualityGateRequest,
    api_key: APIKey = Depends(get_current_api_key),
) -> JobResponse:
    """
    Validate project quality against configured gates.

    This endpoint triggers the qe-quality-gate agent with risk assessment.

    **Quality Gates Checked:**
    - Code coverage threshold
    - Cyclomatic complexity
    - Code duplication
    - Security vulnerabilities (if enabled)
    - Test pass rate
    - Code style violations

    **Example:**
    ```bash
    curl -X POST http://localhost:8080/api/v1/quality/gate \\
      -H "Authorization: Bearer $API_KEY" \\
      -H "Content-Type: application/json" \\
      -d '{
        "project_path": ".",
        "min_coverage": 80.0,
        "max_complexity": 10,
        "max_duplicates": 3.0,
        "security_checks": true
      }'
    ```

    **Response:**
    ```json
    {
      "job_id": "quality-gate-123jkl",
      "status": "queued",
      "created_at": "2025-01-12T10:33:00Z",
      "stream_url": "ws://localhost:8080/api/v1/job/quality-gate-123jkl/stream"
    }
    ```

    **Quality Gate Result Format:**
    ```json
    {
      "passed": false,
      "score": 7.5,
      "gates": {
        "coverage": {"passed": true, "value": 85.3, "threshold": 80.0},
        "complexity": {"passed": false, "value": 12, "threshold": 10},
        "duplicates": {"passed": true, "value": 2.1, "threshold": 3.0},
        "security": {"passed": true, "vulnerabilities": 0}
      },
      "blockers": ["Cyclomatic complexity exceeds threshold in 3 functions"]
    }
    ```
    """
    try:
        # Enqueue quality gate validation job
        job_id = await enqueue_quality_gate(
            project_path=request.project_path,
            min_coverage=request.min_coverage,
            max_complexity=request.max_complexity,
            max_duplicates=request.max_duplicates,
            security_checks=request.security_checks,
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
