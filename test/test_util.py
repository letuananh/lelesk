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
from lelesk import LeLeskWSD, LeskCache


class TestMain(unittest.TestCase):

    def test_synset_search(self):
        wsd = LeLeskWSD()
        nsses = wsd.smart_synset_search('love', 'n')
        vsses = wsd.smart_synset_search('love', 'v')
        self.assertEqual(len(nsses), 6)  # There should be 6 noun synsets
        self.assertEqual(len(vsses), 4)
        doge = wsd.smart_synset_search('doge', 'n')
        self.assertEqual(len(doge), 1)

    def test_lelesk_set(self):
        wsd = LeLeskWSD()
        fish = wsd.smart_synset_search('fish', 'n')
        leset = wsd.build_lelesk_set(fish[0].sid)
        self.assertIn('fish', leset)
        self.assertIn('aquatic', leset)
        self.assertIn('shark', leset)
        # TODO: Test this method properly

    def test_caching(self):
        wsd = LeLeskWSD()
        # make sure that we have a token list
        fish = wsd.smart_synset_search('fish', 'n')
        leset = wsd.build_lelesk_set(fish[0].sid)
        self.assertEqual(len(leset), 192)

        # try to cache our token list now ...
        DB_PATH = os.path.abspath('./data/test_leskcache.db')
        print('Test DB loc: {}'.format(DB_PATH))
        l = LeskCache(db_file=DB_PATH)
        # l = LeskCache()
        l.setup()
        l.cache(str(fish[0].sid), leset)
        l.cache(fish[0].sid, leset)  # cache this twice
        ls = l.select(fish[0].sid)
        self.assertEqual(len(ls), 192)


if __name__ == '__main__':
    unittest.main()
