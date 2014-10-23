#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright (c) 2014, Le Tuan Anh <tuananh.ke@gmail.com>

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

import sys
import nltk
from nltk import WordNetLemmatizer
from collections import namedtuple
from collections import defaultdict as dd
import sqlite3
import os.path
import xml.etree.ElementTree as ET
import re
from nltk.corpus import stopwords
from operator import itemgetter
from le_utile import *
#-----------------------------------------------------------------------
# CONFIGURATION
#-----------------------------------------------------------------------
WORDNET_30_PATH = os.path.expanduser('~/wordnet/sqlite-30.db')
WORDNET_30_GLOSSTAG_PATH = os.path.expanduser('~/wordnet/glosstag')
#-----------------------------------------------------------------------
reword = re.compile('\w+')

class XMLCache:
        cache = dict()

        @staticmethod
        def parse(file_path):
                if not XMLCache.cache.has_key(file_path):
                        XMLCache.cache[file_path] = ET.parse(file_path).getroot()
                return XMLCache.cache[file_path]

        @staticmethod
        def cache_all(root_folder, verbose=True):
                fcount = 0
                for root, subfolders, files in os.walk(root_folder):
                        for filename in files:
                                if filename.endswith('-wngloss.xml') or filename.endswith('-wnann.xml') or filename.endswith('-wnword.xml'):
                                        fullpath = os.path.join(root, filename)
                                        XMLCache.parse(fullpath)
                                        if verbose:
                                                print('Caching file: %s' % fullpath)
                                # print filename
                                fcount += 1
                print ("Found %s XML files" % fcount)

class SenseGloss:
	def __init__(self, sid, sfrom, sto, stype):
		self.sid = sid
		self.sfrom = sfrom
		self.sto = sto
		self.stype = stype
		self.tokens = []
		
	def __str__(self):
		return "Sense: %s | from-to: [%s-%s] | type: %s" % (
		self.sid, self.sfrom, self.sto, self.stype)

SenseInfo = namedtuple('SenseInfo', ['pos', 'synsetid', 'sensekey'])

class SenseInfo:
	def __init__(self, pos, synsetid, sensekey, wordid='', gloss=''):
		self.pos = pos
		self.sid = synsetid
		self.sk = sensekey
		self.wordid = wordid
		self.gloss = gloss
	
	def get_full_sid(self):
		return self.pos + str(self.sid)[1:]
	def __str__(self):
		return "SenseInfo: pos:%s | synsetid:%s | sensekey:%s" % (self.pos, self.sid, self.sk)
	
class GlossInfo:
	def __init__(self, sid, sfrom, sto, stype, lemma, pos, tag, text, sk):
		self.sid = sid
		self.sfrom = sfrom
		self.sto = sto
		self.stype = stype
		self.lemma = lemma
		self.pos = pos
		self.tag = tag
		self.text = text
		self.sk = sk # sensekey
		
	@staticmethod
	def from_dict(a_dict):
		return GlossInfo(a_dict['sid'], a_dict['sfrom'],a_dict['sto'],a_dict['stype'],a_dict['lemma'], a_dict['pos'], a_dict['tag'], a_dict['text'], a_dict['wnsk'])
	
	def __str__(self):
		return "lemma: %s | pos: %s | tag: %s | text: %s | sk: %s | sid: %s | from-to: [%s-%s] | stype: %s" % 		 (self.lemma, self.pos, self.tag, self.text, self.sk, self.sid, self.sfrom, self.sto, self.stype)

class WordNetGlossTag:
	def __init__(self, wndb_path, glosstag_path):
		self.wndb_path = wndb_path
		self.glosstag_path = glosstag_path
		self.standoff = os.path.join(self.glosstag_path, 'standoff')
		self.load_glosstag()
		
	def load_glosstag(self):
		# Read index (by ID) file
		self.sid_index = dict()
		index_lines = open(os.path.join(self.glosstag_path, 'standoff', 'index.byid.tab')).readlines()
		for line in index_lines:
			parts = [ x.strip() for x in line.split('\t')]
			if len(parts) == 2:
				self.sid_index[parts[0]] = parts[1]
		# Read SK index
		self.sk_index = dict()
		index_lines = open(os.path.join(self.glosstag_path, 'standoff', 'index.bysk.tab')).readlines()
		for line in index_lines:
			parts = [ x.strip() for x in line.split('\t')]
			if len(parts) == 2:
				self.sk_index[parts[0]] = parts[1]
	
	sk_cache = dict()
	def get_senseinfo_by_sk(self, sk):
		if WordNetGlossTag.sk_cache.has_key(sk):
			return WordNetGlossTag.sk_cache[sk]
		conn = sqlite3.connect(WORDNET_30_PATH)
		c = conn.cursor()
		result = c.execute("""SELECT pos, synsetid, sensekey 
								FROM wordsXsensesXsynsets
								WHERE sensekey = ?;""", (sk,)).fetchone()
		sid = None
		if result:
			pos, synid, sk = result
			sid = SenseInfo(pos, synid, sk)
		conn.close()
		WordNetGlossTag.sk_cache[sk] = sid
		return sid

	def cache_all_sensekey(self):
			conn = sqlite3.connect(WORDNET_30_PATH)
		c = conn.cursor()
		result = c.execute("""SELECT pos, synsetid, sensekey FROM wordsXsensesXsynsets""").fetchall()
		for (pos, synid, sk) in result:
			sif = SenseInfo(pos, synid, sk)
			WordNetGlossTag.sk_cache[sk] = sif
		conn.close()
	
	hypehypo_cache=dict()	
	def get_hypehypo(self, sid):
		if WordNetGlossTag.hypehypo_cache.has_key(sid):
			return WordNetGlossTag.hypehypo_cache[sid]
		query = '''SELECT linkid, dpos, dsynsetid, dsensekey, dwordid
					FROM sensesXsemlinksXsenses 
					WHERE ssynsetid = ? and linkid in (1,2,3,4, 11,12,13,14,15,16,40,50,81);'''
		conn = sqlite3.connect(WORDNET_30_PATH)
		c = conn.cursor()
		result = c.execute(query, (sid,)).fetchall()
		senses = []
		for (linkid, dpos, dsynsetid, dsensekey, dwordid) in result:
			senses.append(SenseInfo(dpos, dsynsetid, dsensekey, dwordid))
		conn.close()
		WordNetGlossTag.hypehypo_cache[sid] = senses
		return senses
	
	def cache_all_hypehypo(self):
		query = '''SELECT linkid, ssynsetid, dpos, dsynsetid, dsensekey, dwordid
					FROM sensesXsemlinksXsenses 
					WHERE linkid in (1,2,3,4, 11,12,13,14,15,16,40,50,81);'''
		conn = sqlite3.connect(WORDNET_30_PATH)
		c = conn.cursor()
		result = c.execute(query).fetchall()
		for (linkid, ssynsetid, dpos, dsynsetid, dsensekey, dwordid) in result:
			if not WordNetGlossTag.hypehypo_cache.has_key(ssynsetid):
					 WordNetGlossTag.hypehypo_cache[ssynsetid] = []
			WordNetGlossTag.hypehypo_cache[ssynsetid].append(SenseInfo(dpos, dsynsetid, dsensekey, dwordid))
		conn.close()

	word_cache=dict()
	def get_hypehypo_text(self, sid):
		senses = self.get_hypehypo(sid)
		if not senses: 
			return []
		else:
			lemmas = []
			wordids = [ sense.wordid for sense in senses ]
			need_to_find = []
			for wordid in wordids:
				if WordNetGlossTag.word_cache.has_key(wordid):
					lemmas.append(WordNetGlossTag.word_cache[wordid])
				else:
					need_to_find.append(str(wordid))
			if len(need_to_find) > 0:
				# search in database
				query = '''SELECT wordid, lemma FROM words
							WHERE wordid in (%s);''' % ','.join(need_to_find)
				conn = sqlite3.connect(WORDNET_30_PATH)
				c = conn.cursor()
				result = c.execute(query).fetchall()
				for (wordid, lemma) in result:
					WordNetGlossTag.word_cache[wordid] = lemma
					lemmas.append(lemma)
				conn.close()
			return lemmas
	def cache_all_words(self):
		query = '''SELECT wordid, lemma FROM words'''
		conn = sqlite3.connect(WORDNET_30_PATH)
		c = conn.cursor()
		result = c.execute(query).fetchall()
		for (wordid, lemma) in result:
				WordNetGlossTag.word_cache[wordid] = lemma
		conn.close()

			
	sense_cache = dict()
	def get_all_senses(self, lemma):
		if WordNetGlossTag.sense_cache.has_key(lemma):
			return WordNetGlossTag.sense_cache[lemma]
		conn = sqlite3.connect(WORDNET_30_PATH)
		c = conn.cursor()
		result = c.execute("""SELECT pos, synsetid, sensekey, definition 
								FROM wordsXsensesXsynsets
								WHERE lemma = ?;""", (lemma,)).fetchall()
		senses = []
		for (pos, synsetid, sensekey, definition) in result:
			senses.append(SenseInfo(pos, synsetid, sensekey, '', definition))
		conn.close()
		WordNetGlossTag.sense_cache[lemma] = senses
		return senses
	
	def cache_all_sense_by_lemma(self):
			conn = sqlite3.connect(WORDNET_30_PATH)
	c = conn.cursor()
	result = c.execute("""SELECT lemma, pos, synsetid, sensekey, definition FROM wordsXsensesXsynsets;""").fetchall()

	for (lemma, pos, synsetid, sensekey, definition) in result:
					if not WordNetGlossTag.sense_cache.has_key(lemma):
							WordNetGlossTag.sense_cache[lemma] = []
		WordNetGlossTag.sense_cache[lemma].append(SenseInfo(pos, synsetid, sensekey, '', definition))
	conn.close()

	def get_gloss_by_sk(self, sk):
		sid = self.get_senseinfo_by_sk(sk).get_full_sid()
		return self.get_gloss_by_id(sid)
	
	gloss_cache = dict()
	def get_gloss_by_id(self, sid):
		if WordNetGlossTag.gloss_cache.has_key(sid):
			return WordNetGlossTag.gloss_cache[sid]
		if not sid:
			return None
		gloss_file = self.search_by_id(sid)
		if not gloss_file:
			return None
		gloss_file_loc = os.path.join(self.standoff, gloss_file + '-wngloss.xml')
		gloss_data = XMLCache.parse(gloss_file_loc).find("./{http://www.xces.org/schema/2003}struct[@id='%s']" % (sid + '_d',))
		# Build gloss object
		a_sense = SenseGloss(gloss_data.get('id'), 
							gloss_data.get('from'), 
							gloss_data.get('to'), 
							gloss_data.get('type'))
		# Retrieve each gloss token
		ann_file_loc = os.path.join(self.standoff, gloss_file + '-wnann.xml')
		ann = XMLCache.parse(ann_file_loc).findall("./{http://www.xces.org/schema/2003}struct")
		wnword_file_loc = os.path.join(self.standoff, gloss_file + '-wnword.xml')
		wnword = XMLCache.parse(wnword_file_loc)
		if len(ann) > 0:
			for elem in ann:
				if elem.attrib['id'].startswith(sid):
					features = dd(lambda: '')
					features['sid'] = elem.get('id')
					features['sfrom'] = elem.get('from')
					features['sto'] = elem.get('to')
					features['stype'] = elem.get('type')
					# We only use the gloss part
					#if int(features['sfrom']) > int(a_sense.sto):
					#	break
					for feat in elem:
						features[feat.get('name')] = feat.get('value')
					# Look for sensekey if available
					wnsk = wnword.findall("./{http://www.xces.org/schema/2003}struct[@id='%s']/*[@name='wnsk']" % (elem.get('id'),))
					if len(wnsk) == 1:
						features['wnsk'] = wnsk[0].get('value')
					a_sense.tokens.append(GlossInfo.from_dict(features))
			# Read glosses data
			WordNetGlossTag.gloss_cache[sid] = a_sense
			return a_sense
		else:
			WordNetGlossTag.gloss_cache[sid] = None
			return None
		pass
			
	# Search a synset by ID
	def search_by_id(self, synset_id):
		#print 'searching %s' % synset_id
		if self.sid_index.has_key(synset_id):
			return self.sid_index[synset_id]
		else:
			return None
	
	# Search a synset by sensekey
	def search_by_sk(self, wnsk):
		if self.sk_index.has_key(wnsk):
			return self.sk_index[wnsk]
		else:
			return 'N/A'
	
	@staticmethod
	def get_default(auto_cache=True):
                wng = WordNetGlossTag(WORDNET_30_PATH, WORDNET_30_GLOSSTAG_PATH)
                # Cache everything into memory if needed
                if auto_cache:
                        wng.cache_all_words()
                        wng.cache_all_sense_by_lemma()
                        wng.cache_all_hypehypo()
                        wng.cache_all_sensekey()
                return wng
		
'''
Given a sentence as a raw text string, perform tokenization, lemmatization
'''
def prepare_data(sentence_text):
	# Tokenization
	tokens = nltk.word_tokenize(sentence_text)
	# Lemmatization
	wnl = WordNetLemmatizer()
	tokens = [ wnl.lemmatize(x) for x in tokens]
	return tokens

class GlossTokens:
	def __init__(self):
		self.tokens = []
		self.sk = []

def get_gloss_token(wng, sk):
	gt = GlossTokens()
	senseinfo = wng.get_senseinfo_by_sk(sk)
	if not senseinfo:
		return gt
	sid = senseinfo.get_full_sid()
	gloss = wng.get_gloss_by_id(sid)
	if gloss:
		for token in gloss.tokens:
			# remove stopword & punctuations
			if reword.match(token.text) and token.text not in stopwords.words('english'):
				gt.tokens.append(token.text)
			if token.sk:
				gt.sk.append(token.sk)
	return gt

class WSDCandidate:
	def __init__(self, sense=None):
		self.sense = sense #SenseInfo
		self.tokens = []

def get_sense_candidates(wng, word):
	senses = wng.get_all_senses(word)
	candidates = []
	# sc = len(senses)
	num = 0
        # t = Timer()
        # t2 = Timer()
	for sense in senses:
		num+=1
		# print("Processing sense %s/%s for the word [%s]" % (num, sc, word))
		candidate = WSDCandidate(sense)
		sk = sense.sk
                # t.start()
		gt = get_gloss_token(wng, sk)
		candidate.tokens += gt.tokens
		for child_sk in gt.sk:
                        # t2.start() 
			child_gt = get_gloss_token(wng, child_sk)
			#print child_sk + str(child_gt.tokens)
			candidate.tokens += child_gt.tokens
                        # t2.stop().log('get child gloss')
			# extend hypernyms & hyponyms
                        senseinfo = wng.get_senseinfo_by_sk(child_sk)
			if senseinfo:
                                # t2.start()
				more_tokens = wng.get_hypehypo_text(senseinfo.sid)
				# print("Extending: %s" % more_tokens)
				candidate.tokens += more_tokens # Hype & hypo of tagged tokens
                                #t2.stop().log('Finished hypehypo')
		#print "-" * 20
		#print "Final: %s" % candidate.tokens
		candidates.append(candidate)
                # t.stop().log('Finished build a candidate')
	return candidates
	pass

''' Perform Word-sense disambiguation with extended simplified LESK and 
annotated WordNet 3.0
'''
def lelesk_wsd(word, context):
	wng = WordNetGlossTag.get_default()
	#1. Retrieve candidates for the given word
	candidates = get_sense_candidates(wng, word)
	#2. Calculate overlap between the context and each given word
	context_set = set(context)
	# print(context_set)
	scores = []
	wnl = WordNetLemmatizer()
	for candidate in candidates:
		candidate_set = set([ wnl.lemmatize(x) for x in candidate.tokens])
		# print(candidate_set)
		score = len(context_set.intersection(candidate_set))
		scores.append([candidate, score])
	scores.sort(key=itemgetter(1))
	scores.reverse()
	return scores
	
#-----------------------------------------------------------------------
# Main function
#-----------------------------------------------------------------------
def main():	
        testset = { 'test' : test_wsd, 'optimize' : optimize }
        if len(sys.argv) < 2 or sys.argv[1] not in testset.keys():
                print_usage()
        else:
                testset[sys.argv[1]]()
	pass

def print_usage():
        print('''Usage:
        %s: Show this usage
        %s test: Run bank test
        ''' % (sys.argv[0], sys.argv[0]))
        pass

def test_wsd():
        word = 'bank'
	sentence_texts = ['I went to the bank to deposit money.', 'The river bank is full of dead fish.']
        t = Timer()
	for sentence_text in sentence_texts:
                t.start()
		context = prepare_data(sentence_text)
		print ("WSD for the word: %s" % word)
		print ("Context: %s" % context)
		scores = lelesk_wsd(word, context)
		print ("Top 3 scores")
		for score in scores[:3]:
			print ("Sense: %s - Score: %s - Definition: %s" % (score[0].sense.get_full_sid(), score[1], score[0].sense.gloss))
                t.end('Analysed sentence: %s' % sentence_text)

def optimize():
        wng = WordNetGlossTag.get_default()
        t = Timer()

        # Cache all XML
        t.start()
        XMLCache.cache_all(os.path.join(WORDNET_30_GLOSSTAG_PATH, 'standoff'))
        t.end('Cached all XML')

        t.start()
        wng.cache_all_words()
        t.stop().log('Cache all words')

        t.start()
        wng.cache_all_sensekey()
        t.stop().log('Cache all sensekeys')

        t.start()
        wng.cache_all_hypehypo()
        t.stop().log('Cache all hypehypo')

        t.start()
        wng.cache_all_sense_by_lemma()
        t.stop().log('Cache all sense by lemma')

        # Profiling select senses from database
        t.start()
        senses = wng.get_all_senses('table')
        print len(senses)
        t.stop().log('Test select all senses')

        # Profiling get by sk
        t.start()
        sk = 'side%1:15:01::'
	file_loc = wng.search_by_sk(sk)
	sid = wng.get_senseinfo_by_sk(sk).get_full_sid()
	print ("Looking at %s - File loc: %s - SID: %s" % (sk,file_loc, sid))
	a_sense = wng.get_gloss_by_sk(sk)
	dump_sense(a_sense)
        t.stop().log('Profiling select by sensekey')

        # Profiling loading
        t.start()
	wng = WordNetGlossTag.get_default()
	print wng.search_by_id('a00002527')
	gloss = wng.get_gloss_by_id('a00002527')
	dump_sense(gloss)
        t.stop().log('Test search gloss')

        # Profiling loading again
        t.start()
	wng = WordNetGlossTag.get_default()
	print wng.search_by_id('a00002527')
	gloss = wng.get_gloss_by_id('a00002527')
	dump_sense(gloss)
        t.stop().log('Test search gloss again')


        # Profiling expand the word table
        t.start()
        test_expand()
        t.stop()
        t.log('Expanding [table]')

        # The application should run faster from the second time
        t.start()
        test_expand()
        t.stop().log('Expanding [table] again ...')
 
        pass

def test_expand():
	wng = WordNetGlossTag.get_default()
	word = 'table'
	print ("Retrieving candidates for the word %s" % word)
	candidates = get_sense_candidates(wng, 'table')
	if candidates:
		print("Candidate count: %s" % len(candidates))
		for candidate in candidates:
                        continue
			print "-" * 80
			print str(candidate.sense)
			print "-" * 80
			print candidate.tokens
	pass
	
def dump_sense(a_sense, show_tagged_only=True):
	if a_sense:
		print a_sense
		for token in a_sense.tokens:
			if not show_tagged_only or token.sk:
				print ('\t' + str(token))

def test_wordnetgloss():
	wng = WordNetGlossTag.get_default()
	print wng.search_by_id('a00002527')
	gloss = wng.get_gloss_by_id('a00002527')
	dump_sense(gloss)
	#
	print("-" * 80)
	#
	sk = 'side%1:15:01::'
	file_loc = wng.search_by_sk(sk)
	sid = wng.get_senseinfo_by_sk(sk).get_full_sid()
	print ("Looking at %s - File loc: %s - SID: %s" % (sk,file_loc, sid))
	a_sense = wng.get_gloss_by_sk(sk)
	dump_sense(a_sense)
	#
	print('-' * 80)
	# 
	senses = wng.get_all_senses('side')
	for sense in senses:
		print sense
	pass	

if __name__ == "__main__":
	main()
