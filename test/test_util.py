#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Test utility functions
Latest version can be found at https://github.com/letuananh/lelesk

@author: Le Tuan Anh <tuananh.ke@gmail.com>
'''

# Copyright (c) 2014, Le Tuan Anh <tuananh.ke@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

__author__ = "Le Tuan Anh <tuananh.ke@gmail.com>"
__copyright__ = "Copyright 2014, lelesk"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

# -------------------------------------------------------------------

import os
import unittest
import logging
from lelesk import LeLeskWSD, LeskCache
from lelesk.util import tokenize


################################################################
# Configuration
################################################################
TEST_DIR = os.path.dirname(__file__)
TEST_CACHE = os.path.join(TEST_DIR, 'data', 'test_cache.db')


def get_logger():
    return logging.getLogger(__name__)


class TestMain(unittest.TestCase):

    def test_known_concepts(self):
        wsd = LeLeskWSD()
        ss = wsd.smart_synset_search('Ali Baba', pos=None, deep_select=True)
        self.assertTrue(ss)
        self.assertIn('Ali Baba', list(ss)[0].lemmas)

    def test_synset_search(self):
        wsd = LeLeskWSD()
        nsses = wsd.smart_synset_search('love', 'n')
        vsses = wsd.smart_synset_search('love', 'v')
        self.assertEqual(len(nsses), 6)  # There should be 6 noun synsets
        self.assertEqual(len(vsses), 4)
        doge = wsd.smart_synset_search('doge', 'n')
        self.assertEqual(len(doge), 1)
        # verb?
        speckled = wsd.smart_synset_search('speckle', 'v')
        self.assertEqual(len(speckled), 2)

    def test_lelesk_set(self):
        wsd = LeLeskWSD()
        fish_synsets = wsd.smart_synset_search('fish', 'n')
        n02512053 = fish_synsets['02512053-n']
        leset = wsd.build_lelesk_set(n02512053.ID)
        get_logger().warning(leset)
        self.assertEqual(len(leset), 192)
        self.assertIn('fish', leset)
        self.assertIn('aquatic', leset)
        self.assertIn('shark', leset)
        # now with cache
        wsd = LeLeskWSD(dbcache=LeskCache())
        lesetc = wsd.build_lelesk_set(n02512053.ID)
        self.assertEqual(set(leset), set(lesetc))
        # TODO: Test this method properly

    def test_tokenize(self):
        text = 'I have eaten some cakes and gave my dogs some too.'
        actual = tokenize(text)
        print(actual)

    def test_stopwords(self):
        wsd = LeLeskWSD()
        print(wsd.stopwords)

    def test_caching(self):
        wsd = LeLeskWSD()
        # make sure that we have a token list
        fish_synsets = wsd.smart_synset_search('fish', 'n')
        n02512053 = fish_synsets['02512053-n']
        leset = wsd.build_lelesk_set(n02512053.ID)
        self.assertEqual(len(leset), 192)

        # try to cache our token list now ...
        DB_PATH = os.path.abspath('./data/test_leskcache.db')
        print('Test DB loc: {}'.format(DB_PATH))
        l = LeskCache(db_file=DB_PATH)
        # l = LeskCache()
        l.cache(str(n02512053.ID), leset)
        l.cache(n02512053.ID, leset)  # cache this twice
        ls = l.select(n02512053.ID)
        self.assertEqual(len(ls), 192)


if __name__ == '__main__':
    unittest.main()
