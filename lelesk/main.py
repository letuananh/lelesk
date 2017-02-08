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

import os.path
import operator
import itertools
from collections import defaultdict as dd
from collections import namedtuple

import nltk
from nltk import WordNetLemmatizer
from nltk.corpus import stopwords
# from chirptext.leutile import StringTool
from chirptext.leutile import Counter, Timer, uniquify, header, TextReport, jilog
from puchikarui import Schema, Execution  # DataSource, Table

from .config import LLConfig
from yawlib.config import YLConfig
from yawlib.glosswordnet import SQLiteGWordNet
from yawlib.wordnetsql import WordNetSQL as WSQL

#-----------------------------------------------------------------------
# CONFIGURATION
#-----------------------------------------------------------------------


ScoreTup = namedtuple('Score', 'candidate score freq'.split())


class LeLeskWSD:
    ''' Le's LESK algorithm for Word-Sense Disambiguation
    '''
    def __init__(self, wng_db_loc=None, wn30_loc=None, verbose=False, report_file=None):
        if report_file is None:
            self.report_file = TextReport()
        else:
            self.report_file = report_file
        if verbose:
            print("Initializing LeLeskWSD object ...")
        self.wng_db_loc = wng_db_loc if wng_db_loc else YLConfig.WORDNET_30_GLOSS_DB_PATH
        self.wn30_loc = wn30_loc if wn30_loc else YLConfig.WORDNET_30_PATH
        self.gwn = SQLiteGWordNet(self.wng_db_loc)
        self.wn = WSQL(self.wn30_loc)
        self.tokenized_sentence_cache = {}
        self.lemmatized_word_cache = {}
        self.lelesk_tokens_sid_cache = {}  # cache tokens of a given sid

        self.lemmatizer = WordNetLemmatizer()
        self.candidates_cache = {}
        self.verbose = verbose
        self.word_cache = {}
        if verbose:
            print("LeLeskWSD object has been initialized ...")

    def smart_synset_search(self, term, pos):
        sses = self.gwn.get_synsets_by_term(term=term, pos=pos)
        if len(sses) == 0:
            # try replace '-' with space
            sses = self.gwn.get_synsets_by_term(term=term.replace('-', ' '), pos=pos)
        return sses

    def build_lelesk_for_word(self, a_word, pos=None, dump_candidate=True, report_file=None):
        if report_file is None:
            report_file = self.report_file
        cache_key = (a_word, pos)
        if cache_key in self.word_cache:
            return self.word_cache[cache_key]
        sses = self.smart_synset_search(term=a_word, pos=pos)
        report_file.print("Retrieving LeLesk candidates for word ``%s'' (pos=%s)" % (a_word, pos))
        x = itertools.count(1)
        candidates = []
        cantemp = namedtuple('WSDCandidate', 'id synset tokens'.split())
        for ss in sses:
            canid = next(x)
            report_file.header('>>> CANDIDATE #%s <<<' % canid, 'h2')
            tokens = self.build_lelesk_set(ss.sid, report_file=report_file)
            candidates.append(cantemp(canid, ss, tokens))
            report_file.print('')

        if dump_candidate:
            report_file.header("Final candidates for the word ``%s'' and their tokens" % a_word, 'h2')
            for candidate in candidates:
                report_file.print("\tCandidate #%s: %s (%s) => set(%s)" % (
                candidate.id, candidate.synset.sid, candidate.synset.get_terms_text(), candidate.tokens))
        self.word_cache[cache_key] = candidates
        return candidates

    def build_lelesk_set(self, a_sid, report_file=None):
        if report_file is None:
            report_file = self.report_file
        if a_sid in self.lelesk_tokens_sid_cache:
            return self.lelesk_tokens_sid_cache[a_sid]
        ''' Try to get by WN30 synsetID first, then try by GWN synsetID
        '''
        lelesk_tokens = []

        wn30_ss = self.wn.get_senseinfo_by_sid(a_sid)
        ss = None
        if not wn30_ss:
            sses = self.gwn.get_synset_by_id(a_sid)
            if len(sses) > 0:
                ss = sses[0]
        else:
            ss = self.gwn.get_synset_by_sk(wn30_ss.sensekey)

        if not ss:
            report_file.print("Synset ID [%s] not found" % (a_sid))
            return False
        else:
            report_file.print("Synset: %s (terms=%s | keys=%s)" % (ss.sid, ss.terms, ss.keys), level=1)
            for gloss in [ g for g in ss.raw_glosses if g.cat == 'orig' ]:
                report_file.print("%s" % gloss, level=2) 
            report_file.print("Tokens => %s" % (ss.get_gramwords()), level=2) # Get gloss items
            report_file.print("Tagged => %s" % ss.get_tags(), level=2) # Get tagged sensekeys
            report_file.print("")
            lelesk_tokens.extend(ss.get_terms_text())
            lelesk_tokens.extend(ss.get_gramwords())  


        report_file.header("Retrieving tagged synsets", 'h3')
        sscol = self.gwn.get_synset_by_sks(ss.get_tags())
        for s in sscol:
            report_file.print("Synset: %s (terms=%s | keys=%s)" % (s.sid, s.terms, s.keys), level=2)
            lelesk_tokens.extend(s.get_terms_text())
            lelesk_tokens.extend(s.get_gramwords()) 

            # get raw glosses
            for gloss in [ g for g in s.raw_glosses if g.cat == 'orig' ]:
                report_file.print("%s" % gloss, level=2) 
            report_file.print("Tokens => %s" % (s.get_gramwords()), level=3) # Get gloss items
            report_file.print("Tagged => %s" % s.get_tags(), level=3) # Get tagged sensekeys

            report_file.print("")

        report_file.header("Retrieving hypernyms & hyponyms of %s " % ss.sid, 'h3')
        wn30_hh_sids = self.wn.get_hypehypo(ss.sid) # Get hypehypo information from WordNet 30 DB
        gwn_sids = [ str(sid.dpos) + str(sid.dsynsetid)[1:] for sid in wn30_hh_sids ] # Convert them to GWN sids 
        sscol = self.gwn.get_synsets_by_ids(gwn_sids) # Get synsets from Gloss WordNet
        # dump_synsets(ss)
        for s in sscol:
            report_file.print("Synset: %s (terms=%s | keys=%s)" % (s.sid, s.terms, s.keys), level=2)
            lelesk_tokens.extend(s.get_terms_text())
            lelesk_tokens.extend(s.get_gramwords()) 

            # get raw glosses
            for gloss in s.raw_glosses:
                if gloss.cat == 'orig':
                    report_file.print("%s" % gloss, level=2) 
            # Get gloss items
            report_file.print("Tokens => %s" % (s.get_gramwords()), level=3)
            # Get tagged sensekeys
            report_file.print("Tagged => %s" % s.get_tags(), level=3)

            report_file.print("")

        report_file.header("Lelesk tokens", 'h3')
        report_file.print("Full list                    : %s" % lelesk_tokens, level=2)
        uniquified_lelesk_tokens = [ w for w in uniquify(lelesk_tokens) if w not in stopwords.words('english') ]
        report_file.print("Full set (no dup & stopwords): %s" % uniquified_lelesk_tokens, level=2)

        self.lelesk_tokens_sid_cache[a_sid] = uniquified_lelesk_tokens
        return uniquified_lelesk_tokens
        pass

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
        tokens = [ self.lemmatize(x) for x in tokens ] + tokens
        return [ w.lower() for w in tokens if w not in stopwords.words('english') ]

    def lelesk_wsd(self, word, sentence_text, expected_sense='', lemmatizing=True, pos=None, context=None, report_file=None):
        if report_file is None:
            report_file = self.report_file
        ''' Perform Word-sense disambiguation with extended simplified LESK and annotated WordNet 3.0
        '''
        report_file.header("LELESK:: Disambiguating word ``%s'' in context ``%s''" % (word, sentence_text), level='h0')

        #1. Retrieve candidates for the given word
        if (word, pos) not in self.candidates_cache:
            self.candidates_cache[(word, pos)] = self.build_lelesk_for_word(word, pos=pos, report_file=report_file)
        candidates = self.candidates_cache[(word, pos)]
        
        #2. Calculate overlap between the context and each given word
        if not context:
            context = uniquify(self.prepare_data(sentence_text))

        scores = []

        context_set = set(context)
        for candidate in candidates:
            candidate_set = set(candidate.tokens)
            score = len(context_set.intersection(candidate_set))
            scores.append(
                ScoreTup(
                    candidate
                    , score
                    , self.wn.get_tagcount(candidate.synset.sid.to_wnsql())
                )
            )
            # scores.append([candidate, score, candidate.sense.tagcount])
        scores.sort(key=operator.itemgetter(1, 2))
        scores.reverse()

        if self.verbose or report_file.mode is not None:
            report_file.print("-" * 40)
            report_file.print("WSD for the word: %s" % (word,))
            report_file.print("Sentence text   : %s" % (sentence_text,))
            report_file.print("Context bag     : set(%s)" % context)
            report_file.print("POS             : %s" % (pos,))
            if expected_sense:
                report_file.print('Expected sense  : %s' % (expected_sense,))
            if len(scores) > 0:
                report_file.print('Suggested sense : %s (score=%s|freq=%s) - %s' % (
                    scores[0].candidate.synset.sid
                    ,scores[0].score
                    ,scores[0].freq
                    ,scores[0].candidate.synset.get_orig_gloss()))
            else:
                report_file.print('No sense found')
            candidate_count = itertools.count(2)
            for score in scores[1:]:
                report_file.print('Ranked #%s : %s (score=%s|freq=%s) - %s' % (
                    next(candidate_count)
                    ,score.candidate.synset.sid
                    ,score.score
                    ,score.freq
                    ,score.candidate.synset.get_orig_gloss()))
        return scores

    def mfs_wsd(self, word, sentence_text, expected_sense='', lemmatizing=True, pos=None, report_file=None):
        '''Perform Word-sense disambiguation with just most-frequent senses
        '''
        if report_file is None:
            report_file = self.report_file
        report_file.header("MFS-WSD:: Disambiguating word ``%s'' in context ``%s''" % (word, sentence_text))
        
        #1. Retrieve candidates for the given word
        if (word, pos) not in self.candidates_cache:
            self.candidates_cache[(word, pos)] = self.build_lelesk_for_word(word, pos=pos, report_file=report_file)
        candidates = self.candidates_cache[(word, pos)]
        
        scores = []
        
        for candidate in candidates:
            freq = self.wn.get_tagcount(candidate.synset.sid.to_wnsql())
            score = freq
            scores.append(
                ScoreTup(
                    candidate
                    , score
                    , freq
                )
            )
        scores.sort(key=operator.itemgetter(1))
        scores.reverse()

        if self.verbose or report_file.mode is not None:
            report_file.print("-" * 40)
            report_file.print("WSD for the word: %s" % (word,))
            report_file.print("Sentence text   : %s" % (sentence_text,))
            report_file.print("POS             : %s" % (pos,))
            if expected_sense:
                report_file.print('Expected sense  : %s' % (expected_sense,))
            if len(scores) > 0:
                report_file.print('Suggested sense : %s (score=%s|freq=%s) - %s' % (
                    scores[0].candidate.synset.sid
                    ,scores[0].score
                    ,scores[0].freq
                    ,scores[0].candidate.synset.get_orig_gloss()))
            else:
                report_file.print('No sense found')
            candidate_count = itertools.count(2)
            for score in scores[1:]:
                report_file.print('Ranked #%s : %s (score=%s|freq=%s) - %s' % (
                    next(candidate_count)
                    ,score.candidate.synset.sid
                    ,score.score
                    ,score.freq
                    ,score.candidate.synset.get_orig_gloss()))
        return scores        


class LeskCacheSchema(Schema):
    def __init__(self, data_source=None):
        Schema.__init__(self, data_source)
        # tokens: synsetid token
        self.add_table('tokens', 'synsetid token'.split())
        # synset: synsetid offset pos synsetid_wn30 freq
        self.add_table('synset', 'synsetid offset pos synsetid_gwn freq'.split())
        # sensekey: synsetid sensekey
        self.add_table('sensekey', 'synsetid sensekey'.split())
        # term: synsetid term
        self.add_table('term', 'synsetid term'.split())


class LeskCache:
    def __init__(self, wsd, db_file=None, debug_dir=None, report_file=None):
        ''' Create an instance of LeskCache

        Arguments:
            wsd       -- An instance of LeLeskWSD
            db_file   -- Path to Cache DB file (default to ./data/lesk_cache.db)
            debug_dir -- Details of how tokens are generated for synset will be stored here.
            (Default values are defined in config.py)
        '''
        if report_file is None:
            self.report_file = TextReport()
        else:
            self.report_file = report_file
        self.wsd = wsd
        self.db_file = db_file if db_file else LLConfig.LELESK_CACHE_DB_LOC
        self.db = LeskCacheSchema(self.db_file)
        self.script_file = LLConfig.LELESK_CACHE_DB_INIT_SCRIPT
        self.debug_dir = debug_dir if debug_dir else LLConfig.LELESK_CACHE_DEBUG_DIR

    def info(self):
        header("Pre-generate LESK tokens for all synsets for faster WSD")
        print("Path to WordNet Gloss Corpus: %s" % self.wsd.wng_db_loc)
        print("Path to WordNet 3.0 SQLite  : %s" % self.wsd.wn30_loc)
        print("Path to LeLesk cache DB     : %s" % self.db_file)
        print("Debug info will be stored in: %s" % self.debug_dir)
        print("--")
        print("")

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

    def setup(self):
        ''' Setup cache DB'''
        with Execution(self.db) as exe:
            print('Creating database file ...')
            exe.ds.executefile(self.script_file)
            try:
                for token in exe.schema.tokens.select():
                    print(meta)
            except Exception as e:
                print("Error while setting up database ... e = %s" % e)
        pass  # end setup()

    def generate(self, report_file=None):
        if report_file is None:
            report_file = self.report_file
        synsets = self.wsd.gwn.all_synsets(deep_select=False)
        with Execution(self.db) as exe:
            total_synsets = len(synsets)
            for idx, synset in enumerate(synsets):
                jilog("Generating tokens for %s (%s/%s)" % (synset.id, idx, total_synsets))
                debug_file = TextReport(os.path.join(self.debug_dir, synset.offset + '.txt'))
                tokens = self.wsd.build_lelesk_set(synset.id, debug_file)
                for token in tokens:
                    exe.schema.tokens.insert([synset.id, token])
                report_file.print("tokens of %s => %s" % (synset.id, tokens))
            exe.ds.commit()

