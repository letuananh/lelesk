#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Shared functions of LeLesk tools
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

import os.path
import argparse
from puchikarui import Schema, Execution#, DataSource, Table
from chirptext.leutile import StringTool, Counter, Timer, uniquify, header, jilog, TextReport
from glosswordnet import XMLGWordNet, SQLiteGWordNet
import itertools
from wordnetsql import WordNetSQL as WSQL
from collections import defaultdict as dd
from collections import namedtuple
from lelesk import LeLeskWSD
from lelesk import LeskCache
from config import LLConfig

#-----------------------------------------------------------------------
# CONFIGURATION
#-----------------------------------------------------------------------
# >>> WARNING: Do NOT change these values here. Change config.py instead!
#
WORDNET_30_PATH = LLConfig.WORDNET_30_PATH
WORDNET_30_GLOSSTAG_PATH = LLConfig.WORDNET_30_GLOSSTAG_PATH
WORDNET_30_GLOSS_DB_PATH = LLConfig.WORDNET_30_GLOSS_DB_PATH
DB_INIT_SCRIPT = LLConfig.DB_INIT_SCRIPT

#-----------------------------------------------------------------------

def get_synset_by_id(wng_db_loc, synsetid, report_file=None):
    ''' Search synset in WordNet Gloss Corpus by synset ID 
    '''
    if report_file == None:
        report_file = TextReport() # Default to stdout
    report_file.print("Looking for synsets by synsetid (Provided: %s)\n" % synsetid)
 
    db = SQLiteGWordNet(wng_db_loc)
    if len(synsetid) == 10 and synsetid[8] == '-':
        synsetid = synsetid[9] + synsetid[:8]
    synsets = db.get_synset_by_id(synsetid)
    dump_synsets(synsets, report_file)

def get_synset_by_sk(wng_db_loc, sk, report_file=None):
    ''' Search synset in WordNet Gloss Corpus by sensekey 
    '''
    if report_file == None:
        report_file = TextReport() # Default to stdout
    report_file.print("Looking for synsets by sensekey (Provided: %s)\n" % sk)
    
    db = SQLiteGWordNet(wng_db_loc)
    synsets = db.get_synset_by_sk(sk)
    dump_synsets(synsets, report_file)
    
def get_synsets_by_term(wng_db_loc, t, pos, report_file=None):
    ''' Search synset in WordNet Gloss Corpus by term 
    '''
    if report_file == None:
        report_file = TextReport() # Default to stdout
    report_file.print("Looking for synsets by term (Provided: %s | pos = %s)\n" % (t, pos))

    db = SQLiteGWordNet(wng_db_loc)
    synsets = db.get_synsets_by_term(t, pos)
    dump_synsets(synsets, report_file)

#-----------------------------------------------------------------------

def dump_synsets(synsets, report_file=None):
    ''' Dump a SynsetCollection to stdout

    Arguments:
        synsets     -- List of synsets to dump
        report_file -- An instance of TextReport
    '''
    if report_file == None:
        report_file = TextReport() # Default to stdout

    if synsets:
        for synset in synsets:
            dump_synset(synset, report_file=report_file)
        report_file.print("Found %s synset(s)" % synsets.count())
    else:
        report_file.print("None was found!")

def dump_synset(ss, compact_gloss=False, compact_tags=False, more_compact=True, report_file=None):
    ''' Print synset details for debugging purpose

    Arguments:
        ss            -- Synset object to dump
        compact_gloss -- Don't dump gloss tokens' details
        compact_tags  -- Don't dump tagged senses' details
        more_compact  -- Don't dump full details of synset
        report_file   -- Report file to write to

    '''
    if report_file == None:
        report_file = TextReport() # Default to stdout
    
    if more_compact:
        report_file.header("Synset: %s (terms=%s | keys=%s)" % (ss.get_synsetid(), ss.terms, ss.keys), 'h0')
    else:
        report_file.header("Synset: %s" % ss, 'h0')

    for rgloss in ss.raw_glosses:
        if more_compact:
            if rgloss.cat != 'orig':
                continue
        report_file.print(rgloss)

    gloss_count = itertools.count(1)
    for gloss in ss.glosses:
        report_file.header("Gloss #%s: %s" % (next(gloss_count), gloss), 'h2')

        # Dump gloss items
        if compact_gloss:
            report_file.print("Tokens => %s" % gloss.get_gramwords(), level=2)
        else:
            for item in gloss.items:
                # print("\t%s - { %s }" % (uniquify(item.get_gramwords()), item))
                report_file.print("%s - { %s }" % (set(item.get_gramwords()), item), level=2)
            report_file.print(("-" * 10), level=1)
        
        # Dump tags
        if compact_tags:
            report_file.print("Tags => %s" % gloss.get_tagged_sensekey(), level=2)
        else:
            for tag in gloss.tags:
                report_file.print("%s" % tag, level=1)
    report_file.print('')

#--------------------------------------------------------

def main():
    jilog("This is a library, not a tool")

if __name__ == "__main__":
    main()
