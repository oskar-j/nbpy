"""Tests for NBPClient (with mock responses)."""

import pytest
import random
import requests
import responses
from collections import Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
from nbpy import BASE_URI
from nbpy.currencies import NBPCurrency, currencies


class MockAPIHelperError(Exception):
    """Exception for HelperError class."""
    pass


class MockAPIHelper(object):
    """Base helper class for full mock API calls."""
    def __init__(self, currency, bid_ask=False):
        from nbpy.currencies import NBPCurrency

        if not isinstance(currency, NBPCurrency):
            raise MockAPIHelperError('{} is not NBPCurrency'.format(currency))

        self.currency = currency
        self.bid_ask = bid_ask

    @property
    def table(self):
        """'A' or 'B' if bid_ask is False, otherwise 'C'."""
        if self.bid_ask:
            return 'C'
        else:
            tables = self.currency.tables.copy()
            tables.discard('C')
            return tables.pop()

    def current(self, **kwargs):
        raise NotImplementedError()

    def today(self, **kwargs):
        raise NotImplementedError()

    def last(self, n, **kwargs):
        raise NotImplementedError()

    def date(self, date, **kwargs):
        raise NotImplementedError()

    def date_range(self, start_date, end_date, **kwargs):
        raise NotImplementedError()


class MockHTTPAddress(MockAPIHelper):
    """Helper class for full API addresses for various calls."""

    def _uri(self, resource):
        """Returns URI for `resource`."""
        return "{b_uri}/exchangerates/rates/{table}/{code}/{resource}".format(
            b_uri=BASE_URI,
            table=self.table.lower(),
            code=self.currency.code.lower(),
            resource=resource.lower()
        )

    def current(self, **kwargs):
        """Return URI for current()."""
        return self._uri('')

    def today(self, **kwargs):
        """Return URI for today()."""
        return self._uri('today')

    def last(self, n, **kwargs):
        """Return URI for last()."""
        return self._uri('last/{:d}'.format(n))

    def date(self, date, **kwargs):
        """Return URI for date()."""
        return self._uri(date.strftime("%Y-%m-%d"))

    def date_range(self, start_date, end_date, **kwargs):
        """Return URI for date_range()."""
        return self._uri("{start}/{end}".format(
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d")
        ))

class MockJSONData(MockAPIHelper):
    """Helper class for creating mock JSON data."""

    def common_data(method):
        """Decorator adding common data for all methods."""
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            return {
                'table': self.table,
                'currency': self.currency.name,
                'code': self.currency.code,
                'rates': method(self, *args, **kwargs)
            }
        return wrapper

    def source_id(self, date):
        """Random source."""
        return "{count}/{table}/NBP/{year}".format(
            count=random.randint(1, 365),
            table=self.table,
            year=date.year
        )

    @staticmethod
    def rnd_value():
        """Random value from [0.0, 5.0] rounded to 5 decimal places."""
        return round(random.uniform(0.0, 5.0), 5)

    def exchange_rate(self, date):
        """Random exchange rate."""
        rate = {
            "no": self.source_id(date),
            "effectiveDate": date.strftime("%Y-%m-%d"),
        }

        if self.bid_ask:
            rate = dict(rate, **{
                "bid": self.rnd_value(),
                "ask": self.rnd_value(),
            })
        else:
            rate = dict(rate, **{
                "mid": self.rnd_value(),
            })

        return rate

    @common_data
    def current(self, **kwargs):
        """Mock data for most recent exchange rates."""
        return [self.exchange_rate(datetime.today())]

    @common_data
    def today(self, **kwargs):
        """Mock data for today exchange rates."""
        return [self.exchange_rate(datetime.today())]

    @common_data
    def last(self, n, **kwargs):
        """Mock data for the last n exchange rates."""
        date = datetime.today()
        rates = []
        for _ in range(n):
            rates.append(self.exchange_rate(date))
            date -= timedelta(days=1)
        return rates

    @common_data
    def date(self, date, **kwargs):
        """Mock data for exchange rates from given date."""
        return [self.exchange_rate(date)]

    @common_data
    def date_range(self, start_date, end_date, **kwargs):
        """Mock data for exchange rates from given date range."""
        date = start_date
        rates = []
        while date <= end_date:
            rates.append(self.exchange_rate(date))
            date += timedelta(days=1)
        return rates


###
# Calls to test (with args names)
###
calls_to_test = {
    'current': (),
    'today': (),
    'date': ('date',),
    'last': ('n',),
    'date_range': ('start_date', 'end_date')
}

###
# Kwargs for NBPClient
###
client_kwargs = [
    {
        'currency_code': currency,
        'as_float': as_float,
        'suppress_errors': suppress_errors
    }
    for currency in currencies
    for as_float in (False, True)
    for suppress_errors in (False, True)
]

@pytest.mark.parametrize('kwargs', client_kwargs)
def test_converter_basic(kwargs):
    """Basic NBPClient initialization check."""
    from nbpy import NBPClient
    converter = NBPClient(**kwargs)

    assert converter.currency_code == kwargs['currency_code']
    assert converter.as_float == kwargs['as_float']
    assert converter.suppress_errors == kwargs['suppress_errors']


@pytest.fixture(params=client_kwargs)
def converter(request):
    """NBPClient object."""
    from nbpy import NBPClient
    return NBPClient(**request.param)


def register_response(url, status_code, json_data=None):
    """Register fake response."""
    response_kwargs = {
        'method': 'GET',
        'url': url,
        'status': status_code,
        'content_type': 'application/json'
    }

    if status_code == 200:
        response = responses.Response(json=json_data, **response_kwargs)
    else:
        response = responses.Response(**response_kwargs)
    responses.add(response)


@pytest.mark.parametrize("bid_ask,status_code",
                         [(bid_ask, status_code)
                          for bid_ask in (False, True)   
                          for status_code in (200, 400, 404)])
@responses.activate
def test_calls(converter, bid_ask, status_code):
    """Test NBPClient API calls."""
    from nbpy.errors import BidAskUnavailable, APIError

    currency = currencies[converter.currency_code]

    # Mock helpers
    http_address = MockHTTPAddress(currency, bid_ask)
    json_data = MockJSONData(currency, bid_ask)

    # Values used in test
    request_data = {
        'n': 5,                              # for last()
        'date': datetime(2017, 10, 15),      # for date()
        'start_date': datetime(2017, 10, 1), # for date_range()
        'end_date': datetime(2017, 10, 14),  # for date_range()
    }

    # Clear existing responses
    responses.reset()

    # Should bid/ask calls fail
    bid_ask_should_fail = (bid_ask and 'C' not in currency.tables)

    for call, args in calls_to_test.items():
        # URI and JSON data
        url = getattr(http_address, call)(**request_data)
        json = getattr(json_data, call)(**request_data)

        # Call and arguments
        test_call = getattr(converter, call)
        args = [
            request_data[arg].strftime("%Y-%m-%d") # required for NBPClient
            if isinstance(request_data[arg], datetime)
            else request_data[arg]
            for arg in args
        ]

        # Register necessary response
        register_response(url, status_code, json)

        # HTTP Error subtest
        def test_http_error(exception_cls):
            if converter.suppress_errors:
                # Exceptions suppressed
                assert test_call(*args, bid_ask=bid_ask) is None
            else:
                with pytest.raises(exception_cls):
                    test_call(*args, bid_ask=bid_ask)

        if status_code != 200:
            # HTTP Errors
            if bid_ask_should_fail:
                test_http_error(BidAskUnavailable)
            else:
                test_http_error(APIError)

        elif bid_ask_should_fail:
            # HTTP OK, but bid/ask call should fail for currency
            test_http_error(BidAskUnavailable)

        else:
            # All should be fine
            result = test_call(*args, bid_ask=bid_ask)
            _test_call_result(
                result, currency,
                bid_ask=bid_ask,
                as_float=converter.as_float
            )


def _test_call_result(result, currency, **kwargs):
    """Test call result."""
    if isinstance(result, Sequence):
        for exchange_rate in result:
            # Test for each exchange rate
            _test_call_result(exchange_rate, currency, **kwargs)

    else:
        from nbpy.exchange_rate import NBPExchangeRate

        bid_ask = kwargs.get('bid_ask')
        as_float = kwargs.get('as_float')

        assert isinstance(result, NBPExchangeRate)
        assert result.currency_code == currency.code
        assert result.currency_name == currency.name

        # Check mid, bid and ask
        if as_float:
            rates_cls = float
        else:
            rates_cls = Decimal

        if bid_ask:
            assert isinstance(result.bid, rates_cls)
            assert isinstance(result.ask, rates_cls)
        else:
            assert isinstance(result.mid, rates_cls)