"""Defines NBPCurrencyExchangeRate class."""

from datetime import datetime
from nbpy.errors import UnknownCurrencyCode
from nbpy.currencies import currencies
from nbpy.utils import validate_date


__all__ = ('NBPExchangeRate',)


class NBPExchangeRate(object):
    """Holds information about exchange rates for given currency and day."""

    def __init__(self, currency_code, date, **kwargs):
        r"""
        Initialize for currency code, date and avg (mid) value.

        :param currency_code:
            Valid currency code (i.e. defined in nbpy.currencies.currencies).

        :param date:
            ``datetime.datetime`` object or properly formatted date string
            (``YYYY-MM-DD``).

        :param \**kwargs:
            See below.

        :Keyword Arguments:
            * *mid* (``decimal.Decimal`` or ``float``) --
              Average exchange rate for ``date``. Ignored if both ``bid`` and
              ``ask`` are given.
            * *bid* (``decimal.Decimal`` or ``float``) --
              Bid exchange rate for ``date``. If given, ``ask`` is also required.
            * *ask* (``decimal.Decimal`` or ``float``) --
              Ask exchange rate for ``date``. If given, ``bid`` is also required.
        """
        self.currency_code = currency_code
        self.date = date

        if 'bid' in kwargs and 'ask' in kwargs:
            self.bid = kwargs.get('bid')
            self.ask = kwargs.get('ask')
        else:
            self.mid = kwargs.get('mid')

    def __repr__(self):
        """Return repr(self)."""
        try:
            return "{cls_name}({code}->PLN, {date}, bid={bid}, ask={ask})".format(
                cls_name=self.__class__.__name__,
                code=self.currency_code,
                date=self.date.strftime('%Y-%m-%d'),
                bid=self.bid,
                ask=self.ask
            )
        except AttributeError:
            return "{cls_name}({code}->PLN, {date}, mid={mid})".format(
                cls_name=self.__class__.__name__,
                code=self.currency_code,
                date=self.date.strftime('%Y-%m-%d'),
                mid=self.mid
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
    def currency_name(self):
        """Full currency name."""
        return currencies[self.currency_code].name

    @property
    def date(self):
        """Datetime object."""
        return self._date

    @date.setter
    def date(self, date):
        validate_date(date)

        if isinstance(date, datetime):
            self._date = date
        else:
            self._date = datetime.strptime(date, "%Y-%m-%d")

    def __call__(self, amount):
        """Convert amount in chosen currency to PLN."""
        try:
            return {
                'bid': self.bid * amount,
                'ask': self.ask * amount,
                'mid': self.mid * amount,
            }
        except AttributeError:
            return {
                'mid': self.mid * amount,
            }

    def __mul__(self, amount):
        """Convert amount in chosen currency to PLN."""
        return self(amount)

    def __rmul__(self, amount):
        """Convert amount in chosen currency to PLN."""
        return self(amount)
