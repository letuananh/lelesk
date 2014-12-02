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
from .le_utile import *
from .wnglosstag import *
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
		if file_path not in XMLCache.cache:
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
						print(('Caching file: %s' % fullpath))
				# print filename
				fcount += 1
		print(("Found %s XML files" % fcount))

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

#SenseInfo = namedtuple('SenseInfo', ['pos', 'synsetid', 'sensekey'])

class SenseInfo:
	def __init__(self, pos, synsetid, sensekey, wordid='', gloss=''):
		self.pos = pos
		self.sid = synsetid
		self.sk = sensekey
		self.wordid = wordid
		self.gloss = gloss
	
	def get_full_sid(self):
		return self.pos + str(self.sid)[1:]
		
	def __repr__(self):
		return str(self)
		
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

class WordNetSQL:
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
		if sk in WordNetSQL.sk_cache:
			return WordNetSQL.sk_cache[sk]
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
		WordNetSQL.sk_cache[sk] = sid
		return sid
	def cache_all_sensekey(self):
		conn = sqlite3.connect(WORDNET_30_PATH)
		c = conn.cursor()
		result = c.execute("""SELECT pos, synsetid, sensekey FROM wordsXsensesXsynsets""").fetchall()
		for (pos, synid, sk) in result:
			sif = SenseInfo(pos, synid, sk)
			WordNetSQL.sk_cache[sk] = sif
		conn.close()
	
	hypehypo_cache=dict()	
	def get_hypehypo(self, sid):
		if sid in WordNetSQL.hypehypo_cache:
			return WordNetSQL.hypehypo_cache[sid]
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
		WordNetSQL.hypehypo_cache[sid] = senses
		return senses
	def cache_all_hypehypo(self):
		query = '''SELECT linkid, ssynsetid, dpos, dsynsetid, dsensekey, dwordid
					FROM sensesXsemlinksXsenses 
					WHERE linkid in (1,2,3,4, 11,12,13,14,15,16,40,50,81);'''
		conn = sqlite3.connect(WORDNET_30_PATH)
		c = conn.cursor()
		result = c.execute(query).fetchall()
		for (linkid, ssynsetid, dpos, dsynsetid, dsensekey, dwordid) in result:
			if ssynsetid not in WordNetSQL.hypehypo_cache:
					 WordNetSQL.hypehypo_cache[ssynsetid] = []
			WordNetSQL.hypehypo_cache[ssynsetid].append(SenseInfo(dpos, dsynsetid, dsensekey, dwordid))
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
				if wordid in WordNetSQL.word_cache:
					lemmas.append(WordNetSQL.word_cache[wordid])
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
					WordNetSQL.word_cache[wordid] = lemma
					lemmas.append(lemma)
				conn.close()
			return lemmas
	def cache_all_words(self):
		query = '''SELECT wordid, lemma FROM words'''
		conn = sqlite3.connect(WORDNET_30_PATH)
		c = conn.cursor()
		result = c.execute(query).fetchall()
		for (wordid, lemma) in result:
				WordNetSQL.word_cache[wordid] = lemma
		conn.close()

	sense_map_cache=None
	def all_senses(self):
		if WordNetSQL.sense_map_cache:
			return WordNetSQL.sense_map_cache
		_query = """SELECT lemma, pos, synsetid, sensekey, definition 
								FROM wordsXsensesXsynsets;"""
		conn = self.get_conn()
		c = conn.cursor()
		result = c.execute(_query).fetchall()
		# Build lemma map
		lemma_map = {}
		senses = []
		for (lemma, pos, synsetid, sensekey, definition) in result:
			# ss_type
			# One character code indicating the synset type:
			# n NOUN
			# v VERB
			# a ADJECTIVE
			# s ADJECTIVE SATELLITE
			# r ADVERB
			if pos == 's' or pos == 'r':
				pos = 'a'
			sinfo = SenseInfo(pos, synsetid, sensekey, '', definition)
			# add to map
			if lemma not in lemma_map:
				lemma_map[lemma] = []
			lemma_map[lemma].append(sinfo)
		# close connection & return results
		conn.close()
		WordNetSQL.sense_map_cache=lemma_map
		return lemma_map

	def get_conn(self):
		conn = sqlite3.connect(WORDNET_30_PATH)
		return conn

	lemma_list_cache = dict()
	def search_senses(self, lemma_list, pos=None, a_conn=None):
		if len(lemma_list) == 0:
			return list()
		
		CACHE_JOIN_TOKEN='|\t'*12
		cache_key=CACHE_JOIN_TOKEN.join(lemma_list)
		# caching method
		if cache_key in WordNetSQL.lemma_list_cache:
			return WordNetSQL.lemma_list_cache[cache_key]
		
		# Build query
		_query = """SELECT pos, synsetid, sensekey, definition 
								FROM wordsXsensesXsynsets
								WHERE (%s) """ % 'or '.join(["lemma=?"] * len(lemma_list))
		_args = list(lemma_list)
		if pos:
			_query += " and pos = ?";
			_args.append(pos)
		
		# Query
		if a_conn:
			conn = a_conn
		else:
			conn = sqlite3.connect(WORDNET_30_PATH)
		c = conn.cursor()
		result = c.execute(_query, _args).fetchall()

		# Build results
		senses = []
		for (pos, synsetid, sensekey, definition) in result:
			senses.append(SenseInfo(pos, synsetid, sensekey, '', definition))
		if not a_conn:
			conn.close()
		
		# store to cache
		WordNetSQL.lemma_list_cache[cache_key] = senses
		return senses
	
	sense_cache = dict()
	def get_all_senses(self, lemma, pos=None):
		if lemma in WordNetSQL.sense_cache:
			return WordNetSQL.sense_cache[lemma]
		conn = sqlite3.connect(WORDNET_30_PATH)
		c = conn.cursor()
		if pos:
			result = c.execute("""SELECT pos, synsetid, sensekey, definition 
								FROM wordsXsensesXsynsets
								WHERE lemma = ? and pos = ?;""", (lemma, pos)).fetchall()
		else:
			result = c.execute("""SELECT pos, synsetid, sensekey, definition 
								FROM wordsXsensesXsynsets
								WHERE lemma = ?;""", (lemma,)).fetchall()
		senses = []
		for (pos, synsetid, sensekey, definition) in result:
			senses.append(SenseInfo(pos, synsetid, sensekey, '', definition))
		conn.close()
		WordNetSQL.sense_cache[lemma] = senses
		return senses
		
	def cache_all_sense_by_lemma(self):
		conn = sqlite3.connect(WORDNET_30_PATH)
		c = conn.cursor()
		result = c.execute("""SELECT lemma, pos, synsetid, sensekey, definition FROM wordsXsensesXsynsets;""").fetchall()

		for (lemma, pos, synsetid, sensekey, definition) in result:
			if lemma not in WordNetSQL.sense_cache:
				WordNetSQL.sense_cache[lemma] = []
			WordNetSQL.sense_cache[lemma].append(SenseInfo(pos, synsetid, sensekey, '', definition))
		conn.close()

	def get_gloss_by_sk(self, sk):
		sid = self.get_senseinfo_by_sk(sk).get_full_sid()
		return self.get_gloss_by_id(sid)
	
	gloss_cache = dict()
	def get_gloss_by_id(self, sid):
		if sid in WordNetSQL.gloss_cache:
			return WordNetSQL.gloss_cache[sid]
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
			WordNetSQL.gloss_cache[sid] = a_sense
			return a_sense
		else:
			WordNetSQL.gloss_cache[sid] = None
			return None
		pass
			
	# Search a synset by ID
	def search_by_id(self, synset_id):
		#print 'searching %s' % synset_id
		if synset_id in self.sid_index:
			return self.sid_index[synset_id]
		else:
			return None
	
	# Search a synset by sensekey
	def search_by_sk(self, wnsk):
		if wnsk in self.sk_index:
			return self.sk_index[wnsk]
		else:
			return 'N/A'
	
	@staticmethod
	def get_default(auto_cache=True):
		wnsql = WordNetSQL(WORDNET_30_PATH, WORDNET_30_GLOSSTAG_PATH)
		# Cache everything into memory if needed
		if auto_cache:
			wnsql.cache_all_words()
			wnsql.cache_all_sense_by_lemma()
			wnsql.cache_all_hypehypo()
			wnsql.cache_all_sensekey()
		return wnsql
		
'''
Given a sentence as a raw text string, perform tokenization, lemmatization
'''
def prepare_data(res, sentence_text):
	# Tokenization
	tokens = nltk.word_tokenize(sentence_text)
	# Lemmatization
	tokens = [ res.lemmatize(x) for x in tokens] + tokens
	return tokens

class GlossTokens:
	def __init__(self):
		self.tokens = []
		self.sk = []

def get_gloss_token(res, sk):
	tokens = []
	ss_gloss = res.sscol.by_sk(sk)
	
	gt = GlossTokens()
	senseinfo = res.wnsql.get_senseinfo_by_sk(sk)
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

def get_sense_candidates(res, word):
	lemmatized_word = res.lemmatize(word)
	senses = res.wnsql.get_all_senses(lemmatized_word)
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
		synset_gloss = res.sscol.by_sk(sk)
		if not synset_gloss:
			continue
		candidate.tokens.extend([ x.text for x in synset_gloss.def_gloss ])
		for child_token in synset_gloss.def_gloss:
			# t2.start() 
			# Find gloss of each token in the gloss of the current sense
			if res.sscol.by_sk(child_token.sk):
				child_gloss = res.sscol.by_sk(child_token.sk)
				candidate.tokens.extend([ x.text for x in child_gloss.def_gloss ])
			# t2.stop().log('get child gloss')
			# extend hypernyms & hyponyms of each token in the gloss
			# of the current sense
			senseinfo = res.wnsql.get_senseinfo_by_sk(child_token.sk)
			if senseinfo:
				# t2.start()
				more_tokens = res.wnsql.get_hypehypo_text(senseinfo.sid)
				# print("Extending: %s" % more_tokens)
				candidate.tokens += more_tokens # Hype & hypo of tagged tokens
				#t2.stop().log('Finished hypehypo')
		#print "-" * 20
		candidate.tokens = [_f for _f in candidate.tokens if _f]
		#print "Final: %s" % candidate.tokens
		candidates.append(candidate)
		# t.stop().log('Finished build a candidate')
	return candidates
	pass

class WSDResources:
	
	__singleton_instance = None
	wnsql=None
	wnl=None
	
	def __init__(self, lightweight=False):
		# self.sscol = WNGlossTag.read_all_glosstag(os.path.join(WORDNET_30_GLOSSTAG_PATH, 'merged'), verbose=True)
		if not lightweight:
			self.sscol = WNGlossTag.build_lelesk_data(os.path.join(WORDNET_30_GLOSSTAG_PATH, 'merged'), verbose=False)
		self.wnsql = WordNetSQL.get_default()
		self.wnl = WordNetLemmatizer()
		self.lemmatize_cache = dict()

	def lemmatize(self, word):
		if word not in self.lemmatize_cache:
			self.lemmatize_cache[word] = self.wnl.lemmatize(word)
		return self.lemmatize_cache[word]

	@staticmethod
	def singleton(lightweight=False):
		if WSDResources.__singleton_instance == None:
			WSDResources.__singleton_instance = WSDResources(lightweight)
		return WSDResources.__singleton_instance
	
candidates_cache=dict()	
''' 
Perform Word-sense disambiguation with extended simplified LESK and 
annotated WordNet 3.0
'''
def lelesk_wsd(word, context, res=None, verbose=False):
	# Preparation: Load all resources (SQLite cache, WNGlossTag, etc.)
	if res==None:
		res = WSDResources.singleton()
	#1. Retrieve candidates for the given word
	if word not in candidates_cache:
		candidates_cache[word] = get_sense_candidates(res, word)
	candidates = candidates_cache[word]
	#2. Calculate overlap between the context and each given word
	context_set = set(context)
	if verbose: print(context_set)
	scores = []
	for candidate in candidates:
		candidate_set = set([ res.lemmatize(x) for x in candidate.tokens] + candidate.tokens)
		if verbose: print(candidate_set)
		score = len(context_set.intersection(candidate_set))
		scores.append([candidate, score])
	scores.sort(key=itemgetter(1))
	scores.reverse()
	return scores
	
#-----------------------------------------------------------------------
# Main function
#-----------------------------------------------------------------------
def main():	
	testset = { 'test' : test_wsd, 'optimize' : optimize, 'candidates' : test_candidates, 'batch' : batch_wsd, 'semcor' : test_semcor }
	if len(sys.argv) < 2 or sys.argv[1] not in list(testset.keys()):
		print_usage()
	elif len(sys.argv) == 3 and sys.argv[1] == 'candidates':
		testset[sys.argv[1]](sys.argv[2])
	elif len(sys.argv) == 3 and sys.argv[1] == 'batch':
		testset[sys.argv[1]](sys.argv[2])
	elif len(sys.argv) == 3 and sys.argv[1] == 'semcor':
		testset[sys.argv[1]](sys.argv[2])
	else:
		testset[sys.argv[1]]()
	pass

def print_usage():
	print(('''Usage:
	%s: Show this usage
	%s test: Run bank test
	%s candidates your_chosen_word: Find candidates for a given word
	%s batch path_to_your_file: Perform WSD on a batch file
	%s batch path_to_semcor_test_file: Perform WSD on Semcor (e.g. semcor_wn30.txt)
	''' % ((sys.argv[0],) * 5)))
	pass

Token = namedtuple('Token', ['text', 'sk'])
def test_semcor(file_name, verbose=True):
	t = Timer()
	total_timer = Timer()
	total_timer.start()
	lines = open(file_name).readlines()
	print(("Found %s sentences in %s" % (len(lines), file_name)))
	
	t.start('Loading needed resource ...')
	res = WSDResources.singleton()
	t.end('Needed resources have been loaded')
	
	print(('-' * 80))
	
	c = Counter()
	sentence_count = len(lines)
	for line in lines:
		c.count('sentence')
		#if c['sentence'] > 100:
		#	break
		parts = line.split('\t')
		if not parts:
			continue
		tokens = []
		for part in parts:
			if not part:
				continue
			tk = part.split('|')
			if not tk or len(tk) != 2:
				continue
			tokens.append(Token(tk[0], tk[1]))
		sentence_text = ' '.join([ x.text for x in tokens ])
		test_items = [ x for x in tokens if x.sk ]
		for test_item in test_items:
			c.count("Word (total)")
			word = test_item.text
			# sentence_text = parts[1].strip()
			# Perform WSD on given word & sentence
			t.start()
			context = prepare_data(res, sentence_text)
			if verbose:
				print(("WSD for the word: %s" % word))
				print(("Context         : %s" % sentence_text))
				print(("Context tokens  : %s" % set(context)))
				print(("Expected sense  : %s" % test_item.sk)) 
			scores = lelesk_wsd(word, context)
			if scores and len(scores) > 0:
				correct_word = False
				for score in scores:
					sid = score[0].sense.get_full_sid()
					sks = res.sscol.by_sid(sid).keys
					if test_item.sk in sks:
						correct_word = True
				if correct_word:
					c.count('Word (correct)')
				else:
					c.count('Word (wrong)')
			else:
				c.count('Word (no sense)')
			
			if verbose:
				print ("Top 3 scores")
			
			# Check top hit
			if len(scores) > 0:
				sid = scores[0][0].sense.get_full_sid()
				sks = res.sscol.by_sid(sid).keys
				if test_item.sk in sks:
					c.count('top1') 
			
			for score in scores[:3]:
				# score = [0] - synset, [1] - score in number
				sid = score[0].sense.get_full_sid()
				sks = res.sscol.by_sid(sid).keys
				if test_item.sk in sks:
					c.count('top3') 
				if verbose:
					print(("Sense: %s - Sensekey: %s- Score: %s - Definition: %s" % (sid, sks, score[1], score[0].sense.gloss)))
			t.end('Sentence (#%s/%s) | Analysed word ["%s"] on sentence: %s' % (c['sentence'], sentence_count, word, sentence_text))
			print(('-' * 80))
	jilog("Batch job finished")
	print(('-' * 80))
	c.summarise()
	total_timer.end("Total runtime")
	print('Done!')
	
	pass

def batch_wsd(file_loc):
	t = Timer()
	t.start("Reading file %s" % file_loc)
	lines = open(os.path.expanduser(file_loc)).readlines()
	t.end("File has been loaded")
	
	t.start('Loading needed resource ...')
	WSDResources.singleton()
	t.end('Needed resources have been loaded')
	
	print(('-' * 80))
		
	for line in lines:
		parts = line.split('\t')
		if parts and len(parts) == 2:
			word = parts[0].strip()
			sentence_text = parts[1].strip()
			# Perform WSD on given word & sentence
			t.start()
			context = prepare_data(res, sentence_text)
			print(("WSD for the word: %s" % word))
			print(("Context: %s" % sentence_text))
			print(("Context tokens: %s" % set(context)))
			scores = lelesk_wsd(word, context)
			print ("Top 3 scores")
			for score in scores[:3]:
				print(("Sense: %s - Score: %s - Definition: %s" % (score[0].sense.get_full_sid(), score[1], score[0].sense.gloss)))
			t.end('Analysed word ["%s"] on sentence: %s' % (word, sentence_text))
			print(('-' * 80))
	jilog("Batch job finished")
	print('Done!')

def test_wsd():
	word = 'bank'
	sentence_texts = ['I went to the bank to deposit money.', 'The river bank is full of dead fish.']
	t = Timer()
	t.start('Loading needed resource ...')
	WSDResources.singleton()
	t.end('Needed resources have been loaded')
	for sentence_text in sentence_texts:
		t.start()
		context = prepare_data(res, sentence_text)
		print(("WSD for the word: %s" % word))
		print(("Context: %s" % context))
		scores = lelesk_wsd(word, context)
		print ("Top 3 scores")
		for score in scores[:3]:
			print(("Sense: %s - Score: %s - Definition: %s" % (score[0].sense.get_full_sid(), score[1], score[0].sense.gloss)))
		t.end('Analysed sentence: %s' % sentence_text)

def optimize():
	t = Timer()

	# Load needed resources
	t.start('Started loading needed resources ...')
	res = WSDResources.singleton()
	t.end('Preload all needed resources')

	t.start()
	res.wnsql.cache_all_words()
	t.stop().log('Cache all words')

	t.start()
	res.wnsql.cache_all_sensekey()
	t.stop().log('Cache all sensekeys')

	t.start()
	res.wnsql.cache_all_hypehypo()
	t.stop().log('Cache all hypehypo')

	t.start()
	res.wnsql.cache_all_sense_by_lemma()
	t.stop().log('Cache all sense by lemma')

	# Profiling select senses from database
	t.start()
	senses = res.wnsql.get_all_senses('table')
	print(len(senses))
	t.stop().log('Test select all senses')

	# Profiling get by sk
	t.start()
	sk = 'side%1:15:01::'
	file_loc = res.wnsql.search_by_sk(sk)
	sid = res.wnsql.get_senseinfo_by_sk(sk).get_full_sid()
	print(("Looking at %s - File loc: %s - SID: %s" % (sk,file_loc, sid)))
	a_sense = res.wnsql.get_gloss_by_sk(sk)
	dump_sense(a_sense)
	t.stop().log('Profiling select by sensekey')

	# Profiling loading
	t.start()
	print(res.wnsql.search_by_id('a00002527'))
	gloss = res.wnsql.get_gloss_by_id('a00002527')
	dump_sense(gloss)
	t.stop().log('Test search gloss')

	# Profiling loading again
	t.start()
	print(res.wnsql.search_by_id('a00002527'))
	gloss = res.wnsql.get_gloss_by_id('a00002527')
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

def test_candidates(word):
	res = WSDResources.singleton()
	if not word:
		word = 'table'
	print(('Retrieving candidates for the word ["%s"]' % word))
	candidates = get_sense_candidates(res, word)
	if candidates:
		print(("Candidates count: %s" % len(candidates)))
		for candidate in candidates:
			print("-" * 80)
			print(str(candidate.sense))
			print("-" * 80)
			print(candidate.tokens)
	pass
	
def dump_sense(a_sense, show_tagged_only=True):
	if a_sense:
		print(a_sense)
		for token in a_sense.tokens:
			if not show_tagged_only or token.sk:
				print(('\t' + str(token)))

def test_wordnetgloss():
	wng = WordNetSQL.get_default()
	print(wng.search_by_id('a00002527'))
	gloss = wng.get_gloss_by_id('a00002527')
	dump_sense(gloss)
	#
	print(("-" * 80))
	#
	sk = 'side%1:15:01::'
	file_loc = wng.search_by_sk(sk)
	sid = wng.get_senseinfo_by_sk(sk).get_full_sid()
	print(("Looking at %s - File loc: %s - SID: %s" % (sk,file_loc, sid)))
	a_sense = wng.get_gloss_by_sk(sk)
	dump_sense(a_sense)
	#
	print(('-' * 80))
	# 
	senses = wng.get_all_senses('side')
	for sense in senses:
		print(sense)
	pass	

if __name__ == "__main__":
	main()
