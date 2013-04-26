#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Gather historic click data from bitly"""
from __future__ import division  # 1/2 == 0.5, as in Py3
from __future__ import absolute_import  # avoid hiding global modules with locals
from __future__ import print_function  # force use of print("hello")
from __future__ import unicode_literals  # force unadorned strings "" to be unicode without prepending u""
import argparse
import time
import os
from multiprocessing.dummy import Pool
import datetime
#from dateutil import parser as dt_parser
import config  # assumes env var BITLY_HISTORICS_CONFIG is configured
from bitly_api import BitlyError
import bitly_api
import tools
import unicodecsv

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
bitly = bitly_api.Connection(access_token=access_token)

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
    config.logger.info("Found {} items that we already track for {}".format(nbr_bitly_links_for_this_domain, domain))
    links_for_site = bitly.search(domain=domain, query="", limit=1000)
    add_links_raw_to_mongodb(links_for_site)
    bitly_links_for_this_domain = config.mongo_bitly_links_raw.find({'domain': domain})
    nbr_bitly_links_for_this_domain_after_update = bitly_links_for_this_domain.count()
    config.logger.info("Found {} new links for {}".format(nbr_bitly_links_for_this_domain_after_update - nbr_bitly_links_for_this_domain, domain))
    return links_for_site


def _hash_is_active(updated_at, clicks):
    """If most recent click date is close to updated_at, keep updating, else assume this hash is dead"""
    most_recent_dt_click = clicks[-1]
    most_recent_dt = most_recent_dt_click[0]
    return updated_at - most_recent_dt < config.TIMEDELTA_FOR_HASH_TO_BE_CONSIDERED_INACTIVE


def get_bitly_links_to_update():
    all_links = config.mongo_bitly_links_raw.find()
    bitly_links_to_update = []
    recent_cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=config.UPDATE_FROM_N_HOURS_AGO)
    for link in all_links:
        aggregate_link = link['aggregate_link']
        global_hash = tools.get_hash(aggregate_link)
        clicks = config.mongo_bitly_clicks.find_one({'global_hash': global_hash})
        updated_at = config.A_LONG_TIME_AGO
        hash_is_active = True
        if clicks:
            updated_at = clicks['updated_at']
            click_events = clicks['clicks']
            if click_events:
                hash_is_active = _hash_is_active(updated_at, click_events)
            else:
                config.logger.warning("This hash has 0 clicks, our logic keeps it alive regardless of its age:" + repr(aggregate_link))

            # retain this for debugging but it isn't useful to report during
            # production
            #if not hash_is_active:
                #config.logger.info("THIS HASH IS CONSIDERED TO BE OUT OF DATE:" + repr(aggregate_link))
        if updated_at < recent_cutoff and hash_is_active:
            bitly_links_to_update.append(aggregate_link)
    return bitly_links_to_update


def _get_new_link_clicks_then_add_to_mongodb(aggregate_link):
    NEW_LINK_CLICKS_UNIT = "hour"  # "hour" for hourly clicks, "day" for daily click totals
    response = bitly.link_clicks(link=aggregate_link, rollup=False, unit=NEW_LINK_CLICKS_UNIT)
    hsh = tools.get_hash(aggregate_link)
    document = get_existing_bitly_clicks_for(hsh)
    nbr_clicks_before_update = len(document['clicks'])
    add_response_to_document(response, document)
    nbr_clicks_after_update = len(document['clicks'])
    store_bitly_clicks_for(document)
    config.logger.debug("Stored {} new clicks (new total {}) with {} bin size for {}".format(nbr_clicks_after_update - nbr_clicks_before_update, nbr_clicks_after_update, NEW_LINK_CLICKS_UNIT, aggregate_link))


def _update_bitly_clicks(aggregate_link):
    RATE_LIMIT_SLEEP = 10  # 10 seconds default pause if we get rate limited
    while True:
        try:
            _get_new_link_clicks_then_add_to_mongodb(aggregate_link)
            #_get_new_clicks_add_to_mongodb(aggregate_link)
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
                #print("IGNORING ERROR for {}:{}".format(aggregate_link, repr(err)))
                config.logger.info("IGNORING ERROR for {}:{}".format(aggregate_link, repr(err)))
                time.sleep(0.1)  # pause for a moment and then we retry
            else:
                if err.code == 403:
                    # err.message u'RATE_LIMIT_EXCEEDED'
                    #print("Sleeping for {} due to code 403 {}".format(RATE_LIMIT_SLEEP, err.message))
                    config.logger.info("Sleeping for {} due to code 403 {}".format(RATE_LIMIT_SLEEP, err.message))
                    time.sleep(RATE_LIMIT_SLEEP)  # wait a bit, try again
                    RATE_LIMIT_SLEEP = RATE_LIMIT_SLEEP * 2  # double our wait time
                    RATE_LIMIT_SLEEP = min(RATE_LIMIT_SLEEP, 30 * 60)  # max of 30 mins
                else:
                    # what other errors have we encountered?
                    config.logger.error("UNKNOWN ERROR: " + repr(err))
                    #import pdb; pdb.set_trace()  # is there an error code for over capacity?


def update_bitly_clicks():
    """Update click data for documents that are out of date"""
    bitly_links_to_update = get_bitly_links_to_update()
    if bitly_links_to_update:
        config.logger.info("About to update {} links".format(len(bitly_links_to_update)))

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
    lines = [row.strip().split(',') for row in open(filename).readlines()]
    for line_nbr, (bitly_url, desired_domain) in enumerate(lines):
        possible_existing_document = config.mongo_bitly_links_raw.find_one({'aggregate_link': bitly_url})
        if possible_existing_document is None:  # we haven't stored this exact url yet
            try:
                aggregate_link, html_title, canonical_url, domain = get_title_canonical_url_from(bitly_url)
                # get the aggregate_url which should be canonical at bitly's end
                if desired_domain in domain:  # see inconsistent behaviour below
                    existing_document = config.mongo_bitly_links_raw.find_one({'aggregate_link': aggregate_link})
                    if not existing_document:
                        print(aggregate_link, html_title, canonical_url, desired_domain)
                        print("Adding:", aggregate_link, line_nbr)
                        # Note that we add using desired_domain as this is the same
                        # domain as we'd find via a bitly.search command
                        # This is to support odd Bitly behaviour - a search that
                        # includes a site with subdomain (e.g. blog.asos.com) will
                        # have domain set to "asos.com". A call to link_info
                        # however on the same bitly URL will have domain set to the
                        # full subdomain (for this example blog.asos.com). We
                        # preserve the root domain form for consistency.
                        add_entries_to_mongodb(aggregate_link, html_title, canonical_url, desired_domain)
                    else:
                        print("We already seem to have", bitly_url, end=" ")
                        if bitly_url != aggregate_link:
                            print(" aggregate_link version", aggregate_link)
                        else:
                            print()
                else:
                    print("Ignoring off-topic domain:", bitly_url, domain, desired_domain)
            except BitlyError as err:
                print("Received BitlyError: {}".format(repr(err)))
        else:
            print("We already seem to have", bitly_url, line_nbr)


def export_list_of_bitly_links(filename):
    """Export a list of bit.ly links and domains (for use by add_from_file)"""
    if not os.path.exists(filename):
        outfile = unicodecsv.writer(open(filename, "w"))
    else:
        raise IOError("File '{}' exists, please choose an output filename that does not already exist".format(filename))

    # get an iterator for all of our raw link data
    all_links = config.mongo_bitly_links_raw.find()
    for link in all_links:
        bitly_url = link['aggregate_link']  # e.g. u'http://bit.ly/XVCfdH'
        domain = link['domain']  # e.g. u'independent.co.uk'
        outfile.writerow([bitly_url, domain])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Project description')
    parser.add_argument('--add-domain', '-a', help='Add or update domain e.g. "asos.com"')
    parser.add_argument('--add-from-file', '-f', help="Add bit.ly links from a text file (bypassing bitly.com search) '--add-from-file new_links.txt'")
    parser.add_argument('--update-clicks', '-u', action="store_true", help='Fetch updated click data for all out-of-date bitly links')
    parser.add_argument('--list-domains', '-l', action="store_true", help='List the distinct domains (e.g. ["asos.com", "bbc.co.uk"]) that we track')
    parser.add_argument('--update-everything', '-e', action="store_true", help="Add all new URLs for existing domains and then update click history for all our links")
    parser.add_argument('--export-list-of-bitly-links', '-b', help="Export our stored bit.ly links and domains (for --add-from-file) to a file e.g. '--export-list-of-bitly-links existing_bitly_links.txt'")
    args = parser.parse_args()

    if args.add_from_file:
        add_from_file(args.add_from_file)

    if args.export_list_of_bitly_links:
        export_list_of_bitly_links(args.export_list_of_bitly_links)

    if args.add_domain:
        # get list of links for a root site
        links_for_site = get_link_result(args.add_domain)

    if args.update_clicks:
        update_bitly_clicks()

    if args.list_domains:
        domains = list_domains_we_track()
        print("We track:", domains)

    if args.update_everything:
        # update in parallel
        domains = list_domains_we_track()
        P = Pool(POOL_SIZE_FOR_BITLY_UPDATES)
        P.map(get_link_result, [str(domain) for domain in domains])
        print("Updating bitly click history for all of our links")
        update_bitly_clicks()
