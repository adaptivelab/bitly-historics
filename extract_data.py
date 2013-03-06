"""1 liner to explain this project"""
#!/usr/bin/python
# -*- coding: utf-8 -*-
# http://www.python.org/dev/peps/pep-0263/
import argparse
import datetime
import time
import csv
from collections import Counter
import config  # assumes env var BITLY_HISTORICS_CONFIG is configured
import bitly_api
import historics
from dateutil import parser as dt_parser

# Usage:
# $ export BITLY_HISTORICS_CONFIG=production
# $ python extract_data.py -d asos.com topman.com topshop.com hm.com urbanoutfitters.com topman.com zara.com urbanoutfitters.co.uk nordstrom.com gap.com americanapparel.net
# to write an output use: "--summary-csv clicks_summary.csv"
# which *might* be read by datawrapper.com

# To filter from a recent date (to current date) e.g.:
# $ python extract_data.py --ff 2013-02-10T00:00 -d asos.com topman.com topshop.com hm.com urbanoutfitters.com topman.com zara.com urbanoutfitters.co.uk nordstrom.com gap.com americanapparel.net

# To extract daily clicks for 1 brand use e.g.:
# $ python extract_data.py --ff 2013-01-31T00:00 -d topshop.com --clicks-daily-csv dailyclicks.csv

# use this to compare to the 'initial' field in bitly_links_raw
#    filter_to_as_initial = time.strftime("%Y%m%d%H%M%S", filter_to.timetuple())
#    filter_from_as_initial = time.strftime("%Y%m%d%H%M%S", filter_from.timetuple())

# TODO
# does not yet allow multiple domains for outputting clicks per day (pandas?)

def get_clicks_for_domain(domain, filter_from, filter_to):
    documents = config.mongo_bitly_links_raw.find({"domain": domain})
    hashes = [historics.get_hash(document['aggregate_link']) for document in documents]
    counter = Counter()
    total_clicks = 0
    for global_hash in hashes:
        clicks = config.mongo_bitly_clicks.find_one({"global_hash": global_hash})
        for date, clicks_per_day in clicks['clicks']:
            if filter_from < date and filter_to > date:
                items_to_count = [date] * clicks_per_day
                counter.update(items_to_count)
                total_clicks += clicks_per_day

    dates_clicks = counter.items()
    dates_clicks.sort()

    return dates_clicks, total_clicks


if __name__ == "__main__":
    filter_from = datetime.datetime.now() - datetime.timedelta(days=30)
    filter_from_str = time.strftime("%Y-%m-%dT%H:%M", filter_from.timetuple())
    filter_to = datetime.datetime.now()
    filter_to_str = time.strftime("%Y-%m-%dT%H:%M", filter_to.timetuple())

    parser = argparse.ArgumentParser(description='Project description')
    parser.add_argument('--domains', '-d', nargs='*', help='Get all results for domains (e.g. "-d asos.com topman.com")')
    parser.add_argument('--ff', type=str, default=filter_from_str, help='Filter From date range, defaults to --ff %s' % (filter_from_str))
    parser.add_argument('--ft', type=str, default=None, help='Filter To date range, defaults to --ff %s' % (filter_to_str))
    parser.add_argument('--summary-csv', '-s', help="Write a total count of clicks for each specified domain to specified file e.g. --summary-csv clicks.csv")
    parser.add_argument('--clicks-daily-csv', '-c', help="Write a list of daily counts of clicks for 1 specified domain to specified file e.g. --clicks-daily-csv dailyclicks.csv")
    args = parser.parse_args()
    print args

    access_token = config.BITLY_ACCESS_TOKEN
    bitly = bitly_api.Connection(access_token=access_token)

    # default will be to look at the last 30 days only
    if args.ff:
        filter_from = dt_parser.parse(args.ff)
    if args.ft:
        filter_to = dt_parser.parse(args.ft)
    print "Filtering from {} to {}".format(filter_from, filter_to)

    if args.domains:
        summary_csv_writer = None
        if args.summary_csv:
            summary_csv_writer = csv.writer(open(args.summary_csv, 'w'))
        for domain in args.domains:
            dates_clicks, total_clicks = get_clicks_for_domain(domain, filter_from, filter_to)
            if summary_csv_writer:
                summary_csv_writer.writerow([domain, total_clicks])

        clicks_daily_writer = None
        if args.clicks_daily_csv:
            clicks_daily_writer = csv.writer(open(args.clicks_daily_csv, 'w'))
            assert len(args.domains) == 1
            domain = args.domains[0]
            dates_clicks, total_clicks = get_clicks_for_domain(domain, filter_from, filter_to)
            if clicks_daily_writer:
                clicks_daily_writer.writerow(['date', 'clicks'])
                for date, clicks in dates_clicks:
                    simple_date = time.strftime("%Y-%m-%d", date.timetuple())
                    clicks_daily_writer.writerow([simple_date, clicks])


