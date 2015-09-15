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

    # Test retrieving sense candidates for a word
    python3 wsdtk.py --candidates "love" --pos "v"

    # test WSD batch mode
    python3 wsdtk.py -b data/test.txt -o data/test_report.txt -r data/test_debug.txt


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
import itertools
from collections import defaultdict as dd
from collections import namedtuple

from puchikarui import Schema, Execution#, DataSource, Table
from chirptext.leutile import StringTool, Counter, Timer, uniquify, header, jilog, TextReport, Table

from .main import LeLeskWSD, LeskCache
from .config import LLConfig
from .common import dump_synsets, dump_synset, get_synset_by_id, get_synset_by_sk, get_synsets_by_term
from .glosswordnet import XMLGWordNet, SQLiteGWordNet
from .wordnetsql import WordNetSQL as WSQL

#-----------------------------------------------------------------------
# CONFIGURATION
#-----------------------------------------------------------------------
# >>> WARNING: Do NOT change these values here. Change config.py instead!
#
WORDNET_30_PATH = LLConfig.WORDNET_30_PATH
WORDNET_30_GLOSSTAG_PATH = LLConfig.WORDNET_30_GLOSSTAG_PATH
WORDNET_30_GLOSS_DB_PATH = LLConfig.WORDNET_30_GLOSS_DB_PATH
DB_INIT_SCRIPT = LLConfig.DB_INIT_SCRIPT
NTUMC_PRONOUNS= LLConfig.NTUMC_PRONOUNS
#-----------------------------------------------------------------------

def generate_tokens(wsd):
    ''' Pre-generate LESK tokens for all synsets for faster WSD
    '''
    lesk_cache  = LeskCache(wsd, report_file=wsd.report_file)
    lesk_cache.info()
    lesk_cache.setup()
    lesk_cache.generate()
    print("Done!")

#-----------------------------------------------------------------------

OutputLine=namedtuple('OutputLine', 'results word correct_sense suggested_sense sentence_text'.split())

def batch_wsd(infile_loc, wsd_obj, outfile_loc=None, method='lelesk', use_pos=False, assume_perfect_POS=False, lemmatizing=False, pretokenized=False):
    ''' Perform WSD in batch mode (input is a text file with each line is a sentence)
        
        Arguments:
            infile_loc         -- path to input file (Tab separated file)
            wsd_obj            -- WSD component (e.g. LeLeskWSD object)
            outfile_loc        -- Path to output (log) file
            method             -- 'lelesk' or 'mfs'
            use_pos            -- Use part-of-speech or not
            assume_perfect_POS -- If True then use POS from input file
            lemmatizing        -- Lemmatize tokens
            pretokenized       -- Use context's tokens from input file
    '''
    tbatch = Timer() # total time used to process this batch
    tbatch.start("Batch WSD started | Method=%s | File = %s" % (method, infile_loc))
    t = Timer()
    t.start("Reading file %s" % infile_loc)
    lines = open(os.path.expanduser(infile_loc)).readlines()
    t.end("File has been loaded")
    
    c=Counter('Match InTop3 Wrong NoSense TotalSense'.split())
    outputlines = []
    # Counters for different type of words
    match_count = Counter()
    top3_count = Counter()
    wrong_count = Counter()
    nosense_count = Counter()


    # sample line in input file:
    # adventure 00796315-n  n   The Adventure of the Speckled Band  the|adventure|of|the|speckle|band
    total_lines = len(lines)
    processed = 0
    for line in lines:
        processed += 1
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
            t.start('Analysing word ["%s"] on sentence: %s' % (word, sentence_text))
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
            t.end('Analysed word ["%s"] (%s/%s completed)' % (word, processed, total_lines))
    print("")
    tbatch.start("Batch WSD finished | Method=%s | File = %s" % (method, infile_loc))
    

    if outfile_loc:
        jilog("Writing output file ==> %s..." % (outfile_loc,))

        with open(outfile_loc, 'w') as outfile:
            outfile.write("Sections\n")
            outfile.write("::SENTENCES::\n")
            outfile.write("::MATCH-TOKENS::\n")
            outfile.write("::TOP3-TOKENS::\n")
            outfile.write("::WRONG-TOKENS::\n")
            outfile.write("::NOSENSE-TOKENS::\n")
            outfile.write("::SUMMARY::\n")
            outfile.write(("-" * 20) + '\n')

            outfile.write("::SENTENCES::\n")
            tbl = Table()
            tbl.add_row("results word correct_sense suggested_sense sentence_text".split())
            for line in outputlines:
                tbl.add_row((line.results ,line.word ,line.correct_sense ,line.suggested_sense ,line.sentence_text))
            print_tbl = lambda x: outfile.write('%s\n' % x)
            # write table
            tbl.print(print_func=print_tbl)
            
            outfile.write("\n")
            # dump counter tokens
            dump_counter(match_count, outfile, '::MATCH-TOKENS::')
            dump_counter(top3_count, outfile, '::TOP3-TOKENS::')
            dump_counter(wrong_count, outfile, '::WRONG-TOKENS::')
            dump_counter(nosense_count, outfile, '::NOSENSE-TOKENS::')
            # write summary
            totalcount = len(match_count) + len(top3_count) + len(wrong_count) + len(nosense_count)
            outfile.write("\n")
            outfile.write("::SUMMARY::\n")
            outfile.write("%s\n" % (tbatch))
            outfile.write("\n")
            outfile.write("| Information                         |    Instance | Classes |\n")
            outfile.write("|:------------------------------------|--------:|-----------:\n")
            outfile.write("| Correct sense ranked the first      |   %s | %s |\n" % (str(c['Match']).rjust(5, ' '), str(len(match_count)).rjust(5, ' ')))
            outfile.write("| Correct sense ranked the 2nd or 3rd |   %s | %s |\n" % (str(c['InTop3']).rjust(5, ' '), str(len(top3_count)).rjust(5, ' ')))
            outfile.write("| Wrong                               |   %s | %s |\n" % (str(c['Wrong']).rjust(5, ' '), str(len(wrong_count)).rjust(5, ' ')))
            outfile.write("| NoSense                             |   %s | %s |\n" % (str(c['NoSense']).rjust(5, ' '), str(len(nosense_count)).rjust(5, ' ')))
            outfile.write("| TotalSense                          |   %s | %s |\n" % (str(c['TotalSense']).rjust(5, ' '), str('').rjust(5, ' '))) # totalcount is wrong!
    jilog("Batch job finished")

def dump_counter(counter, file_obj, header):
    tbl = Table()
    tbl.add_row(["Synset ID", "Lemma", "Count"])
    items = counter.sorted_by_count()
    for k, v in items:
        tbl.add_row(k.split('\t') + [v])

    print_tbl = lambda x: file_obj.write('%s\n' % x)
    file_obj.write("\n")

    # write header
    file_obj.write("\n%s\n" % header)
    # write table
    tbl.print(print_func=print_tbl)

#-----------------------------------------------------------------------

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

    parser.add_argument('-d', '--leskdb', help='Generate tokens for all synsets for all synsets for faster WSD', action="store_true")

    parser.add_argument('-r', '--report', help='Path to report file (default will be stdout)')

    # Optional argument(s)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")
    
    # Parse input arguments
    args = parser.parse_args()

    wng_db_loc = args.glosswn if args.glosswn else WORDNET_30_GLOSS_DB_PATH
    wn30_loc = args.wnsql if args.wnsql else WORDNET_30_PATH
    report = TextReport(args.report) if args.report else TextReport()
    wsd = LeLeskWSD(wng_db_loc, wn30_loc, verbose=not args.quiet, report_file=report)
    wsd_method = args.method if args.method else 'lelesk'
    

    # Now do something ...
    if args.synset:
        get_synset_by_id(wng_db_loc, args.synset, report)
    elif args.sensekey:
        get_synset_by_sk(wng_db_loc, args.sensekey, report)
    elif args.term:
        get_synsets_by_term(wng_db_loc, args.term, args.pos, report_file=report)
    # Retrieve lelesk tokens for a synset (given a synsetid)
    elif args.lelesk:
        wsd.build_lelesk_set(args.lelesk)
    # Retrieve all synset candidates and their tokens for a word
    elif args.candidates:
        wsd.build_lelesk_for_word(args.candidates, args.pos)
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
        batch_wsd(args.batch, wsd, args.output, wsd_method)
        pass
    elif args.leskdb:
        generate_tokens(wsd)
    else:
        parser.print_help()
    pass # end main()

if __name__ == "__main__":
    main()


# Note:
# How to use this tool
# ./main.py --candidates "love" --pos "v"