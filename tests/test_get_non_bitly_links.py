#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
import sys
sys.path.append('../')
import unittest
import get_non_bitly_links
import tools


class Test(unittest.TestCase):
    def setUp(self):
        pass

    def test_extract_bitly_hashes(self):
        """Check we extract the URLs that we expect to match"""
        all_urls_result = ([u'http://bbc.in/WOYkWi'], set(['WOYkWi']))
        matched_hashes = get_non_bitly_links.extract_bitly_hashes(all_urls_result[0], get_non_bitly_links.bitly_pseudonyms)
        expected_result = all_urls_result[1]
        self.assertEqual(expected_result, matched_hashes)

        all_urls_result = ([u'http://bbc.in/WOYkWi', u'http://wedonotcare.com'], set(['WOYkWi']))
        matched_hashes = get_non_bitly_links.extract_bitly_hashes(all_urls_result[0], get_non_bitly_links.bitly_pseudonyms)
        expected_result = all_urls_result[1]
        self.assertEqual(expected_result, matched_hashes)

        all_urls_result = ([u'http://bbc.in/WOYkWi', u'http://asos.to/XXXX', u'http://wedonotcare.com'], set(['WOYkWi', 'XXXX']))
        matched_hashes = get_non_bitly_links.extract_bitly_hashes(all_urls_result[0], get_non_bitly_links.bitly_pseudonyms)
        expected_result = all_urls_result[1]
        self.assertEqual(expected_result, matched_hashes)

    def test_make_bitly_url(self):
        bitly_url = tools.make_bitly_url('abcd')
        self.assertEqual('http://bit.ly/abcd', bitly_url)
