#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LeLESK utilities
"""

# This code is a part of lelesk library: https://github.com/letuananh/lelesk
# :copyright: (c) 2014 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

from texttaglib.chirptext.cli import setup_logging
setup_logging('logging.json', 'logs')


from nltk.tokenize import word_tokenize
from nltk import pos_tag
from nltk.stem import WordNetLemmatizer

wnl = WordNetLemmatizer()


PUNCS = '''[][!"#$%&'()*+,./:;<=>?@\\^_`{|}~-]“”'''


def ptpos_to_wn(ptpos, default='x'):
    ''' Penn Treebank Project POS to WN '''
    # Ref: http://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html
    # CC Coordinating conjunction
    # CD Cardinal number
    # DT Determiner
    # EX Existential there
    # FW Foreign word
    # IN Preposition or subordinating conjunction
    # -----------------------------
    # JJ Adjective
    # JJR Adjective, comparative
    # JJS Adjective, superlative
    # -----------------------------
    # LS List item marker
    # MD Modal
    # -----------------------------
    # NN Noun, singular or mass
    # NNS Noun, plural
    # NNP Proper noun, singular
    # NNPS Proper noun, plural
    # -----------------------------
    # PDT Predeterminer
    # POS Possessive ending
    # PRP Personal pronoun
    # PRP$ Possessive pronoun
    # -----------------------------
    # RB Adverb
    # RBR Adverb, comparative
    # RBS Adverb, superlative
    # -----------------------------
    # RP Particle
    # SYM Symbol
    # TO to
    # UH Interjection
    # -----------------------------
    # VB Verb, base form
    # VBD Verb, past tense
    # VBG Verb, gerund or present participle
    # VBN Verb, past participle
    # VBP Verb, non­3rd person singular present
    # VBZ Verb, 3rd person singular present
    # -----------------------------
    # WDT Wh­determiner
    # WP Wh­pronoun
    # WP$ Possessive wh­pronoun
    # WRB Wh­adverb
    if ptpos.startswith('JJ'):
        return 'a'
    elif ptpos.startswith('NN'):
        return 'n'
    elif ptpos.startswith('RB'):
        return 'r'
    elif ptpos.startswith('VB'):
        return 'v'
    else:
        return default


def tokenize(sent):
    words = word_tokenize(sent)
    tags = pos_tag(words)
    tokens = [(w, t, wnl.lemmatize(w, pos=ptpos_to_wn(t, default='n'))) for w, t in tags]
    return tokens
