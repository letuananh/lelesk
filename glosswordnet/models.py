#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Gloss WordNet Data Transfer Object
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

from chirptext.leutile import StringTool, Counter, uniquify

#-----------------------------------------------------------------------
# CONFIGURATION
#-----------------------------------------------------------------------

# How to use this library?
# from glosswordnet.models import SynsetCollection, Synset, GlossRaw, SenseKey, Term, Gloss, GlossGroup, SenseTag, GlossItem

class SynsetCollection:
    ''' Synset collection which provides basic synset search function (by_sid, by_sk, etc.)
    '''
    def __init__(self):
        self.synsets = []
        self.sid_map = {}
        self.sk_map = {}
        
    def add(self, synset):
        self.synsets.append(synset)
        self.sid_map[synset.sid] = synset
        if synset.keys:
            for key in synset.keys:
                self.sk_map[key] = synset
    
    def __getitem__(self, name):
        return self.synsets[name]

    def by_sid(self, sid):
        if sid in self.sid_map:
            return self.sid_map[sid]
        else:
            return None
    
    def by_sk(self, sk):
        if sk in self.sk_map:
            return self.sk_map[sk]
        else:
            return None
    
    def __iter__(self):
        return iter(self.synsets)

    def count(self):
        return len(self.synsets)

    def __len__(self):
        return self.count()

    # Merge with another Synset Collection
    def merge(self, another_scol):
        for synset in another_scol.synsets:
            self.add(synset)

    def new_synset(self, sid, ofs, pos):
        ss = Synset(sid, ofs, pos)
        self.add(ss)
        return ss

class GlossRaw:
    ''' Raw glosses extracted from WordNet Gloss Corpus.
        Each synset has a orig_gloss, a text_gloss and a wsd_gloss
    '''

    # Categories
    ORIG = 'orig' 
    TEXT = 'text'
    
    def __init__(self, synset, cat, gloss):
        self.synset = synset
        self.cat = StringTool.strip(cat)
        self.gloss = StringTool.strip(gloss)

    def __str__(self):
        return "[gloss-%s] %s" % (self.cat, self.gloss)

class SenseKey:
    ''' Sensekey of a synset. Another way to identify a synset is to use the combination synsetid-pos.
    '''
    def __init__(self, synset, sensekey):
        self.synset = synset
        self.sensekey = sensekey

    def __repr__(self):
        return "sk:`%s'" % self.sensekey

    def __str__(self):
        return "sensekey: `%s'" % self.sensekey

class Term:
    ''' Text form a synset
    '''
    def __init__(self, synset, term):
        self.synset = synset
        self.term = term

    def __repr__(self):
        return "t:`%s'" % self.term

    def __str__(self):
        return "term: `%s'" % self.term
        
class Synset:
    ''' Each synset object comes with sensekeys (ref: SenseKey), terms (ref: Term), and 3 glosses (ref: GlossRaw).
    '''

    def __init__(self, sid, ofs=None, pos=None):
        self.sid   = sid
        self.ofs   = ofs if ofs else sid[1:]
        self.pos   = pos if pos else sid[0]
        self.keys  = []       # list of SenseKey
        self.terms = []       # list of Term
        self.raw_glosses = [] # list of GlossRaw
        self.glosses = []     # list of Gloss

    def add_term(self, term):
        t = Term(self, term)
        self.terms.append(t)
    
    def add_sensekey(self, sk):
        sensekey = SenseKey(self, sk)
        self.keys.append(sensekey)

    def add_raw_gloss(self, cat, gloss):
        gr = GlossRaw(self, cat, gloss)
        self.raw_glosses.append(gr)

    def add_gloss(self, origid, cat, gid=-1):
        g = Gloss(self, origid, cat, gid)
        self.glosses.append(g)
        return g

    def get_synsetid(self):
        ''' Get canonical synset ID (E.g. 12345678-n)
        '''
        return "%s-%s" % (self.ofs, self.pos)

    def get_orig_gloss(self):
        for gr in self.raw_glosses:
            if gr.cat == 'orig':
                return gr.gloss
        return ''

    def to_wn30_synsetid(self):
        if len(self.keys) > 0:
            parts = self.keys[0].sensekey.split("%") # E.g. cause_to_be_perceived%2:39:00::
            if len(parts) == 2:
                nums = parts[1].split(":")
                if len(nums) >= 3:
                    return nums[0] + self.ofs
        print("Invalid sensekey")
        return ''

    def to_wnsqlite_sid(self):
        posnum = '4'
        if self.pos == 'n':
            posnum = '1'
        elif self.pos == 'v':
            posnum = '2'
        elif self.pos == 'a':
            posnum = '3'
        return posnum + str(self.ofs)

    def get_gramwords(self, nopunc=True):
        words = []
        for gloss in self.glosses:
            words.extend(gloss.get_gramwords(nopunc))
        return words

    def get_tags(self):
        keys = []
        for gloss in self.glosses:
            keys.extend(gloss.get_tagged_sensekey())
        return keys

    def get_terms_text(self):
        terms = []
        for term in self.terms:
            terms.append(term.term)
            if ' ' in term.term:
                terms.extend(term.term.split())
        return uniquify(terms)

    def __str__(self):
        return "sid: %s | terms: %s | keys: %s | glosses: %s | ofs-pos: %s-%s" % (
            self.sid, self.terms, self.keys, self.glosses, self.ofs, self.pos)
   
class Gloss:
    def __init__(self, synset, origid, cat, gid):
        self.synset = synset
        self.gid = gid
        self.origid = origid # Original ID from Gloss WordNet
        self.cat = cat
        self.items = []      # list of GlossItem objects
        self.tags = []       # Sense tags
        self.groups = []     # Other group labels
        pass

    def get_tagged_sensekey(self):
        return [ x.sk for x in self.tags if x ]

    def get_gramwords(self,nopunc=True):
        tokens = []
        for item in self.items:
            words = [ x for x in item.get_gramwords(nopunc)  if x ]
            tokens.extend(words)
        return tokens

    def add_gloss_item(self, tag, lemma, pos, cat, coll, rdf, origid, sep=None, text=None, itemid=-1):
        gt = GlossItem(self, tag, lemma, pos, cat, coll, rdf, origid, sep, text,itemid)
        gt.order = len(self.items)
        self.items.append(gt)
        return gt

    def tag_item(self, item, cat, tag, glob, glemma, glob_id, coll, origid, sid, sk, lemma, tagid=-1):
        tag = SenseTag(item, cat, tag, glob, glemma, glob_id, coll, origid, sid, sk, lemma, tagid)
        self.tags.append(tag)
        return tag

    def __repr__(self):
        return "gloss-%s" % (self.cat)

    def __str__(self):
        return "{Gloss oid='%s' type='%s' items: %s}" % (self.origid, self.cat, self.items)   

class GlossItem:
    ''' A word token (belong to a gloss)
    '''
    def __init__(self, gloss, tag, lemma, pos, cat, coll, rdf, origid, sep=None, text=None, itemid=-1):
        self.itemid = itemid
        self.gloss = gloss
        self.order = -1
        self.tag = StringTool.strip(tag)
        self.lemma = StringTool.strip(lemma)
        self.pos = StringTool.strip(pos)
        self.cat = StringTool.strip(cat)
        self.coll = StringTool.strip(coll)
        self.rdf = StringTool.strip(rdf)
        self.sep = StringTool.strip(sep)
        self.text = StringTool.strip(text)
        self.origid = StringTool.strip(origid)
        pass
    
    def get_lemma(self):
        return self.text if self.text else self.lemma
    
    def get_gramwords(self, nopunc=True):
        '''
        Return grammatical words from lemma
        E.g.
        prefer%2|preferred%3 => [ 'prefer', 'preferred' ]
        '''
        if nopunc and self.cat == 'punc':
            return set()
        lemmata = set()
        if self.lemma:
            tokens = self.lemma.split('|')
            for token in tokens:
                parts = token.split("%")
                lemmata.add(parts[0])
        else:
            lemmata.add(self.get_lemma())
        return lemmata

    def __repr__(self):
        # return "l:`%s'" % (self.get_lemma())
        return "'%s'" % self.get_lemma()

    def __str__(self):
        return "(itemid: %s | id:%s | tag:%s | lemma:%s | pos:%s | cat:%s | coll:%s | rdf: %s | sep:%s | text:%s)" % (
            self.itemid, self.origid, self.tag, self.lemma, self.pos, self.cat, self.coll, self.rdf, self.sep, self.text)

class GlossGroup:
    ''' A group tag (i.e. labelled GlossItem group)
    '''

    def __init__(self, label=''):
        self.label = label
        self.items = []    # List of GlossItem belong to this group

class SenseTag:
    ''' Sense annotation object
    '''
    def __init__(self, item, cat, tag, glob, glemma, glob_id, coll, origid, sid, sk, lemma, tagid=-1):
        self.tagid = tagid       # tag id
        self.cat = cat              # coll, tag, etc.      
        self.tag = tag        # from glob tag
        self.glob = glob      # from glob tag
        self.glemma = glemma  # from glob tag
        self.glob_id    = glob_id     # from glob tag
        self.coll = coll      # from cf tag
        self.origid = origid  # from id tag
        self.sid = sid              # infer from sk & lemma
        self.gid = item.gloss.gid   # gloss ID
        self.sk = sk          # from id tag
        self.lemma = lemma    # from id tag
        self.item = item            # ref to gloss item (we can access gloss obj via self.item)

    def __repr__(self):
        return "%s (sk:%s)" % (self.lemma, self.sk)

    def __str__(self):
        return "%s (sk:%s | itemid: %s | cat:%s | tag:%s | glob:%s | glemma:%s | gid:%s | coll:%s | origid: %s)" % (
            self.lemma, self.sk, self.item.itemid, self.cat, self.tag, self.glob, self.glemma, self.glob_id, self.coll, self.origid)
