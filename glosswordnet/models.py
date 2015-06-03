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

from chirptext.leutile import StringTool, Counter

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
    
    def count(self):
        return len(self.synsets)

    # Merge with another Synset Collection
    def merge(self, another_scol):
        for synset in another_scol.synsets:
            self.add(synset)

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

    def __init__(self, sid, ofs, pos):
        self.sid   = sid
        self.ofs   = ofs
        self.pos   = pos
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

    def add_gloss(self, origid, cat):
        g = Gloss(self, origid, cat)
        self.glosses.append(g)
        return g

    def __str__(self):
        return "sid: %s | ofs: %s | pos: %s | keys: %s | terms: %s | glosses: %s" % (self.sid, self.ofs, self.pos, self.keys, self.terms, self.glosses)
   
class Gloss:
    def __init__(self, synset, origid, cat):
        self.synset = synset
        self.gid = -1
        self.origid = origid # Original ID from Gloss WordNet
        self.cat = cat
        self.items = []      # list of GlossItem objects
        self.tags = []       # Sense tags
        self.groups = []     # Other group labels
        pass

    def add_gloss_item(self, tag, lemma, pos, cat, coll, rdf, origid, sep=None, text=None):
        gt = GlossItem(self, tag, lemma, pos, cat, coll, rdf, origid, sep, text)
        gt.order = len(self.items)
        self.items.append(gt)
        return gt

    def tag_item(self, item, cat, tag, glob, glemma, glob_id, coll, origid, sid, sk, lemma):
        tag = SenseTag(item, cat, tag, glob, glemma, glob_id, coll, origid, sid, sk, lemma)
        self.tags.append(tag)
        return tag

    def __repr__(self):
        return "gloss-%s" % (self.cat)

    def __str__(self):
        return "{Gloss oid='%s' type='%s' items: %s}" % (self.origid, self.cat, self.items)   

class GlossItem:
    ''' A word token (belong to a gloss)
    '''
    def __init__(self, gloss, tag, lemma, pos, cat, coll, rdf, origid, sep=None, text=None):
        self.itemid = None
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
    
    def get_gramword(self):
        '''
        Return grammatical words from lemma
        E.g.
        prefer%2|preferred%3 => [ 'prefer', 'preferred' ]
        '''
        lemmata = []
        if self.lemma:
            tokens = self.lemma.split('|')
            for token in tokens:
                parts = token.split("%")
                lemmata.append(parts[0])
        else:
            lemmata.append(self.get_lemma())
        return lemmata

    def __repr__(self):
        # return "l:`%s'" % (self.get_lemma())
        return "'%s'" % self.get_lemma()

    def __str__(self):
        return "(id:%s | tag:%s | lemma:%s | pos:%s | cat:%s | coll:%s | rdf: %s | sep:%s | text:%s)" % (
            self.origid, self.tag, self.lemma, self.pos, self.cat, self.coll, self.rdf, self.sep, self.text)

class GlossGroup:
    ''' A group tag (i.e. labelled GlossItem group)
    '''

    def __init__(self, label=''):
        self.label = label
        self.items = []    # List of GlossItem belong to this group

class SenseTag:
    ''' Sense annotation object
    '''
    def __init__(self, item, cat, tag, glob, glemma, glob_id, coll, origid, sid, sk, lemma):
        self.tagid = None       # tag id
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
        return "%s (sk:%s | cat:%s | tag:%s | glob:%s | glemma:%s | gid:%s | coll:%s | origid: %s)" % (
            self.lemma, self.sk, self.cat, self.tag, self.glob, self.glemma, self.glob_id, self.coll, self.origid)
