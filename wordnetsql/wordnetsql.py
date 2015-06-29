#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
WordNet SQLite wrapper
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
__copyright__ = "Copyright 2014, lelesk"
__credits__ = [ "Le Tuan Anh" ]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

#-----------------------------------------------------------------------

from glosswordnet.models import SynsetCollection, Synset, GlossRaw, SenseKey, Term, Gloss, GlossGroup, SenseTag, GlossItem
from puchikarui import Schema, Execution#, DataSource, Table
import itertools
from collections import defaultdict as dd

#-----------------------------------------------------------------------

class WordNet3Schema(Schema):
    def __init__(self, data_source=None):
        Schema.__init__(self, data_source)
        self.add_table('wordsXsensesXsynsets', 'wordid lemma casedwordid synsetid senseid sensenum lexid tagcount sensekey pos lexdomainid definition'.split(), alias='wss')
        self.add_table('sensesXsemlinksXsenses', 'linkid ssynsetid swordid ssenseid scasedwordid ssensenum slexid stagcount ssensekey spos slexdomainid sdefinition dsynsetid dwordid dsenseid dcasedwordid dsensenum dlexid dtagcount dsensekey dpos dlexdomainid ddefinition'.split(), alias='sss')

class WordNetSQL:
    def __init__(self, db_path):
        self.db_path = db_path
        self.sk_cache = dd(set)
        self.sid_cache = dd(set)
        self.hypehypo_cache = dd(set)

        self.schema = WordNet3Schema(self.db_path)
        self.tagcount_cache = dd(lambda: 0)
    
    def get_all_synsets(self):
        with Execution(self.schema) as exe:
            return exe.schema.wss.select(columns=['synsetid', 'lemma', 'sensekey', 'tagcount'])

    def cache_tagcounts(self):
        with Execution(self.schema) as exe:
            results = exe.schema.wss.select(columns=['synsetid', 'tagcount'])
        for res in results:
            self.tagcount_cache[res.synsetid] += res.tagcount

    def get_tagcount(self, sid):
        if sid in self.tagcount_cache:
            return self.tagcount_cache[sid]
        with Execution(self.schema) as exe:
            results = exe.schema.wss.select(where='synsetid=?',values=[sid], columns=['tagcount'])
        counter = 0
        for res in results:
            counter += res.tagcount
        self.tagcount_cache[sid] = counter
        return counter

    def get_senseinfo_by_sk(self, sk):
        if sk in self.sk_cache:
            return self.sk_cache[sk]
        result = None
        with Execution(self.schema) as exe:
            result = exe.schema.wss.select_single(where='sensekey=?', values=[sk]
                , columns=['pos', 'synsetid', 'sensekey'])
        self.sk_cache[sk] = result
        return result

    def get_senseinfo_by_sid(self, sid):
        if sid in self.sid_cache:
            return self.sid_cache[sid]
        result = None
        with Execution(self.schema) as exe:
            result = exe.schema.wss.select_single(where='synsetid=?', values=[sid]
                , columns=['pos', 'synsetid', 'sensekey'])
        self.sid_cache[sid] = result
        return result
 
    def get_all_sensekeys(self):
        results = None
        with Execution(self.schema) as exe:
            results = exe.schema.wss.select(columns=['pos', 'synsetid', 'sensekey'])
        return results

    def cache_all_sensekey(self):
        with Execution(self.schema) as exe:
            results = exe.schema.wss.select(columns=['pos', 'synsetid', 'sensekey'])
            for result in results:
                self.sk_cache[result.sensekey] = result
    
    def get_hypehypo(self, sid):
        ''' Get all hypernyms and hyponyms of a given synset
        '''
        if sid in self.hypehypo_cache:
            return self.hypehypo_cache[sid]
        result = None
        with Execution(self.schema) as exe:
            result = exe.schema.sss.select(where='ssynsetid = ? and linkid in (1,2,3,4, 11,12,13,14,15,16,40,50,81)'
                , values=[sid], columns=['linkid', 'dpos', 'dsynsetid', 'dsensekey', 'dwordid'])
        for r in result:
            self.hypehypo_cache[sid].add(r)
        return self.hypehypo_cache[sid]

    def cache_all_hypehypo(self):
        with Execution(self.schema) as exe:
            results = exe.schema.sss.select(columns=['linkid', 'dpos', 'dsynsetid', 'dsensekey', 'dwordid', 'ssynsetid'])
            for result in results:        
                self.hypehypo_cache[result.ssynsetid].update(result)

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