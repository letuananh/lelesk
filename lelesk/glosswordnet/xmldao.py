#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Gloss WordNet XML Data Access Object - Access Gloss WordNet in XML format
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

from lxml import etree
from chirptext.leutile import StringTool, Counter
from glosswordnet.models import SynsetCollection, Synset, GlossRaw, SenseKey, Term, Gloss, GlossGroup, SenseTag, GlossItem

#-----------------------------------------------------------------------

class XMLGWordNet:
    ''' GWordNet XML Data Access Object
    '''    
    def __init__(self, memory_save=False, verbose=False):
        self.synsets = SynsetCollection()
        self.memory_save = memory_save
        self.verbose = verbose

    def readfiles(self, files):
        ''' Read from multiple XML files
        '''
        for filename in files:
            self.read(filename)

    def read(self, file_name):
        ''' Read all synsets from an XML file
        '''
        if self.verbose:
            print('Loading %s' %file_name)
        tree = etree.iterparse(file_name)
        c = Counter()

        for event, element in tree:
            if event == 'end' and element.tag == 'synset':
                synset = self.parse_synset(element)
                element.clear()
                self.synsets.add(synset)
            # end if end-synset
            c.count(element.tag)

        if self.verbose:
            c.summarise()
        return self.synsets

    def parse_synset(self, element):
        synset = Synset(element.get('id'),element.get('ofs'),element.get('pos')) if not self.memory_save else Synset(element.get('id'), '', '')
        for child in element:
            if child.tag == 'terms':
                for grandchild in child:
                    if grandchild.tag == 'term':
                        synset.add_term(StringTool.strip(grandchild.text))
            elif child.tag == 'keys':
                for grandchild in child:
                    if grandchild.tag == 'sk':
                        synset.add_sensekey(StringTool.strip(grandchild.text))
            elif child.tag == 'gloss' and child.get('desc') == 'orig' and not self.memory_save:
                if child[0].tag == 'orig':
                    synset.add_raw_gloss(GlossRaw.ORIG, StringTool.strip(child[0].text))
            elif child.tag == 'gloss' and child.get('desc') == 'text' and not self.memory_save:
                if child[0].tag == 'text':
                    synset.add_raw_gloss(GlossRaw.TEXT, StringTool.strip(child[0].text))
            elif child.tag == 'gloss' and child.get('desc') == 'wsd':
                for grandchild in child:
                    if grandchild.tag in ('def', 'ex'):
                        gloss = synset.add_gloss(grandchild.get('id'), StringTool.strip(grandchild.tag))
                        self.parse_gloss(grandchild, gloss)
                        # rip definition
                        pass
        #print("A synset")
        # print len(element)
        #print ','.join([ '%s (%s)' % (x.tag, ','.join([y.tag for y in x])) for x in element ])
        return synset

    def parse_gloss(self, a_node, gloss):
        ''' Parse a def node or ex node in Gloss WordNet
        '''
        # What to be expected in a node? aux/mwf/wf/cf/qf
        # mwf <- wf | cf
        # aux <- mwf | qf | wf | cf
        # qf <- mwf | qf | wf | cf
        for child_node in a_node:
            self.parse_node(child_node, gloss)
        pass

    def parse_node(self, a_node, gloss):
        ''' Parse node in a def node or an ex node.
            There are 5 possible tags: 
            wf : single-word form
            cf : collocation form
            mwf: multi-word form
            qf : single- and double-quoted forms
            aux: auxiliary info
        '''
        if a_node.tag == 'wf':
            return self.parse_wf(a_node, gloss)
        elif a_node.tag == 'cf':
            return self.parse_cf(a_node, gloss)
        elif a_node.tag == 'mwf':
            return self.parse_mwf(a_node, gloss)
        elif a_node.tag == 'qf':
            return self.parse_qf(a_node, gloss)
        elif a_node.tag == 'aux':
            return self.parse_aux(a_node, gloss)
        else:
            print("WARNING: I don't understand %s tag" % (a_node.tag))
        pass

    def tag_glossitem(self, id_node, glossitem, tag_obj):
        ''' Parse ID element and tag a glossitem
        '''
        sk = StringTool.strip(id_node.get('sk'))
        origid = StringTool.strip(id_node.get('id'))
        coll = StringTool.strip(id_node.get('coll'))
        lemma = StringTool.strip(id_node.get('lemma'))

        if tag_obj is None:
            tag_obj = glossitem.gloss.tag_item(glossitem, '', '', '', '', '', coll, origid, '', sk, lemma)
        else:
            tag_obj.sk     = sk
            tag_obj.origid = origid
            tag_obj.coll   = coll
            tag_obj.lemma  = lemma

        # WEIRD STUFF: lemma="purposefully ignored" sk="purposefully_ignored%0:00:00::"
        if lemma == 'purposefully ignored' and sk == "purposefully_ignored%0:00:00::":
            tag_obj.cat = 'PURPOSEFULLY_IGNORED'

    def parse_wf(self, wf_node, gloss):
        ''' Parse a word feature node and then add to gloss object
        '''
        tag = wf_node.get('tag') if not self.memory_save else ''
        lemma = wf_node.get('lemma') if not self.memory_save else ''
        pos = wf_node.get('pos')
        cat = wf_node.get('type') # if wf_node.get('type') else 'wf'
        coll = None # wf_node.get('coll')
        rdf = wf_node.get('rdf')
        origid = wf_node.get('id')
        sep = wf_node.get('sep')
        text = StringTool.strip(wf_node.xpath("string()")) # XML mixed content, don't use text attr here
        wf_obj = gloss.add_gloss_item(tag, lemma, pos, cat, coll, rdf, origid, sep, text)
        # Then parse id tag if available
        for child in wf_node:
            if child.tag == 'id':
                self.tag_glossitem(child, wf_obj, None)
        return wf_obj

    def parse_cf(self, cf_node, gloss):
        ''' Parse a word feature node and then add to gloss object
        '''
        tag = cf_node.get('tag') if not self.memory_save else ''
        lemma = StringTool.strip(cf_node.get('lemma')) if not self.memory_save else ''
        pos = cf_node.get('pos')
        cat = cf_node.get('type') # if cf_node.get('type') else 'cf'
        coll = cf_node.get('coll')
        rdf = cf_node.get('rdf')
        origid = cf_node.get('id')
        sep = cf_node.get('sep')
        text = StringTool.strip(cf_node.xpath("string()"))
        cf_obj =  gloss.add_gloss_item(tag, lemma, pos, cat, coll, rdf, origid, sep, text)
        # Parse glob info if it's available
        for child_node in cf_node:
            if child_node.tag == 'glob':
                glob_tag = child_node.get('tag')
                glob_glob = child_node.get('glob')
                glob_lemma = child_node.get('lemma')
                glob_coll = child_node.get('coll')
                glob_id = child_node.get('id')
                #            def tag_item(self, item,   cat,  tag,      glob,      glemma,     gid,     coll,      origid, sid, sk, lemma):
                tag_obj = cf_obj.gloss.tag_item(cf_obj, 'cf', glob_tag, glob_glob, glob_lemma, glob_id, glob_coll, '', '', '', '')
                for grandchild in child_node:
                    if grandchild.tag == 'id':
                        self.tag_glossitem(grandchild, cf_obj, tag_obj)
        return cf_obj

    def parse_mwf(self, mwf_node, gloss):
        child_nodes = [] 
        for child_node in mwf_node:
            a_node = self.parse_node(child_node, gloss)
        # [TODO] Add mwf tag to child nodes

    def parse_qf(self, qf_node, gloss):
        child_nodes = [] 
        for child_node in qf_node:
            a_node = self.parse_node(child_node, gloss)
        # [TODO] Add qf tag to child nodes

    def parse_aux(self, aux_node, gloss):
        child_nodes = [] 
        for child_node in aux_node:
            a_node = self.parse_node(child_node, gloss)
        # [TODO] Add aux tag to child nodes
