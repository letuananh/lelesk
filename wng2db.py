#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
A tool for converting Gloss WordNet into SQLite
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

# import sys
import os.path
import argparse
from lxml import etree
from chirptext.leutile import StringTool, Counter
from puchikarui import Schema#, DataSource, Table
#-----------------------------------------------------------------------
# CONFIGURATION
#-----------------------------------------------------------------------
WORDNET_30_PATH = os.path.expanduser('~/wordnet/sqlite-30.db')
WORDNET_30_GLOSSTAG_PATH = os.path.expanduser('~/wordnet/glosstag')
WORDNET_30_GLOSS_DB_PATH = os.path.expanduser('~/wordnet/glosstag.db')
DB_INIT_SCRIPT = os.path.expanduser('./script/wngdb.sql')
#-----------------------------------------------------------------------

class SchemaDemo(Schema):
    def __init__(self, data_source=None):
        Schema.__init__(self, data_source)
        self.add_table('meta', 'title license WNVer url maintainer'.split())
        self.add_table('synset', ['id', 'offset', 'pos'])
        self.add_table('gloss', 'id sid orig gloss'.split())
        self.add_table('glossitem', 'id ord gid tag lemma pos cat coll rdf sep text origid'.split())
        self.add_table('sensetag', 'id cat tag glob glob_lemma coll origid sid gid sk tag_lemma tag_id tag_text itemid'.split())

#-----------------------------------------------------------------------

#-----------------------------------------------------------------------

def header(msg):
    print('')
    print('-' * 80)
    print(msg)
    print('')

class TaggedWord:
    def __init__(self, text, sk, lemma=None):
        self.text = text
        self.sk = sk
        self.lemma = lemma

class SynsetCollection:
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

    # Categories
    ORIG = 'orig' 
    TEXT = 'text'
    
    def __init__(self, synset, cat, gloss):
        self.synset = synset
        self.cat = cat
        self.gloss = gloss

class SenseKey:
    def __init__(self, synset, sensekey):
        self.synset = synset
        self.sensekey = sensekey

class Term:
    def __init__(self, synset, term):
        self.synset = synset
        self.term = term
        
class Synset:

    def __init__(self, sid, ofs, pos):
        self.sid   = sid
        self.ofs   = ofs
        self.pos   = pos
        self.keys  = []
        self.terms = []
        self.raw_glosses = []
        self.glosses = []

    def add_term(self, term):
        t = Term(self, term)
        self.terms.append(t)
    
    def add_sensekey(self, sk):
        sensekey = SenseKey(self, sk)
        self.keys.append(sensekey)

    def add_raw_gloss(self, cat, gloss):
        gr = GlossRaw(self, cat, gloss)
        self.raw_glosses.append(gr)

    def add_gloss(self, origid):
        g = Gloss(self, origid)
        self.glosses.append(g)

    def __str__(self):
        return "sid: %s | ofs: %s | pos: %s | keys: %s | terms: %s | glosses: %s" % (self.sid, self.ofs, self.pos, self.keys, self.terms, self.glosses)
   
class Gloss:
    def __init__(self, synset, origid):
        self.synset = synset
        self.origid = origid
        self.items = []
        self.tags = []
        pass

    def add_gloss_item(self, tag, lemma, pos, cat, coll, rdf, origid, sep = None, text = None):
        gt = GlossItem(self, tag, lemma, pos, cat, coll, rdf, origid, sep, text)
        self.tokens.append(gt)
        return gt

    def tag_item(self, item, cat, tag, glob, glemma, coll, origid, sid, sk, lemma, tag_id, text):
        tag = SenseTag(self, item, cat, tag, glob, glemma, coll, origid, sid, sk, lemma, tag_id, text)
        self.tags.append(tag)
        return tag

class SenseTag:
    def __init__(self, gloss, item, cat, tag, glob, glemma, coll, origid, sid, sk, lemma, tag_id, text):
        self.id = None
        self.cat = cat
        self.tag = tag
        self.glob = glob
        self.glemma = glemma
        self.coll = coll
        self.origid = origid
        self.sid = sid
        self.gloss = gloss
        self.sk = sk
        self.lemma = lemma
        self.tag_id = tag_id
        self.text = text
        self.item = item

    def __str__(self):
        return "%s (sk:%s)" % (self.lemma, self.sk)

class GlossItem:
    def __init__(self, gloss, tag, lemma, pos, cat, coll, rdf, origid, sep=None, text=None):
        self.id = None
        self.gloss = gloss
        self.tag = tag
        self.lemma = lemma
        self.pos = pos
        self.cat = cat
        self.coll = coll
        self.rdf = rdf
        self.sep = sep
        self.text = text
        self.origid = origid
        pass
    
    def __repr__(self):
        return str(self)
        
    def __str__(self):
        return "%s (id:%s)" % (self.lemma, self.origid)

class XMLGWordNet:
    @staticmethod
    def element_to_Synset(element, memory_save=True):
        synset = Synset(element.get('id'),element.get('ofs'),element.get('pos')) if not memory_save else Synset(element.get('id'), '', '')
        for child in element:
            if child.tag == 'terms':
                for grandchild in child:
                    if grandchild.tag == 'term':
                        synset.add_term(StringTool.strip(grandchild.text))
            elif child.tag == 'keys':
                for grandchild in child:
                    if grandchild.tag == 'sk':
                        synset.add_sensekey(StringTool.strip(grandchild.text))
            elif child.tag == 'gloss' and child.get('desc') == 'orig' and not memory_save:
                if child[0].tag == 'orig':
                    synset.add_raw_gloss(GlossRaw.ORIG, StringTool.strip(child[0].text))
            elif child.tag == 'gloss' and child.get('desc') == 'text' and not memory_save:
                if child[0].tag == 'text':
                    synset.add_raw_gloss(GlossRaw.TEXT, StringTool.strip(child[0].text))
            elif child.tag == 'gloss' and child.get('desc') == 'wsd':
                for grandchild in child:
                    if grandchild.tag in ('def', 'ex'):
                        gloss = synset.add_gloss(grandchild.get('id'))
                        XMLGWordNet.rip_gloss(grandchild, gloss)
                        # rip definition
                        pass
        #print("A synset")
        # print len(element)
        #print ','.join([ '%s (%s)' % (x.tag, ','.join([y.tag for y in x])) for x in element ])
        return synset

    @staticmethod
    def rip_gloss(a_node, gloss):
        ''' Parse a def node or ex node in Gloss WordNet
        '''
        # What to be expected in a node? aux/mwf/wf/cf/qf
        # mwf <- wf | cf
        # aux <- mwf | qf | wf | cf
        # qf <- mwf | qf | wf | cf

    @staticmethod
    def read_xml_data(file_name, synsets=None, memory_save=True):
        print('Loading %s' %file_name)
        tree = etree.iterparse(file_name)
        c = Counter()
        if synsets == None:
            synsets = SynsetCollection()
        for event, element in tree:
            #print("%s, %4s, %s" % (event, element.tag, element.text))
            if event == 'end' and element.tag == 'synset':
                synset = XMLGWordNet.element_to_Synset(element, memory_save)
                element.clear()
                synsets.add(synset)
                # print("Synset: [%s]" % synset)
            # end if end-synset
            c.count(element.tag)
        # print r
        # c.summarise()
        return synsets
        pass

    @staticmethod
    def extract_for_lesk(file_name, synsets, memory_save=True):
        print('Loading %s' %file_name)
        tree = etree.iterparse(file_name)
        c = Counter()
        if synsets == None:
            synsets = SynsetCollection()
        for event, element in tree:
            #print("%s, %4s, %s" % (event, element.tag, element.text))
            if event == 'end' and element.tag == 'synset':
                synset = XMLGWordNet.element_to_Synset(element, memory_save)
                simplified_synset = Synset(synset.sid, '', '')
                simplified_synset.keys.extend(synset.keys)
                simplified_synset.terms.extend(synset.terms)
                for token in synset.def_gloss:
                    simplified_synset.def_gloss.append(TaggedWord(token.text, token.sk, token.lemma))
                element.clear()
                synsets.add(simplified_synset)
                # print("Synset: [%s]" % synset)
            # end if end-synset
            c.count(element.tag)
        # print r
        # c.summarise()
        return synsets
        pass

    @staticmethod
    def rip_def_gloss(grandchild, synset, memory_save=True):
        for token_elem in grandchild:
            if token_elem.tag == 'wf':
                # Add gloss def
                lm = token_elem.get('lemma') if not memory_save else ''
                tag = token_elem.get('tag') if not memory_save else ''
                tk = synset.add_gloss_token(token_elem.get('id'), lm,token_elem.get('pos'),tag)
                if len(token_elem) >= 1 and token_elem[0].tag == 'id':
                    tk.sk = token_elem[0].get('sk')
                    if token_elem[0].text:
                        tk.text = StringTool.strip(token_elem[0].text)
                    else:
                        tk.text = StringTool.strip(token_elem[0].get('lemma'))
                else:
                    tk.text = StringTool.strip(token_elem.text)
            if token_elem.tag == 'cf':
                lm = token_elem.get('lemma') if not memory_save else ''
                tag = token_elem.get('tag') if not memory_save else ''
                tk = synset.add_gloss_token(token_elem.get('id'), lm,token_elem.get('pos'),tag)
                if len(token_elem) >= 1 and token_elem[0].tag == 'glob' and len(token_elem[0]) == 1 and token_elem[0][0].tag == 'id':
                    for tk_kid in token_elem[0]:
                        kid_sk = tk_kid.get('sk')
                        kid_txt = tk_kid.get('lemma')
                        if kid_sk and kid_txt:
                            tk.sk = kid_sk
                            tk.text = StringTool.strip(kid_txt)
                else:
                    tk.text = StringTool.strip(token_elem.text)
        # end each def token

def process(a_file, db):
    synsets = XMLGWordNet.read_xml_data(a_file)
    print(synsets.count())
    pass

def convert(wng_loc, wng_db_loc):
    merged_folder = os.path.join(wng_loc, 'merged')
    xml_file = os.path.join(merged_folder, 'test.xml')
    print("Path to glosstag folder: %s" % (merged_folder))
    print("Processing file  : %s" % (xml_file))
    print("Path to output database: %s" % (wng_db_loc))
    print("Script to execute: %s" % (DB_INIT_SCRIPT))

    db = SchemaDemo.connect(wng_db_loc)
    header('Creating database file ...')
    db.ds().executefile(DB_INIT_SCRIPT)
    try:
        for meta in db.meta.select():
            print(meta)
    except Exception:
        print("Error while setting up database ...")

    header('Extracting Gloss WordNet ...')
    process(xml_file, db)
    db.close()
    pass

def main():
    '''Main entry of wng2db

    Available commands:
        test: Run bank test
        candidates -i CHOSEN_WORD: Find candidates for a given word
        batch -i PATH_TO_FILE: Perform WSD on a batch file
        batch -i PATH_TO_SEMCOR_TEST_FILE: Perform WSD on Semcor (e.g. semcor_wn30.txt)
    '''
    # It's easier to create a user-friendly console application by using argparse
    # See reference at the top of this script
    parser = argparse.ArgumentParser(description="Convert Gloss WordNet from XML into SQLite DB.")
    
    # Positional argument(s)
    parser.add_argument('-i', '--wng_location', help='Path to Gloss WordNet folder (default = ~/wordnet/glosstag')
    parser.add_argument('-o', '--wng_db', help='Path to database file (default = ~/wordnet/glosstag.db')

    # Optional argument(s)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")
    
    # Parse input arguments
    args = parser.parse_args()
    # Now do something ...
    wng_loc = args.wng_location if args.wng_location else WORDNET_30_GLOSSTAG_PATH
    wng_db_loc = args.wng_db if args.wng_db else WORDNET_30_GLOSS_DB_PATH
    convert(wng_loc, wng_db_loc)
    pass # end main()

if __name__ == "__main__":
    main()


# Note:
# How to use this tool
# ./main.py candidates -i "dear|a"
