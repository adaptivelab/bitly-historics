#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Gather historic click data from bitly"""
import argparse
import time
from multiprocessing.dummy import Pool
import datetime
from dateutil import parser as dt_parser
import config  # assumes env var BITLY_HISTORICS_CONFIG is configured
from bitly_api import BitlyError
import bitly_api_extended
import tools

# Usage:
# $ BITLY_HISTORICS_CONFIG=production python start_here.py --help
# $ BITLY_HISTORICS_CONFIG=production python start_here.py hello -o bob
# or for dev:
# export BITLY_HISTORICS_CONFIG=production
# $ %run historics.py  # in ipython

# Add or update existing bitly links for asos.com
# $ BITLY_HISTORICS_CONFIG=production python historics.py --a asos.com
# Update click histories for all out of date links
# $ BITLY_HISTORICS_CONFIG=production python historics.py --update-clicks Y

# nbr of thread workers
POOL_SIZE_FOR_BITLY_UPDATES = 10

# bitly api
access_token = config.BITLY_ACCESS_TOKEN
#bitly = bitly_api.Connection(access_token=access_token)
bitly = bitly_api_extended.get_bitly_connection(access_token)

# Bitly API limits
# http://dev.bitly.com/best_practices.html
# max 5 concurrent connections, per-minute and per-hour rate limits


def process_link_clicks_response(response):
    """Given a response from bitly turn the timestamps into datetime objects, return a sorted list of pairs of dt and clicks"""
    sorted_link_clicks = []
    for d in response:
        clicks = d['clicks']
        dt = datetime.datetime.fromtimestamp(d['dt'])
        sorted_link_clicks.append((dt, clicks))
    sorted_link_clicks.sort()
    return sorted_link_clicks


def get_existing_bitly_clicks_for(hsh):
    """Get record from mongo's bitly_clicks for this hash"""
    document = config.mongo_bitly_clicks.find_one({"global_hash": hsh})
    if not document:
        document = {"global_hash": hsh,
                    "clicks": []}
    return document


def store_bitly_clicks_for(document):
    """Given a hash, store the document with its updated clicks"""
    document['updated_at'] = datetime.datetime.utcnow()
    config.mongo_bitly_clicks.save(document)


def add_response_to_document(response, document):
    """Add new clicks to our document, merging with existing clicks"""
    new_clicks = process_link_clicks_response(response)
    existing_clicks = document['clicks']
    # build a dictionary of existing (and possibly outdated) clicks
    clicks_dict = {}
    for dt, clicks in existing_clicks:
        clicks_dict[dt] = clicks
    # merge new clicks into dict
    for dt, clicks in new_clicks:
        clicks_dict[dt] = clicks
    print clicks_dict
    dt_clicks = [(item[0], item[1]) for item in clicks_dict.items()]
    dt_clicks.sort()
    document['clicks'] = dt_clicks


def add_links_raw_to_mongodb(links):
    """Add links to mongodb if not already present"""
    for link in links:
        # we only want to add if record doesn't already exist
        aggregate_link = link['aggregate_link']
        if not config.mongo_bitly_links_raw.find_one({'aggregate_link': aggregate_link}):
            config.mongo_bitly_links_raw.save(link)


def get_link_result(domain):
    """Search for domain (e.g. "asos.com"), get a set of link results, add to mongo"""
    bitly_links_for_this_domain = config.mongo_bitly_links_raw.find({'domain': domain})
    nbr_bitly_links_for_this_domain = bitly_links_for_this_domain.count()
    print "Found {} items that we already track".format(nbr_bitly_links_for_this_domain)
    links_for_site = bitly.search(domain=domain, query="", limit=1000)
    add_links_raw_to_mongodb(links_for_site)
    bitly_links_for_this_domain = config.mongo_bitly_links_raw.find({'domain': domain})
    nbr_bitly_links_for_this_domain_after_update = bitly_links_for_this_domain.count()
    print "Found {} new links for {}".format(nbr_bitly_links_for_this_domain_after_update - nbr_bitly_links_for_this_domain, domain)
    return links_for_site


def get_bitly_links_to_update():
    all_links = config.mongo_bitly_links_raw.find()
    bitly_links_to_update = []
    recent_cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=config.UPDATE_FROM_N_HOURS_AGO)
    for link in all_links:
        aggregate_link = link['aggregate_link']
        global_hash = tools.get_hash(aggregate_link)
        clicks = config.mongo_bitly_clicks.find_one({'global_hash': global_hash})
        updated_at = config.A_LONG_TIME_AGO
        if clicks:
            updated_at = clicks['updated_at']
        if updated_at < recent_cutoff:
            bitly_links_to_update.append(aggregate_link)
    return bitly_links_to_update


def get_popularity_per_day(clicks_by_day_result):
    """Convert clicks_by_day result into [(datetime, nbr_clicks),...]"""
    # THIS WILL BE OBSOLETE
    popularity_per_day = []
    clicks_list = clicks_by_day_result[0].get('clicks', [])
    for click_dict in clicks_list:
        clicks = click_dict["clicks"]  # e.g. 113
        day_start = click_dict["day_start"]  # e.g. 1359003600
        dt = dt_parser.parse(time.asctime(time.gmtime(day_start)))
        popularity_per_day.append((dt, clicks))
    popularity_per_day.sort()
    return popularity_per_day


def add_clicks_to_mongodb(click_response):
    """Add clicks to mongodb if not already present"""
    # THIS WILL BE OBSOLETE
    # create full bitly link (as stored in links from a bitly search)
    global_hash = click_response[0]['global_hash']
    popularity_per_day = get_popularity_per_day(click_response)
    document = config.mongo_bitly_clicks.find_one({"global_hash": global_hash})
    known_clicks = {}
    if document:
        # we have an entry so we append our datetime & click counts
        bitly_clicks = document["clicks"]
        known_clicks = {day_start: clicks for day_start, clicks in bitly_clicks}
        for day_start, nbr_clicks in popularity_per_day:
            known_clicks[day_start] = nbr_clicks
        # turn the dict back into a sorted list
        bitly_clicks = [(day_start, clicks) for day_start, clicks in known_clicks.items()]
        bitly_clicks.sort()
        document["clicks"] = bitly_clicks
    else:
        document = {"global_hash": global_hash,
                    "clicks": popularity_per_day}
    document['updated_at'] = datetime.datetime.utcnow()
    config.mongo_bitly_clicks.save(document)


def _update_bitly_clicks(aggregate_link):
    RATE_LIMIT_SLEEP = 10  # 10 seconds default pause if we get rate limited
    while True:
        try:
            clicks = bitly.clicks_by_day(shortUrl=aggregate_link, days=config.NUMBER_OF_DAYS_DATA_TO_COLLECT)
            print "Updating {}, we have up to {} days of data to add".format(aggregate_link, len(clicks[0]['clicks']))
            add_clicks_to_mongodb(clicks)
            break  # exit the loop as we've successfully fetched from bitly
        except BitlyError as err:
            # rarely we see this error, we catch all bitly errors here
            # and wait and then retry
            #raise BitlyError(data.get('status_code', 500), data.get('status_txt', 'UNKNOWN_ERROR'))
            #bitly_api.bitly_api.BitlyError: INTERNAL_ERROR
            #(Pdb++) err.message
            #u'INTERNAL_ERROR'
            #(Pdb++) err.code
            #502
            if err.code == 502:
                # IGNORING ERROR for http://bit.ly/VFPCJr:BitlyError(u'RATE_LIMIT_EXCEEDED',)
                print "IGNORING ERROR for {}:{}".format(aggregate_link, repr(err))
                time.sleep(0.1)  # pause for a moment and then we retry
                print "Retrying..."
            else:
                if err.code == 403:
                    # err.message u'RATE_LIMIT_EXCEEDED'
                    print "Sleeping for {} due to code 403 {}".format(RATE_LIMIT_SLEEP, err.message)
                    time.sleep(RATE_LIMIT_SLEEP)  # wait a bit, try again
                    RATE_LIMIT_SLEEP = RATE_LIMIT_SLEEP * 2  # double our wait time
                    RATE_LIMIT_SLEEP = min(RATE_LIMIT_SLEEP, 30 * 60)  # max of 30 mins
                else:
                    # what other errors have we encountered?
                    print "UNKNOWN ERROR:", repr(err)
                    #import pdb; pdb.set_trace()  # is there an error code for over capacity?


def update_bitly_clicks():
    """Update click data for documents that are out of date"""
    bitly_links_to_update = get_bitly_links_to_update()
    # update using a thread pool in parallel
    P = Pool(POOL_SIZE_FOR_BITLY_UPDATES)
    P.map(_update_bitly_clicks, bitly_links_to_update)


def list_domains_we_track():
    """Show list of distinct domains that we track"""
    domains = config.mongo_bitly_links_raw.distinct('domain')
    return domains


def add_entries_to_mongodb(bitly_url, title, canonical_url, domain):
    """Add an entry into mongodb's bitly_links_raw collection"""
    doc = {'url': canonical_url,
           'title': title,
           'domain': domain,
           'aggregate_link': bitly_url}
    config.mongo_bitly_links_raw.save(doc)


def get_title_canonical_url_from(bitly_url):
    result = bitly.link_info(bitly_url)
    # Example result:
    # {u'content_length': 127541, u'category': u'text', u'domain': u'www.bbc.co.uk', u'original_url': u'http://www.bbc.co.uk/news/uk-england-birmingham-21711661#TWEET650950',
    # u'html_title': u"BBC News - Christina Edkins stabbing: Bus passengers 'heard screaming'", u'favicon_url': u'http://www.bbc.co.uk/favicon.ico', u'aggregate_link': u'http://bit.ly/WPg3gl',
    # u'content_type': u'text/html', u'indexed': 1362753138, u'canonical_url': u'http://www.bbc.co.uk/news/uk-england-birmingham-21711661'}
    aggregate_link = result['aggregate_link']
    html_title = result['html_title']
    canonical_url = result['canonical_url']
    domain = result['domain']
    if domain.startswith('www.'):
        # chop off a leading www (the bitly search result does not seem to
        # include www for domains!
        domain = domain[len('www.'):]
    return aggregate_link, html_title, canonical_url, domain


def add_from_file(filename):
    """Read list of bit.ly links from file, add to mongodb"""
    #lines = [row.strip() for row in open(filename).readlines()]
    lines = [row.strip().split(',') for row in open(filename).readlines()]
    for bitly_url, desired_domain in lines:
        aggregate_link, html_title, canonical_url, domain = get_title_canonical_url_from(bitly_url)
        # get the aggregate_url which should be canonical at bitly's end
        if domain == desired_domain:
            existing_document = config.mongo_bitly_links_raw.find_one({'aggregate_link': aggregate_link})
            if not existing_document:
                print aggregate_link, html_title, canonical_url
                print "Adding:", aggregate_link
                add_entries_to_mongodb(aggregate_link, html_title, canonical_url, domain)
            else:
                print "We already seem to have", bitly_url,
                if bitly_url != aggregate_link:
                    print " aggregate_link version", aggregate_link
                else:
                    print
        else:
            print "Ignoring off-topic domain:", domain


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Project description')
    parser.add_argument('--add-domain', '-a', help='Add or update domain e.g. "asos.com"')
    parser.add_argument('--add-from-file', '-f', help="Add bit.ly links from a text file (bypassing bitly.com search) '--add-from-file new_links.txt'")
    parser.add_argument('--update-clicks', '-u', action="store_true", help='Fetch updated click data for all out-of-date bitly links')
    parser.add_argument('--list-domains', '-l', action="store_true", help='List the distinct domains (e.g. ["asos.com", "bbc.co.uk"]) that we track')
    parser.add_argument('--update-everything', '-e', action="store_true", help="Add all new URLs for existing domains and then update click history for all our links")
    args = parser.parse_args()

    if args.add_from_file:
        add_from_file(args.add_from_file)

    if args.add_domain:
        # get list of links for a root site
        links_for_site = get_link_result(args.add_domain)

    if args.update_clicks:
        update_bitly_clicks()

    if args.list_domains:
        domains = list_domains_we_track()
        print "We track:", domains

    if args.update_everything:
        # update in parallel
        domains = list_domains_we_track()
        P = Pool(POOL_SIZE_FOR_BITLY_UPDATES)
        P.map(get_link_result, [str(domain) for domain in domains])
        print "Updating bitly click history for all of our links"
        update_bitly_clicks()
