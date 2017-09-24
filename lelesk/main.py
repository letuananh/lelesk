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

import logging
import os.path
import operator
from collections import defaultdict as dd
from collections import namedtuple

import nltk
# from nltk import WordNetLemmatizer
from nltk.corpus import stopwords
from chirptext import FileHelper
from chirptext import Counter, Timer, uniquify, header, TextReport
from puchikarui import Schema

from .config import LLConfig
from yawlib import SynsetID, YLConfig
from yawlib import GWordnetSQLite as GWNSQL
from yawlib import WordnetSQL as WSQL

#-----------------------------------------------------------------------
# CONFIGURATION
#-----------------------------------------------------------------------


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

ScoreTup = namedtuple('Score', 'candidate score freq'.split())
WSDCandidate = namedtuple('WSDCandidate', 'id synset tokens'.split())


class LeLeskWSD:
    ''' Le's LESK algorithm for Word-Sense Disambiguation
    '''
    def __init__(self, wng_db_loc=None, wn30_loc=None, verbose=False, dbcache=None):
        if verbose:
            print("Initializing LeLeskWSD object ...")
        self.wng_db_loc = wng_db_loc if wng_db_loc else YLConfig.GWN30_DB
        self.wn30_loc = wn30_loc if wn30_loc else YLConfig.WNSQL30_PATH
        self.gwn = GWNSQL(self.wng_db_loc)
        self.wn = WSQL(self.wn30_loc)
        self.tokenized_sentence_cache = {}
        self.lemmatized_word_cache = {}
        self.lelesk_tokens_sid_cache = {}  # cache tokens of a given sid

        if dbcache and not isinstance(dbcache, LeskCache):
            dbcache = LeskCache(dbcache)
        self.dbcache = dbcache
        self._lemmatizer = None
        self.candidates_cache = {}
        self.verbose = verbose
        self.word_cache = {}
        if verbose:
            print("LeLeskWSD object has been initialized ...")

    @property
    def lemmatizer(self):
        if self._lemmatizer is None:
            self._lemmatizer = nltk.WordNetLemmatizer()
        return self._lemmatizer

    def smart_synset_search(self, term, pos):
        sses = self.gwn.get_synsets_by_term(term=term, pos=pos)
        if len(sses) == 0:
            # try replace '-' with space
            sses = self.gwn.get_synsets_by_term(term=term.replace('-', ' '), pos=pos)
        return sses

    def build_lelesk_for_word(self, a_word, pos=None):
        cache_key = (a_word, pos)
        if cache_key in self.word_cache:
            return self.word_cache[cache_key]
        synsets = self.smart_synset_search(term=a_word, pos=pos)
        candidates = self.build_candidates(synsets)
        self.word_cache[cache_key] = candidates
        return candidates

    def build_candidates(self, synsets):
        candidates = []
        for idx, ss in enumerate(synsets):
            tokens = self.build_lelesk_set(ss.sid)
            candidates.append(WSDCandidate(idx + 1, ss, tokens))
        return candidates

    def build_lelesk_set(self, a_sid):
        sid_obj = SynsetID.from_string(a_sid)
        if self.dbcache:
            # try to fetch from DB then ...
            lelesk_tokens = self.dbcache.select(sid_obj)
            if lelesk_tokens:
                return lelesk_tokens
        # otherwise build the token list ...
        if a_sid in self.lelesk_tokens_sid_cache:
            return self.lelesk_tokens_sid_cache[a_sid]
        # Try to get by WN30 synsetID first, then try by GWN synsetID
        lelesk_tokens = []

        wn30_ss = self.wn.get_senseinfo_by_sid(a_sid)
        ss = None
        if not wn30_ss:
            sses = self.gwn.get_synset_by_id(a_sid)
            if len(sses) > 0:
                ss = sses[0]
        else:
            try:
                ss = self.gwn.get_synset_by_sk(wn30_ss.sensekey)
            except:
                # TODO: no sensekey???
                ss = None
        if not ss:
            return []
        else:
            lelesk_tokens.extend(ss.get_tokens())
            lelesk_tokens.extend(ss.get_gramwords())

        # Retrieving tagged synsets
        sscol = self.gwn.get_synset_by_sks(ss.get_tags())
        for s in sscol:
            lelesk_tokens.extend(s.get_tokens())
            lelesk_tokens.extend(s.get_gramwords())

        # Get hypehypo information from WordNet 30 DB
        wn30_hh_sids = self.wn.get_hypehypo(ss.sid)
        # Convert them to GWN sids
        gwn_sids = [str(sid.dpos) + str(sid.dsynsetid)[1:] for sid in wn30_hh_sids]
        # Get synsets from Gloss WordNet
        sscol = self.gwn.get_synsets_by_ids(gwn_sids)
        # dump_synsets(ss)
        for s in sscol:
            lelesk_tokens.extend(s.get_tokens())
            lelesk_tokens.extend(s.get_gramwords())

        uniquified_lelesk_tokens = [w for w in uniquify(lelesk_tokens) if w not in stopwords.words('english')]

        self.lelesk_tokens_sid_cache[a_sid] = uniquified_lelesk_tokens
        # try to cache this token list ...
        if self.dbcache:
            self.dbcache.cache(sid_obj, uniquified_lelesk_tokens)
        return uniquified_lelesk_tokens

    def tokenize(self, sentence_text):
        if sentence_text not in self.tokenized_sentence_cache:
            self.tokenized_sentence_cache[sentence_text] = nltk.word_tokenize(sentence_text)
        return self.tokenized_sentence_cache[sentence_text]

    def lemmatize(self, word):
        if word not in self.lemmatized_word_cache:
            self.lemmatized_word_cache[word] = self.lemmatizer.lemmatize(word)
        return self.lemmatized_word_cache[word]

    def prepare_data(self, sentence_text):
        '''Given a sentence as a raw text string, perform tokenization, lemmatization
        '''
        # Tokenization
        tokens = self.tokenize(sentence_text)
        # Lemmatization
        tokens = [self.lemmatize(x) for x in tokens] + tokens
        return [w.lower() for w in tokens if w not in stopwords.words('english')]

    def lelesk_wsd(self, word, sentence_text='', expected_sense='', lemmatizing=True, pos=None, context=None, synsets=None):
        ''' Perform Word-sense disambiguation with extended simplified LESK and annotated WordNet 3.0
        '''
        # 1. Retrieve candidates for the given word
        if not synsets:
            if (word, pos) not in self.candidates_cache:
                self.candidates_cache[(word, pos)] = self.build_lelesk_for_word(word, pos=pos)
            candidates = self.candidates_cache[(word, pos)]
        else:
            candidates = self.build_candidates(synsets)

        # 2. Calculate overlap between the context and each given word
        if not context:
            context = uniquify(self.prepare_data(sentence_text))

        scores = []

        context_set = set(context)
        for candidate in candidates:
            candidate_set = set(candidate.tokens)
            score = len(context_set.intersection(candidate_set))
            scores.append(ScoreTup(candidate, score, self.wn.get_tagcount(candidate.synset.sid.to_wnsql())))
            # scores.append([candidate, score, candidate.sense.tagcount])
        scores.sort(key=operator.itemgetter(1, 2))
        scores.reverse()
        return scores

    def mfs_wsd(self, word, sentence_text, expected_sense='', lemmatizing=True, pos=None, synsets=None):
        '''Perform Word-sense disambiguation with just most-frequent senses
        '''
        # 1. Retrieve candidates for the given word
        if not synsets:
            if (word, pos) not in self.candidates_cache:
                self.candidates_cache[(word, pos)] = self.build_lelesk_for_word(word, pos=pos)
            candidates = self.candidates_cache[(word, pos)]
        else:
            candidates = self.build_candidates(synsets)
        scores = []
        #
        for candidate in candidates:
            freq = self.wn.get_tagcount(candidate.synset.sid.to_wnsql())
            score = freq
            scores.append(ScoreTup(candidate, score, freq))
        scores.sort(key=operator.itemgetter(1))
        scores.reverse()
        return scores


class LeskCacheSchema(Schema):
    def __init__(self, data_source=None, setup_file=LLConfig.LELESK_CACHE_DB_INIT_SCRIPT):
        Schema.__init__(self, data_source, setup_file=setup_file)
        # tokens: synsetid token
        self.add_table('tokens', 'synsetid token'.split())
        # synset: synsetid offset pos synsetid_wn30 freq
        self.add_table('synset', 'synsetid offset pos synsetid_gwn freq'.split())
        # sensekey: synsetid sensekey
        self.add_table('sensekey', 'synsetid sensekey'.split())
        # term: synsetid term
        self.add_table('term', 'synsetid term'.split())


class LeskCache:
    def __init__(self, db_file=None, wsd=None, debug_dir=None):
        ''' Create an instance of LeskCache

        Arguments:
            wsd       -- An instance of LeLeskWSD
            db_file   -- Path to Cache DB file (default to ./data/lesk_cache.db)
            debug_dir -- Details of how tokens are generated for synset will be stored here.
            (Default values are defined in config.py)
        '''
        self.wsd = wsd
        self.db_file = db_file if db_file else LLConfig.LELESK_CACHE_DB_LOC
        self.debug_dir = debug_dir if debug_dir else LLConfig.LELESK_CACHE_DEBUG_DIR
        self.db = LeskCacheSchema(self.db_file)
        # try to setup DB if needed
        if self.db_file is not None:
            # Create dir if needed
            logger.info("LeskCache DB is located at {}".format(self.db_file))
            if self.db_file != ':memory:':
                FileHelper.create_dir(os.path.dirname(self.db_file))

    def info(self):
        header("Pre-generate LESK tokens for all synsets for faster WSD")
        print("Path to WordNet Gloss Corpus: %s" % self.wsd.wng_db_loc)
        print("Path to WordNet 3.0 SQLite  : %s" % self.wsd.wn30_loc)
        print("Path to LeLesk cache DB     : %s" % self.db_file)
        print("Debug info will be stored in: %s" % self.debug_dir)
        print("--")
        print("")

    def cache(self, synsetid, tokens):
        # delete tokens first
        self.db.ds.execute('DELETE FROM tokens WHERE synsetid=?', [str(synsetid)])
        with self.db.ctx() as ctx:
            for token in tokens:
                self.db.tokens.insert(str(synsetid), token, ctx=ctx)

    def select(self, synsetid):
        result = self.db.tokens.select('synsetid=?', (str(synsetid),))
        if result:
            return [x.token for x in result]
        else:
            return None

    def validate(self):
        gwn = self.wsd.gwn
        wn = self.wsd.wn
        t = Timer()

        print("Validating WordNet databases ...")
        # Comparing synsets
        wn_synsets = wn.get_all_synsets()
        synsetids = set()
        for row in wn_synsets:  # 'synsetid', 'lemma', 'sensekey', 'tagcount'
            synsetids.add(row.synsetid)
        print("Synsets in WordNet SQLite: %s" % len(synsetids))

        t.start("Selecting from WordNet Gloss Corpus")
        gwn_synsets = gwn.all_synsets(deep_select=False)
        offset_map = {}
        for synset in gwn_synsets:
            offset_map[synset.offset] = synset.id
        t.end("Done GWN")
        print("Synsets in WordNet Gloss Corpus: %s" % len(gwn_synsets))

        c = Counter()
        for synsetid in synsetids:
            if str(synsetid)[1:] in offset_map:
                c.count("Match")
            else:
                c.count("Nah")
        c.summarise()

        if c['Match'] != len(gwn_synsets):
            print("Invalid WordNet version detected. Execution aborted!")
            return
        else:
            print("GWN DB and WN30 SQLite DB matched. Proceed with data generation")
        print('')

        t.start('Caching WN30 sensekey map')
        wnsks = wn.get_all_sensekeys()
        wn_skmap = {}
        wn_sidmap = dd(list)
        # map by sensekeys and synsetid
        for item in wnsks:
            wn_skmap[item.sensekey] = item.synsetid
            wn_sidmap[str(item.synsetid)[1:]].append(item.sensekey)
        t.end("Done WN30")

        t.start('Caching GWN sensekey map')
        gwn_ss = gwn.get_all_sensekeys()
        gwn_skmap = {}
        for item in gwn_ss:
            gwn_skmap[item.sensekey] = item.sid
        t.end("Done GWN")

        t.start('Caching GWN tagged sensekey')
        gwn_tags = gwn.get_all_sensekeys_tagged()
        t.end("Done tagged sensekey")

        print("wn30 sensekeys: %s" % len(wnsks))
        print("gwn synsets   : %s" % len(gwn_ss))
        print("All tagged sk : %s" % len(gwn_tags))

        c = Counter()
        for tag in gwn_tags:
            if tag not in gwn_skmap:
                print("sk [%s] does not exist in GWN" % tag)
                c.count("GWN Not Found")
            else:
                c.count("GWN Found")
            if tag not in wn_skmap:
                if tag in gwn_skmap:
                    gwn_sid = gwn_skmap[tag][1:]
                    # print("Searching %s" % (gwn_sid))
                    if gwn_sid in wn_sidmap:
                        candidates = wn_sidmap[gwn_sid]
                        derivative = None
                        for cand in candidates:
                            if tag.split('%')[0] == cand.split('%')[0]:
                                derivative = cand
                                break
                        if derivative:
                            c.count("WN30 Found derivative")
                        else:
                            # not found at all
                            c.count("WN30 Not Found At all")
                            print("sk [%s] does not exist in WN30 at all ..." % tag)
                else:
                    c.count("WN30 & GWN Not Found")
                    print("sk [%s] does not exist in WN30" % tag)
            else:
                c.count("WN30 Found")
        c.summarise()

    def generate(self):
        synsets = self.wsd.gwn.all_synsets(deep_select=False)
        with self.db.ds.open() as ctx:
            total_synsets = len(synsets)
            for idx, synset in enumerate(synsets):
                logger.info("Generating tokens for %s (%s/%s)" % (synset.id, idx, total_synsets))
                debug_file = TextReport(os.path.join(self.debug_dir, synset.offset + '.txt'))
                tokens = self.wsd.build_lelesk_set(synset.id, debug_file)
                for token in tokens:
                    self.db.tokens.insert(synset.id, token, ctx=ctx)
