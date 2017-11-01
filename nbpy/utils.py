"""Various utilities."""

from functools import wraps
from collections import Sequence

def first_if_sequence(func):
    """If func's result is a sequence, return only first element."""
    @wraps(func)
    def first(cls, *args, **kwargs):
        result = func(cls, *args, **kwargs)
        if isinstance(result, Sequence):
            return result[0]
        return result
    return first
