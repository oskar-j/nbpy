"""Various utilities."""

from datetime import datetime
from functools import wraps
from collections import Sequence
from nbpy.errors import DateFormattingError


def validate_date(date):
    """Check if date is datetime or properly formatted string (YYYY-MM-DD)."""
    if not isinstance(date, datetime):
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except:
            raise DateFormattingError(
                "{} not properly formatted date (YYYY-MM-DD)".format(date)
            )


def first_if_sequence(func):
    """If func's result is a sequence, return only first element."""
    @wraps(func)
    def first(cls, *args, **kwargs):
        result = func(cls, *args, **kwargs)
        if isinstance(result, Sequence):
            return result[0]
        return result
    return first
