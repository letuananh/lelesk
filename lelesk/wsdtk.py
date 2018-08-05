#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Word Sense Disambiguation Toolkit
Latest version can be found at https://github.com/letuananh/lelesk

Usage:
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
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

__author__ = "Le Tuan Anh <tuananh.ke@gmail.com>"
__copyright__ = "Copyright 2014, lelesk"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

# import sys
import os.path
from collections import namedtuple

from chirptext.leutile import Timer, Counter, Table
from chirptext.cli import CLIApp, setup_logging
from chirptext import texttaglib as ttl
from yawlib import YLConfig

from .main import LeLeskWSD, LeskCache

# -----------------------------------------------------------------------

OutputLine = namedtuple('OutputLine', 'results word correct_sense suggested_sense sentence_text'.split())
setup_logging('logging.json', 'logs')


def generate_tokens(wsd):
    ''' Pre-generate LESK tokens for all synsets for faster WSD
    '''
    lesk_cache = LeskCache(wsd)
    lesk_cache.info()
    lesk_cache.generate()
    print("Done!")


# -----------------------------------------------------------------------

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
    tbatch = Timer()  # total time used to process this batch
    tbatch.start("Batch WSD started | Method=%s | File = %s" % (method, infile_loc))
    t = Timer()
    t.start("Reading file %s" % infile_loc)
    lines = open(os.path.expanduser(infile_loc)).readlines()
    t.end("File has been loaded")

    c = Counter('Match InTop3 Wrong NoSense TotalSense'.split())
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
                scores = wsd_obj.mfs_wsd(word, sentence_text, correct_sense, lemmatizing=lemmatizing, pos=pos)
            else:
                if pretokenized and context and len(context) > 0:
                    scores = wsd_obj.lelesk_wsd(word, sentence_text, correct_sense, lemmatizing=lemmatizing, pos=pos, context=context)
                else:
                    scores = wsd_obj.lelesk_wsd(word, sentence_text, correct_sense, lemmatizing=lemmatizing, pos=pos)
            suggested_senses = [score.candidate.synset.ID for score in scores[:3]]
            # c.count("TotalSense")

            if correct_sense in YLConfig.NTUMC_PRONOUNS:
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
        print("Writing output file ==> %s..." % (outfile_loc,))

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
    print("Batch job finished")


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


def get_lelesk_set(cli, args):
    ''' Get hyponyms and hypernyms given a synsetID '''
    wsd = build_wsd_object(cli, args)
    print(wsd.build_lelesk_set(args.synsetid))


def build_wsd_object(cli, args):
    wsd = LeLeskWSD(args.glosswn, args.wnsql, verbose=not args.quiet, dbcache=LeskCache())
    return wsd


def tokenize_text(cli, args):
    wsd = build_wsd_object(cli, args)
    tokens = wsd.prepare_data(args.text)
    for surface, pos, lemma in tokens:
        print(surface, pos, lemma)


def wsd_word(cli, args):
    ''' Perform WSD on a given WORD in a given CONTEXT'''
    print("WSD sentence: {}".format(args.context))
    sent = wsd_sent(ttl.Sentence(text=args.context), cli, args)
    print("Text: {}".format(sent.text))
    print("Tokens: {}".format(sent.tokens))
    for c in sent.concepts:
        print(c)
    # wsd = build_wsd_object(cli, args)
    # if not args.method or args.method != 'mfs':
    #     print("Performing LELESK on [{}] - Context: {}".format(args.word, args.context))
    #     output = wsd.lelesk_wsd(args.word, args.context)
    # else:
    #     print("Performing MFS on [{}] - Context: {}".format(args.word, args.context))
    #     output = wsd.mfs_wsd(args.word, args.context)
    # for score in output:
    #     c = score.candidate
    #     print("  - Score: {} | {}: {} | freq={}".format(score.score, c.synset, c.synset.definition, score.freq))


def wsd_ttl(cli, args):
    ''' Perform WSD on a TTL profile '''
    wsd = build_wsd_object(cli, args)
    doc = ttl.read(args.input, mode=args.ttl_format)  # input TTL
    # doc_path = os.path.dirname(args.output)
    # doc_name = os.path.basename(args.output)
    # new_doc = ttl.Document(doc_name, doc_path)
    if args.ttl_format == ttl.MODE_JSON:
        _writer = ttl.JSONWriter.from_path(args.output)
    else:
        _writer = ttl.TxtWriter.from_path(args.output)
    stopwords = set(wsd.stopwords)
    if not args.method or args.method.lower() in ('lesk', 'lelesk'):
        wsd_method = "LELESK"
        wsd_func = wsd.lelesk_wsd
    elif args.method.lower() == 'mfs':
        wsd_method = "MFS"
        wsd_func = wsd.mfs_wsd
    else:
        print("Unknown WSD method: {}".format(args.method))
        exit()
    print("WSD method: {}".format(wsd_method))
    for idx, sent in enumerate(doc):
        if args.topk and args.topk - 1 < idx:
            break
        print("Sent {}/{}: {} ".format(idx + 1, len(doc), sent.text))
        wsd_sent(sent, cli, args, wsd, stopwords, wsd_method, wsd_func)
        # if not sent.tokens:
        #     sent.tokens = wsd.tokenize(sent.text)
        # # lemmatize if needed
        # if not args.nolemmatize:
        #     wsd.lemmatize_ttl(sent)
        # # build WSD context
        # context = set(token.text.lower() for token in sent.tokens)
        # context.update(token.lemma.lower() for token in sent.tokens if token.lemma)
        # context = context - stopwords
        # for token in sent:
        #     if token.lemma in stopwords or token.text in stopwords:
        #         continue
        #     cli.logger.debug("Performing {} on [{}] - Context: {}".format(wsd_method, token.text, sent.text))
        #     output = wsd_func(token.lemma if token.lemma else token.text, sent.text, context=context)
        #     if output:
        #         c = output[0].candidate
        #         concept = sent.new_concept(c.synset.ID, clemma=token.lemma, tokens=[token])
        #         if not args.notag:
        #             # also make tags
        #             sent.new_tag(str(c.synset.ID), token.cfrom, token.cto, tagtype='WN')
        #         cli.logger.debug(concept)
        # write sentence
        _writer.write_sent(sent)
        # new_doc.add_sent(sent)
    # ttl.write(args.output, new_doc, mode=args.ttl_format)
    print("Output was written to {}".format(args.output))
    print("Done")
    pass


def wsd_sent(sent, cli, args, wsd=None, stopwords=None, wsd_method=None, wsd_func=None):
    if wsd is None:
        wsd = build_wsd_object(cli, args)
    if wsd_method is None or wsd_func is None:
        if not args.method or args.method.lower() in ('lesk', 'lelesk'):
            wsd_method = "LELESK"
            wsd_func = wsd.lelesk_wsd
        elif args.method.lower() == 'mfs':
            wsd_method = "MFS"
            wsd_func = wsd.mfs_wsd
    if stopwords is None:
        stopwords = set(wsd.stopwords)
    if not sent.tokens:
        sent.tokens = wsd.tokenize(sent.text)
    # lemmatize if needed
    if not args.nolemmatize:
        wsd.lemmatize_ttl(sent)
    # build WSD context
    context = set(token.text.lower() for token in sent.tokens)
    context.update(token.lemma.lower() for token in sent.tokens if token.lemma)
    context = context - stopwords
    cli.logger.debug("Sent #{} tokens: {}".format(sent.ID, [(t.text, t.lemma, t.pos) for t in sent]))
    cli.logger.debug("Sent #{} context: {}".format(sent.ID, context))
    for token in sent:
        if token.lemma in wsd.PUNCS or token.text in wsd.PUNCS:
            continue
        output = wsd_func(token.lemma if token.lemma else token.text, sent.text, context=context)
        if output:
            c = output[0].candidate
            concept = sent.new_concept(c.synset.ID, clemma=token.lemma if token.lemma else token.text, tokens=[token])
            if not args.notag:
                # also make tags
                sent.new_tag(str(c.synset.ID), token.cfrom, token.cto, tagtype='WN')
            cli.logger.debug("  #{} /{}/ tk:[{}] => {}".format(sent.ID, wsd_method, (token.text, token.lemma, token.pos), concept))
    return sent


def find_candidates(cli, args):
    ''' Retrieve Word Sense Disambiguation candidates for a word '''
    wsd = build_wsd_object(cli, args)
    candidates = wsd.build_lelesk_for_word(args.word, args.pos, deep_select=True)
    for candidate in candidates:
        print(candidate.id, candidate.synset.ID, candidate.synset.lemmas, candidate.synset.definition)


# -----------------------------------------------------------------------

def main():
    '''Main entry of WSD toolkit
    '''
    app = CLIApp(desc='LeLesk - Word-Sense Disambiguation Toolkit', logger=__name__)
    # Positional argument(s)
    app.parser.add_argument('-w', '--wnsql', help='Location to WordNet 3.0 SQLite database', default=YLConfig.WNSQL30_PATH)
    app.parser.add_argument('-g', '--glosswn', help='Location to Gloss WordNet SQLite database', default=YLConfig.GWN30_DB)

    task = app.add_task('lelesk', func=get_lelesk_set)
    task.add_argument('synsetid', help='Synset ID')

    task = app.add_task('candidates', func=find_candidates)
    task.add_argument('word', help='Word to search for synsets')
    task.add_argument('--pos', default=None)
    task.add_argument('--show_tokens', action="store_true")

    task = app.add_task('tokenize', func=tokenize_text)
    task.add_argument('text', help='Sentence text to analyse')

    task = app.add_task('wsd', func=wsd_word)
    task.add_argument('context', help='Context to perform WSD')
    task.add_argument('--word', help='word to perform WSD')
    task.add_argument('--notag', help='Also use sentence level tags for annotations', action='store_true')
    task.add_argument('--nolemmatize', help='Do not perform lemmatization', action='store_true')
    task.add_argument('-m', '--method', help='WSD method (mfs/lelesk)', choices=['mfs', 'lelesk'])

    task = app.add_task('ttl', func=wsd_ttl)
    task.add_argument('input', help='TTL profile')
    task.add_argument('output', help='Output TTL profile')
    task.add_argument('-n', '--topk', help='Only process top k sentences', type=int)
    task.add_argument('--notag', help='Also use sentence level tags for annotations', action='store_true')
    task.add_argument('--nolemmatize', help='Do not perform lemmatization', action='store_true')
    task.add_argument('-m', '--method', help='WSD method (mfs/lelesk)', choices=['mfs', 'lelesk', 'lesk'], default='lelesk')
    task.add_argument('--ttl_format', help='TTL format', default=ttl.MODE_TSV, choices=[ttl.MODE_JSON, ttl.MODE_TSV])
    app.run()

    # parser.add_argument('-b', '--batch', help='Batch mode (e.g. python3 wsdtk.py -b myfile.txt')
    # parser.add_argument('-o', '--output', help='Output log for batch mode')
    # parser.add_argument('-m', '--method', help='WSD method (mfs/lelesk)')
    # parser.add_argument('-d', '--leskdb', help='Generate tokens for all synsets for all synsets for faster WSD', action="store_true")
    # parser.add_argument('-r', '--report', help='Path to report file (default will be stdout)')

    # wsd = LeLeskWSD(wng_db_loc, wn30_loc, verbose=not args.quiet, dbcache=LeskCache())
    # wsd_method = args.method if args.method else 'lelesk'

    # perform WSD for a single word given a context
    # if args.wsd:
    #     word = args.wsd
    #     context = args.context
    #     if not context:
    #         print("Please use ./wsdtk.py -W MYWORD -x 'This is a context where MYWORD appear'")
    #     else:
    #         wsd.lelesk_wsd(word, context)
    # # batch mode WSD
    # elif args.batch:
    #     batch_wsd(args.batch, wsd, args.output, wsd_method)
    #     pass
    # elif args.leskdb:
    #     generate_tokens(wsd)
    # else:
    #     parser.print_help()
    # pass  # end main()


if __name__ == "__main__":
    main()
