#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
A tool for converting Gloss WordNet into SQLite
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


TEST_DIR = os.path.dirname(__file__)
TEST_CACHE = os.path.join(TEST_DIR, 'data', 'test_cache.db')


class TestMain(unittest.TestCase):

    def dump_scores(self, scores):
        for candidate, score, freq in scores:
            print("Candidate: {c} | score: {s} | freq: {f}".format(c=candidate.synset, s=score, f=freq))

    def test_data(self):
        return 'fish', 'there are so many fish in the river'

    def test_basic(self):
        print("Test LeLesk WSD")
        # without using cache
        #
        l = LeLeskWSD()
        w, sent = self.test_data()
        scores = l.lelesk_wsd(w, sent, context=sent.split())
        self.dump_scores(scores)
        self.assertEqual(scores[0].candidate.synset.ID, '02512053-n')
        self.assertEqual(scores[0].score, 2)
        self.assertEqual(scores[0].freq, 12)
        # wit tokenizer
        #
        l = LeLeskWSD()
        w, sent = self.test_data()
        scores = l.lelesk_wsd(w, sent)
        self.dump_scores(scores)
        self.assertEqual(scores[0].candidate.synset.ID, '02512053-n')
        self.assertEqual(scores[0].score, 2)
        self.assertEqual(scores[0].freq, 12)

        # With using cache
        #
        l = LeLeskWSD(dbcache=LeskCache(TEST_CACHE))
        scores = l.lelesk_wsd(w, sent, context=sent.split())
        self.dump_scores(scores)
        self.assertEqual(scores[0].candidate.synset.ID, '02512053-n')
        self.assertEqual(scores[0].score, 2)
        self.assertEqual(scores[0].freq, 12)

    def test_cache(self):
        l = LeLeskWSD(dbcache=":memory:")
        l.dbcache.select('01775164-v')

    def test_mfs(self):
        print("Test MFS WSD")
        # without cache
        l = LeLeskWSD()
        l.connect()
        w, sent = self.test_data()
        scores = l.mfs_wsd(w, sent)
        self.assertEqual(scores[0].candidate.synset.ID, '02512053-n')
        self.assertEqual(scores[0].score, 12)
        self.assertEqual(scores[0].freq, 12)

        # with cache
        l = LeLeskWSD(dbcache=LeskCache(TEST_CACHE))
        l.connect()
        w, sent = self.test_data()
        scores = l.mfs_wsd(w, sent)
        self.assertEqual(scores[0].candidate.synset.ID, '02512053-n')
        self.assertEqual(scores[0].score, 12)
        self.assertEqual(scores[0].freq, 12)
        # self.dump_scores(scores)

    def test_fast_wsd(self):
        # disable lemmatizer => faster
        l = LeLeskWSD()
        l.connect()
        w, sent = self.test_data()
        scores = l.mfs_wsd(w, sent, lemmatizing=False)
        self.assertTrue(scores)


if __name__ == '__main__':
    unittest.main()
