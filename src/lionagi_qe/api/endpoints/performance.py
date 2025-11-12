"""
Performance testing endpoints.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from ..auth import APIKey, get_current_api_key
from ..models import JobResponse, JobStatus, PerformanceTestRequest
from ..workers.tasks import enqueue_performance_test

router = APIRouter()


@router.post("/performance/test", response_model=JobResponse)
async def run_performance_test(
    request: PerformanceTestRequest,
    api_key: APIKey = Depends(get_current_api_key),
) -> JobResponse:
    """
    Execute performance/load testing with configurable virtual users.

    This endpoint triggers the qe-performance-tester agent with k6/JMeter/Gatling.

    **Performance Metrics:**
    - Request throughput (requests/sec)
    - Response times (p50, p95, p99)
    - Error rate
    - Concurrent users
    - Resource utilization

    **Example:**
    ```bash
    curl -X POST http://localhost:8080/api/v1/performance/test \\
      -H "Authorization: Bearer $API_KEY" \\
      -H "Content-Type: application/json" \\
      -d '{
        "target_url": "https://api.example.com/users",
        "duration_seconds": 60,
        "virtual_users": 50,
        "ramp_up_seconds": 10,
        "think_time_ms": 1000
      }'
    ```

    **Response:**
    ```json
    {
      "job_id": "perf-test-789pqr",
      "status": "queued",
      "created_at": "2025-01-12T10:35:00Z",
      "stream_url": "ws://localhost:8080/api/v1/job/perf-test-789pqr/stream"
    }
    ```

    **Performance Test Result Format:**
    ```json
    {
      "duration_seconds": 60,
      "virtual_users": 50,
      "metrics": {
        "total_requests": 12500,
        "successful_requests": 12487,
        "failed_requests": 13,
        "requests_per_second": 208.3,
        "response_times": {
          "min": 45,
          "max": 1203,
          "avg": 187,
          "p50": 152,
          "p95": 456,
          "p99": 892
        },
        "error_rate": 0.104
      }
    }
    ```
    """
    try:
        # Enqueue performance test job
        job_id = await enqueue_performance_test(
            target_url=request.target_url,
            duration_seconds=request.duration_seconds,
            virtual_users=request.virtual_users,
            ramp_up_seconds=request.ramp_up_seconds,
            think_time_ms=request.think_time_ms,
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
