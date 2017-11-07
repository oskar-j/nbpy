"""Mock API helper classes."""

import random
from datetime import datetime, timedelta
from functools import wraps
from nbpy import BASE_URI
from nbpy.currencies import NBPCurrency


class MockAPIHelperError(Exception):
    """Exception for HelperError class."""
    pass


class MockAPIHelper(object):
    """Base helper class for full mock API calls."""
    def __init__(self, currency, bid_ask=False):
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