"""NBPy errors."""

__all__ = (
    'NBPError',
    'UnknownCurrencyCode', 'DateFormattingError',
    'BidAskUnavailable', 'APIError',
)


class NBPError(Exception):
    """General exception for NBPy."""
    pass


class UnknownCurrencyCode(NBPError):
    """Raised for unknown currency codes."""
    pass


class DateFormattingError(NBPError):
    """Raised for improperly formatted date strings (not YYYY-MM-DD)."""
    pass


class BidAskUnavailable(NBPError):
    """Raised for bid/ask requests for not supported currencies."""
    pass


class APIError(NBPError):
    """Raised for API errors (400, 404, connection problems etc.)."""
    pass
