#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Some shared code"""

BITLY_URL = "http://bit.ly/"


def get_hash(bitly_url):
    """Return 'Wozuff' from a link like 'http://bit.ly/Wozuff'"""
    assert bitly_url.startswith(BITLY_URL)
    hsh = bitly_url[len(BITLY_URL):]
    if hsh.endswith("/"):
        hsh = hsh[:-1]
    return hsh


def make_bitly_url(hsh):
    """Convert 'Wozuff' into 'http://bit.ly/Wozuff'"""
    return BITLY_URL + hsh
