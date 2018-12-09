"""NBPy package."""

import sys
import warnings
import requests
from decimal import Decimal
from functools import lru_cache
from .version import version as __version__
from .errors import UnknownCurrencyCode, BidAskUnavailable, APIError
from .utils import validate_date, first_if_sequence
from .currencies import currencies
from .exchange_rate import NBPExchangeRate


__all__ = ('NBPClient',)


if not sys.version_info >= (3, 3):
    warnings.warn("NBPy supports only Python 3.3 and above.")

#: Base URI
BASE_URI = "http://api.nbp.pl/api"


class NBPClient(object):
    """NBP Web API client."""

    # Template URI for NBP API calls
    _uri_template = BASE_URI + "/exchangerates/rates/{table}/{code}/{tail}"

    def __init__(self, currency_code, **kwargs):
        r"""
        Initialize for given ``currency_code``.

        :param currency_code:
            Valid currency code (i.e. defined in nbpy.currencies.currencies).

        :param \**kwargs:
            See below.

        :Keyword Arguments:
            * *as_float* (``bool``) --
              If ``True``, all exchange rates will be returned as ``float``s,
              otherwise as ``decimal.Decimal``. Default: ``False``.
            * *suppress_errors* (``bool``) --
              If ``True``, all ``BidAskUnavailable``s and ``APIError``s are
              suppressed and instead all API calls returns ``None``.
              Default: ``False``.
            * *cache_size* (``int``) --
              LRU cache size for API calls. Default: ``128``.
        """
        self.currency_code = currency_code

        #: If True, values will be floats instead of decimals.
        self.as_float = kwargs.get('as_float', False)

        #: If True, instead of raising APIErrors return None
        self.suppress_errors = kwargs.get('suppress_errors', False)

        #: Max size for LRU cache.
        self._cache_size = kwargs.get('cache_size', 128)

        # Proxy settings (for requests)
        self._proxy_url = kwargs.get('proxy_url', None)  # should have url:port format
        self._proxy_secure_url = kwargs.get('proxy_https_url', None)
        self._proxy_secure = kwargs.get('proxy_is_https', False)

        cache_decorator = lru_cache(maxsize=self.cache_size)
        self._get_response_data = cache_decorator(self._get_response_data)

    def __repr__(self):
        """Return repr(self)."""
        return "{cls_name}({code}, as_float={as_float!s}, suppress_errors={suppress_errors!s}, cache_size={cache_size})".format(
            cls_name=self.__class__.__name__,
            code=self.currency_code,
            as_float=self.as_float,
            suppress_errors=self.suppress_errors,
            cache_size=self.cache_size
        )

    @property
    def currency_code(self):
        """Currency code (ISO 4217)."""
        return self._currency_code

    @currency_code.setter
    def currency_code(self, code):
        code = code.upper()
        if code not in currencies:
            raise UnknownCurrencyCode(code)
        self._currency_code = code

    @property
    def cache_size(self):
        """Read-only LRU cache size."""
        return self._cache_size

    def _get_response_data(self, uri_tail, bid_ask=False):
        """Return HTTP response data from API call."""
        table = currencies[self.currency_code].tables.copy()

        if bid_ask:
            # Only bid/ask rates
            if 'C' not in table:
                if self.suppress_errors:
                    # Return None if errors suppressed
                    return None
                error_msg = "Bid/ask unavailable for {}".format(
                    self.currency_code
                )
                raise BidAskUnavailable(error_msg)
            table = 'C'
        else:
            # Only mid rate
            table.discard('C')
            table = table.pop()

        uri = self._uri_template.format(
            code=self.currency_code.lower(),
            table=table.lower(),
            tail=uri_tail.lower()
        )

        if self._proxy_url is not None:
            proxy_dict = {'http': self._proxy_url, }
            if self._proxy_secure:
                if self._proxy_secure_url is not None:
                    proxy_dict['https'] = self._proxy_secure_url
                else:
                    proxy_dict['https'] = proxy_dict['http'].replace('http', 'https')
        else:
            proxy_dict = None

        # Send request to API, raise exception on error
        try:
            headers = {'Accept': 'application/json'}
            r = requests.get(uri, headers=headers, proxies=proxy_dict)
            r.raise_for_status()
        except Exception as e:
            if self.suppress_errors:
                # Return None if errors suppressed
                return None
            raise APIError(str(e))

        # Parse data with values as decimals
        if self.as_float:
            parse_float_cls = float
        else:
            parse_float_cls = Decimal

        rates = r.json(parse_float=parse_float_cls)['rates']
        rates = {rate['effectiveDate']: rate for rate in rates}

        return sorted([
            NBPExchangeRate(
                currency_code=self.currency_code,
                date=rate['effectiveDate'],
                **rate
            ) for rate in rates.values()
        ], key=lambda r: r.date)

    @first_if_sequence
    def current(self, bid_ask=False):
        """Return earliest available exchange rate."""
        return self._get_response_data('', bid_ask)

    @first_if_sequence
    def today(self, bid_ask=False):
        """Return exchange rate from today."""
        return self._get_response_data('today', bid_ask)

    def last(self, n, bid_ask=False):
        """Return last ``n`` exchange rates."""
        uri_tail = "last/{:d}".format(n)
        return self._get_response_data(uri_tail, bid_ask)

    @first_if_sequence
    def date(self, date, bid_ask=False):
        """Return exchange rate from ``date``."""
        validate_date(date)

        return self._get_response_data(date, bid_ask)

    def date_range(self, start_date, end_date, bid_ask=False):
        """Return exchange rates from ``start_date`` to ``end_date``."""
        validate_date(start_date)
        validate_date(end_date)

        uri_tail = "{}/{}".format(start_date, end_date)
        return self._get_response_data(uri_tail, bid_ask)

    def __call__(self, bid_ask=False):
        """Return ``self.current()``."""
        return self.current(bid_ask)
