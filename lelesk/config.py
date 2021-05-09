#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
LeLESK configuration module
'''

# This code is a part of lelesk library: https://github.com/letuananh/lelesk
# :copyright: (c) 2014 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os


class LLConfig:
    LELESK_DIR = os.path.dirname(os.path.abspath(__file__))
    LELESK_CACHE_DB_INIT_SCRIPT = os.path.join(LELESK_DIR, 'script', 'lesk_cache.sql')
    LELESK_CACHE_DB_LOC = os.path.expanduser('./data/temp/lesk_cache.db')
    LELESK_CACHE_DEBUG_DIR = os.path.expanduser('./data/temp/debug')
