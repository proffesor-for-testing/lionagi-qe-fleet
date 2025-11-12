"""
Fleet status and management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException

from ..auth import APIKey, get_current_api_key
from ..models import FleetStatusRequest, FleetStatusResponse
from ..workers.tasks import get_fleet_status

router = APIRouter()


@router.post("/fleet/status", response_model=FleetStatusResponse)
async def check_fleet_status(
    request: FleetStatusRequest,
    api_key: APIKey = Depends(get_current_api_key),
) -> FleetStatusResponse:
    """
    Get current status of the Agentic QE Fleet.

    Returns information about active agents, job queue, and performance metrics.

    **Example:**
    ```bash
    curl -X POST http://localhost:8080/api/v1/fleet/status \\
      -H "Authorization: Bearer $API_KEY" \\
      -H "Content-Type: application/json" \\
      -d '{
        "verbose": true,
        "include_metrics": true
      }'
    ```

    **Response:**
    ```json
    {
      "total_agents": 19,
      "active_agents": 15,
      "idle_agents": 4,
      "busy_agents": 11,
      "total_jobs": 1247,
      "queued_jobs": 3,
      "running_jobs": 11,
      "agents": [
        {
          "id": "qe-test-generator-01",
          "type": "qe-test-generator",
          "status": "busy",
          "current_task": "Generating unit tests for user.service.ts",
          "tasks_completed": 42,
          "avg_execution_time": 15.3
        }
      ],
      "metrics": {
        "avg_job_duration": 45.2,
        "success_rate": 98.7,
        "queue_wait_time": 2.1,
        "agent_utilization": 73.2
      }
    }
    ```
    """
    try:
        # Get fleet status from orchestrator
        status = await get_fleet_status(
            verbose=request.verbose, include_metrics=request.include_metrics
        )

        return status

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
