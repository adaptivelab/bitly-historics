#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple extension to bitly_api to allow us to retrieve history by a specified number of days"""
import warnings
import bitly_api
from bitly_api import BitlyError

# The bitly_api provided by bitly is missing an optional paramter from
# clicks_by_day, Ian provided a Pull request in January 2013:
# https://github.com/bitly/bitly-api-python/pull/14
# which hasn't been merged, we need this extra days= parameter to enable
# histories of more than 7 days. This monkey patch solution will be used until
# either the Pull request is accepted by bitly or until the API is deprecated.
# In January an investigation into the bitly API suggested that we cannot get a
# 30 day history daily click rate using their new API calls, hence the need to
# use their deprecated older API call.

# This monkeypatching can be removed if this missing parameter is added to a
# later version of the bitly_api or if the new API provides the functionality
# that we need.

# This monkeypatching is tested by:
# tests/test_bitly_extended.py


def _clicks_by_day(self, hash=None, shortUrl=None, days=None):
    """ given a bitly url or hash, get a time series of clicks
    per day for the last 30 days in reverse chronological order
    (most recent to least recent) """
    warnings.warn("/v3/clicks_by_day is depricated in favor of /v3/link/clicks?unit=day", DeprecationWarning)
    if not hash and not shortUrl:
        raise BitlyError(500, 'MISSING_ARG_SHORTURL')
    params = dict()
    if hash:
        params['hash'] = hash
    if shortUrl:
        params['shortUrl'] = shortUrl
    if days:
        params['days'] = str(days)

    data = self._call(self.host, 'v3/clicks_by_day', params, self.secret)
    return data['data']['clicks_by_day']


def get_bitly_connection(access_token):
    """Get monkeypatched bitly_api connection"""
    bitly_api.Connection.clicks_by_day = _clicks_by_day
    bitly = bitly_api.Connection(access_token=access_token)
    return bitly
