"""NBPy package."""

import json
import requests
from decimal import Decimal
from functools import lru_cache
from .version import version as __version__
from .errors import UnknownCurrencyCode, APIError
from .currencies import currencies


__all__ = ['NBPConverter']


class NBPConverter(object):
    """Converter between PLN and other currencies/troy ounces of gold."""

    # API base URI
    _base_uri = "http://api.nbp.pl/api"

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

    def _get_response_data(self, uri_tail, all_values=False):
        """Return HTTP response data from API call."""
        tables = currencies[self.currency_code].tables
        if not all_values:
            # Avoid bid/ask values
            tables.discard('C')

        rates = {}

        for table in tables:
            uri = self._uri_template.format(
                code=self.currency_code,
                table=table,
                tail=uri_tail
            )

            # Send request to API, raise exception on error
            try:
                headers = {'Accept': 'application/json'}
                r = requests.get(uri, headers=headers)
                r.raise_for_status()
            except Exception as e:
                raise APIError(str(e))

            # Parse data with values as decimals
            if self.as_float:
                parse_float_cls = float
            else:
                parse_float_cls = Decimal

            _data = json.loads(r.text, parse_float=parse_float_cls)['rates']
            _data = {r['effectiveDate']: r for r in _data}
            for date in _data:
                if date in rates:
                    rates[date].update(_data[date])
                else:
                    rates[date] = _data[date]

        return rates

    def current(self, all_values=False):
        return self._get_response_data('', all_values)

    def today(self, all_values=False):
        return self._get_response_data('today', all_values)

    def last(self, n, all_values=False):
        uri_tail = "last/{:d}".format(n)
        return self._get_response_data(uri_tail, all_values)

    def date(self, date, all_values=False):
        return self._get_response_data(date, all_values)

    def date_range(self, start_date, end_date, all_values=False):
        uri_tail = "{}/{}".format(start_date, end_date)
        return self._get_response_data(uri_tail, all_values)

    def __call__(self, all_values=False):
        return self.current(all_values)