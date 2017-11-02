NPBy
=========

A utility package for calling [NBP (Polish National Bank) Web API](http://api.nbp.pl/en.html) and converting various currencies to Polish zloty using its exchange rates.

NBPy requires Python 3.0 or newer

Usage
------
NBPy provides a ``NBPClient`` class for generating API callers, given available currency code:

```python
>>> import nbpy
>>> #: Available currencies
>>> nbpy.currencies
{'EUR': NBPCurrency(Euro, code=EUR, tables={'A', 'C'}), 'USD': NBPCurrency(United States dollar, code=USD, tables={'A', 'C'}), ...}
>>> nbp = nbpy.NBPClient('eur')
>>> nbp
NBPClient(USD, as_float=False, suppress_api_errors=False, cache_size=128)
>>> nbp.currency_code = 'EUR'
>>> nbp
NBPClient(EUR, as_float=False, suppress_api_errors=False, cache_size=128)
```

``currency_code`` has to be one of the available codes from ``nbpy.currencies`` otherwise ``NBPClient`` returns ``UnknownCurrencyCode``.

```python
>>> from nbpy.errors import UnknownCurrencyCode
>>> 'XYZ' in nbpy.currencies
False
>>> try:
...     nbp.currency_code = 'XYZ'
... except UnknownCurrencyCode:
...     print('XYZ is unknown')
...
XYZ is unknown
```

### API calls
All API calls defined in ``NBPClient`` returns either a ``NBPExchangeRate`` object or a list its instances.

`.current()` returns current exchange rate for currency. Note that it doesn't necessarily mean current day: for weekends, holidays and before official announcements by Polish National Bank method returns last available value.

```python
>>> nbp.current()
NBPExchangeRate(EUR->PLN, 2017-10-31, mid=4.2498)
>>> #: Calling NBPClient object is synonymous with current()
>>> nbp()
NBPExchangeRate(EUR->PLN, 2017-10-31, mid=4.2498)
```

`.today()` returns exchange rate for current day, if available. Otherwise, raises ``APIError``.

```python
>>> nbp.today()
NBPExchangeRate(EUR->PLN, 2017-10-31, mid=4.2498)
...
>>> #: A day later, during national holiday
>>> from nbpy.errors import APIError
>>> try:
...     nbp.today()
... except APIError:
...     print("No data available")
...
No data available
```

`.date(date)` returns exchange rate for given day, if available. Otherwise, raises ``APIError``. Argument ``date`` has to be either ``datetime.datetime`` or a properly formatted date string (``YYYY-MM-DD``), otherwise method raises ``DateFormattingError``.

```python
>>> from nbpy.errors import APIError, DateFormattingError
>>> nbp.date('2017-10-02')
NBPExchangeRate(EUR->PLN, 2017-10-02, mid=4.3137)
>>> try:
...     nbp.date('2017-10-01')
... except APIError:
...     print("No data available for date")
...
No data available for date
>>> try:
...     nbp.date('01/10/17')
... except DateFormattingError:
...     print("Improperly formatted date string")
...
Improperly formatted date string
```

`.last(n)` returns last `n` available exchange rates, ordered by date in ascending order.

```python
>>> nbp.last(3)
[NBPExchangeRate(EUR->PLN, 2017-10-27, mid=4.2520),
 NBPExchangeRate(EUR->PLN, 2017-10-30, mid=4.2403),
 NBPExchangeRate(EUR->PLN, 2017-10-31, mid=4.2498)]
```

`.date_range(start_date, end_date)` returns exchange rates for given date range `[start_date, end_date]`, ordered by date in ascending order. Both arguments are restricted in the same way as `date` for `date()` method.

If range covers more than 93 days, method raises ``APIError``.

```python
>>> from nbp.errors import APIError
>>> nbp.date_range('2017-10-01', '2017-10-14')
[NBPExchangeRate(EUR->PLN, 2017-10-02, mid=4.3137),
 NBPExchangeRate(EUR->PLN, 2017-10-03, mid=4.3105),
 NBPExchangeRate(EUR->PLN, 2017-10-04, mid=4.3025), ...]
>>> try:
...     nbp.date_range('2017-01-01', '2017-06-01')
... except APIError:
...     print('Invalid date range')
...
Invalid date range
```

#### Bid/ask rates
By default all API call methods return average exchange rate (`mid`). However, by passing `bid_ask=True` you can additionally get bid/ask values. Not that not every currency has them available: for such case `bid_ask` is ignored.

```python
>>> nbp()
NBPExchangeRate(EUR->PLN, 2017-10-31, mid=4.2498)
>>> nbp(bid_ask=True)
NBPExchangeRate(EUR->PLN, 2017-11-02, bid=4.2036, ask=4.2886)
>>> #: No bid/ask values for CUP
>>> nbp.currency_code = 'CUP'
>>> nbp()
NBPExchangeRate(CUP->PLN, 2017-10-31, mid=3.6529)
>>> from nbpy.errors import BidAskUnavailable
>>> try:
...     nbp(bid_ask=True)
... except BidAskUnavailable:
...     print('Bid/ask unavailable')
...
Bid/ask unavailable
```

### Suppressing API errors
If you want API calls to always return something, despite possible issues with API, you can pass ``suppress_api_errors=True`` to ``NBPClient``. With this flag turned on API calls instead of raising ``APIError``s will return ``None``.

```python
>>> from nbp.errors import APIError
>>> try:
...     nbp.date_range('2017-01-01', '2017-06-01')
... except APIError:
...     print('Invalid date range')
...
Invalid date range
>>> nbp.suppress_api_errors = True
>>> print(nbp.date_range('2017-01-01', '2017-06-01'))
None
```

### Cache size
For efficiency, ``NBPClient`` utilizes LRU cache for by saving last 128 calls. You can change this value by passing ``cache_size`` to ``NBPClient``. This value can be set only during object initialization.

```python
>>> nbp = NBPClient('eur', cache_size=64)
>>> nbp
NBPClient(EUR, as_float=False, suppress_api_errors=False, cache_size=64)
>>> try:
...     nbp.cache_size = 128
... except AttributeError:
...     print("Can't overwrite cache_size")
...
Can't overwrite cache_size
```

### Rates as floats
By default all exchange rates are parsed as ``decimal.Decimal`` objects. You can change this behaviour by passing ``as_float=True``, which will force all exchange rates to be parsed as ``float``s.

```python
>>> nbp = NBPClient('eur')
>>> type(nbp().mid)
<class 'decimal.Decimal'>
>>> nbp = NBPClient('eur', as_float=True)
>>> type(nbp().mid)
<class 'float'>
```

Exchange rates
--------------
``NBPClient`` calls returns an ``NBPExchangeRate`` object (their list), which can be used as a converter for calculating given amount in foreign currency to Polish zlotys.

```python
>>> exchange_rate = nbp()
>>> exchange_rate
NBPExchangeRate(EUR->PLN, 2017-10-31, mid=4.2498)
>>> amount = 1000
>>> exchange_rate(amount)
{'mid': Decimal('4249.8000')}
>>> exchange_rate * amount
{'mid': Decimal('4249.8000')}
>>> amount * exchange_rate
{'mid': Decimal('4249.8000')}
>>>
>>> exchange_rate = nbp(all_values=True)
>>> exchange_rate
NBPExchangeRate(EUR->PLN, 2017-11-02, bid=4.2036, ask=4.2886)
>>> exchange_rate(amount)
{'bid': Decimal('4204.3000'), 'ask': Decimal('4289.3000')}
```

License
-------
[MIT](LICENSE)