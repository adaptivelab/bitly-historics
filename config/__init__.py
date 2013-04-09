"""Configuration provided by 'import config' and BITLY_HISTORICS_CONFIG env var"""
#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import datetime
import pymongo

from twitter_secrets import *

# Read BITLY_HISTORICS_CONFIG environment variable (raise error if missing or badly
# configured), use this to decide on our config and import the relevant python
# file

# This assumes that locally we have suitable python files e.g. production.py,
# testing.py
CONFIG_ENV_VAR = "BITLY_HISTORICS_CONFIG"
CONFIG_ENV_VAR_PRODUCTION = "production"
CONFIG_ENV_VAR_TESTING = "testing"
config_set = False  # only set to True if we have find a valid ENV VAR
config_choice = os.getenv(CONFIG_ENV_VAR)
if config_choice == CONFIG_ENV_VAR_PRODUCTION:
    from production import *
    config_set = True
if config_choice == CONFIG_ENV_VAR_TESTING:
    from testing import *
    config_set = True
if not config_set:
    raise ValueError("ALERT! ENV VAR \"{}\" must be set e.g. \"export {}={}\"".format(CONFIG_ENV_VAR, CONFIG_ENV_VAR, CONFIG_ENV_VAR_TESTING))

# Global Bitly token - NOTE this is Ian's PRIVATE TOKEN
BITLY_ACCESS_TOKEN_FILENAME = "config/bitly_access_token.txt"
BITLY_ACCESS_TOKEN = open(BITLY_ACCESS_TOKEN_FILENAME).readline().strip()

# Default datetime to use to indicate that a Document is out of date
A_LONG_TIME_AGO = datetime.datetime(1970, 1, 1)
# Number of hours that we're out of date before we fetch new click data
UPDATE_FROM_N_HOURS_AGO = 1
# Collect N days worth of historic click data
NUMBER_OF_DAYS_DATA_TO_COLLECT = 30

# Time window before a hash with no new clicks is considered to be dead
TIMEDELTA_FOR_HASH_TO_BE_CONSIDERED_INACTIVE = datetime.timedelta(days=5)

# Common mongodb configuration
MONGO_BITLY_LINKS_RAW = 'bitly_links_raw'
MONGO_BITLY_CLICKS = 'bitly_clicks'

conn = pymongo.Connection()
db = conn[MONGO_DB]
mongo_bitly_links_raw = db[MONGO_BITLY_LINKS_RAW]
mongo_bitly_clicks = db[MONGO_BITLY_CLICKS]
mongo_bitly_links_raw.ensure_index('domain')
mongo_bitly_links_raw.ensure_index('aggregate_link')
mongo_bitly_links_raw.ensure_index('global_hash')
mongo_bitly_clicks.ensure_index('global_hash')

