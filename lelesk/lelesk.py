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

import os.path
import argparse
import operator
import itertools
from collections import defaultdict as dd
from collections import namedtuple
from chirptext.leutile import StringTool, Counter, Timer, uniquify, header
from glosswordnet import XMLGWordNet, SQLiteGWordNet
from wordnetsql import WordNetSQL as WSQL

import nltk
from nltk import WordNetLemmatizer
from nltk.corpus import stopwords
#-----------------------------------------------------------------------
# CONFIGURATION
#-----------------------------------------------------------------------

ScoreTup = namedtuple('Score', 'candidate score freq'.split())

class LeLeskWSD:
    ''' Le's LESK algorithm for Word-Sense Disambiguation
    '''
    def __init__(self, wng_db_loc, wn30_loc, verbose=True):
        if verbose:
            print("Initializing LeLeskWSD object ...")
        self.wng_db_loc = wng_db_loc
        self.wn30_loc = wn30_loc
        self.gwn = SQLiteGWordNet(wng_db_loc)
        self.wn = WSQL(wn30_loc)
        self.tokenized_sentence_cache = {}
        self.lemmatized_word_cache = {}
        self.lelesk_tokens_sid_cache = {} # cache tokens of a given sid

        # Cache data for faster access
        #t = Timer()
        #t.start("Importing data into memory for faster access")
        #self.wn.cache_tagcounts()
        #self.wn.cache_all_hypehypo()
        #t.end("Data imported ..")

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

    def build_lelesk_for_word(self, a_word, pos=None, dump_candidate=True):
        cache_key = (a_word, pos)
        if cache_key in self.word_cache:
            return self.word_cache[cache_key]
        sses = self.smart_synset_search(term=a_word, pos=pos)
        print("Retrieving LeLesk candidates for word ``%s''" % a_word)
        x = itertools.count(1)
        candidates = []
        cantemp = namedtuple('WSDCandidate', 'id synset tokens'.split())
        for ss in sses:
            canid = next(x)
            header('>>> CANDIDATE #%s <<<' % canid,'h2')
            tokens = self.build_lelesk_set(ss.sid)
            candidates.append(cantemp(canid, ss, tokens))
            print('')

        if dump_candidate:
            header("Final candidates for the word ``%s'' and their tokens" % a_word, 'h2')
            for candidate in candidates:
                print("\tCandidate #%s: %s (%s) => set(%s)" % (
                candidate.id, candidate.synset.get_synsetid(), candidate.synset.get_terms_text(), candidate.tokens))
        self.word_cache[cache_key] = candidates
        return candidates

    def build_lelesk_set(self, a_sid):
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
            sses = self.gwn.get_synset_by_sk(wn30_ss.sensekey)
            if len(sses) > 0:
                ss = sses[0]

        if not ss:
            print("Synset ID [%s] not found" % (a_sid))
            return False
        else:
            print("\tSynset: %s (terms=%s | keys=%s)" % (ss.get_synsetid(), ss.terms, ss.keys))
            for gloss in [ g for g in ss.raw_glosses if g.cat == 'orig' ]:
                print("\t\t%s" % gloss) 
            print("\t\tTokens => %s" % (ss.get_gramwords())) # Get gloss items
            print("\t\tTagged => %s" % ss.get_tags()) # Get tagged sensekeys
            print("")
            lelesk_tokens.extend(ss.get_terms_text())
            lelesk_tokens.extend(ss.get_gramwords())  


        header("Retrieving tagged synsets", 'h3')
        sscol = self.gwn.get_synset_by_sks(ss.get_tags())
        for s in sscol:
            print("\t\tSynset: %s (terms=%s | keys=%s)" % (s.get_synsetid(), s.terms, s.keys))
            lelesk_tokens.extend(s.get_terms_text())
            lelesk_tokens.extend(s.get_gramwords()) 

            # get raw glosses
            for gloss in [ g for g in s.raw_glosses if g.cat == 'orig' ]:
                print("\t\t%s" % gloss) 
            print("\t\t\tTokens => %s" % (s.get_gramwords())) # Get gloss items
            print("\t\t\tTagged => %s" % s.get_tags()) # Get tagged sensekeys

            print("")

        header("Retrieving hypernyms & hyponyms of %s " % ss.get_synsetid(), 'h3')
        wn30_hh_sids = self.wn.get_hypehypo(ss.to_wn30_synsetid()) # Get hypehypo information from WordNet 30 DB
        gwn_sids = [ str(sid.dpos) + str(sid.dsynsetid)[1:] for sid in wn30_hh_sids ] # Convert them to GWN sids 
        sscol = self.gwn.get_synset_by_ids(gwn_sids) # Get synsets from Gloss WordNet
        # dump_synsets(ss)
        for s in sscol:
            print("\t\tSynset: %s (terms=%s | keys=%s)" % (s.get_synsetid(), s.terms, s.keys))
            lelesk_tokens.extend(s.get_terms_text())
            lelesk_tokens.extend(s.get_gramwords()) 

            # get raw glosses
            for gloss in s.raw_glosses:
                if gloss.cat == 'orig':
                    print("\t\t%s" % gloss) 
            # Get gloss items
            print("\t\t\tTokens => %s" % (s.get_gramwords()))
            # Get tagged sensekeys
            print("\t\t\tTagged => %s" % s.get_tags())

            print("")

        header("Lelesk tokens", 'h3')
        print("\t\tFull list                    : %s" % lelesk_tokens)
        uniquified_lelesk_tokens = [ w for w in uniquify(lelesk_tokens) if w not in stopwords.words('english') ]
        print("\t\tFull set (no dup & stopwords): %s" % uniquified_lelesk_tokens)

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

    def lelesk_wsd(self, word, sentence_text, expected_sense='', lemmatizing=True, pos=None, context=None):
        ''' Perform Word-sense disambiguation with extended simplified LESK and annotated WordNet 3.0
        '''
        header("LELESK:: Disambiguating word ``%s'' in context ``%s''" % (word, sentence_text))
        
        #1. Retrieve candidates for the given word
        if (word, pos) not in self.candidates_cache:
            self.candidates_cache[(word, pos)] = self.build_lelesk_for_word(word, pos=pos)
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
                    , self.wn.get_tagcount(candidate.synset.to_wn30_synsetid())
                )
            )
            # scores.append([candidate, score, candidate.sense.tagcount])
        scores.sort(key=operator.itemgetter(1, 2))
        scores.reverse()

        if self.verbose:
            print("-" * 40)
            print("WSD for the word: %s" % (word,))
            print("Sentence text   : %s" % (sentence_text,))
            print("Context bag     : set(%s)" % context)
            print("POS             : %s" % (pos,))
            if expected_sense:
                print('Expected sense  : %s' % (expected_sense,))
            if len(scores) > 0:
                print('Suggested sense : %s (score=%s|freq=%s) - %s' % (
                    scores[0].candidate.synset.get_synsetid()
                    ,scores[0].score
                    ,scores[0].freq
                    ,scores[0].candidate.synset.get_orig_gloss()))
            else:
                print('No sense found')
            candidate_count = itertools.count(2)
            for score in scores[1:]:
                print('Ranked #%s : %s (score=%s|freq=%s) - %s' % (
                    next(candidate_count)
                    ,score.candidate.synset.get_synsetid()
                    ,score.score
                    ,score.freq
                    ,score.candidate.synset.get_orig_gloss()))
        return scores

    def mfs_wsd(self, word, sentence_text, expected_sense='', lemmatizing=True, pos=None):
        '''Perform Word-sense disambiguation with just most-frequent senses
        '''
        header("MFS-WSD:: Disambiguating word ``%s'' in context ``%s''" % (word, sentence_text))
        
        #1. Retrieve candidates for the given word
        if (word, pos) not in self.candidates_cache:
            self.candidates_cache[(word, pos)] = self.build_lelesk_for_word(word, pos=pos)
        candidates = self.candidates_cache[(word, pos)]
        
        scores = []
        
        for candidate in candidates:
            freq = self.wn.get_tagcount(candidate.synset.to_wn30_synsetid())
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

        if self.verbose:
            print("-" * 40)
            print("WSD for the word: %s" % (word,))
            print("Sentence text   : %s" % (sentence_text,))
            print("POS             : %s" % (pos,))
            if expected_sense:
                print('Expected sense  : %s' % (expected_sense,))
            if len(scores) > 0:
                print('Suggested sense : %s (score=%s|freq=%s) - %s' % (
                    scores[0].candidate.synset.get_synsetid()
                    ,scores[0].score
                    ,scores[0].freq
                    ,scores[0].candidate.synset.get_orig_gloss()))
            else:
                print('No sense found')
            candidate_count = itertools.count(2)
            for score in scores[1:]:
                print('Ranked #%s : %s (score=%s|freq=%s) - %s' % (
                    next(candidate_count)
                    ,score.candidate.synset.get_synsetid()
                    ,score.score
                    ,score.freq
                    ,score.candidate.synset.get_orig_gloss()))
        return scores        