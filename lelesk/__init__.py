#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Le's LESK - Word Sense Disambiguation Package
Latest version can be found at https://github.com/letuananh/lelesk

Usage:

    [TODO] WIP

@author: Le Tuan Anh <tuananh.ke@gmail.com>
'''

# Copyright (c) 2014, Le Tuan Anh <tuananh.ke@gmail.com>
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

from .main import LeLeskWSD, LeskCache

from .config import LLConfig
from yawlib.config import YLConfig

from yawlib.glosswordnet import XMLGWordNet, SQLiteGWordNet
from yawlib.wordnetsql import WordNetSQL

from yawlib.helpers import get_synset_by_id, get_synset_by_sk, get_synsets_by_term, dump_synsets, dump_synset

__all__ = ['LLConfig', 'YLConfig', 'LeLeskWSD', 'LeskCache', 'XMLGWordNet', 'SQLiteGWordNet', 'WOrdNetSQL', 'get_synset_by_id', 'get_synset_by_sk', 'get_synsets_by_term', 'dump_synsets', 'dump_synset']

