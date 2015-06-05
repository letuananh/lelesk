#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
A tool for converting Gloss WordNet into SQLite
Latest version can be found at https://github.com/letuananh/lelesk

Usage:
    # Search sysets by term (word form) = `love' and POS is verb
    python3 gwn2db.py -t 'love' -p 'v'

    # Search synsets by synset-id
    python3 gwn2db.py -s 'v01775535'

    # Search synsets by sensekey
    python3 gwn2db.py -k 'love%2:37:01::'

    # Create SQLite database for searching
    python3 gwn2db.py -c -i ~/wordnet/glosstag -o ~/wordnet/gwn.db



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
from chirptext.leutile import StringTool, Counter, Timer
from glosswordnet import XMLGWordNet, SQLiteGWordNet
import itertools
#-----------------------------------------------------------------------
# CONFIGURATION
#-----------------------------------------------------------------------
WORDNET_30_PATH = os.path.expanduser('~/wordnet/sqlite-30.db')
# WordNet SQLite can be downloaded from:
#       http://sourceforge.net/projects/wnsql/files/wnsql3/sqlite/3.0/ 

WORDNET_30_GLOSSTAG_PATH = os.path.expanduser('~/wordnet/glosstag')
WORDNET_30_GLOSS_DB_PATH = os.path.expanduser('~/wordnet/glosstag.db')
# Gloss WordNet can be downloaded from: 
#       http://wordnet.princeton.edu/glosstag.shtml

DB_INIT_SCRIPT = os.path.expanduser('./script/wngdb.sql')

#------------------------------------------------------------------------

def header(msg):
    print('')
    print('-' * 80)
    print(msg)
    print('')

#-----------------------------------------------------------------------

def get_synset_by_id(wng_db_loc, synsetid):
    db = SQLiteGWordNet(wng_db_loc)
    synsets = db.get_synset_by_id(synsetid)
    dump_synsets(synsets)

def get_synset_by_sk(wng_db_loc, sk):
    db = SQLiteGWordNet(wng_db_loc)
    synsets = db.get_synset_by_sk(sk)
    dump_synsets(synsets)
    
def get_synsets_by_term(wng_db_loc, t, pos):
    db = SQLiteGWordNet(wng_db_loc)
    synsets = db.get_synsets_by_term(t, pos)
    dump_synsets(synsets)

#-----------------------------------------------------------------------

def dump_synsets(synsets):
    if synsets:
        for synset in synsets:
            dump_synset(synset)
        print("Found %s synset(s)" % synsets.count())
    else:
        print("None was found!")

def dump_synset(ss):
    '''
    Print synset details for debugging purpose
    '''
    print("-" * 80)
    print("Synset: %s" % ss)
    print("-" * 80)

    for rgloss in ss.raw_glosses:
        print(rgloss)

    print('')

    gloss_count = itertools.count(1)
    for gloss in ss.glosses:
        print("Gloss #%s: %s" % (next(gloss_count), gloss))
        for item in gloss.items:
            print("\t%s - { %s }" % (item.get_gramword(), item))
        print("\t" + ("-" * 10))
        for tag in gloss.tags:
            print("\t%s" % tag)
        print('')
    print('')

def dev_mode():
    xml_file = os.path.expanduser('~/wordnet/glosstag/merged/test.xml')
    xmlwn = XMLGWordNet()
    xmlwn.read(xml_file)
    
    for ss in xmlwn.synsets[:5]:
        dump_synset(ss)

#--------------------------------------------------------

def xml2db(xml_files, db):
    t = Timer()

    header("Extracting Gloss WordNet (XML)")
    xmlgwn = XMLGWordNet()
    for xml_file in xml_files:
        t.start('Reading file: %s' % xml_file)
        xmlgwn.read(xml_file)
        t.end("Extraction completed %s" % xml_file)

    header("Inserting dat into SQLite database")
    t.start()
    db.insert_synsets(xmlgwn.synsets)
    t.end('Insertion completed.')
    pass

def convert(wng_loc, wng_db_loc, createdb):
    merged_folder = os.path.join(wng_loc, 'merged')
    
    print("Path to glosstag folder: %s" % (merged_folder))
    print("Path to output database: %s" % (wng_db_loc))
    print("Script to execute: %s" % (DB_INIT_SCRIPT))

    db = SQLiteGWordNet(wng_db_loc)
    if createdb:
        header('Preparing database file ...')
        db.setup(DB_INIT_SCRIPT)
    #--
    xmlfiles = [
        #os.path.join(merged_folder, 'test.xml')
        os.path.join(merged_folder, 'adv.xml')
        ,os.path.join(merged_folder, 'adj.xml')
        ,os.path.join(merged_folder, 'verb.xml')
        ,os.path.join(merged_folder, 'noun.xml')
    ]
    header('Importing data from XML to SQLite')
    xml2db(xmlfiles, db)
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
    # parser.add_argument('task', help='Task to perform (create/import/synset)')

    parser.add_argument('-i', '--wng_location', help='Path to Gloss WordNet folder (default = ~/wordnet/glosstag')
    parser.add_argument('-o', '--wng_db', help='Path to database file (default = ~/wordnet/glosstag.db')
    parser.add_argument('-c', '--create', help='Create DB and then import data', action='store_true')
    parser.add_argument('-d', '--dev', help='Dev mode (do not use)', action='store_true')
    parser.add_argument('-s', '--synset', help='Retrieve synset information by synsetid')
    parser.add_argument('-k', '--sensekey', help='Retrieve synset information by sensekey')
    parser.add_argument('-t', '--term', help='Retrieve synset information by term (word form)')
    parser.add_argument('-p', '--pos', help='Specify part-of-speech')



    # Optional argument(s)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")
    
    # Parse input arguments
    args = parser.parse_args()

    wng_loc = args.wng_location if args.wng_location else WORDNET_30_GLOSSTAG_PATH
    wng_db_loc = args.wng_db if args.wng_db else WORDNET_30_GLOSS_DB_PATH

    # Now do something ...
    if args.dev:
        dev_mode()
    elif args.create:
        convert(wng_loc, wng_db_loc, True)
    elif args.synset:
        get_synset_by_id(wng_db_loc, args.synset)
    elif args.sensekey:
        get_synset_by_sk(wng_db_loc, args.sensekey)
    elif args.term:
        get_synsets_by_term(wng_db_loc, args.term, args.pos)
    else:
        parser.print_help()
    pass # end main()

if __name__ == "__main__":
    main()


# Note:
# How to use this tool
# ./main.py candidates -i "dear|a"
