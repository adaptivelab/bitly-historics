#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Get bitly-like (but not bitly.com) links, convert to bitly equivalents and output in a file"""
import argparse
import sys
from ttp import ttp
import twitter
import requests
import tools
import config

MAX_NBR_TWEETS_TO_FETCH = 200

api = twitter.Api(consumer_key=config.CONSUMER_KEY,
                  consumer_secret=config.CONSUMER_SECRET,
                  access_token_key=config.ACCESS_TOKEN_KEY,
                  access_token_secret=config.ACCESS_TOKEN_SECRET)

tweet_parser = ttp.Parser()

bitly_pseudonym_domain_names = {'bbc.in': 'bbc.co.uk',
                                'asos.to': 'asos.com'}
#bitly_pseudonyms = set(["http://" + domain for domain in bitly_pseudonym_domain_names.keys()])


def get_urls_and_all_redirects(tweet_text):
    """Given a tweet get any t.co URLs, visit all, build list of all redirected URLs"""
    res = tweet_parser.parse(tweet_text)
    all_urls = set()
    for url in res.urls:
        all_urls.add(url)
        request_result = requests.get(url)
        redirect_history = request_result.history
        # history might look like:
        # (<Response [301]>, <Response [301]>)
        # where each response object has a URL, in the above example they are:
        # u'http://t.co/8o0z9BbEMu', u'http://bbc.in/16dClPF'
        for redirect in redirect_history:
            all_urls.add(redirect.url)
    return all_urls


def extract_bitly_hashes(all_urls, bitly_pseudonym_domain_names):
    """Turn all_urls like [u'http://bbc.in/WOYkWi'] into a set of hashes like set([u"WOYkWi"])"""
    matched_hashes = set()
    for url in all_urls:
        for bitly_pseudonym_raw, target_domain_name in bitly_pseudonym_domain_names.items():
            bitly_pseudonym = "http://" + bitly_pseudonym_raw
            if url.startswith(bitly_pseudonym):
                hsh = url[len(bitly_pseudonym) + 1:]
                hsh = hsh.strip('/')  # remove a trailing / if present
                matched_hashes.add((hsh, target_domain_name))
    return matched_hashes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Project description')
    parser.add_argument('--screen_names', '-s', nargs='*', help="Get all bitly-like links from named screen_names e.g. '--screen_names BBCNews BBCBreaking'")
    parser.add_argument('--number_tweets', '-n', default=MAX_NBR_TWEETS_TO_FETCH, help="Number of tweets to fetch (default is %d)" % (MAX_NBR_TWEETS_TO_FETCH))
    parser.add_argument('--output', '-o', default=None, help="Filename for output e.g. '--output new_links.txt'")
    args = parser.parse_args()
    print args

    if args.screen_names:
        discovered_bitly_urls = set()
        for screen_name in args.screen_names:
            if "statuses" not in dir():
                statuses = api.GetUserTimeline(screen_name=screen_name, count=args.number_tweets)
                for status in statuses:
                    all_urls = get_urls_and_all_redirects(status.text)
                    #print all_urls
                    matched_hashes = extract_bitly_hashes(all_urls, bitly_pseudonym_domain_names)
                    discovered_bitly_urls.update([(tools.make_bitly_url(hsh), target_domain_name) for (hsh, target_domain_name) in matched_hashes])

        if args.output:
            f = open(args.output, 'w')
        else:
            f = sys.stdout
        for discovered_url in discovered_bitly_urls:
            f.write(",".join(discovered_url) + "\n")
        if args.output:
            f.close()
