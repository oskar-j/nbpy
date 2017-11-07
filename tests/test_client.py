"""Tests for NBPClient (with mock responses)."""

import pytest
import requests
import responses
from collections import Sequence
from datetime import datetime
from decimal import Decimal
from nbpy.currencies import NBPCurrency, currencies
from .mock_api_helpers import MockHTTPAddress, MockJSONData


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