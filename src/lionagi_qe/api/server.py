"""
FastAPI server for Agentic QE Fleet REST API.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .auth import get_current_api_key
from .models import ErrorResponse
from .rate_limit import RateLimitMiddleware
from .endpoints import test, coverage, quality, security, performance, jobs, fleet

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Agentic QE Fleet API server...")
    logger.info("API documentation available at /docs")
    logger.info("OpenAPI spec available at /openapi.json")

    yield

    # Shutdown
    logger.info("Shutting down Agentic QE Fleet API server...")


# Create FastAPI app
app = FastAPI(
    title="Agentic QE Fleet API",
    description="""
    REST API for triggering Agentic QE Fleet agents from external CI/CD systems.

    ## Features

    - **Test Generation**: AI-powered test generation with sublinear optimization
    - **Test Execution**: Multi-framework test execution with parallel processing
    - **Coverage Analysis**: Real-time gap detection with O(log n) algorithms
    - **Quality Gates**: Intelligent quality validation with risk assessment
    - **Security Scanning**: Multi-layer security with SAST/DAST scanning
    - **Performance Testing**: Load testing with k6, JMeter, Gatling integration

    ## Authentication

    All endpoints require authentication using API keys or JWT tokens:

    ```
    Authorization: Bearer <api_key>
    ```

    Generate an API key using the CLI:

    ```bash
    aqe api generate-key --name "ci-cd-integration"
    ```

    ## Rate Limiting

    - **Default**: 100 requests per minute per API key
    - Rate limit headers included in all responses
    - Configurable per API key

    ## WebSocket Streaming

    Real-time job progress available via WebSocket:

    ```
    ws://localhost:8080/api/v1/job/{job_id}/stream
    ```
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled errors.

    Args:
        request: FastAPI request
        exc: Exception raised

    Returns:
        JSON error response
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    error_response = ErrorResponse(
        error="internal_server_error",
        message="An internal error occurred. Please try again later.",
        details={"path": str(request.url), "method": request.method},
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
    )


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint.

    Returns system health status without authentication.
    """
    return {
        "status": "healthy",
        "service": "agentic-qe-fleet-api",
        "version": "1.0.0",
    }


# Include API routers
app.include_router(test.router, prefix="/api/v1", tags=["Test Generation"])
app.include_router(coverage.router, prefix="/api/v1", tags=["Coverage Analysis"])
app.include_router(quality.router, prefix="/api/v1", tags=["Quality Gates"])
app.include_router(security.router, prefix="/api/v1", tags=["Security Scanning"])
app.include_router(performance.router, prefix="/api/v1", tags=["Performance Testing"])
app.include_router(jobs.router, prefix="/api/v1", tags=["Job Management"])
app.include_router(fleet.router, prefix="/api/v1", tags=["Fleet Status"])


def start_server(host: str = "0.0.0.0", port: int = 8080, reload: bool = False):
    """
    Start the API server.

    Args:
        host: Host address to bind to
        port: Port to listen on
        reload: Enable auto-reload for development
    """
    import uvicorn

    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"API documentation: http://{host}:{port}/docs")

    uvicorn.run(
        "lionagi_qe.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    start_server()
