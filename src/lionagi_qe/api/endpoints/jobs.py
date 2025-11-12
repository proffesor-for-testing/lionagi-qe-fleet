"""
Job management and WebSocket streaming endpoints.
"""

import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from ..auth import APIKey, get_current_api_key
from ..models import JobStatusResponse
from ..workers.tasks import get_job_result, get_job_status, stream_job_progress

router = APIRouter()


@router.get("/job/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status_endpoint(
    job_id: str, api_key: APIKey = Depends(get_current_api_key)
) -> JobStatusResponse:
    """
    Get current status and progress of a job.

    Returns detailed information about job execution, including progress,
    current step, and results (if completed).

    **Example:**
    ```bash
    curl -X GET http://localhost:8080/api/v1/job/test-gen-123abc/status \\
      -H "Authorization: Bearer $API_KEY"
    ```

    **Response (Running):**
    ```json
    {
      "job_id": "test-gen-123abc",
      "status": "running",
      "created_at": "2025-01-12T10:30:00Z",
      "started_at": "2025-01-12T10:30:02Z",
      "progress": 45.2,
      "current_step": "Analyzing code structure..."
    }
    ```

    **Response (Completed):**
    ```json
    {
      "job_id": "test-gen-123abc",
      "status": "completed",
      "created_at": "2025-01-12T10:30:00Z",
      "started_at": "2025-01-12T10:30:02Z",
      "completed_at": "2025-01-12T10:31:15Z",
      "progress": 100.0,
      "result": {
        "tests_generated": 15,
        "coverage_achieved": 92.3,
        "files_created": ["tests/user.service.test.ts"]
      }
    }
    ```

    **Response (Failed):**
    ```json
    {
      "job_id": "test-gen-123abc",
      "status": "failed",
      "created_at": "2025-01-12T10:30:00Z",
      "started_at": "2025-01-12T10:30:02Z",
      "completed_at": "2025-01-12T10:30:45Z",
      "progress": 30.0,
      "error": "Target file not found: src/services/user.service.ts"
    }
    ```
    """
    try:
        # Get job status from job store
        status = await get_job_status(job_id)

        if not status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return status

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/job/{job_id}/stream")
async def stream_job_progress_ws(websocket: WebSocket, job_id: str):
    """
    Stream real-time job progress via WebSocket.

    Provides live updates on job execution, including progress percentage,
    current steps, and intermediate results.

    **Connection:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8080/api/v1/job/test-gen-123abc/stream');

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      console.log(`Progress: ${update.progress}%`);
      console.log(`Step: ${update.message}`);
    };
    ```

    **Message Format:**
    ```json
    {
      "type": "progress",
      "progress": 45.2,
      "message": "Analyzing code structure...",
      "timestamp": "2025-01-12T10:30:15Z"
    }
    ```

    **Completion Message:**
    ```json
    {
      "type": "complete",
      "progress": 100.0,
      "result": {
        "tests_generated": 15,
        "coverage_achieved": 92.3
      },
      "timestamp": "2025-01-12T10:31:15Z"
    }
    ```

    **Error Message:**
    ```json
    {
      "type": "error",
      "error": "Target file not found",
      "timestamp": "2025-01-12T10:30:45Z"
    }
    ```
    """
    await websocket.accept()

    try:
        # Stream job progress updates
        async for update in stream_job_progress(job_id):
            await websocket.send_json(update)

            # Close connection on completion or error
            if update["type"] in ["complete", "error"]:
                await websocket.close()
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        error_message = {
            "type": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
        try:
            await websocket.send_json(error_message)
        except:
            pass
        finally:
            await websocket.close()


@router.get("/job/{job_id}/result")
async def get_job_result_endpoint(
    job_id: str, api_key: APIKey = Depends(get_current_api_key)
):
    """
    Get the final result of a completed job.

    **Example:**
    ```bash
    curl -X GET http://localhost:8080/api/v1/job/test-gen-123abc/result \\
      -H "Authorization: Bearer $API_KEY"
    ```

    **Response:**
    ```json
    {
      "job_id": "test-gen-123abc",
      "status": "completed",
      "result": {
        "tests_generated": 15,
        "coverage_achieved": 92.3,
        "files_created": [
          "tests/user.service.test.ts",
          "tests/auth.service.test.ts"
        ],
        "execution_time": 73.2
      }
    }
    ```
    """
    try:
        result = await get_job_result(job_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
