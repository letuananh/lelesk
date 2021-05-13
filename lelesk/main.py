#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Le's LESK - Word Sense Disambiguation Package
"""

# This code is a part of lelesk library: https://github.com/letuananh/lelesk
# :copyright: (c) 2014 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import logging
import os.path
import operator
from collections import defaultdict as dd
from collections import namedtuple

import nltk
from nltk.corpus import stopwords
from texttaglib.chirptext import FileHelper
from texttaglib.chirptext import Counter, Timer, uniquify, header, TextReport
from texttaglib.puchikarui import Schema

from .config import LLConfig
from .util import ptpos_to_wn, PUNCS
from yawlib import SynsetID, YLConfig
from yawlib import GWordnetSQLite as GWNSQL
from yawlib import WordnetSQL as WSQL

# -----------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------

ScoreTup = namedtuple('Score', 'candidate score freq'.split())
WSDCandidate = namedtuple('WSDCandidate', 'id synset tokens'.split())


class LeLeskWSD:
    """ Le's LESK algorithm for Word-Sense Disambiguation
    """
    def __init__(self, wng_db_loc=None, wn30_loc=None, verbose=False, dbcache=None):
        logging.getLogger(__name__).debug("Initializing LeLeskWSD object ...")
        self.wng_db_loc = wng_db_loc if wng_db_loc else YLConfig.GWN30_DB
        self.wn30_loc = wn30_loc if wn30_loc else YLConfig.WNSQL30_PATH
        self.gwn = GWNSQL(self.wng_db_loc)
        self.wn = WSQL(self.wn30_loc)
        self.__stopwords = None  # this should be loaded only once
        self.PUNCS = set(PUNCS)

        if dbcache and not isinstance(dbcache, LeskCache):
            dbcache = LeskCache(dbcache)
        self.dbcache = dbcache
        self._lemmatizer = None
        self.candidates_cache = {}
        self.verbose = verbose
        self.word_cache = {}

        # database context for faster access
        self.__dbcache_ctx = None
        self.__gwn_ctx = None
        self.__wn_ctx = None
        logging.getLogger(__name__).debug("LeLeskWSD object has been initialized ...")

    def connect(self):
        """ Use a single database connection for DB access """
        self.disconnect()
        if self.dbcache is not None:
            self.__dbcache_ctx = self.dbcache.db.ctx()
        self.__gwn_ctx = self.gwn.ctx()
        self.__wn_ctx = self.wn.ctx()

    def disconnect(self):
        if self.__dbcache_ctx is not None:
            self.__dbcache_ctx.close()
            self.__dbcache_ctx = None
        if self.__gwn_ctx is not None:
            self.__gwn_ctx.close()
            self.__gwn_ctx = None
        if self.__wn_ctx is not None:
            self.__wn_ctx.close()
            self.__wn_ctx = None

    @property
    def stopwords(self):
        if self.__stopwords is None:
            self.__stopwords = stopwords.words('english')
            self.__stopwords.extend(PUNCS)
        return self.__stopwords

    @property
    def lemmatizer(self):
        if self._lemmatizer is None:
            self._lemmatizer = nltk.WordNetLemmatizer()
        return self._lemmatizer

    def lemmatize(self, words):
        """ Return a list of triplets (surface, pos, lemma) """
        tags = nltk.pos_tag(words)
        tokens = [(w, pos, self.lemmatizer.lemmatize(w, pos=ptpos_to_wn(pos, default='n'))) for w, pos in tags]
        return tokens  # [(surface, tag, lemma)]

    def lemmatize_ttl(self, sent):
        tags = nltk.pos_tag([t.text for t in sent.tokens])
        for token, (surface, pos) in zip(sent, tags):
            token.pos = pos
            token.lemma = self.lemmatizer.lemmatize(surface, pos=ptpos_to_wn(pos, default='n'))
        return sent

    def tokenize(self, sentence_text):
        return nltk.word_tokenize(sentence_text)

    def smart_synset_search(self, lemma, pos, deep_select=False):
        sses = self.gwn.search(lemma=lemma, pos=pos, deep_select=deep_select, ctx=self.__gwn_ctx)
        if len(sses) == 0:
            # try replace '-' with space
            sses = self.gwn.search(lemma=lemma.replace('-', ' '), pos=pos, ctx=self.__gwn_ctx)
        return sses

    def build_lelesk_for_word(self, a_word, pos=None, deep_select=False):
        cache_key = (a_word, pos)
        if cache_key in self.word_cache:
            return self.word_cache[cache_key]
        synsets = self.smart_synset_search(lemma=a_word, pos=pos, deep_select=deep_select)
        candidates = self.build_candidates(synsets)
        self.word_cache[cache_key] = candidates
        return candidates

    def build_candidates(self, synsets):
        candidates = []
        for idx, ss in enumerate(synsets):
            tokens = self.build_lelesk_set(ss.ID)
            candidates.append(WSDCandidate(idx + 1, ss, tokens))
        return candidates

    def build_lelesk_set(self, a_sid):
        sid_obj = SynsetID.from_string(a_sid)
        if self.dbcache is not None:
            # try to fetch from DB then ...
            lelesk_tokens = self.dbcache.select(sid_obj, ctx=self.__dbcache_ctx)
            if lelesk_tokens:
                return lelesk_tokens
        lelesk_tokens = []
        ss = self.gwn.get_synset(a_sid, ctx=self.__gwn_ctx)
        lelesk_tokens.extend(ss.get_tokens())
        lelesk_tokens.extend(ss.get_gramwords())
        # Retrieving tagged synsets
        sscol = self.gwn.get_by_keys(ss.get_tags(), ctx=self.__gwn_ctx)
        for s in sscol:
            lelesk_tokens.extend(s.get_tokens())
            lelesk_tokens.extend(s.get_gramwords())

        # Get hypehypo information from WordNet 30 DB
        ssids = self.wn.hypehypo(ss.ID, ctx=self.__wn_ctx)
        # Get synsets from Gloss WordNet
        sscol = self.gwn.get_synsets(ssids, ctx=self.__gwn_ctx)
        # dump_synsets(ss)
        for s in sscol:
            lelesk_tokens.extend(s.get_tokens())
            lelesk_tokens.extend(s.get_gramwords())

        uniquified_lelesk_tokens = [w for w in uniquify(lelesk_tokens) if w not in self.stopwords]
        # try to cache this token list ...
        if self.dbcache:
            self.dbcache.cache(sid_obj, uniquified_lelesk_tokens)
        return uniquified_lelesk_tokens

    def prepare_data(self, sentence_text, remove_stop_words=True):
        """Given a sentence as a raw text string, perform tokenization, lemmatization
        """
        # Tokenization
        words = self.tokenize(sentence_text)
        # Lemmatization
        tokens = self.lemmatize(words)
        if remove_stop_words:
            return [t for t in tokens if t[0] not in self.stopwords and t[2] not in self.stopwords]
        else:
            return tokens

    def lelesk_wsd(self, word, sentence_text='', expected_sense='', lemmatizing=True, pos=None, context=None, synsets=None, remove_stop_words=True, **kwargs):
        """ Perform Word-sense disambiguation with extended simplified LESK and annotated WordNet 3.0
        """
        # 1. Retrieve candidates for the given word
        if not synsets:
            if (word, pos) not in self.candidates_cache:
                self.candidates_cache[(word, pos)] = self.build_lelesk_for_word(word, pos=pos)
            candidates = self.candidates_cache[(word, pos)]
        else:
            candidates = self.build_candidates(synsets)

        # 2. Calculate overlap between the context and each given word
        if not context:
            context = uniquify([x[2] for x in self.prepare_data(sentence_text, remove_stop_words=remove_stop_words)])

        if remove_stop_words:
            context_set = set(x for x in context if self.stopwords and x not in self.stopwords)
        else:
            context_set = set(context)
            
        scores = []

        logging.getLogger(__name__).info("candidate for {} => {}".format(word, list(c.synset for c in candidates)))
        for candidate in candidates:
            candidate_set = set(candidate.tokens)
            score = len(context_set.intersection(candidate_set))
            scores.append(ScoreTup(candidate, score, self.wn.get_tagcount(candidate.synset.ID.to_wnsql(), ctx=self.__wn_ctx)))
            # scores.append([candidate, score, candidate.sense.tagcount])
        scores.sort(key=operator.itemgetter(1, 2))
        scores.reverse()
        return scores

    def mfs_wsd(self, word, sentence_text, expected_sense='', lemmatizing=True, pos=None, synsets=None, **kwargs):
        """Perform Word-sense disambiguation with just most-frequent senses
        """
        # 1. Retrieve candidates for the given word
        if not synsets:
            synsets = self.smart_synset_search(lemma=word, pos=pos)
        candidates = []
        for idx, ss in enumerate(synsets):
            candidates.append(WSDCandidate(idx + 1, ss, []))

        scores = []
        for candidate in candidates:
            freq = self.wn.get_tagcount(candidate.synset.ID.to_wnsql(), ctx=self.__wn_ctx)
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
        """ Create an instance of LeskCache

        Arguments:
            wsd       -- An instance of LeLeskWSD
            db_file   -- Path to Cache DB file (default to ./data/lesk_cache.db)
            debug_dir -- Details of how tokens are generated for synset will be stored here.
            (Default values are defined in config.py)
        """
        self.wsd = wsd
        self.db_file = db_file if db_file else LLConfig.LELESK_CACHE_DB_LOC
        self.debug_dir = debug_dir if debug_dir else LLConfig.LELESK_CACHE_DEBUG_DIR
        self.db = LeskCacheSchema(self.db_file)
        # try to setup DB if needed
        if self.db_file is not None:
            # Create dir if needed
            logging.getLogger(__name__).info("LeskCache DB is located at {}".format(self.db_file))
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

    def select(self, synsetid, ctx=None):
        result = self.db.tokens.select('synsetid=?', (str(synsetid),), ctx=ctx)
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
            gwn_skmap[item.sensekey] = item.ID
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
                logging.getLogger(__name__).info("Generating tokens for %s (%s/%s)" % (synset.id, idx, total_synsets))
                debug_file = TextReport(os.path.join(self.debug_dir, synset.offset + '.txt'))
                tokens = self.wsd.build_lelesk_set(synset.id, debug_file)
                for token in tokens:
                    self.db.tokens.insert(synset.id, token, ctx=ctx)
