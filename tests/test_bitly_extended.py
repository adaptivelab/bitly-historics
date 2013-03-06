#!/usr/local/bin/python
"""
This is a py.test script

NOTE this script contains some extra tests developed by Ian Ozsvald to check if the extended functionality
that we need is supported

Example usage on Unix:
bitly-api-python $ BITLY_ACCESS_TOKEN=<accesstoken> nosetests
or 'export' the two environment variables prior to running nosetests
"""
import os
import sys
sys.path.append('../')
import bitly_api
import unittest

BITLY_ACCESS_TOKEN = "BITLY_ACCESS_TOKEN"

class Test(unittest.TestCase):
    def setUp(self):
        """Create a Connection base on username and access token credentials"""
        if BITLY_ACCESS_TOKEN not in os.environ:
            raise ValueError("Environment variable '{}' required".format(BITLY_ACCESS_TOKEN))
        access_token = os.getenv(BITLY_ACCESS_TOKEN)
        self.bitly = bitly_api.Connection(access_token=access_token)


    def testClicksByDay(self):
        hsh = "UV5wy8"
        data = self.bitly.clicks_by_day(hsh)
        print data, len(data)
        assert data is not None
        assert len(data) == 1


    def testClicksBy30Day(self):
        hsh = "UV5wy8"
        data = self.bitly.clicks_by_day(hsh, days=30)
        print data, len(data)
        assert data is not None
        assert len(data) == 1

