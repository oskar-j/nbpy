"""NBPy package."""

from functools import lru_cache
from .version import version as __version__


__all__ = ['NBPConverter', 'NBPError']


class NBPError(Exception):
    """General exception for NBPy."""
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