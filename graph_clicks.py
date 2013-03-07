#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Graph stored bitly click data"""
import argparse
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datacursor import DataCursor
import config  # assumes env var BITLY_HISTORICS_CONFIG is configured
import historics

# Usage:
# Graph all of our data for a hash
# BITLY_HISTORICS_CONFIG=production python graph_clicks.py -g XR1aPQ
# show all asos.com behaviour:
# BITLY_HISTORICS_CONFIG=production python graph_clicks.py --d asos.com
# BITLY_HISTORICS_CONFIG=production python graph_clicks.py --d guardian.co.uk
# show all clicks for all sites:
# BITLY_HISTORICS_CONFIG=production python graph_clicks.py --a Y


def plot_clicks(clicks, ax):
    """Plot volume of daily clicks as a line chart"""
    lines = None
    if clicks is None:
        print "Clicks is None in plot_clicks - this might just mean that we haven't fetched data yet"
    else:
        dates, clicks_per_day = zip(*clicks['clicks'])
        global_hash = clicks['global_hash']
        aggregate_link = 'http://bit.ly/' + global_hash
        document = config.mongo_bitly_links_raw.find_one({'aggregate_link': aggregate_link})
        title = document.get('title', '<no title>')
        lines = ax.plot_date(dates, clicks_per_day, '-', label=title + " (%s+)" % (aggregate_link))
    return lines


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Project description')
    parser.add_argument('--global-hash', '-g', nargs="*", help='Plot a specific global hash(es) e.g. " -g XR1aPQ VWUGMX" ')
    parser.add_argument('--all-hashes', '-a', help='Plots all the hashes that we know about')
    parser.add_argument('--domain', '-d', help='Graph all results for a domain (e.g. "-d asos.com")')
    parser.add_argument('--logy', '-l', action="store_true", default=False, help="Plot y axis with Log scale (defaults to Linear)")
    args = parser.parse_args()

    fig = plt.figure()
    ax = fig.add_subplot(111)
    title = "Bit.ly clicks per day"

    if args.domain:
        documents = config.mongo_bitly_links_raw.find({"domain": args.domain})
        hashes = [historics.get_hash(document['aggregate_link']) for document in documents]
        plotted_lines = []
        for global_hash in hashes:
            clicks = config.mongo_bitly_clicks.find_one({"global_hash": global_hash})
            #import pdb; pdb.set_trace()

            lines = plot_clicks(clicks, ax)
            if lines:
                plotted_lines += lines
        title = "Bit.ly clicks per day for {} hashes for {}".format(len(hashes), args.domain)
        dc = DataCursor(plotted_lines)

    if args.global_hash:
        for global_hash in args.global_hash:
            clicks = config.mongo_bitly_clicks.find_one({"global_hash": global_hash})
            plot_clicks(clicks, ax)
        title = "Bit.ly clicks per day for {} hashes".format(len(args.global_hash))

    if args.all_hashes:
        all_clicks = config.mongo_bitly_clicks.find()
        for clicks in all_clicks:
            plot_clicks(clicks, ax)

    ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H:%M:%S')
    fig.autofmt_xdate()

    if args.logy:
        ax.set_yscale('symlog', linthreshy=10)

    ax.set_ylabel('Clicks')
    ax.set_title(title)

    if args.global_hash:
        ax.legend()
    ax.grid()
    plt.show()
