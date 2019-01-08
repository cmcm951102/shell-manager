#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
from threading import Lock

CRITICAL = 150
ERROR = 140
WARNING = 130
INFO = 120
DEBUG = 110
NOTSET = 100
levelNames = {
    CRITICAL : 'x',
    ERROR : '-',
    WARNING : '!',
    INFO : '+',
    DEBUG : '*',
    NOTSET : '@',
}
for level, levelname in levelNames.items():
	logging.addLevelName(level, levelname)

Logger=logging.getLogger('L')
formatter=logging.Formatter('[%(levelname)s][%(T)s]: %(message)s')
console_handler=logging.StreamHandler(sys.stdout)
console_handler.formatter=formatter
Logger.addHandler(console_handler)
Logger.setLevel(INFO)
print_lock=Lock()

def _pack_T(T):
	pack=dict()
	pack['extra'] = {'T' : T}
	return pack

def info(msg, T):
	print_lock.acquire()
	Logger.log(INFO, msg, **_pack_T(T))
	print_lock.release()

def error(msg, T):
	print_lock.acquire()
	Logger.log(ERROR, msg, **_pack_T(T))
	print_lock.release()

def warn(msg, T):
	print_lock.acquire()
	Logger.log(WARNING, msg, **_pack_T(T))
	print_lock.release()

def warning(msg, T):
	print_lock.acquire()
	Logger.log(WARNING, msg, **_pack_T(T))
	print_lock.release()

def debug(msg, T):
	print_lock.acquire()
	Logger.log(DEBUG, msg, **_pack_T(T))
	print_lock.release()

def log(level,msg,T):
	print_lock.acquire()
	Logger.log(level, msg, **_pack_T(T))
	print_lock.release()
