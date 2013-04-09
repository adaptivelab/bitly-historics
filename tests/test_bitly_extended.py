#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a py.test script

NOTE this script contains some extra tests developed by Ian Ozsvald to check if the extended functionality
that we need is supported

Example usage on Unix:
bitly-api-python $ nosetests
or 'export' the two environment variables prior to running nosetests
"""
import sys
sys.path.append('../')
import unittest
import datetime
from config import BITLY_ACCESS_TOKEN
import bitly_api_extended
import fixtures


class Test(unittest.TestCase):
    def setUp(self):
        """Create a Connection base on username and access token credentials"""
        access_token = BITLY_ACCESS_TOKEN
        self.bitly = bitly_api_extended.get_bitly_connection(access_token=access_token)

    def testClicksByDay(self):
        """Test the default clicks_by_day provided by the bitly_api"""
        hsh = "UV5wy8"
        data = self.bitly.clicks_by_day(hsh)
        assert data is not None
        assert len(data) == 1

    def testClicksBy30Day(self):
        """Test the monkeypatched days= parameter (in bitly_api_extended)"""
        hsh = "UV5wy8"
        data = self.bitly.clicks_by_day(hsh, days=30)
        assert data is not None
        assert len(data) == 1

    def testLinkClicksDaily(self):
        """Test bitly's original v3/link/clicks method"""
        link = "http://bitly.com/UV5wy8"
        result = self.bitly.link_clicks(link=link, rollup=False, unit="day")
        # we *expect* to get a set of results but it is always possible that
        # bitly has reset the data for this link. To verify manually visit:
        # http://bitly.com/UV5wy8+ to see their web stats panel (it should show
        # a spike of data around late November 2012 for a week, then very low
        # numbers)
        self.assertTrue(len(result) > 0, len(result))
        # we expect that result looks like:
        # [{u'clicks': 1, u'dt': 1362456000},
        # {u'clicks': 2, u'dt': 1358395200}, ...]
        res0 = result[0]
        self.assertIsInstance(res0['clicks'], int)
        self.assertIsInstance(res0['dt'], int)
        # extract the timestamp, confirm that it is a date
        dt = datetime.datetime.fromtimestamp(res0['dt'])
        # it really ought to be 2012 otherwise something odd is happening in
        # their data
        self.assertTrue(dt.year > 2010, dt)

        # now repeat the same test using fixture data (based on a portion of
        # results from the above URL)
        result = fixtures.link_clicks0
        self.assertTrue(len(result) > 0, len(result))
        res0 = result[0]
        self.assertIsInstance(res0['clicks'], int)
        self.assertIsInstance(res0['dt'], int)
        dt = datetime.datetime.fromtimestamp(res0['dt'])
        self.assertTrue(dt.year > 2010, dt)
