#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Global configuration file for LeLesk
Latest version can be found at https://github.com/letuananh/lelesk

@author: Le Tuan Anh <tuananh.ke@gmail.com>
'''

# Copyright (c) 2015, Le Tuan Anh <tuananh.ke@gmail.com>
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

__author__ = "Le Tuan Anh <tuananh.ke@gmail.com>"
__copyright__ = "Copyright 2014, lelesk"
__credits__ = [ "Le Tuan Anh" ]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

import os

class LLConfig:
    WORDNET_30_PATH = os.path.expanduser('~/wordnet/sqlite-30.db')
    # WordNet SQLite can be downloaded from:
    #       http://sourceforge.net/projects/wnsql/files/wnsql3/sqlite/3.0/ 

    WORDNET_30_GLOSSTAG_PATH = os.path.expanduser('~/wordnet/glosstag')
    WORDNET_30_GLOSS_DB_PATH = os.path.expanduser('~/wordnet/glosstag.db')
    # Gloss WordNet can be downloaded from: 
    #       http://wordnet.princeton.edu/glosstag.shtml

    DB_INIT_SCRIPT = os.path.expanduser('./script/wngdb.sql')
    # script used to initialise WordNet Gloss database 
    
    LELESK_CACHE_DB_INIT_SCRIPT = os.path.expanduser('./script/lesk_cache.sql')
    LELESK_CACHE_DB_LOC         = os.path.expanduser('./data/lesk_cache.db')
    LELESK_CACHE_DEBUG_DIR      = os.path.expanduser('./debug')