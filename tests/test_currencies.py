"""Tests for nbpy.currencies submodule."""

import pytest


@pytest.fixture(scope='module')
def data():
    """Data used to initialize NBPCurrency object."""
    return {
        'code': 'TST',
        'name': 'Test currency',
        'tables': ('A', 'B', 'C', 'C')
    }

@pytest.fixture(scope='module')
def currency(data):
    """NBPCurrency object."""
    from nbpy.currencies import NBPCurrency
    return NBPCurrency(**data)

def test_init_code(data, currency):
    assert currency.code == data['code']

def test_init_name(data, currency):
    assert currency.name == data['name']

def test_init_tables(data, currency):
    assert tuple(currency.tables) == tuple(set(data['tables']))


@pytest.fixture(scope='module')
def currencies():
    """List of all available currencies."""
    from nbpy.currencies import currencies
    return currencies

def test_currencies_types(currencies):
    from nbpy.currencies import NBPCurrency

    for code, currency in currencies.items():
        assert isinstance(code, str)
        assert isinstance(currency, NBPCurrency)

def test_currencies_codes(currencies):
    from nbpy.currencies import NBPCurrency

    for code, currency in currencies.items():
        assert code == currency.code

def test_currencies_tables(currencies):
    from nbpy.currencies import NBPCurrency

    for currency in currencies.values():
        for table in currency.tables:
            assert table in ('A', 'B', 'C')