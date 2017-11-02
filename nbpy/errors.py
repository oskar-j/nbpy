"""NBPy errors."""

__all__ = [
    'NBPError', 'UnknownCurrencyCode', 'DateFormattingError', 'APIError'
]


class NBPError(Exception):
    """General exception for NBPy."""
    pass


class UnknownCurrencyCode(NBPError):
    """Raised for unknown currency codes."""
    pass


class DateFormattingError(NBPError):
    """Raised for improperly formatted date strings (not YYYY-MM-DD)."""
    pass


class APIError(NBPError):
    """Raised for API errors (400, 404, connection problems etc.)."""
    pass
