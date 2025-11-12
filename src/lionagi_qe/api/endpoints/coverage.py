"""
Coverage analysis endpoints.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from ..auth import APIKey, get_current_api_key
from ..models import CoverageAnalysisRequest, JobResponse, JobStatus
from ..workers.tasks import enqueue_coverage_analysis

router = APIRouter()


@router.post("/coverage/analyze", response_model=JobResponse)
async def analyze_coverage(
    request: CoverageAnalysisRequest,
    api_key: APIKey = Depends(get_current_api_key),
) -> JobResponse:
    """
    Analyze code coverage and identify gaps using O(log n) algorithms.

    This endpoint triggers the qe-coverage-analyzer agent with real-time gap detection.

    **Example:**
    ```bash
    curl -X POST http://localhost:8080/api/v1/coverage/analyze \\
      -H "Authorization: Bearer $API_KEY" \\
      -H "Content-Type: application/json" \\
      -d '{
        "source_path": "src/",
        "test_path": "tests/",
        "min_coverage": 80.0,
        "include_gaps": true
      }'
    ```

    **Response:**
    ```json
    {
      "job_id": "cov-analyze-789ghi",
      "status": "queued",
      "created_at": "2025-01-12T10:32:00Z",
      "stream_url": "ws://localhost:8080/api/v1/job/cov-analyze-789ghi/stream"
    }
    ```

    **Coverage Result Format:**
    ```json
    {
      "overall_coverage": 85.3,
      "line_coverage": 87.2,
      "branch_coverage": 82.1,
      "function_coverage": 91.5,
      "gaps": [
        {
          "file": "src/services/user.service.ts",
          "lines": [45, 46, 47],
          "type": "uncovered",
          "priority": "high"
        }
      ]
    }
    ```
    """
    try:
        # Enqueue coverage analysis job
        job_id = await enqueue_coverage_analysis(
            source_path=request.source_path,
            test_path=request.test_path,
            min_coverage=request.min_coverage,
            include_gaps=request.include_gaps,
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
