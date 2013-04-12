#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract data for reporting"""
from __future__ import division  # 1/2 == 0.5, as in Py3
from __future__ import absolute_import  # avoid hiding global modules with locals
from __future__ import print_function  # force use of print("hello")
from __future__ import unicode_literals  # force unadorned strings "" to be unicode without prepending u""
import argparse
import datetime
import time
from dateutil import parser as dt_parser
import unicodecsv
from collections import Counter
import config  # assumes env var BITLY_HISTORICS_CONFIG is configured
import historics
import tools

# Usage:
# $ export BITLY_HISTORICS_CONFIG=production
# $ python extract_data.py -d asos.com topman.com topshop.com hm.com urbanoutfitters.com topman.com zara.com urbanoutfitters.co.uk nordstrom.com gap.com americanapparel.net
# to write an output use: "--summary-csv clicks_summary.csv"
# which *might* be read by datawrapper.de

# To filter from a recent date (to current date) e.g.:
# $ python extract_data.py --ff 2013-02-10T00:00 -d asos.com topman.com topshop.com hm.com urbanoutfitters.com topman.com zara.com urbanoutfitters.co.uk nordstrom.com gap.com americanapparel.net

# To extract daily clicks for 1 brand use e.g.:
# $ python extract_data.py --ff 2013-01-31T00:00 -d topshop.com --clicks-daily-csv dailyclicks.csv

# use this to compare to the 'initial' field in bitly_links_raw
#    filter_to_as_initial = time.strftime("%Y%m%d%H%M%S", filter_to.timetuple())
#    filter_from_as_initial = time.strftime("%Y%m%d%H%M%S", filter_from.timetuple())

# TODO
# does not yet allow multiple domains for outputting clicks per day (pandas?)


def get_links_for_domain(domain, filter_from, filter_to):
    """Build dict of click stats for all links pointing at a domain"""
    documents = config.mongo_bitly_links_raw.find({"domain": domain})
    hashes_bitlyurl_urls = [(historics.get_hash(document['aggregate_link']), document['aggregate_link'], document['url']) for document in documents]
    info_per_hash = {}
    for global_hash, bitlyurl, url in hashes_bitlyurl_urls:
        clicks = config.mongo_bitly_clicks.find_one({"global_hash": global_hash})
        nbr_positive_click_days = 0  # nbr days that had >=1 click
        total_clicks = 0  # count total nbr of clicks for this link
        dates_with_activity = []  # days when >=1 click occurred
        if clicks is not None:
            for date, clicks_per_day in clicks['clicks']:
                if clicks_per_day > 0:
                    total_clicks += clicks_per_day
                    dates_with_activity.append(date)

        nbr_positive_click_days = len(dates_with_activity)
        first_clicked_datetime = min(dates_with_activity)
        first_clicked = datetime.date(first_clicked_datetime.year, first_clicked_datetime.month, first_clicked_datetime.day)
        bitlyurl = bitlyurl + "+"  # add + and we get statistics via bitly.com in the browser
        info_per_hash[global_hash] = {'nbr_positive_click_days': nbr_positive_click_days,
                                      'bitly_url': bitlyurl,
                                      'url': url,
                                      'total_clicks': total_clicks,
                                      'first_clicked': first_clicked}
    return info_per_hash


def get_clicks_for_domain(domain, filter_from, filter_to):
    documents = config.mongo_bitly_links_raw.find({"domain": domain})
    hashes = [tools.get_hash(document['aggregate_link']) for document in documents]
    counter = Counter()
    total_clicks = 0
    for global_hash in hashes:
        clicks = config.mongo_bitly_clicks.find_one({"global_hash": global_hash})
        if clicks is not None:
            for date, clicks_per_day in clicks['clicks']:
                if filter_from < date and filter_to > date:
                    items_to_count = [date] * clicks_per_day
                    counter.update(items_to_count)
                    total_clicks += clicks_per_day

    dates_clicks = counter.items()
    dates_clicks.sort()

    return dates_clicks, total_clicks


def get_clicks_for_domain_links(domain, filter_from, filter_to):
    documents = config.mongo_bitly_links_raw.find({"domain": domain})
    hashes = [tools.get_hash(document['aggregate_link']) for document in documents]
    clicks_per_link = {}
    for global_hash in hashes:
        clicks = config.mongo_bitly_clicks.find_one({"global_hash": global_hash})
        if clicks:
            counts = 0
            for date, clicks_per_day in clicks['clicks']:
                if filter_from < date and filter_to > date:
                    #items_to_count = [date] * clicks_per_day
                    #counter.update(items_to_count)
                    counts += clicks_per_day
            if counts > 0:
                clicks_per_link[global_hash] = counts

    c = Counter(clicks_per_link)
    return c


def summarise_aggregate_links(global_hash_click_counter, top_n_results=None):
    for global_hash, count in global_hash_click_counter.most_common(top_n_results):
        aggregate_link = tools.make_bitly_url(global_hash)
        link_raw = config.mongo_bitly_links_raw.find_one({"aggregate_link": aggregate_link})
        # prepare and output string, make sure it is UTF-8 encoded as we're
        # bound to see some unicode (which the console neeeds to know about)
        out_str = link_raw.get('summaryTitle', "<no title>") + " " + link_raw['url'] + " " + aggregate_link + "+ " + str(count)
        out_str = out_str.encode('utf-8')
        print(out_str)


if __name__ == "__main__":
    filter_from = datetime.datetime.now() - datetime.timedelta(days=30)
    filter_from_str = time.strftime("%Y-%m-%dT%H:%M", filter_from.timetuple())
    filter_to = datetime.datetime.now()
    filter_to_str = time.strftime("%Y-%m-%dT%H:%M", filter_to.timetuple())

    parser = argparse.ArgumentParser(description='Project description')
    parser.add_argument('--domains', '-d', nargs='*', help="Get all results for domains e.g. '-d asos.com topman.com')")
    parser.add_argument('--ff', type=str, default=filter_from_str, help="Filter From date range, defaults to '--ff %s'" % (filter_from_str))
    parser.add_argument('--ft', type=str, default=None, help="Filter To date range, defaults to '--ff %s'" % (filter_to_str))
    parser.add_argument('--summary-csv', '-s', help="Write a total count of clicks for each specified domain to specified file e.g. '--summary-csv clicks.csv'")
    parser.add_argument('--clicks-daily-csv', '-c', help="Write a list of daily counts of clicks for 1 specified domain to specified file e.g. '--clicks-daily-csv dailyclicks.csv'")
    parser.add_argument('--get-clicks-for-domain-links', '-g', default=20, type=int, help="Get sum of clicks for each link for a domain e.g. '--get-clicks-for-domain-links 30 -d guardian.co.uk'")
    parser.add_argument('--link-report', '-l', help="Write a report per domain on link click totals, nbr days of click activity e.g. '--link-report link_report' generates 'link_report_<domain>.csv'")
    args = parser.parse_args()
    print(args)

    # default will be to look at the last 30 days only
    if args.ff:
        filter_from = dt_parser.parse(args.ff)
    if args.ft:
        filter_to = dt_parser.parse(args.ft)
    print("Filtering from {} to {}".format(filter_from, filter_to))

    if args.get_clicks_for_domain_links:
        for domain in args.domains:
            global_hash_click_counter = get_clicks_for_domain_links(domain, filter_from, filter_to)
            summarise_aggregate_links(global_hash_click_counter, args.get_clicks_for_domain_links)

    if args.domains and (args.summary_csv or args.clicks_daily_csv or args.link_report):
        summary_csv_writer = None
        if args.summary_csv:
            summary_csv_writer = unicodecsv.writer(open(args.summary_csv, 'w'))
        for domain in args.domains:
            dates_clicks, total_clicks = get_clicks_for_domain(domain, filter_from, filter_to)
            if summary_csv_writer:
                summary_csv_writer.writerow([domain, total_clicks])
            else:
                print("Found {} results for {}".format(len(dates_clicks), domain))

        clicks_daily_writer = None
        if args.clicks_daily_csv:
            clicks_daily_writer = unicodecsv.writer(open(args.clicks_daily_csv, 'w'))
            assert len(args.domains) == 1
            domain = args.domains[0]
            dates_clicks, total_clicks = get_clicks_for_domain(domain, filter_from, filter_to)
            if clicks_daily_writer:
                clicks_daily_writer.writerow(['date', 'clicks'])
                for date, clicks in dates_clicks:
                    simple_date = time.strftime("%Y-%m-%d", date.timetuple())
                    clicks_daily_writer.writerow([simple_date, clicks])

        if args.link_report:
            for domain in args.domains:
                base_file_name = "%s_%s.csv" % (args.link_report, domain)
                info_per_hash = get_links_for_domain(domain, filter_from, filter_to)
                example_dict = info_per_hash[info_per_hash.keys()[0]]
                print("Open %s for output" % (base_file_name))
                writer = unicodecsv.DictWriter(open(base_file_name, 'wb'), fieldnames=example_dict.keys())
                writer.writeheader()
                for hsh, info in info_per_hash.items():
                    writer.writerow(info)
