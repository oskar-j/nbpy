"""Tests for NBPConverter (with mock responses)."""

import pytest
import math
import random
import responses
from datetime import datetime, timedelta
from decimal import Decimal
from collections import Sequence
from nbpy import BASE_URI


# Test currency codes
test_currency_codes = ('EUR', 'HRK', 'GYD')

# Kwargs for NBPConverter
converter_kwargs = [
    {
        'currency_code': currency_code,
        'as_float': as_float,
        'suppress_api_errors': suppress_api_errors
    }
    for currency_code in test_currency_codes
    for as_float in (False, True)
    for suppress_api_errors in (False, True)
]

def _converter(**kwargs):
    from nbpy import NBPConverter
    return NBPConverter(**kwargs)

@pytest.mark.parametrize('kwargs', converter_kwargs)
def test_converter_basic(kwargs):
    converter = _converter(**kwargs)

    assert converter.currency_code == kwargs['currency_code']
    assert converter.as_float == kwargs['as_float']
    assert converter.suppress_api_errors == kwargs['suppress_api_errors']

@pytest.fixture(params=converter_kwargs)
def converter(request):
    """NBPConverter object."""
    return _converter(**request.param)


class MockJSONData(object):
    """Helper class for creating mock JSON data."""

    def __init__(self, table, currency_obj, tail):
        self.table = table.upper()
        self.currency = currency_obj
        self.uri = BASE_URI + '/exchangerates/rates/{}/{}/{}'.format(
            self.table.lower(), self.currency.code.lower(), tail
        )

    def source_id(self, date):
        return "{count}/{table}/NBP/{year}".format(
            count=random.randint(1, 365),
            table=self.table,
            year=date.year
        )

    def rate_value(self):
        return round(random.uniform(0.0, 5.0), 5)

    def rate(self, date):
        rate = {
            "no": self.source_id(date),
            "effectiveDate": date.strftime("%Y-%m-%d"),
        }

        if self.table == 'C':
            rate = dict(rate, **{
                "bid": self.rate_value(),
                "ask": self.rate_value(),
            })
        else:
            rate = dict(rate, **{
                "mid": self.rate_value(),
            })

        return rate

    @staticmethod
    def _date_range(date, end_date):
        while date <= end_date:
            yield date
            date += timedelta(days=1)

    def data(self, start_date, end_date=None):
        if not end_date:
            end_date = start_date
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        rates = [
            self.rate(date)
            for date in self._date_range(start_date, end_date)
        ]

        return {
            'table': self.table,
            'currency': self.currency.name,
            'code': self.currency.code,
            'rates': rates
        }


def _prepare_responses(**kwargs):
    """
    Prepare responses for given currency, date and resource.

    Returns generated currency rates (for future comparison).
    """
    currency = kwargs.get('currency')
    date = kwargs.get('date')
    resource = kwargs.get('resource')
    as_float = kwargs.get('as_float', False)
    status_code = kwargs.get('status_code', 200)

    # Clear existing responses
    responses.reset()

    for table in currency.tables:
        # Create mock data
        mock = MockJSONData(table, currency, resource)

        if status_code == 200:
            responses.add(
                responses.Response(
                    method='GET', url=mock.uri,
                    json=mock.data(date), status=status_code,
                    content_type='application/json'
                )
            )
        else:
            responses.add(
                responses.Response(
                    method='GET', url=mock.uri,
                    status=status_code,
                    content_type='application/json'
                )
            )

def _test_exchange_rate_single(exchange_rate, **kwargs):
    """Perform checks for NBPExchangeRate object."""
    from nbpy.exchange_rate import NBPExchangeRate

    currency = kwargs.get('currency')
    date = kwargs.get('date')
    all_values = kwargs.get('all_values', False)
    as_float = kwargs.get('as_float', False)

    # Basic checks
    assert isinstance(exchange_rate, NBPExchangeRate)
    assert exchange_rate.currency_code == currency.code
    assert exchange_rate.currency_name == currency.name
    assert exchange_rate.date == datetime.strptime(date, '%Y-%m-%d')

    # Check mid, bid and ask
    if as_float:
        rates_cls = float
    else:
        rates_cls = Decimal

    assert isinstance(exchange_rate.mid, rates_cls)

    if all_values and 'C' in currency.tables:
        assert isinstance(exchange_rate.bid, rates_cls)
        assert isinstance(exchange_rate.ask, rates_cls)

    if not all_values and 'C' in currency.tables:
        # Check if bid and ask not set
        with pytest.raises(AttributeError):
            exchange_rate.bid
        with pytest.raises(AttributeError):
            exchange_rate.ask

def _test_exchange_rate(exchange_rate, **kwargs):
    """Perform checks for NBPExchangeRate object or their sequence."""
    if isinstance(exchange_rate, Sequence):
        for er in exchange_rate:
            _test_exchange_rate_single(er, **kwargs)
    else:
        _test_exchange_rate_single(exchange_rate, **kwargs)

@pytest.mark.parametrize("all_values", (False, True))
@responses.activate
def test_current(converter, all_values):
    from nbpy.currencies import currencies

    # Setup
    kwargs = {
        'currency': currencies[converter.currency_code],
        'date': datetime.today().strftime('%Y-%m-%d'),
        'resource': '',
        'all_values': all_values,
        'as_float': converter.as_float,
        'status_code': 200,
    }

    _prepare_responses(**kwargs)
    exchange_rate = converter.current(all_values=all_values)
    _test_exchange_rate(exchange_rate, **kwargs)

@pytest.mark.parametrize("all_values,status_code",
                         [(all_values, status_code)
                          for all_values in (False, True)   
                          for status_code in (200, 400, 404)])
@responses.activate
def test_today(converter, all_values, status_code):
    from nbpy.currencies import currencies
    from nbpy.errors import APIError

    # Setup
    kwargs = {
        'currency': currencies[converter.currency_code],
        'date': datetime.today().strftime('%Y-%m-%d'),
        'resource': 'today',
        'all_values': all_values,
        'as_float': converter.as_float,
        'status_code': status_code,
    }

    _prepare_responses(**kwargs)

    if status_code == 200:
        exchange_rate = converter.today(all_values=all_values)
        _test_exchange_rate(exchange_rate, **kwargs)
    elif converter.suppress_api_errors:
        exchange_rate = converter.today(all_values=all_values)
        assert exchange_rate is None
    else:
        with pytest.raises(APIError):
            exchange_rate = converter.today(all_values=all_values)