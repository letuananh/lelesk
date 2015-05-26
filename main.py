#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
A library for performing Word Sense Disambiguation using Python
Latest version can be found at https://github.com/letuananh/lelesk

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
__copyright__ = "Copyright 2015, lelesk"
__credits__ = [ "Le Tuan Anh" ]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

import sys
import os.path
import re
import sqlite3
import argparse
from operator import itemgetter
from collections import namedtuple
from collections import defaultdict as dd
import xml.etree.ElementTree as ET

import nltk
from nltk import WordNetLemmatizer
from nltk.corpus import stopwords

from chirptext.leutile import *
from wnglosstag import *

#-----------------------------------------------------------------------
# CONFIGURATION
#-----------------------------------------------------------------------
#WORDNET_30_PATH = os.path.expanduser('~/wk/cldata/ntumc/wn-ntumc.db')
WORDNET_30_PATH = os.path.expanduser('~/wordnet/sqlite-30.db')
WORDNET_30_GLOSSTAG_PATH = os.path.expanduser('~/wordnet/glosstag')
NTUMC_PRONOUNS= ["77000021-n", "77000107-a", "77000043-a", "77000041-n", 
                 "77000002-n", "77000061-a", "09604451-n", "09604451-n",
                 "80000333-n", "77000024-a", "80000379-n", "77000050-a", 
                 "77000091-n", "77000082-n", "77000031-n", "07000079-a", 
                 "77000031-n", "77000016-n", "77000052-n", "77000079-n", 
                 "77000039-a", "77000041-n", "77000046-n", "80000413-n", 
                 "77000058-a", "77000061-n", "77000092-n", "77000015-n", 
                 "77000053-n", "77000046-n", "77000015-n", "80000413-n"
                 ]
#-----------------------------------------------------------------------
reword = re.compile('\w+')

Token = namedtuple('Token', ['text', 'sk'])

class XMLCache:
    cache = dict()

    @staticmethod
    def parse(file_path):
        if file_path not in XMLCache.cache:
                XMLCache.cache[file_path] = ET.parse(file_path).getroot()
        return XMLCache.cache[file_path]

    @staticmethod
    def cache_all(root_folder, verbose=True):
        fcount = 0
        for root, subfolders, files in os.walk(root_folder):
            for filename in files:
                if filename.endswith('-wngloss.xml') or filename.endswith('-wnann.xml') or filename.endswith('-wnword.xml'):
                    fullpath = os.path.join(root, filename)
                    XMLCache.parse(fullpath)
                    if verbose:
                        print(('Caching file: %s' % fullpath))
                # print filename
                fcount += 1
        print(("Found %s XML files" % fcount))

class SenseGloss:
    def __init__(self, sid, sfrom, sto, stype):
        self.sid = sid
        self.sfrom = sfrom
        self.sto = sto
        self.stype = stype
        self.tokens = []
        
    def __str__(self):
        return "Sense: %s | from-to: [%s-%s] | type: %s" % (
        self.sid, self.sfrom, self.sto, self.stype)

class SenseInfo:
    '''Store WordNet Sense Information (synsetID, pos, sensekey, etc.)
    '''

    def __init__(self, pos, synsetid, sensekey, wordid='', gloss='', tagcount=0, lemma=''):
        self.pos = pos
        self.sid = synsetid
        self.sk = sensekey
        self.wordid = wordid
        self.gloss = gloss
        self.tagcount = tagcount
        self.lemma = lemma

    @staticmethod
    def normalise_synsetid(sid):
        if len(sid) < 10:
            return '0' * (10 - len(sid)) + sid
        elif len(sid) > 10:
            return sid[-10:]
        else:
            return sid
    
    def get_full_sid(self):
        return self.pos + str(self.sid)[1:]
        
    def __repr__(self):
        return str(self)

    def get_canonical_synsetid(self):
        return '%s-%s' % (str(self.sid)[1:], self.pos)

    def get_gwn_sid(self):
        csid = self.get_canonical_synsetid()
        return csid[-1] + csid[:8]

    def __str__(self):
        return "SenseInfo: pos:%s | synsetid:%s | sensekey:%s | freq: %s" % (self.pos, self.get_canonical_synsetid(), self.sk, self.tagcount)
    
class GlossInfo:
    '''
    '''
    def __init__(self, sid, sfrom, sto, stype, lemma, pos, tag, text, sk):
        self.sid = sid
        self.sfrom = sfrom
        self.sto = sto
        self.stype = stype
        self.lemma = lemma
        self.pos = pos
        self.tag = tag
        self.text = text
        self.sk = sk # sensekey
        
    @staticmethod
    def from_dict(a_dict):
        return GlossInfo(a_dict['sid'], a_dict['sfrom'],a_dict['sto'],a_dict['stype'],a_dict['lemma'], a_dict['pos'], a_dict['tag'], a_dict['text'], a_dict['wnsk'])
    
    def __str__(self):
        return "lemma: %s | pos: %s | tag: %s | text: %s | sk: %s | sid: %s | from-to: [%s-%s] | stype: %s" %        (self.lemma, self.pos, self.tag, self.text, self.sk, self.sid, self.sfrom, self.sto, self.stype)

class WordNetSQL:
    def __init__(self, wndb_path, glosstag_path):
        self.wndb_path = wndb_path
        self.glosstag_path = glosstag_path
        self.standoff = os.path.join(self.glosstag_path, 'standoff')
        self.load_glosstag()
        
    def load_glosstag(self):
        # Read index (by ID) file
        self.sid_index = dict()
        index_lines = open(os.path.join(self.glosstag_path, 'standoff', 'index.byid.tab')).readlines()
        for line in index_lines:
            parts = [ x.strip() for x in line.split('\t')]
            if len(parts) == 2:
                self.sid_index[parts[0]] = parts[1]
        # Read SK index
        self.sk_index = dict()
        index_lines = open(os.path.join(self.glosstag_path, 'standoff', 'index.bysk.tab')).readlines()
        for line in index_lines:
            parts = [ x.strip() for x in line.split('\t')]
            if len(parts) == 2:
                self.sk_index[parts[0]] = parts[1]
    
    sk_cache = dict()
    def get_senseinfo_by_sk(self, sk):
        if sk in WordNetSQL.sk_cache:
            return WordNetSQL.sk_cache[sk]
        conn = sqlite3.connect(WORDNET_30_PATH)
        c = conn.cursor()
        result = c.execute("""SELECT pos, synsetid, sensekey 
                                FROM wordsXsensesXsynsets
                                WHERE sensekey = ?;""", (sk,)).fetchone()
        sid = None
        if result:
            pos, synid, sk = result
            sid = SenseInfo(pos, synid, sk)
        conn.close()
        WordNetSQL.sk_cache[sk] = sid
        return sid
    def cache_all_sensekey(self):
        conn = sqlite3.connect(WORDNET_30_PATH)
        c = conn.cursor()
        result = c.execute("""SELECT pos, synsetid, sensekey FROM wordsXsensesXsynsets""").fetchall()
        for (pos, synid, sk) in result:
            sif = SenseInfo(pos, synid, sk)
            WordNetSQL.sk_cache[sk] = sif
        conn.close()
    
    hypehypo_cache=dict()   
    def get_hypehypo(self, sid):
        ''' Get all hypernyms and hyponyms of a given synset
        '''
        if sid in WordNetSQL.hypehypo_cache:
            return WordNetSQL.hypehypo_cache[sid]
        query = '''SELECT linkid, dpos, dsynsetid, dsensekey, dwordid
                    FROM sensesXsemlinksXsenses 
                    WHERE ssynsetid = ? and linkid in (1,2,3,4, 11,12,13,14,15,16,40,50,81);'''
        conn = sqlite3.connect(WORDNET_30_PATH)
        c = conn.cursor()
        result = c.execute(query, (sid,)).fetchall()
        senses = []
        for (linkid, dpos, dsynsetid, dsensekey, dwordid) in result:
            senses.append(SenseInfo(dpos, dsynsetid, dsensekey, dwordid))
        conn.close()
        WordNetSQL.hypehypo_cache[sid] = senses
        return senses

    def cache_all_hypehypo(self):
        query = '''SELECT linkid, ssynsetid, dpos, dsynsetid, dsensekey, dwordid
                    FROM sensesXsemlinksXsenses 
                    WHERE linkid in (1,2,3,4, 11,12,13,14,15,16,40,50,81);'''
        conn = sqlite3.connect(WORDNET_30_PATH)
        c = conn.cursor()
        result = c.execute(query).fetchall()
        for (linkid, ssynsetid, dpos, dsynsetid, dsensekey, dwordid) in result:
            if ssynsetid not in WordNetSQL.hypehypo_cache:
                     WordNetSQL.hypehypo_cache[ssynsetid] = []
            WordNetSQL.hypehypo_cache[ssynsetid].append(SenseInfo(dpos, dsynsetid, dsensekey, dwordid))
        conn.close()

    word_cache=dict()
    def get_hypehypo_text(self, sid):
        senses = self.get_hypehypo(sid)
        if not senses: 
            return []
        else:
            lemmas = []
            wordids = [ sense.wordid for sense in senses ]
            need_to_find = []
            for wordid in wordids:
                if wordid in WordNetSQL.word_cache:
                    lemmas.append(WordNetSQL.word_cache[wordid])
                else:
                    need_to_find.append(str(wordid))
            if len(need_to_find) > 0:
                # search in database
                query = '''SELECT wordid, lemma FROM words
                            WHERE wordid in (%s);''' % ','.join(need_to_find)
                conn = sqlite3.connect(WORDNET_30_PATH)
                c = conn.cursor()
                result = c.execute(query).fetchall()
                for (wordid, lemma) in result:
                    WordNetSQL.word_cache[wordid] = lemma
                    lemmas.append(lemma)
                conn.close()
            return lemmas

    def cache_all_words(self):
        query = '''SELECT wordid, lemma FROM words'''
        conn = sqlite3.connect(WORDNET_30_PATH)
        c = conn.cursor()
        result = c.execute(query).fetchall()
        for (wordid, lemma) in result:
                WordNetSQL.word_cache[wordid] = lemma
        conn.close()

    sense_map_cache=None
    def all_senses(self, keep_pos=False):
        if WordNetSQL.sense_map_cache:
            return WordNetSQL.sense_map_cache
        _query = """SELECT lemma, pos, synsetid, sensekey, definition, tagcount
                                FROM wordsXsensesXsynsets ORDER BY lemma, pos, tagcount DESC;"""
        conn = self.get_conn()
        c = conn.cursor()
        result = c.execute(_query).fetchall()
        # Build lemma map
        lemma_map = {}
        for (lemma, pos, synsetid, sensekey, definition, tagcount) in result:
            # ss_type
            # One character code indicating the synset type:
            # n NOUN
            # v VERB
            # a ADJECTIVE
            # s ADJECTIVE SATELLITE
            # r ADVERB
            if not keep_pos and pos == 's' or pos == 'r':
                pos = 'a'
            sinfo = SenseInfo(pos, synsetid, sensekey, '', definition, tagcount, lemma)
            # add to map
            if lemma not in lemma_map:
                lemma_map[lemma] = []
            lemma_map[lemma].append(sinfo)
        # close connection & return results
        conn.close()
        WordNetSQL.sense_map_cache=lemma_map
        return lemma_map

    def get_conn(self):
        conn = sqlite3.connect(WORDNET_30_PATH)
        return conn

    lemma_list_cache = dict()
    def search_senses(self, lemma_list, pos=None, a_conn=None):
        if len(lemma_list) == 0:
            return list()
        
        CACHE_JOIN_TOKEN='|\t'*12
        cache_key=CACHE_JOIN_TOKEN.join(lemma_list)
        # caching method
        if cache_key in WordNetSQL.lemma_list_cache:
            return WordNetSQL.lemma_list_cache[cache_key]
        
        # Build query lemma, pos, synsetid, sensekey, definition, tagcount
        _query = """SELECT lemma, pos, synsetid, sensekey, definition, tagcount 
                                FROM wordsXsensesXsynsets
                                WHERE (%s) """ % 'or '.join(["lemma=?"] * len(lemma_list))
        _args = list(lemma_list)
        if pos:
            _query += " and pos = ?";
            _args.append(pos)
        
        # Query
        if a_conn:
            conn = a_conn
        else:
            conn = sqlite3.connect(WORDNET_30_PATH)
        c = conn.cursor()
        result = c.execute(_query, _args).fetchall()

        # Build results
        senses = []
        for (lemma, pos, synsetid, sensekey, definition, tagcount) in result:
            senses.append(SenseInfo(pos, synsetid, sensekey, '', definition, tagcount, lemma))
        if not a_conn:
            conn.close()
        
        # store to cache
        WordNetSQL.lemma_list_cache[cache_key] = senses
        return senses
    
    sense_cache = dict()
    def get_all_senses(self, lemma, pos=None):
        '''Get all senses of a lemma

        Return an object with the type of lelesk.SenseInfo
        '''
        if (lemma, pos) in WordNetSQL.sense_cache:
            return WordNetSQL.sense_cache[(lemma, pos)]
        conn = sqlite3.connect(WORDNET_30_PATH)
        c = conn.cursor()
        if pos:
            if pos == 'a':
                result = c.execute("""SELECT pos, synsetid, sensekey, definition, tagcount 
                                    FROM wordsXsensesXsynsets
                                    WHERE lemma = ? and pos IN ('a', 's');""", (lemma,)).fetchall() 
            else:
                result = c.execute("""SELECT pos, synsetid, sensekey, definition, tagcount 
                                    FROM wordsXsensesXsynsets
                                    WHERE lemma = ? and pos = ?;""", (lemma, pos)).fetchall()   
        else:
            result = c.execute("""SELECT pos, synsetid, sensekey, definition, tagcount 
                                FROM wordsXsensesXsynsets
                                WHERE lemma = ?;""", (lemma,)).fetchall()
        senses = []
        # print("Found result: %s" % len(result))
        for (rpos, synsetid, sensekey, definition, tagcount) in result:
            if rpos == 's':
                rpos = 'a'
            senses.append(SenseInfo(rpos, synsetid, sensekey, '', definition, tagcount))
        conn.close()
        WordNetSQL.sense_cache[(lemma, pos)] = senses
        return senses
        
    def cache_all_sense_by_lemma(self):
        conn = sqlite3.connect(WORDNET_30_PATH)
        c = conn.cursor()
        result = c.execute("""SELECT lemma, pos, synsetid, sensekey, definition FROM wordsXsensesXsynsets;""").fetchall()

        for (lemma, pos, synsetid, sensekey, definition) in result:
            if lemma not in WordNetSQL.sense_cache:
                WordNetSQL.sense_cache[lemma] = []
            WordNetSQL.sense_cache[lemma].append(SenseInfo(pos, synsetid, sensekey, '', definition))
        conn.close()

    def get_gloss_by_sk(self, sk):
        sid = self.get_senseinfo_by_sk(sk).get_full_sid()
        return self.get_gloss_by_id(sid)
    
    gloss_cache = dict()
    def get_gloss_by_id(self, sid):
        if sid in WordNetSQL.gloss_cache:
            return WordNetSQL.gloss_cache[sid]
        if not sid:
            return None
        gloss_file = self.search_by_id(sid)
        if not gloss_file:
            return None
        gloss_file_loc = os.path.join(self.standoff, gloss_file + '-wngloss.xml')
        gloss_data = XMLCache.parse(gloss_file_loc).find("./{http://www.xces.org/schema/2003}struct[@id='%s']" % (sid + '_d',))
        # Build gloss object
        a_sense = SenseGloss(gloss_data.get('id'), 
                            gloss_data.get('from'), 
                            gloss_data.get('to'), 
                            gloss_data.get('type'))
        # Retrieve each gloss token
        ann_file_loc = os.path.join(self.standoff, gloss_file + '-wnann.xml')
        ann = XMLCache.parse(ann_file_loc).findall("./{http://www.xces.org/schema/2003}struct")
        wnword_file_loc = os.path.join(self.standoff, gloss_file + '-wnword.xml')
        wnword = XMLCache.parse(wnword_file_loc)
        if len(ann) > 0:
            for elem in ann:
                if elem.attrib['id'].startswith(sid):
                    features = dd(lambda: '')
                    features['sid'] = elem.get('id')
                    features['sfrom'] = elem.get('from')
                    features['sto'] = elem.get('to')
                    features['stype'] = elem.get('type')
                    # We only use the gloss part
                    #if int(features['sfrom']) > int(a_sense.sto):
                    #   break
                    for feat in elem:
                        features[feat.get('name')] = feat.get('value')
                    # Look for sensekey if available
                    wnsk = wnword.findall("./{http://www.xces.org/schema/2003}struct[@id='%s']/*[@name='wnsk']" % (elem.get('id'),))
                    if len(wnsk) == 1:
                        features['wnsk'] = wnsk[0].get('value')
                    a_sense.tokens.append(GlossInfo.from_dict(features))
            # Read glosses data
            WordNetSQL.gloss_cache[sid] = a_sense
            return a_sense
        else:
            WordNetSQL.gloss_cache[sid] = None
            return None
        pass
            
    # Search a synset by ID
    def search_by_id(self, synset_id):
        #print 'searching %s' % synset_id
        if synset_id in self.sid_index:
            return self.sid_index[synset_id]
        else:
            return None
    
    # Search a synset by sensekey
    def search_by_sk(self, wnsk):
        if wnsk in self.sk_index:
            return self.sk_index[wnsk]
        else:
            return 'N/A'
    
    @staticmethod
    def get_default(auto_cache=True):
        wnsql = WordNetSQL(WORDNET_30_PATH, WORDNET_30_GLOSSTAG_PATH)
        # Cache everything into memory if needed
        if auto_cache:
            wnsql.cache_all_words()
            wnsql.cache_all_sense_by_lemma()
            wnsql.cache_all_hypehypo()
            wnsql.cache_all_sensekey()
        return wnsql
        
class GlossTokens:
    def __init__(self):
        self.tokens = []
        self.sk = []

class WSDCandidate:
    def __init__(self, sense=None):
        '''Data Transfer Object which holds information about a sense and tokens of its definition & 
        '''
        self.sense = sense #SenseInfo (can access sensekey, synsetID, etc.)
        self.tokens = []

    def get_distinct_tokens(self):
        return set(self.tokens)

    def __str__(self):
        return "%s - (Def: %s)" % (self.sense.get_canonical_synsetid(), self.sense.gloss)

class WSDResources:
    
    __singleton_instance = None
    wnsql=None
    wnl=None
    
    def __init__(self, lightweight=False, verbose=False):
        # self.sscol = WNGlossTag.read_all_glosstag(os.path.join(WORDNET_30_GLOSSTAG_PATH, 'merged'), verbose=True)
        if not lightweight:
            self.sscol = WNGlossTag.build_lelesk_data(os.path.join(WORDNET_30_GLOSSTAG_PATH, 'merged'), verbose=verbose, memory_save=False)
        self.wnsql = WordNetSQL.get_default()
        self.wnl = WordNetLemmatizer()
        self.lemmatize_cache = dict()

    def lemmatize(self, word):
        if word not in self.lemmatize_cache:
            self.lemmatize_cache[word] = self.wnl.lemmatize(word)
        return self.lemmatize_cache[word]

    @staticmethod
    def singleton(lightweight=False, verbose=False):
        if WSDResources.__singleton_instance == None:
            WSDResources.__singleton_instance = WSDResources(lightweight=lightweight, verbose=verbose)
        return WSDResources.__singleton_instance

class WSDToolKit:
    def __init__(self, verbose=False, lightweight=False):
        self.candidates_cache=dict()    
        self.verbose = verbose
        t = Timer()
        # Preparation: Load all resources (SQLite cache, WNGlossTag, etc.)
        if self.verbose:
            t.start('Loading needed resource ...')
        self.res = WSDResources.singleton(lightweight=lightweight, verbose=verbose)
        if self.verbose:
            t.end('Needed resources have been loaded')
        self.candidate_cache={}
        pass

    def extend_tokenlist(self, tokenlist, twlist):
        for item in twlist:
            temp_list = set()
            if item.text:
                temp_list.add(item.text)
            if item.lemma:
                lemmaparts = item.lemma.split('|')
                for lemmapart in lemmaparts:
                    parts = lemmapart.split('%')
                    if parts:
                        temp_list.add(parts[0])
            tokenlist += list(temp_list)

    def get_sense_candidates(self, word, lemmatizing=True, pos=None, extended=True, glossedwn=True):
        '''Get WordNet sense candidates for a given word (return a list of WSDCandidate object)
        '''
        if (word, lemmatizing, pos) in self.candidate_cache:
            return self.candidate_cache[(word, lemmatizing, pos)]
        lemmatized_word = self.res.lemmatize(word) if lemmatizing else word
        senses = self.res.wnsql.get_all_senses(lemmatized_word, pos)
        candidates = []
        sc = len(senses)
        num = 0
        # t = Timer()
        # t2 = Timer()
        print("Found %s candidate(s)" % (len(senses)))
        for sense in senses:
            num+=1
            if self.verbose: print("Processing sense %s/%s for the word [%s]" % (num, sc, word))
            candidate = WSDCandidate(sense)
            sk = sense.sk
            # t.start()
            synset_gloss = self.res.sscol.by_sk(sk)
            if not synset_gloss:
                print("Sensekey [%s] - [synsetid=%s] notfound" % (sk, sense.get_canonical_synsetid()))
                print("try to search by id then ...")
                synset_gloss = self.res.sscol.by_sid(sense.get_gwn_sid())
                if not synset_gloss:
                    print("I gave up, I couldn't find it by synset ID either ...")
                    continue
            # print("I'm extending candidate %s by %s elements" % (sense.get_gwn_sid(), len(synset_gloss.def_gloss)))
            self.extend_tokenlist(candidate.tokens, synset_gloss.def_gloss)
            print("Base tokens: %s" % (candidate.tokens)) 

            # candidate.tokens += [ x.text for x in synset_gloss.def_gloss ]
            
            # Add tokens from gloss from hypenym & hyponym
            more_tokens = self.res.wnsql.get_hypehypo_text(sense.get_gwn_sid())
            print("Tokens from hypehypo of %s: %s" % (sense.get_gwn_sid(), more_tokens))
            if more_tokens:
                candidate.tokens += more_tokens

            print("Extending child tokens in def_gloss...")
            for child_token in synset_gloss.def_gloss:
                # t2.start() 
                # Find gloss of each token in the gloss of the current sense
                senseinfo = self.res.wnsql.get_senseinfo_by_sk(child_token.sk)
                if self.res.sscol.by_sk(child_token.sk):
                    child_gloss = self.res.sscol.by_sk(child_token.sk)
                    # x is GlossToken object
                    more_tokens = []
                    self.extend_tokenlist(more_tokens, child_gloss.def_gloss)
                    print("Adding tokens from gloss of %s: %s" % (child_token.sk, more_tokens))
                    candidate.tokens += more_tokens
                    # candidate.tokens += [ x.text for x in child_gloss.def_gloss ]
                if senseinfo:
                    more_tokens = self.res.wnsql.get_hypehypo_text(senseinfo.sid)
                    print("Adding tokens from hypehypo of %s: %s" % (senseinfo.sid, more_tokens))
                    candidate.tokens += more_tokens # Hype & hypo of tagged tokens
#                else:
#                    print("Adding tokens from all senses of ``%s''" % (child_token.text))
#                    # TODO: try to search by using tokens text?
#                    child_senses = self.res.wnsql.get_all_senses(child_token.text)
#                    if child_senses:
#                        for child_sense in child_senses:
#                            more_tokens = self.res.wnsql.get_hypehypo_text(child_sense.sid)
#                            candidate.tokens += more_tokens # Hype & hypo of tagged tokens
#                    pass
                # t2.stop().log('get child gloss')                
                #----------------------------------------------------------------
            # Filter out special character
            candidate.tokens = [ _f for _f in candidate.tokens if _f and _f not in """!"#$%&\'()*+,-./:;?@[\\]^_`{|}~``''""" ]
            print("Final tokens list: %s" % (candidate.tokens,))
            candidates.append(candidate)
        self.candidate_cache[(word, lemmatizing, pos)] = candidates
        return candidates
        pass

    def prepare_data(self, sentence_text):
        '''Given a sentence as a raw text string, perform tokenization, lemmatization
        '''
        # Tokenization
        tokens = nltk.word_tokenize(sentence_text)
        # Lemmatization
        tokens = [ self.res.lemmatize(x) for x in tokens] + tokens
        return tokens

    def lelesk_wsd(self, word, sentence_text, expected_sense='', lemmatizing=True, pos=None, context=None):
        '''Perform Word-sense disambiguation with extended simplified LESK and annotated WordNet 3.0
        '''
        if not context:
            context = self.prepare_data(sentence_text)
        
        #1. Retrieve candidates for the given word
        if (word, pos) not in self.candidates_cache:
            self.candidates_cache[(word, pos)] = self.get_sense_candidates(word, lemmatizing, pos=pos)
        candidates = self.candidates_cache[(word, pos)]
        #2. Calculate overlap between the context and each given word
        context_set = set(context)
        if self.verbose: print("Context set: %s" % sorted(context_set))
        scores = []
        for candidate in candidates:
            candidate_set = set([ self.res.lemmatize(x) for x in candidate.tokens ] + candidate.tokens)
            if self.verbose: print("Candidate for %s: %s" % (candidate.sense.get_canonical_synsetid(), sorted(candidate_set),))
            score = len(context_set.intersection(candidate_set))
            scores.append([candidate, score, candidate.sense.tagcount])
        scores.sort(key=itemgetter(1, 2))
        scores.reverse()

        if self.verbose:
            print("WSD for the word: %s" % (word,))
            print("Sentence text   : %s" % (sentence_text,))

            print("Context         : %s" % context,)
            print("POS             : %s" % (pos,))
            if expected_sense:
                print('Expected sense  : %s' % (expected_sense,))
                if len(scores) > 0:
                    print('Suggested sense : %s' % (scores[0][0].sense.get_canonical_synsetid(),))
                else:
                    print('No sense found')
            #print("Top 3 scores:")
            #for score in scores[:3]:
            #   print(("\tSense: %s - Score: %s - Definition: %s" % (score[0].sense.get_canonical_synsetid(), score[1], score[0].sense.gloss)))
        return scores

    def mfs_wsd(self, word, sentence_text, expected_sense='', lemmatizing=True, pos=None):
        '''Perform Word-sense disambiguation with just most-frequent senses
        '''
        
        #1. Retrieve candidates for the given word
        if (word, pos) not in self.candidates_cache:
            self.candidates_cache[(word, pos)] = self.get_sense_candidates(word, lemmatizing, pos=pos)
        candidates = self.candidates_cache[(word, pos)]
        scores = []
        for candidate in candidates:
            scores.append([candidate, candidate.sense.tagcount])
        scores.sort(key=itemgetter(1))
        scores.reverse()

        if self.verbose:
            print("WSD for the word: %s" % (word,))
            print("Sentence text   : %s" % (sentence_text,))
            print("POS             : %s" % (pos,))
            if expected_sense:
                print('Expected sense  : %s' % (expected_sense,))
                if len(scores) > 0:
                    print('Suggested sense : %s' % (scores[0][0].sense.get_canonical_synsetid(),))
                else:
                    print('No sense found')
        return scores

#------------------------------------------------------------------------------

def test_semcor(file_name, verbose=True):
    t = Timer()
    total_timer = Timer()
    total_timer.start()
    lines = open(file_name).readlines()
    print(("Found %s sentences in %s" % (len(lines), file_name)))
    
    wsd=WSDToolKit(True)
        
    print(('-' * 80))
    
    c = Counter()
    sentence_count = len(lines)
    fh = FileHub()
    for line in lines:
        c.count('sentence')
        #if c['sentence'] > 100:
        #   break
        parts = line.split('\t')
        if not parts:
            continue
        tokens = []
        for part in parts:
            if not part:
                continue
            tk = part.split('|')
            if not tk or len(tk) != 2:
                continue
            tokens.append(Token(tk[0], tk[1]))
        sentence_text = ' '.join([ x.text for x in tokens ])
        test_items = [ x for x in tokens if x.sk ]
        for test_item in test_items:
            c.count("Word (total)")
            word = test_item.text
            # sentence_text = parts[1].strip()
            # Perform WSD on given word & sentence
            t.start()
            scores = wsd.lelesk_wsd(word, context, test_item.sk)
            if scores and len(scores) > 0:
                correct_word = False
                for score in scores:
                    sid = score[0].sense.get_full_sid()
                    sks = res.sscol.by_sid(sid).keys
                    if test_item.sk in sks:
                        correct_word = True
                if correct_word:
                    c.count('Word (correct)')
                else:
                    c.count('Word (wrong)')
                    fh.writeline('data/wrongsense', res.lemmatize(word))
            else:
                c.count('Word (no sense)')
                fh.writeline('data/nosense', res.lemmatize(word))
            
            if verbose:
                print ("Top 3 scores")
            
            # Check top hit
            if len(scores) > 0:
                sid = scores[0][0].sense.get_full_sid()
                sks = res.sscol.by_sid(sid).keys
                if test_item.sk in sks:
                    c.count('top1') 
            
            for score in scores[:3]:
                # score = [0] - synset, [1] - score in number
                sid = score[0].sense.get_full_sid()
                sks = res.sscol.by_sid(sid).keys
                if test_item.sk in sks:
                    c.count('top3') 
                if verbose:
                    print(("Sense: %s - Sensekey: %s- Score: %s - Definition: %s" % (sid, sks, score[1], score[0].sense.gloss)))
            t.end('Sentence (#%s/%s) | Analysed word ["%s"] on sentence: %s' % (c['sentence'], sentence_count, word, sentence_text))
            print(('-' * 80))
    jilog("Batch job finished")
    print(('-' * 80))
    c.summarise()
    total_timer.end("Total runtime")
    print('Done!')
    
    pass

def batch_wsd(infile_loc, outfile_loc=None, method='lelesk', use_pos=False, assume_perfect_POS=False, lemmatizing=False, pretokenized=False):
    t = Timer()
    t.start("Reading file %s" % infile_loc)
    lines = open(os.path.expanduser(infile_loc)).readlines()
    t.end("File has been loaded")
    
    wsd=WSDToolKit(lightweight=False, verbose=True)
    
    print(('-' * 80))
    c=Counter('Match InTop3 Wrong NoSense TotalSense'.split())
    OutputLine=namedtuple('OutputLine', 'results word correct_sense suggested_sense sentence_text'.split())
    outputlines = []
    # Counters for different type of words
    match_count = Counter()
    top3_count = Counter()
    wrong_count = Counter()
    nosense_count = Counter()
    for line in lines:
        if line.startswith('#'):
            # it is a comment line
            continue
        parts = line.split('\t')
        if parts:
            context = None
            if len(parts) == 3: 
                word = parts[0].strip()
                correct_sense = SenseInfo.normalise_synsetid(parts[1].strip())
                pos = None
                sentence_text = parts[2].strip()
            elif len(parts) == 4:
                word = parts[0].strip()
                correct_sense = SenseInfo.normalise_synsetid(parts[1].strip())
                pos = parts[2].strip()
                sentence_text = parts[3].strip()
            elif len(parts) == 5:
                word = parts[0].strip()
                correct_sense = SenseInfo.normalise_synsetid(parts[1].strip())
                pos = parts[2].strip()
                sentence_text = parts[3].strip()
                context = parts[4].strip().split('|')
            if pos in ('', 'x'):
                pos = None

            if assume_perfect_POS:
                pos = correct_sense[-1]
            if not use_pos:
                # if use choose to ignore POS
                pos = None

            results = 'X'
            # Perform WSD on given word & sentence
            t.start()
            if method == 'mfs':
                # jilog("Activating MFS WSD")
                scores = wsd.mfs_wsd(word, sentence_text, correct_sense, lemmatizing=lemmatizing, pos=pos)
            else:
                if pretokenized and context and len(context) > 0:
                    # jilog("Activating Lelesk with pretokenized")
                    scores = wsd.lelesk_wsd(word, sentence_text, correct_sense, lemmatizing=lemmatizing, pos=pos, context=context)
                else:
                    # jilog("Activating Lelesk with NTLK tokenizer")
                    scores = wsd.lelesk_wsd(word, sentence_text, correct_sense, lemmatizing=lemmatizing, pos=pos)
            suggested_senses = [ score[0].sense.get_canonical_synsetid() for score in scores[:3] ]
            # c.count("TotalSense")

            if correct_sense in NTUMC_PRONOUNS:
                c.count("IGNORED")
                continue
            else:
                c.count("TotalSense")

            if len(suggested_senses) == 0:
                nosense_count.count(correct_sense + '\t' + word)
                c.count("NoSense")
                results = '_'
            elif correct_sense == suggested_senses[0]:
                match_count.count(correct_sense + '\t' + word)
                c.count("Match")
                results = 'O'
            elif correct_sense in suggested_senses:
                top3_count.count(correct_sense + '\t' + word)
                c.count("InTop3")
                results = 'V'
            else:
                wrong_count.count(correct_sense + '\t' + word)
                c.count("Wrong")

            # write to output file
            if len(suggested_senses) > 0:
                outputlines.append(OutputLine(results, word, correct_sense, suggested_senses[0], sentence_text))
            else:
                outputlines.append(OutputLine(results, word, correct_sense, "", sentence_text))
            # Debug information (all scores)
            print ("All scores")
            for score in scores[:3]:
                print(("Sense: %s - Score: %s - Definition: %s" % (score[0].sense.get_canonical_synsetid(), score[1], score[0].sense.gloss)))
            for score in scores[3:]:
                print(("Sense: %s - Score: %s - Definition: %s" % (score[0].sense.get_canonical_synsetid(), score[1], score[0].sense.gloss)))
            print("")
            if context:
                t.end('Analysed word ["%s"] on sentence: %s' % (word, context))
            else:
                t.end('Analysed word ["%s"] on sentence: %s' % (word, sentence_text))
            print(('-' * 80))
    print("-" * 80)
    print("")
    c.summarise()

    if outfile_loc:
        jilog("Writing output file ==> %s..." % (outfile_loc,))
        save_counter_to_file(match_count, outfile_loc + '.match.txt')
        save_counter_to_file(top3_count, outfile_loc + '.top3.txt')
        save_counter_to_file(wrong_count, outfile_loc + '.wrong.txt')
        save_counter_to_file(nosense_count, outfile_loc + '.nosense.txt')

        with open(outfile_loc, 'w') as outfile:
            outfile.write("results\tword\tcorrect_sense\tsuggested_sense\tsentence_text\n")
            for line in outputlines:
                outfile.write('%s\t%s\t%s\t%s\t%s\n' % (line.results ,line.word ,line.correct_sense ,line.suggested_sense ,line.sentence_text))
        jilog("Done.")
    jilog("Batch job finished")

    # Store counters for debugging

    print('Done!')

def save_counter_to_file(counter, filename):
    with open(filename, 'w') as output:
        items = counter.sorted_by_count()
        for k, v in items:
            output.write('%s\t%s\n' % (k, v))

def test_wsd():
    word = 'bank'
    sentence_texts = ['I went to the bank to deposit money.', 'The river bank is full of dead fish.']
    wsd=WSDToolKit(True)
    t = Timer()
    for sentence_text in sentence_texts:
        t.start()
        wsd.lelesk_wsd(word, sentence_text)
        t.end('Analysed sentence: %s' % sentence_text)

def optimize():
    t = Timer()

    # Load needed resources
    t.start('Started loading needed resources ...')
    res = WSDResources.singleton()
    t.end('Preload all needed resources')

    t.start()
    res.wnsql.cache_all_words()
    t.stop().log('Cache all words')

    t.start()
    res.wnsql.cache_all_sensekey()
    t.stop().log('Cache all sensekeys')

    t.start()
    res.wnsql.cache_all_hypehypo()
    t.stop().log('Cache all hypehypo')

    t.start()
    res.wnsql.cache_all_sense_by_lemma()
    t.stop().log('Cache all sense by lemma')

    # Profiling select senses from database
    t.start()
    senses = res.wnsql.get_all_senses('table')
    print(len(senses))
    t.stop().log('Test select all senses')

    # Profiling get by sk
    t.start()
    sk = 'side%1:15:01::'
    file_loc = res.wnsql.search_by_sk(sk)
    sid = res.wnsql.get_senseinfo_by_sk(sk).get_full_sid()
    print(("Looking at %s - File loc: %s - SID: %s" % (sk,file_loc, sid)))
    a_sense = res.wnsql.get_gloss_by_sk(sk)
    dump_sense(a_sense)
    t.stop().log('Profiling select by sensekey')

    # Profiling loading
    t.start()
    print(res.wnsql.search_by_id('a00002527'))
    gloss = res.wnsql.get_gloss_by_id('a00002527')
    dump_sense(gloss)
    t.stop().log('Test search gloss')

    # Profiling loading again
    t.start()
    print(res.wnsql.search_by_id('a00002527'))
    gloss = res.wnsql.get_gloss_by_id('a00002527')
    dump_sense(gloss)
    t.stop().log('Test search gloss again')


    # Profiling expand the word table
    t.start()
    test_expand()
    t.stop()
    t.log('Expanding [table]')

    # The application should run faster from the second time
    t.start()
    test_expand()

    t.stop().log('Expanding [table] again ...')

    pass

def test_candidates(word, lemmatizing=False):
    wsd=WSDToolKit(True)
    if not word:
        word = 'table'
    pos=None
    parts = word.split('|')
    if len(parts) == 2:
        word = parts[0].strip()
        pos = parts[1].strip()
    print(('Retrieving candidates for the word ["%s"]' % word))
    if pos:
        print("Given part-of-speech: %s" % pos)
    candidates = wsd.get_sense_candidates(word, lemmatizing=lemmatizing, pos=pos)
    if candidates:
        print(("Candidates count: %s" % len(candidates)))
        for candidate in candidates:
            print("-" * 80)
            print(str(candidate.sense))
            print("-" * 80)
            print("All tokens: %s" % (candidate.tokens,))
            print("Final set: %s" % (candidate.get_distinct_tokens(),))
            print('')
    pass
    
def dump_sense(a_sense, show_tagged_only=True):
    if a_sense:
        print(a_sense)
        for token in a_sense.tokens:
            if not show_tagged_only or token.sk:
                print(('\t' + str(token)))

def test_wordnetgloss():
    wng = WordNetSQL.get_default()
    print(wng.search_by_id('a00002527'))
    gloss = wng.get_gloss_by_id('a00002527')
    dump_sense(gloss)
    #
    print(("-" * 80))
    #
    sk = 'side%1:15:01::'
    file_loc = wng.search_by_sk(sk)
    sid = wng.get_senseinfo_by_sk(sk).get_full_sid()
    print(("Looking at %s - File loc: %s - SID: %s" % (sk,file_loc, sid)))
    a_sense = wng.get_gloss_by_sk(sk)
    dump_sense(a_sense)
    #
    print(('-' * 80))
    # 
    senses = wng.get_all_senses('side')
    for sense in senses:
        print(sense)
    pass    

#-----------------------------------------------------------------------
# Main function
#-----------------------------------------------------------------------
def main(): 
    '''Main entry of lelesk console application.

    Available commands:
        test: Run bank test
        candidates -i CHOSEN_WORD: Find candidates for a given word
        batch -i PATH_TO_FILE: Perform WSD on a batch file
        batch -i PATH_TO_SEMCOR_TEST_FILE: Perform WSD on Semcor (e.g. semcor_wn30.txt)
    '''
    # Fix configuration
    JILOG_LOCATION = 'data/debug.txt'
    #
    parser = argparse.ArgumentParser(description="A library for performing Word Sense Disambiguation using Python.")
    parser.add_argument('command', choices=['test', 'optimize', 'candidates', 'batch', 'semcor'], help='Command you want to execute (test/optimize/candidates/batch/semcor).')
    parser.add_argument("-i", "--input", help='Input file/word to process')
    parser.add_argument("-o", "--output", help='Output file')
    parser.add_argument("-m", "--method", help='WSD method (lelesk/mfs) default is lelesk')
    parser.add_argument("-p", "--pos", help='Use provided POS information', action="store_true")
    parser.add_argument("-P", "--POS", help='Assume perfect POS information (from expected synsetID)', action="store_true")
    parser.add_argument("-l", "--lemmatize", help='Lemmatize word before performing WSD', action="store_true")
    parser.add_argument("-t", "--pretokenized", help='Sentence text are pre-tokenized', action="store_true")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")

    if len(sys.argv) == 1:
        # User didn't pass any value in, show help
        parser.print_help()
    else:
        args = parser.parse_args()
        if args.verbose:
            print("Application has been started in verbose mode ...")
        task_map = { 'test' : test_wsd, 'optimize' : optimize, 'candidates' : test_candidates, 'batch' : batch_wsd, 'semcor' : test_semcor }
        if args.command in ('candidates', 'batch', 'semcor'):
            if not args.input:
                print("An input is needed for this task ...")
                parser.print_help()
            if args.command == 'batch':
                method = args.method if args.method else 'lelesk'
                usepos = args.pos if args.pos or args.POS else False

                print("Use POS        : %s" % (usepos,))
                print("Use Perfect POS: %s" % (args.POS,))
                batch_wsd(args.input, args.output, method, usepos, args.POS, lemmatizing=args.lemmatize, pretokenized=args.pretokenized)
            elif args.command == 'candidates':
                test_candidates(args.input, lemmatizing=args.lemmatize)
            else:
                task_map[args.command](args.input)
        else:
            task_map[args.command]()
        if args.verbose:
            print("All done ...")
    pass

if __name__ == "__main__":
    main()


# Note:
# How to use this tool
# ./main.py candidates -i "dear|a"
