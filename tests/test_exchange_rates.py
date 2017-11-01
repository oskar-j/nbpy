"""Tests for nbpy.exchange_rates submodule."""

import random
import pytest


# Number of random values for mid, bid/ask, bid and ask
rnd_count = 10


@pytest.fixture
def basic_data():
    """Basic (incomplete) data used to initialize NBPExchangeRate objects."""
    return {
        'currency_code': 'USD',
        'date': '2017-01-01',
        'source_id': '1/A/NBP/2017',
    }

@pytest.fixture(params=[random.uniform(0.0, 5.0)
                        for _ in range(rnd_count)])
def mid_data(request, basic_data):
    """Data used to initialize exchange rates, only with mid."""
    from decimal import Decimal
    return dict(basic_data, **{
        'mid': Decimal(round(request.param, 5))
    })

@pytest.fixture(params=[[random.uniform(0.0, 5.0) for __ in range(3)]
                        for _ in range(rnd_count)])
def bid_ask_data(request, basic_data):
    """Data used to initialize exchange rates, with mid, bid and ask."""
    from decimal import Decimal
    return dict(basic_data, **{
        'mid': Decimal(round(request.param[0], 5)),
        'bid': Decimal(round(request.param[1], 5)),
        'ask': Decimal(round(request.param[2], 5)),
    })

@pytest.fixture(params=[[random.uniform(0.0, 5.0) for __ in range(2)]
                        for _ in range(rnd_count)])
def bid_data(request, basic_data):
    """Data used to initialize exchange rates, without ask."""
    from decimal import Decimal
    return dict(basic_data, **{
        'mid': Decimal(round(request.param[0], 5)),
        'bid': Decimal(round(request.param[1], 5)),
    })

@pytest.fixture(params=[[random.uniform(0.0, 5.0) for __ in range(2)]
                        for _ in range(rnd_count)])
def ask_data(request, basic_data):
    """Data used to initialize exchange rates, without bid."""
    from decimal import Decimal
    return dict(basic_data, **{
        'mid': Decimal(round(request.param[0], 5)),
        'ask': Decimal(round(request.param[1], 5)),
    })


def _test_currency_basic(data):
    from datetime import datetime
    from nbpy.exchange_rate import NBPExchangeRate

    exchange_rate = NBPExchangeRate(**data)

    assert exchange_rate.currency_code == data['currency_code']
    assert exchange_rate.source_id == data['source_id']

    assert isinstance(exchange_rate.date, datetime)
    date = datetime.strptime(data['date'], "%Y-%m-%d")
    assert exchange_rate.date == date

    return exchange_rate

def test_currency_mid(mid_data):
    exchange_rate = _test_currency_basic(mid_data)

    assert exchange_rate.mid == mid_data['mid']

    with pytest.raises(AttributeError):
        exchange_rate.ask
    with pytest.raises(AttributeError):
        exchange_rate.bid

def test_currency_bid_ask(bid_ask_data):
    exchange_rate = _test_currency_basic(bid_ask_data)

    assert exchange_rate.mid == bid_ask_data['mid']
    assert exchange_rate.bid == bid_ask_data['bid']
    assert exchange_rate.ask == bid_ask_data['ask']

def test_currency_bid(bid_data):
    exchange_rate = _test_currency_basic(bid_data)

    assert exchange_rate.mid == bid_data['mid']

    with pytest.raises(AttributeError):
        exchange_rate.ask
    with pytest.raises(AttributeError):
        exchange_rate.bid == bid_data['bid']

def test_currency_ask(ask_data):
    exchange_rate = _test_currency_basic(ask_data)

    assert exchange_rate.mid == ask_data['mid']

    with pytest.raises(AttributeError):
        exchange_rate.ask == ask_data['ask']
    with pytest.raises(AttributeError):
        exchange_rate.bid

def test_currency_no_mid(basic_data):
    from nbpy.exchange_rate import NBPExchangeRate

    with pytest.raises(TypeError):
        exchange_rate = NBPExchangeRate(**basic_data)

def test_currency_unknown_code(basic_data):
    from decimal import Decimal
    from nbpy.exchange_rate import NBPExchangeRate
    from nbpy.errors import UnknownCurrencyCode

    basic_data['currency_code'] = 'XXX'
    basic_data['mid'] = Decimal('1.0')

    with pytest.raises(UnknownCurrencyCode):
        exchange_rate = NBPExchangeRate(**basic_data)

def test_currency_date_formatting_error(basic_data):
    from decimal import Decimal
    from nbpy.exchange_rate import NBPExchangeRate
    from nbpy.errors import DateFormattingError

    basic_data['mid'] = Decimal('1.0')

    test_dates = (
        None, '', 'this is not a date',
        '2017-01-40', '2017-15-01'
        '1-2-3-4', '01/02/2017'
    )
    for date in test_dates:
        basic_data['date'] = date
        with pytest.raises(DateFormattingError):
            exchange_rate = NBPExchangeRate(**basic_data)

def _test_currency_converting(data, amount):
    from decimal import Decimal
    from nbpy.exchange_rate import NBPExchangeRate

    exchange_rate = NBPExchangeRate(**data)
    amount = Decimal(round(amount, 5))

    results = (
        exchange_rate(amount),
        exchange_rate * amount,
        amount * exchange_rate,
    )

    for result_1 in results:
        for result_2 in results:
            assert result_1 == result_2

    assert exchange_rate.mid * amount == data['mid'] * amount

    return amount, exchange_rate

@pytest.mark.parametrize('amount',
                         [random.uniform(0.0, 5.0)
                         for _ in range(rnd_count)])
def test_currency_mid_converting(mid_data, amount):
    amount, exchange_rate = _test_currency_converting(mid_data, amount)

    assert 'bid' not in exchange_rate(amount)
    assert 'ask' not in exchange_rate(amount)

@pytest.mark.parametrize('amount',
                         [random.uniform(0.0, 5.0)
                         for _ in range(rnd_count)])
def test_currency_bid_ask_converting(bid_ask_data, amount):
    amount, exchange_rate = _test_currency_converting(bid_ask_data, amount)

    assert exchange_rate(amount)['bid'] == bid_ask_data['bid'] * amount
    assert exchange_rate(amount)['ask'] == bid_ask_data['ask'] * amount

@pytest.mark.parametrize('amount',
                         [random.uniform(0.0, 5.0)
                         for _ in range(rnd_count)])
def test_currency_bid_converting(bid_data, amount):
    amount, exchange_rate = _test_currency_converting(bid_data, amount)

    assert 'bid' not in exchange_rate(amount)
    assert 'ask' not in exchange_rate(amount)

@pytest.mark.parametrize('amount',
                         [random.uniform(0.0, 5.0)
                         for _ in range(rnd_count)])
def test_currency_ask_converting(ask_data, amount):
    amount, exchange_rate = _test_currency_converting(ask_data, amount)

    assert 'bid' not in exchange_rate(amount)
    assert 'ask' not in exchange_rate(amount)