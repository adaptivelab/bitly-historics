"""Production configuration (imported by __init__.py)"""
#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging

LOG_FILE = "./bitly_historics.log"

logger = logging.getLogger('bitly_historics')
log_hdlr = logging.FileHandler(LOG_FILE)
log_formatter = logging.Formatter('%(asctime)s {%(pathname)s:%(lineno)d} - %(levelname)s - %(message)s', '%y-%m-%d %H:%M:%S')
log_hdlr.setFormatter(log_formatter)
logger.addHandler(log_hdlr)
logger.setLevel(logging.INFO)

MONGO_DB = 'bitly_historics'
