"""Provides Default values for the application."""
HTTP_REQUEST_TIMEOUT = 60

def default_http_request_timeout() -> int:
    """Returns the default HTTP request timeout.

    Returns:
        int: The default HTTP request timeout.
    """
    return HTTP_REQUEST_TIMEOUT
