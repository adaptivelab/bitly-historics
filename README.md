What?
----

This tool is used to track bitly historic click data for specified websites. We're using it to track click-throughs to certain fashion brands (e.g. topshop.com), building up a historic record of clicks by day. Simple graphing and export facilities are provided, MongoDB is used as a longer term store.

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

The `requirements.txt` file contains a reference to https://github.com/bitly/bitly-api-python/commit/11a2d9cfeddfc3361e31dec8d64e57b3280bfbda (as of 6th March 2012), we use a named version of the bitly api (since their PyPI releases are infrequent) and we inherit and override one method (since they're not merging the git pull request supplied months back).

Mongo:
-----

This script expects a default MongoDB instance to be running. To create a version using a named directory (so the data is in the named DB, not the global DB), you can run this script which will also follow the logs:

    $ ./run_log_mongodb.sh

As of March 2012 mongodb.conf refers to "/media/GDRIVEFAT32/SoMA1WkProject/mongodb/<files>" - this drive is mounted via Ian's laptop, the drive is the external 1TB GDRIVE (silver top, black sides). The only special thing about this drive is that it has lots of space, move the mongodb files elsewhere and reconfigure mongodb.conf. This drive uses HFS (Apple's filesystem without journaling) so it can be read by Linux and Macs.

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


Usage:
-----

First - to get help use:

    $ BITLY_HISTORICS_CONFIG=production python historics.py --help

To featch new links for the domains we're tracking, and all the click history for these links (which will be our most common operation) use:

    $ BITLY_HISTORICS_CONFIG=production python historics.py -e

To add a domain, we ask Bitly for all the Bitly links for asos.com:

    $ BITLY_HISTORICS_CONFIG=production python historics.py --a asos.com

and our mongodb is updated with the snapshot of links that they provide.

We can run this same call on another day to get an updated set of links, we'll add new links to our collection. We never remove links from mongodb.

Next let us request updated click data for every Bitly link that we track. We won't request an update if we've already recorded new data in the last 24 hours.

    $ BITLY_HISTORICS_CONFIG=production python historics.py --update-clicks

To draw graphs of all click data for specific hashes:

    $ BITLY_HISTORICS_CONFIG=production python graph_clicks.py -g XR1aPQ VWUGMX

To draw graphs per website:

    $ BITLY_HISTORICS_CONFIG=production python graph_clicks.py --d bbc.co.uk

To extract a CSV file of clicks per brand (we can also do clicks per day):

    $ python extract_data.py --ff 2013-02-10T00:00 -d asos.com topman.com topshop.com hm.com urbanoutfitters.com topman.com zara.com urbanoutfitters.co.uk nordstrom.com gap.com americanapparel.net

Todo:
----

Coverage testing reveals that historics.get_link_result and historics.update_bitly_clicks are untested. We should use fudge to make some tests.

Build a list of domains we want to automatically track
during update go fetch all new links these domains and then fetch their history if necessary (currently we add new links for existing domains by calling --add again)

What might go wrong:
-------------------

 * We use bitly's clicks_by_day API call, this is due to be deprecated. Their replacement call gave an aggregate result, not a breakdown by day, so further investigation will be required here.
 * New error (7th March spotted) UNKNOWN ERROR: BitlyError('<urlopen error [Errno -2] Name or service not known>',) - local web access problem?
 

Tracking at present:
-------------------

To get the list of domains that we track use:

    $ BITLY_HISTORICS_CONFIG=production python historics.py -l

 * topshop.com 185
 * topman.com 119
 ...
