"""NBPy package."""

from functools import lru_cache
from .version import version as __version__
from .currencies import currencies


__all__ = ['NBPConverter', 'NBPError', 'UnknownCurrencyCode']


class NBPError(Exception):
    """General exception for NBPy."""
    pass

class UnknownCurrencyCode(NBPError):
    """Raised for unknown currency codes."""
    pass


class NBPConverter(object):
    """Converter between PLN and other currencies/troy ounces of gold."""

    def __init__(self, currency_code, **kwargs):
        """
        Initialize for given `currency_code` and `amount`.
        """
        self.currency_code = currency_code

        #: If True, values will be floats instead of decimals.
        self.as_float = kwargs.get('as_float', False)

        #: If True, conversion will be from PLN to given currency.
        self.inverse = kwargs.get('inverse', False)

        #: Max size for LRU cache.
        self.cache_size = kwargs.get('cache_size', 128)

        cache_decorator = lru_cache(maxsize=self.cache_size)
        for method in ('current', 'today', 'date', 'date_range'):
            setattr(self, method, cache_decorator(getattr(self, method)))

    @property
    def currency_code(self):
        return self._currency_code

    @currency_code.setter
    def currency_code(self, code):
        code = code.upper()
        if code not in nbp_currencies:
            raise UnknownCurrencyCode(code)
        self._currency_code = code

    def current(self, amount):
        pass

    def today(self, amount):
        pass

    def date(self, amount, date):
        pass

    def date_range(self, amount, start_date, end_date):
        pass

    def __call__(self, amount):
        return self.current(amount)