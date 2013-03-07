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
from config import BITLY_ACCESS_TOKEN
import bitly_api_extended


class Test(unittest.TestCase):
    def setUp(self):
        """Create a Connection base on username and access token credentials"""
        access_token = BITLY_ACCESS_TOKEN
        self.bitly = bitly_api_extended.get_bitly_connection(access_token=access_token)

    def testClicksByDay(self):
        """Test the default clicks_by_day provided by the bitly_api"""
        hsh = "UV5wy8"
        data = self.bitly.clicks_by_day(hsh)
        print data, len(data)
        assert data is not None
        assert len(data) == 1

    def testClicksBy30Day(self):
        """Test the monkeypatched days= parameter (in bitly_api_extended)"""
        hsh = "UV5wy8"
        data = self.bitly.clicks_by_day(hsh, days=30)
        print data, len(data)
        assert data is not None
        assert len(data) == 1
