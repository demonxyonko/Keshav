class ToolError(Exception):
    """Raised when a tool encounters an error."""

    def __init__(self, message):
        self.message = message


class KeshavError(Exception):
    """Base exception for all Keshav errors."""


class TokenLimitExceeded(KeshavError):
    """Exception raised when the token limit is exceeded."""
