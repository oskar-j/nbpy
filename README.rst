NPBy
====

This is a fork of the tool made by [kuszaj/nbpy](https://github.com/kuszaj/nbpy), I added a http(s) proxy connectivity.

A utility package for calling `NBP (Polish National Bank) Web API <http://api.nbp.pl/en.html>`_ and converting various currencies to Polish zloty using its exchange rates.

NBPy requires Python 3.3 or newer

Installation
------------

From source code:

.. code:: shell

    $ pip install git+https://github.com/oskar-j/nbpy


Usage
-----

NBPy provides a ``NBPClient`` class for generating API callers, given available currency code:

.. code:: python

    >>> import nbpy
    >>> #: Available currencies
    >>> nbpy.currencies
    {'EUR': NBPCurrency(Euro, code=EUR, tables={'A', 'C'}), 'USD': NBPCurrency(United States dollar, code=USD, tables={'A', 'C'}), ...}
    >>> nbp = nbpy.NBPClient('eur')
    >>> nbp
    NBPClient(USD, as_float=False, suppress_errors=False, cache_size=128)
    >>> nbp.currency_code = 'EUR'
    >>> nbp
    NBPClient(EUR, as_float=False, suppress_errors=False, cache_size=128)

``currency_code`` has to be one of the available codes from ``nbpy.currencies`` otherwise ``NBPClient`` raises ``UnknownCurrencyCode``.

.. code:: python

    >>> from nbpy.errors import UnknownCurrencyCode
    >>> 'XYZ' in nbpy.currencies
    False
    >>> try:
    ...     nbp.currency_code = 'XYZ'
    ... except UnknownCurrencyCode:
    ...     print('XYZ is unknown')
    ...
    XYZ is unknown

API calls
~~~~~~~~~

All API calls defined in ``NBPClient`` returns either a ``NBPExchangeRate`` object or a list its instances.

``.current()`` returns current exchange rate for currency. Note that it doesn't necessarily mean current day: for weekends, holidays and before official announcements by Polish National Bank method returns last available value.

.. code:: python

    >>> nbp.current()
    NBPExchangeRate(EUR->PLN, 2017-10-31, mid=4.2498)
    >>> #: Calling NBPClient object is synonymous with current()
    >>> nbp()
    NBPExchangeRate(EUR->PLN, 2017-10-31, mid=4.2498)

``.today()`` returns exchange rate for current day, if available.
Otherwise, raises ``APIError``.

.. code:: python

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

``.date(date)`` returns exchange rate for given day, if available. Otherwise, raises ``APIError``. Argument ``date`` has to be either ``datetime.datetime`` or a properly formatted date string (``YYYY-MM-DD``), otherwise method raises ``DateFormattingError``.

.. code:: python

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

``.last(n)`` returns last ``n`` available exchange rates, ordered by date in ascending order.

.. code:: python

    >>> nbp.last(3)
    [NBPExchangeRate(EUR->PLN, 2017-10-27, mid=4.2520),
     NBPExchangeRate(EUR->PLN, 2017-10-30, mid=4.2403),
     NBPExchangeRate(EUR->PLN, 2017-10-31, mid=4.2498)]

``.date_range(start_date, end_date)`` returns exchange rates for given date range ``[start_date, end_date]``, ordered by date in ascending order. Both arguments are restricted in the same way as ``date`` for ``date()`` method.

If range covers more than 93 days, method raises ``APIError``.

.. code:: python

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

Bid/ask rates
^^^^^^^^^^^^^

By default all API call methods return average exchange rate (``mid``). However, by passing ``bid_ask=True`` you can additionally get bid/ask values. Not that not every currency has them available: for such case ``bid_ask`` is ignored.

.. code:: python

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

Suppressing errors
~~~~~~~~~~~~~~~~~~

If you want API calls to always return something, despite possible issues with API, you can pass ``suppress_errors=True`` to ``NBPClient``. With this flag turned on API calls instead of raising ``BidAskUnavailable`` and ``APIError`` exceptions will return ``None``.

.. code:: python

    >>> from nbp.errors import APIError
    >>> try:
    ...     nbp.date_range('2017-01-01', '2017-06-01')
    ... except APIError:
    ...     print('Invalid date range')
    ...
    Invalid date range
    >>> nbp.suppress_errors = True
    >>> print(nbp.date_range('2017-01-01', '2017-06-01'))
    None

Cache size
~~~~~~~~~~

For efficiency, ``NBPClient`` utilizes LRU cache for by saving last 128 calls. You can change this value by passing ``cache_size`` to ``NBPClient``. This value can be set only during object initialization.

.. code:: python

    >>> nbp = NBPClient('eur', cache_size=64)
    >>> nbp
    NBPClient(EUR, as_float=False, suppress_errors=False, cache_size=64)
    >>> try:
    ...     nbp.cache_size = 128
    ... except AttributeError:
    ...     print("Can't overwrite cache_size")
    ...
    Can't overwrite cache_size

Rates as floats
~~~~~~~~~~~~~~~

By default all exchange rates are parsed as ``decimal.Decimal`` objects. You can change this behaviour by passing ``as_float=True``, which will force all exchange rates to be parsed as ``float``.

.. code:: python

    >>> nbp = NBPClient('eur')
    >>> type(nbp().mid)
    <class 'decimal.Decimal'>
    >>> nbp = NBPClient('eur', as_float=True)
    >>> type(nbp().mid)
    <class 'float'>

Exchange rates
--------------

``NBPClient`` calls returns an ``NBPExchangeRate`` object (their list), which can be used as a converter for calculating given amount in foreign currency to Polish zlotys.

.. code:: python

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

Example
-------

Below script prints and summarises a list of invoices in foreign currencies.

.. code:: python

    from datetime import datetime, timedelta
    from decimal import Decimal
    from nbpy import NBPClient
    from nbpy.errors import APIError


    class Invoice(object):
        """Invoice class with builtin currency converter."""

        def __init__(self, currency_code, date, amount):
            self.currency_code = currency_code
            self.date = date
            self.amount = Decimal("{:.2f}".format(amount))

            self._nbp = NBPClient(currency_code)

        @property
        def amount_in_pln(self):
            exchange_rate = None
            date = datetime.strptime(self.date, '%Y-%m-%d')
            while exchange_rate is None:
                # Get exchange rates until valid is found
                try:
                    exchange_rate = self._nbp.date(date.strftime('%Y-%m-%d'))
                    break
                except APIError:
                    date -= timedelta(days=1)

            amount = (exchange_rate * self.amount)['mid']
            return round(amount, 2)


    # List of invoices in foreign currencies
    invoices = [
        Invoice('EUR', '2017-10-03', 650.0),
        Invoice('EUR', '2017-10-06', 890.0),
        Invoice('USD', '2017-10-11', 1230.0),
    ]

    # Print all amounts in their currencies and PLN
    template = "{currency}    {amount:7.2f}  {amount_in_pln:7.2f}"
    for invoice in invoices:
        print(template.format(
            currency=invoice.currency_code,
            amount=invoice.amount,
            amount_in_pln=invoice.amount_in_pln,
        ))

    # Sum all values in PLN
    # Since amount_in_pln were already called, script will use cached values
    # instead of calling NBP Web API
    sum_amount_in_pln = sum([invoice.amount_in_pln for invoice in invoices])

    print("-" * 23)
    print("        total: {sum:8.2f}".format(sum=sum_amount_in_pln))

    # EUR     650.00  2801.82
    # EUR     890.00  3830.74
    # USD    1230.00  4454.94
    # -----------------------
    #         total: 11087.50

License
-------

`MIT <LICENSE>`_