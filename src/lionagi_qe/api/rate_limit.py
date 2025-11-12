"""
Rate limiting middleware for API endpoints.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.

    Tracks requests per API key and enforces configurable limits.
    """

    def __init__(self, app, requests_per_minute: int = 100):
        """
        Initialize rate limiter.

        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests allowed per minute per API key
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # seconds

        # Store: {api_key: [(timestamp1, timestamp2, ...)]}
        self._request_history: Dict[str, list] = defaultdict(list)

    def _get_api_key_from_request(self, request: Request) -> str:
        """
        Extract API key from request headers.

        Args:
            request: Incoming request

        Returns:
            API key string or 'anonymous' if not found
        """
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        return "anonymous"

    def _clean_old_requests(self, timestamps: list, current_time: float) -> list:
        """
        Remove timestamps outside the sliding window.

        Args:
            timestamps: List of request timestamps
            current_time: Current timestamp

        Returns:
            Filtered list of timestamps within window
        """
        window_start = current_time - self.window_size
        return [ts for ts in timestamps if ts > window_start]

    def _check_rate_limit(self, api_key: str) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request should be allowed based on rate limit.

        Args:
            api_key: API key to check

        Returns:
            Tuple of (allowed: bool, stats: dict)
        """
        current_time = time.time()

        # Get and clean request history
        history = self._request_history[api_key]
        history = self._clean_old_requests(history, current_time)
        self._request_history[api_key] = history

        # Check limit
        request_count = len(history)
        allowed = request_count < self.requests_per_minute

        # Calculate stats
        remaining = max(0, self.requests_per_minute - request_count)
        reset_time = int(current_time + self.window_size)

        stats = {
            "limit": self.requests_per_minute,
            "remaining": remaining,
            "reset": reset_time,
            "used": request_count,
        }

        return allowed, stats

    async def dispatch(self, request: Request, call_next):
        """
        Process request and enforce rate limits.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint

        Returns:
            Response with rate limit headers

        Raises:
            HTTPException: If rate limit exceeded
        """
        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        # Get API key and check rate limit
        api_key = self._get_api_key_from_request(request)
        allowed, stats = self._check_rate_limit(api_key)

        # Add rate limit headers to response
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit of {self.requests_per_minute} requests per minute exceeded",
                    "limit": stats["limit"],
                    "reset": stats["reset"],
                },
                headers={
                    "X-RateLimit-Limit": str(stats["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(stats["reset"]),
                    "Retry-After": str(self.window_size),
                },
            )

        # Record this request
        current_time = time.time()
        self._request_history[api_key].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers to successful response
        response.headers["X-RateLimit-Limit"] = str(stats["limit"])
        response.headers["X-RateLimit-Remaining"] = str(stats["remaining"])
        response.headers["X-RateLimit-Reset"] = str(stats["reset"])

        return response


def get_rate_limit_stats(api_key: str, middleware: RateLimitMiddleware) -> Dict[str, int]:
    """
    Get current rate limit statistics for an API key.

    Args:
        api_key: API key to check
        middleware: RateLimitMiddleware instance

    Returns:
        Dictionary with rate limit statistics
    """
    _, stats = middleware._check_rate_limit(api_key)
    return stats
