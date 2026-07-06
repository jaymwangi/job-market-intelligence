class APIError(Exception):
    """Base API exception."""

    pass


class APIConnectionError(APIError):
    """Connection error."""

    pass


class APITimeoutError(APIError):
    """Timeout error."""

    pass


class APIServerError(APIError):
    """Server error."""

    pass


class APINotFoundError(APIError):
    """Resource not found."""

    pass
