#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Word Sense Disambiguation Toolkit
Latest version can be found at https://github.com/letuananh/lelesk

Usage:
    # Search sysets by term (word form) = `love' and POS is verb
    python3 wsdtk.py -t 'love' -p 'v'

    # Search synsets by synset-id
    python3 wsdtk.py -s 'v01775535'

    # Search synsets by sensekey
    python3 wsdtk.py -k 'love%2:37:01::'

    # Build lelesk set
    python3 wsdtk.py -g ~/wordnet/gwn.db -w ~/wordnet/sqlite-30.db -l v01775535 


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
from chirptext.leutile import StringTool, Counter, Timer, uniquify, header, jilog
from glosswordnet import XMLGWordNet, SQLiteGWordNet
import itertools
from wordnetsql import WordNetSQL as WSQL
from collections import defaultdict as dd
from collections import namedtuple

from lelesk import LeLeskWSD
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

OutputLine=namedtuple('OutputLine', 'results word correct_sense suggested_sense sentence_text'.split())

NTUMC_PRONOUNS= ['77000100-n', '77000057-n', '77000054-a', '77000054-n', '77000026-n', '77000065-n'
                , '77000025-n', '77000028-n', '77000004-n', '77010118-n', '77000104-n', '77000113-r', '77000003-n'
                , '77000107-a', '77000098-n', '77000059-n', '77000059-a', '77000008-n', '77000107-n', '77000048-n'
                , '01554230-n', '77010005-a', '77000088-r', '77000053-n', '77000113-a', '77000120-a', '77000123-n'
                , '77000050-n', '77000050-a', '77000093-n', '77000114-r', '77000117-n', '77000040-n', '77000090-n'
                , '77000114-a', '77000046-n', '01551633-n', '77000018-n', '77000009-n', '77000031-n', '77000032-n'
                , '77000078-n', '77000092-n', '77000041-n', '77000043-a', '02267686-n', '77000039-a', '77000095-n'
                , '77000081-n', '77000071-n', '02269039-n', '77000103-n', '77000072-n', '77000022-n', '77000108-n'
                , '77000021-n', '77000035-n', '77010002-a', '77000076-n', '77000085-n', '77000013-n', '77010001-a'
                , '77000074-n', '77000076-a', '02269286-n', '77000082-a', '77000017-n', '77010120-n', '77000082-n'
                , '77000061-a', '77000110-n', '77010006-a', '77000061-n', '77000024-a', '77000011-n', '77000016-n'
                , '77000024-n', '77000023-n', '77000052-n', '77000029-n', '77000064-n', '77000002-n', '77010119-n'
                , '77010003-a', '77010008-n', '77000058-a', '77000056-n', '77000099-n', '77000106-n', '77000058-n'
                , '77000006-n', '77000006-a', '77000139-n', '77000080-a', '02269635-n', '77000121-n', '77000091-a'
                , '77000089-r', '77010000-a', '77000091-n', '77000116-n', '77010004-a', '77000044-n', '77000089-a'
                , '77000122-n', '77000115-n', '77000019-n', '00524607-n', '77000033-n', '77000034-n', '77000045-n'
                , '77000084-n', '02267308-n', '77000109-n', '77000075-a', '77000075-n', '77000097-n', '77000001-n'
                , '77000073-n', '77000094-n', '77010122-n', '77000079-a', '77000111-n', '77000037-n', '77000012-n'
                , '77000079-n', '77000020-n', '77000027-n', '77000070-n', '02070188-n', '77000038-n', '77010121-n'
                , '77000015-n', '77000066-n', '77000137-n', '77000080-n', '77000060-n', '77010007-n', '77000060-a'
                , '77000112-n'
                 ]

def batch_wsd(infile_loc, wsd_obj, outfile_loc=None, method='lelesk', use_pos=False, assume_perfect_POS=False, lemmatizing=False, pretokenized=False):
    t = Timer()
    t.start("Reading file %s" % infile_loc)
    lines = open(os.path.expanduser(infile_loc)).readlines()
    t.end("File has been loaded")
    
    print(('-' * 80))
    c=Counter('Match InTop3 Wrong NoSense TotalSense'.split())
    outputlines = []
    # Counters for different type of words
    match_count = Counter()
    top3_count = Counter()
    wrong_count = Counter()
    nosense_count = Counter()


    # sample line in input file:
    # adventure 00796315-n  n   The Adventure of the Speckled Band  the|adventure|of|the|speckle|band
    for line in lines:
        if line.startswith('#'):
            # it is a comment line
            continue
        parts = line.split('\t')
        if parts:
            context = None
            if len(parts) == 3: 
                word = parts[0].strip()
                correct_sense = parts[1].strip()
                pos = None
                sentence_text = parts[2].strip()
            elif len(parts) == 4:
                word = parts[0].strip()
                correct_sense = parts[1].strip()
                pos = parts[2].strip()
                sentence_text = parts[3].strip()
            elif len(parts) == 5:
                word = parts[0].strip()
                correct_sense = parts[1].strip()
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
                scores = wsd_obj.mfs_wsd(word, sentence_text, correct_sense, lemmatizing=lemmatizing, pos=pos)
            else:
                if pretokenized and context and len(context) > 0:
                    # jilog("Activating Lelesk with pretokenized")
                    scores = wsd_obj.lelesk_wsd(word, sentence_text, correct_sense, lemmatizing=lemmatizing, pos=pos, context=context)
                else:
                    # jilog("Activating Lelesk with NTLK tokenizer")
                    scores = wsd_obj.lelesk_wsd(word, sentence_text, correct_sense, lemmatizing=lemmatizing, pos=pos)
            suggested_senses = [ score.candidate.synset.get_synsetid() for score in scores[:3] ]
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
            #print ("All scores")
            #for score in scores[:3]:
            #    print("Sense: %s - Score: %s - Definition: %s" % (
            #        score.candidate.synset.get_synsetid()
            #        , score.score
            #        , score.candidate.synset.get_orig_gloss()))
            #for score in scores[3:]:
            #    print("Sense: %s - Score: %s - Definition: %s" % (
            #        score.candidate.synset.get_synsetid()
            #        , score.score
            #        , score.candidate.synset.get_orig_gloss()))
            print("")
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

#-----------------------------------------------------------------------

def dump_synsets(synsets):
    ''' Dump a SynsetCollection to stdout
    '''
    if synsets:
        for synset in synsets:
            dump_synset(synset)
        print("Found %s synset(s)" % synsets.count())
    else:
        print("None was found!")

def dump_synset(ss, compact_gloss=False, compact_tags=False, more_compact=True):
    '''
    Print synset details for debugging purpose
    '''
    print("-" * 80)
    if more_compact:
        print("Synset: %s (terms=%s | keys=%s)" % (ss.get_synsetid(), ss.terms, ss.keys))
    else:
        print("Synset: %s" % ss)
    print("-" * 80)

    for rgloss in ss.raw_glosses:
        if more_compact:
            if rgloss.cat != 'orig':
                continue
        print(rgloss)

    gloss_count = itertools.count(1)
    for gloss in ss.glosses:
        print("Gloss #%s: %s" % (next(gloss_count), gloss))

        # Dump gloss items
        if compact_gloss:
            print("\tTokens => %s" % gloss.get_gramwords())
        else:
            for item in gloss.items:
                # print("\t%s - { %s }" % (uniquify(item.get_gramwords()), item))
                print("\t%s - { %s }" % (set(item.get_gramwords()), item))
            print("\t" + ("-" * 10))
        
        # Dump tags
        if compact_tags:
            print("\tTags => %s" % gloss.get_tagged_sensekey())
        else:
            for tag in gloss.tags:
                print("\t%s" % tag)
    print('')

#--------------------------------------------------------

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
    parser.add_argument('-w', '--wnsql', help='Location to WordNet 3.0 SQLite database')
    parser.add_argument('-g', '--glosswn', help='Location to Gloss WordNet SQLite database')

    parser.add_argument('-s', '--synset', help='Retrieve synset information by synsetid')
    parser.add_argument('-k', '--sensekey', help='Retrieve synset information by sensekey')
    parser.add_argument('-t', '--term', help='Retrieve synset information by term (word form)')
    parser.add_argument('-p', '--pos', help='Specify part-of-speech')

    parser.add_argument('-l', '--lelesk', help='Get hyponyms and hypernyms given a synsetID')
    parser.add_argument('-c', '--candidates', help='Retrieve Word Sense Disambiguation candidates for a word')
    parser.add_argument('-W', '--wsd', help='Perform WSD on a word [WSD] with a context X')
    parser.add_argument('-x', '--context', help="Context to perform WSD")

    parser.add_argument('-b', '--batch', help='Batch mode (e.g. python3 wsdtk.py -b myfile.txt')
    parser.add_argument('-o', '--output', help='Output log for batch mode')
    parser.add_argument('-m', '--method', help='WSD method (mfs/lelesk)')

    # Optional argument(s)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")
    
    # Parse input arguments
    args = parser.parse_args()

    wng_db_loc = args.glosswn if args.glosswn else WORDNET_30_GLOSS_DB_PATH
    wn30_loc = args.wnsql if args.wnsql else WORDNET_30_PATH
    wsd = LeLeskWSD(wng_db_loc, wn30_loc, verbose=not args.quiet)
    wsd_method = args.method if args.method else 'lelesk'
    # Now do something ...
    if args.synset:
        get_synset_by_id(wng_db_loc, args.synset)
    elif args.sensekey:
        get_synset_by_sk(wng_db_loc, args.sensekey)
    elif args.term:
        get_synsets_by_term(wng_db_loc, args.term, args.pos)
    # Retrieve lelesk tokens for a synset (given a synsetid)
    elif args.lelesk:
        wsd.build_lelesk_set(args.lelesk)
    # Retrieve all synset candidates and their tokens for a word
    elif args.candidates:
        wsd.build_lelesk_for_word(args.wsd)
    # perform WSD for a single word given a context
    elif args.wsd:
        word = args.wsd
        context = args.context
        if not context:
            print("Please use ./wsdtk.py -W MYWORD -x 'This is a context where MYWORD appear'")
        else:
            wsd.lelesk_wsd(word, context)
    # batch mode WSD
    elif args.batch:
        t1 = Timer()
        t1.start("Batch WSD started | Method=%s | File = %s" % (wsd_method, args.batch))
        batch_wsd(args.batch, wsd, args.output, wsd_method)
        t1.end("Batch WSD ended | Method=%s | File = %s" % (wsd_method, args.batch))
        pass
    else:
        parser.print_help()
    pass # end main()

if __name__ == "__main__":
    main()


# Note:
# How to use this tool
# ./main.py candidates -i "dear|a"
