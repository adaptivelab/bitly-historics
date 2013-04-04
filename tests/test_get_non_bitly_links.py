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
        all_urls_result = ([u'http://bbc.in/WOYkWi'], set([(u'WOYkWi', u'bbc.co.uk')]))
        matched_hashes = get_non_bitly_links.extract_bitly_hashes(all_urls_result[0], get_non_bitly_links.bitly_pseudonym_domain_names)
        expected_result = all_urls_result[1]
        #import pdb; pdb.set_trace()
        self.assertEqual(expected_result, matched_hashes)

        all_urls_result = ([u'http://bbc.in/WOYkWi', u'http://wedonotcare.com'], set([('WOYkWi', 'bbc.co.uk')]))
        matched_hashes = get_non_bitly_links.extract_bitly_hashes(all_urls_result[0], get_non_bitly_links.bitly_pseudonym_domain_names)
        expected_result = all_urls_result[1]
        self.assertEqual(expected_result, matched_hashes)

        all_urls_result = ([u'http://bbc.in/WOYkWi', u'http://asos.to/XXXX', u'http://wedonotcare.com'], set([('WOYkWi', 'bbc.co.uk'), ('XXXX', 'asos.com')]))
        matched_hashes = get_non_bitly_links.extract_bitly_hashes(all_urls_result[0], get_non_bitly_links.bitly_pseudonym_domain_names)
        expected_result = all_urls_result[1]
        self.assertEqual(expected_result, matched_hashes)

    def test_make_bitly_url(self):
        bitly_url = tools.make_bitly_url('abcd')
        self.assertEqual('http://bit.ly/abcd', bitly_url)
