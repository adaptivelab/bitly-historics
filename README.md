What?
----

This tool is used to track bitly historic click data for specified websites. We're using it to track click-throughs to certain brand websites, building up a historic record of clicks by day for analysis and reporting. Some graphing and export facilities are provided (e.g. for output of CSVs for http://datawrapper.de/), MongoDB is used as a longer term store.

Author: ian@morconsulting.com (consulting to http://AdaptiveLab.com) of https://github.com/ianozsvald/

When: early 2013

Installation:
------------

  1. Make sure you have MongoDB installed (we run our own version using our mongodb.conf)
  2. `$ pip install -r requirements.txt`  # install Python libraries
  3. Create a Bitly token (http://dev.bitly.com/), save it in ./config/bitly_access_token.txt (read by ./config/__init__.py)
  4. Run MongoDB (noted in next section), either use a global MongoDB or a local one for data separation from other projects (as defined here) (e.g. "$ ./run_log_mongodb.sh" to run a local instance)
  5. `$ BITLY_HISTORICS_CONFIG=testing nosetests`  # test the basic setup (see Testing)

Note I had to install `pip install numpy` by hand as pip (for reasons I cannot spot) wouldn't install it before matplotlib and matplotlib depends on numpy.

The `requirements.txt` file contains a reference to https://github.com/bitly/bitly-api-python/commit/11a2d9cfeddfc3361e31dec8d64e57b3280bfbda (as of 6th March 2012), we use a named commit of the bitly api that is up to date and is known to work (since their PyPI releases are infrequent) and we inherit and override one method (as my Git Pull request supplied a while ago hasn't been used https://github.com/bitly/bitly-api-python/pull/14).

Mongo:
-----

This script expects a default MongoDB instance to be running. To create a version using a named directory (so the data is in the named DB, not the global DB), you can run this script which will also follow the logs:

    $ ./run_log_mongodb.sh

As of March 2012 `mongodb.conf` refers to `/media/GDRIVEFAT32/SoMA1WkProject/mongodb/<files>` - this drive is mounted via Ian's laptop, the drive is the external 1TB GDRIVE (silver top, black sides). The only special thing about this drive is that it has lots of space, move the mongodb files elsewhere and reconfigure mongodb.conf. This drive uses HFS (Apple's filesystem without journaling) so it can be read by Linux and Macs.

Note that we only use a separate MongoDB here as we prefer to separate production data sources into local projects, if this in run on a server the probably we'd just use the global MongoDB. We don't need any special MongoDB configuration (no sharding or parameter tweaking).

Testing:
-------

    $ BITLY_HISTORICS_CONFIG=testing nosetests
or 

    $ BITLY_HISTORICS_CONFIG=testing python -m unittest discover

You should see 8 tests pass.

To get coverage information use:

    $ BITLY_HISTORICS_CONFIG=testing nosetests --cover-html --with-coverage

and then check the `./cover/index.html` file for historics.py (and other files in this project).


Usage - gathering data:
----------------------

First - to get help use:

    $ BITLY_HISTORICS_CONFIG=production python historics.py --help

To featch new links for the domains we're tracking, and all the click history for these links (which will be our most common operation) use:

    $ BITLY_HISTORICS_CONFIG=production python historics.py -e

To add a domain, we ask Bitly for all the Bitly links for bbc.co.uk:

    $ BITLY_HISTORICS_CONFIG=production python historics.py --add-domain bbc.co.uk

and our mongodb is updated with the snapshot of links that they provide.

We can run this same call on another day to get an updated set of links, we'll add new links to our collection. We never remove links from mongodb.

Next let us request updated click data for every Bitly link that we track. We won't request an update if we've already recorded new data in the last N hours (N is set in configuration).

    $ BITLY_HISTORICS_CONFIG=production python historics.py --update-clicks

Usage - gathering data via tweets:
---------------------------------

We can import data via Twitter by reading tweets from specified accounts and exporting a list of bitly links which can be later imported:

   $ BITLY_HISTORICS_CONFIG=production python get_non_bitly_links.py --screen_names bbcnews -n 20 -o new_links.txt

The above writes a file `new_links.txt` containing bit.ly names inferred from (in this case) the BBC shortener bbc.in, these links are extracted from the first n tweets read on the specified Twitter accounts.

We can import this new list of bit.ly links using:

    $ BITLY_HISTORICS_CONFIG=production python historics.py --add-from-file new_links.txt

NOTE LIMITATION - we only match and export on hard-coded domains (bbc and asos at present), this should be refactored and pulled into a config file.

Usage - graphing:
----------------

To learn about graphing options:

    $ BITLY_HISTORICS_CONFIG=production python graph_clicks.py 

To draw graphs of all click data for specific hashes:

    $ BITLY_HISTORICS_CONFIG=production python graph_clicks.py -g XR1aPQ VWUGMX

To draw graphs per website:

    $ BITLY_HISTORICS_CONFIG=production python graph_clicks.py --d guardian.co.uk

the above call will generate something like the included `example_graph_output.png` (note the tooltip via the `DataCursor` module):

![Example graph output](example_graph_output.png?raw=true)

Usage - CSV export:
------------------

To get help:

    $ BITLY_HISTORICS_CONFIG=production python extract_data.py --help

To extract a CSV file of clicks per website (we can also do clicks per day):

    $ BITLY_HISTORICS_CONFIG=production python extract_data.py --ff 2013-02-10T00:00 -d guardian.co.uk bbc.co.uk

We can export data that works with http://datawrapper.de/ for super-easy web presentable charts.

To extract summaries of click data per link for a domain, writing to e.g. "link_report_guardian.co.uk.csv":

    $ BITLY_HISTORICS_CONFIG=production python extract_data.py --domains guardian.co.uk --link-report link_report

Usage - reporting most-clicked links:
------------------------------------

Output a list of the most clicked links in the time period, restricting to the top 20:

    $ BITLY_HISTORICS_CONFIG=production python extract_data.py --ff 2013-04-08T00:00 -g 20 --domains bbc.co.uk
    

Todo:
----

Coverage testing reveals that historics.get_link_result and historics.update_bitly_clicks are untested. We should use fudge to make some tests.

Build a list of domains we want to automatically track
during update go fetch all new links these domains and then fetch their history if necessary (currently we add new links for existing domains by calling --add again)

Stop collecting data for links that haven't had any clicks for X days (e.g. if no clicks after a week, assume it is a dead link) - might lose some interesting reoccuring stories?

What might go wrong:
-------------------

 * New error (7th March spotted) UNKNOWN ERROR: BitlyError('<urlopen error [Errno -2] Name or service not known>',) - local web access problem?
 * We don't use mocks for web-facing calls (e.g. calls to bitly for search, link_info, click data etc and for the requests library) - we really should - running coverage during the unittests will highlight this 
 * Bitly's search API and lookup API return different results for the domain field (one has the subdomain e.g. news.bbc.co.uk, the other has the root domain e.g. bbc.co.uk) for the same bitly link

Tracking at present:
-------------------

To get the list of domains that we track use:

    $ BITLY_HISTORICS_CONFIG=production python historics.py -l

 * topshop.com 185
 * topman.com 119
 ...
