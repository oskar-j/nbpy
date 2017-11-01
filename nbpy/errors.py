"""NBPy errors."""

__all__ = ['NBPError', 'UnknownCurrencyCode']


class NBPError(Exception):
    """General exception for NBPy."""
    pass


class UnknownCurrencyCode(NBPError):
    """Raised for unknown currency codes."""
    pass