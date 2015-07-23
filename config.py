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

    NTUMC_PRONOUNS = ['77000100-n', '77000057-n', '77000054-a', '77000054-n', '77000026-n', '77000065-n'
                , '77000025-n', '77000028-n', '77000004-n', '77010118-n', '77000104-n', '77000113-r', '77000003-n'
                , '77000107-a', '77000098-n', '77000059-n', '77000059-a', '77000008-n', '77000107-n', '77000048-n'
                , '01554230-n', '77010005-a', '77000088-r', '77000053-n', '77000113-a', '77000120-a', '77000123-n'
                , '77000050-n', '77000050-a', '77000093-n', '77000114-r', '77000117-n', '77000040-n', '77000090-n'
                , '77000114-a', '77000046-n', '01551633-n', '77000018-n', '77000009-n', '77000031-n', '77000032-n'
                , '77000078-n', '77000092-n', '77000041-n', '77000043-a', '02267686-n', '77000039-a', '77000095-n'
                , '77000081-n', '77000071-n', '02269039-n', '77000103-n', '77000072-n', '77000022-n', '77000108-n'
                , '77000021-n', '77000035-n', '77010002-a', '77000076-n', '77000085-n', '77000013-n', '77010001-a'
                , '77000074-n', '77000076-a', '02269286-n', '77000082-a', '77000017-n', '77010120-n', '77000082-n'
                , '77000061-a', '77000110-n', '77010006-a', '77000061-n', '77000024-a', '77000011-n', '77000016-n'
                , '77000024-n', '77000023-n', '77000052-n', '77000029-n', '77000064-n', '77000002-n', '77010119-n'
                , '77010003-a', '77010008-n', '77000058-a', '77000056-n', '77000099-n', '77000106-n', '77000058-n'
                , '77000006-n', '77000006-a', '77000139-n', '77000080-a', '02269635-n', '77000121-n', '77000091-a'
                , '77000089-r', '77010000-a', '77000091-n', '77000116-n', '77010004-a', '77000044-n', '77000089-a'
                , '77000122-n', '77000115-n', '77000019-n', '00524607-n', '77000033-n', '77000034-n', '77000045-n'
                , '77000084-n', '02267308-n', '77000109-n', '77000075-a', '77000075-n', '77000097-n', '77000001-n'
                , '77000073-n', '77000094-n', '77010122-n', '77000079-a', '77000111-n', '77000037-n', '77000012-n'
                , '77000079-n', '77000020-n', '77000027-n', '77000070-n', '02070188-n', '77000038-n', '77010121-n'
                , '77000015-n', '77000066-n', '77000137-n', '77000080-n', '77000060-n', '77010007-n', '77000060-a'
                , '77000112-n'
                 ]
