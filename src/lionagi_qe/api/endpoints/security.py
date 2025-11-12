"""
Security scanning endpoints.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from ..auth import APIKey, get_current_api_key
from ..models import JobResponse, JobStatus, SecurityScanRequest
from ..workers.tasks import enqueue_security_scan

router = APIRouter()


@router.post("/security/scan", response_model=JobResponse)
async def scan_security(
    request: SecurityScanRequest,
    api_key: APIKey = Depends(get_current_api_key),
) -> JobResponse:
    """
    Perform security vulnerability scanning with SAST/DAST analysis.

    This endpoint triggers the qe-security-scanner agent with multi-layer scanning.

    **Security Checks:**
    - **SAST**: Static code analysis for vulnerabilities
    - **Dependency Scanning**: Known CVE detection
    - **Secret Detection**: Hardcoded credentials, API keys
    - **Configuration Issues**: Insecure settings
    - **OWASP Top 10**: Common web vulnerabilities

    **Example:**
    ```bash
    curl -X POST http://localhost:8080/api/v1/security/scan \\
      -H "Authorization: Bearer $API_KEY" \\
      -H "Content-Type: application/json" \\
      -d '{
        "target": ".",
        "scan_dependencies": true,
        "scan_code": true,
        "severity_threshold": "medium"
      }'
    ```

    **Response:**
    ```json
    {
      "job_id": "sec-scan-456mno",
      "status": "queued",
      "created_at": "2025-01-12T10:34:00Z",
      "stream_url": "ws://localhost:8080/api/v1/job/sec-scan-456mno/stream"
    }
    ```

    **Security Scan Result Format:**
    ```json
    {
      "vulnerabilities_found": 3,
      "severity_breakdown": {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 0
      },
      "findings": [
        {
          "severity": "high",
          "type": "SQL Injection",
          "file": "src/database/query.ts",
          "line": 42,
          "description": "Unsafe SQL query construction",
          "recommendation": "Use parameterized queries"
        }
      ]
    }
    ```
    """
    try:
        # Enqueue security scan job
        job_id = await enqueue_security_scan(
            target=request.target,
            scan_dependencies=request.scan_dependencies,
            scan_code=request.scan_code,
            severity_threshold=request.severity_threshold,
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
