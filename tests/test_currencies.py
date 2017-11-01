import pytest


@pytest.fixture(scope='module')
def data():
    return {
        'code': 'TST',
        'name': 'Test currency',
        'tables': ('A', 'B', 'C', 'C')
    }

@pytest.fixture(scope='module')
def currency(data):
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
    from nbpy.currencies import currencies
    return currencies

def test_currencies_types(currencies):
    from nbpy.currencies import NBPCurrency

    for code, currency in currencies.items():
        assert isinstance(code, str)
        assert isinstance(currency, NBPCurrency)