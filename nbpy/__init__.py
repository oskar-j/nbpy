"""NBPy package."""

from functools import lru_cache
from .version import version as __version__
from .errors import UnknownCurrencyCode
from .currencies import currencies


__all__ = ['NBPConverter']


class NBPConverter(object):
    """Converter between PLN and other currencies/troy ounces of gold."""

    # API base URI
    _base_uri = "http://api.nbp.pl/api/"

    # Template URI for NBP API calls
    _uri_template = _base_uri + "/exchangerates/rates/{table}/{code}/{tail}"

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
        if code not in currencies:
            raise UnknownCurrencyCode(code)
        self._currency_code = code

    def _request(self, uri_tail):
        """Return HTTP response object from API call."""
        pass

    def current(self):
        pass

    def today(self):
        pass

    def date(self, date):
        pass

    def date_range(self, start_date, end_date):
        pass

    def __call__(self, amount):
        return self.current(amount)