#!/bin/bash 
# Run this using a crontab line like this:
# */1 * * * * cd /vagrant && ./run_update_all.sh
source envvagrant/bin/activate
BITLY_HISTORICS_CONFIG=production python historics.py -e
