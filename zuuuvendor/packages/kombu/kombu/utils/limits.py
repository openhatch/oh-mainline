"""
kombu.utils.limits
==================

Token bucket implementation for rate limiting.

"""
from __future__ import absolute_import

from kombu.five import monotonic

__all__ = ['TokenBucket']


class TokenBucket(object):
    """Token Bucket Algorithm.

    See http://en.wikipedia.org/wiki/Token_Bucket
    Most of this code was stolen from an entry in the ASPN Python Cookbook:
    http://code.activestate.com/recipes/511490/

    .. admonition:: Thread safety

        This implementation may not be thread safe.

    """

    #: The rate in tokens/second that the bucket will be refilled.
    fill_rate = None

    #: Maximum number of tokens in the bucket.
    capacity = 1

    #: Timestamp of the last time a token was taken out of the bucket.
    timestamp = None

    def __init__(self, fill_rate, capacity=1):
        self.capacity = float(capacity)
        self._tokens = capacity
        self.fill_rate = float(fill_rate)
        self.timestamp = monotonic()

    def can_consume(self, tokens=1):
        """Return :const:`True` if the number of tokens can be consumed
        from the bucket."""
        if tokens <= self._get_tokens():
            self._tokens -= tokens
            return True
        return False

    def expected_time(self, tokens=1):
        """Return the time (in seconds) when a new token is expected
        to be available.

        This will also consume a token from the bucket.

        """
        _tokens = self._get_tokens()
        tokens = max(tokens, _tokens)
        return (tokens - _tokens) / self.fill_rate

    def _get_tokens(self):
        if self._tokens < self.capacity:
            now = monotonic()
            delta = self.fill_rate * (now - self.timestamp)
            self._tokens = min(self.capacity, self._tokens + delta)
            self.timestamp = now
        return self._tokens
