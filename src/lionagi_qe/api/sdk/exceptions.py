"""
SDK exception classes.
"""


class AQEAPIError(Exception):
    """Base exception for AQE API errors."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class AQEAuthenticationError(AQEAPIError):
    """Authentication failed."""

    pass


class AQERateLimitError(AQEAPIError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: int = None,
        limit: int = None,
        reset: int = None,
    ):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after
        self.limit = limit
        self.reset = reset


class AQEConnectionError(AQEAPIError):
    """Connection to API failed."""

    pass
