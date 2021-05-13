#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test LeLesk package
"""

# This code is a part of lelesk library: https://github.com/letuananh/lelesk
# :copyright: (c) 2014 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

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
