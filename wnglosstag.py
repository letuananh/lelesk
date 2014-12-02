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

from lxml import etree
from collections import namedtuple
import os
import sys
from .le_utile import *
import pickle

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
		if self.sid_map.has_key(sid):
			return self.sid_map[sid]
		else:
			return None
	
	def by_sk(self, sk):
		if self.sk_map.has_key(sk):
			return self.sk_map[sk]
		else:
			return None
			
	def count(self):
		return len(self.synsets)

	# Merge with another Synset Collection
	def merge(self, another_scol):
		for synset in another_scol.synsets:
			self.add(synset)

class Synset:
	def __init__(self, sid, ofs, pos, gloss_orig='', gloss_text=''):
		self.sid = sid
		self.ofs = ofs
		self.pos = pos
		self.gloss_orig = gloss_orig
		self.gloss_text = gloss_text
		self.keys = []
		self.terms = []
		self.def_gloss = []
		self.examples = []
	
	def __str__(self):
		return "sid: %s | ofs: %s | pos: %s | orig: %s | text: %s | keys: %s | terms: %s | def_gloss: %s | examples: %s" % (self.sid, self.ofs, self.pos,
		self.gloss_orig, self.gloss_text, self.keys, self.terms, self.def_gloss, self.examples)
	def add_gloss_token(self, tid, lemma, pos, tag, text='', sk=''):
		gt = GlossToken(self, tid, lemma, pos, tag, text, sk)
		self.def_gloss.append(gt)
		return gt
		
	def add_example(self):
		ex = Example(self)
		self.examples.append(ex)
		return ex

class GlossToken:
	def __init__(self, synset, tid, lemma, pos, tag, text='', sk=''):
		self.synset = synset
		self.tid = tid
		self.lemma = lemma
		self.pos = pos
		self.tag = tag
		self.text=text
		self.sk = sk
		pass
	
	def __repr__(self):
		return str(self)
		
	def __str__(self):
		return "(id:%s|sk=%s [%s|txt=%s] tag:%s)" % (self.tid, self.sk, self.lemma, self.text, self.tag)

class Example:
	def __init__(self, synset):
		self.synset = synset
		self.tokens = []
		pass
		
	def add_token(self, eid, lemma, tag, text='', sk=''):
		tk = ExampleToken(self.synset, eid, lemma, tag, text, sk)
		self.tokens.append(tk)
		return tk
	
	def __repr__(self):
		return str(self)
		
	def __str__(self):
		return str(self.tokens)
		
class ExampleToken:
	def __init__(self, synset, eid, lemma, tag, text='', sk=''):
		self.synset = synset
		self.eid = eid
		self.lemma = lemma
		self.tag = tag
		self.text = text
		self.sk = sk
	def __repr__(self):
		return str(self)
	def __str__(self):
		return "(id:%s|sk=%s [%s|txt=%s] tag:%s)" % (self.eid, self.sk, self.lemma, self.text, self.tag)

TaggedWord = namedtuple('TaggedWord', ['text', 'sk'])
		
class WNGlossTag:

	@staticmethod
	def element_to_Synset(element, memory_save=True):
		synset = Synset(element.get('id'),element.get('ofs'),element.get('pos')) if not memory_save else Synset(element.get('id'), '', '')
		for child in element:
			if child.tag == 'terms':
				for grandchild in child:
					if grandchild.tag == 'term':
						synset.terms.append(StringTool.strip(grandchild.text))
			elif child.tag == 'keys':
				for grandchild in child:
					if grandchild.tag == 'sk':
						synset.keys.append(StringTool.strip(grandchild.text))
			elif child.tag == 'gloss' and child.get('desc') == 'orig' and not memory_save:
				if child[0].tag == 'orig':
					synset.gloss_orig = StringTool.strip(child[0].text)
			elif child.tag == 'gloss' and child.get('desc') == 'text' and not memory_save:
				if child[0].tag == 'text':
					synset.gloss_text = StringTool.strip(child[0].text)
			elif child.tag == 'gloss' and child.get('desc') == 'wsd':
				for grandchild in child:
					if grandchild.tag == 'def':
					#	if synset.sid == 'r00104099':
					#		etree.dump(element)
						WNGlossTag.rip_def_gloss(grandchild, synset, memory_save)
					elif grandchild.tag == 'ex' and len(grandchild) > 0:
						# flatten & rip all wf
						example_obj = synset.add_example()
						WNGlossTag.rip_wf_elem(grandchild, example_obj)
						# end each example token
		#print("A synset")
		# print len(element)
		#print ','.join([ '%s (%s)' % (x.tag, ','.join([y.tag for y in x])) for x in element ])
		return synset

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
				synset = WNGlossTag.element_to_Synset(element, memory_save)
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
				synset = WNGlossTag.element_to_Synset(element, memory_save)
				simplified_synset = Synset(synset.sid, '', '')
				simplified_synset.keys.extend(synset.keys)
				simplified_synset.terms.extend(synset.terms)
				for token in synset.def_gloss:
					simplified_synset.def_gloss.append(TaggedWord(token.text, token.sk))
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

	@staticmethod
	def rip_wf_elem(rootnode, example_obj):
		# add examples
		for token_elem in rootnode:
			if token_elem.tag == 'wf':
				tk = example_obj.add_token(token_elem.get('id'),token_elem.get('lemma'),token_elem.get('tag'))
				# Add gloss def
				if len(token_elem) > 1 and token_elem[0].tag == 'id':
					tk.sk = token_elem[0].get('sk')
					if token_elem[0].text:
						tk.text = StringTool.strip(token_elem[0].text)
					else:
						tk.text = StringTool.strip(token_elem[0].get('lemma'))
				else:
					tk.text = StringTool.strip(token_elem.text)
			elif token_elem.tag == 'qf':
				# trip children nodes
				WNGlossTag.rip_wf_elem(token_elem, example_obj)

	@staticmethod
	def build_lelesk_data(root=os.path.expanduser('~/wordnet/glosstag/merged'), verbose=False, memory_save=True):
		t = Timer()
		all_synsets = SynsetCollection()

		t.start()
		file_name = os.path.join(root, 'adj.xml')
		synsets = WNGlossTag.extract_for_lesk(file_name, synsets=all_synsets, memory_save=memory_save)
		if verbose: t.end("Found %s synsets in file [%s]" % (synsets.count(), file_name))

		t.start()
		file_name = os.path.join(root, 'adv.xml')
		synsets = WNGlossTag.extract_for_lesk(file_name, synsets=all_synsets, memory_save=memory_save)
		if verbose: t.end("Found %s synsets in file [%s]" % (synsets.count(), file_name))

		t.start()
		file_name = os.path.join(root, 'verb.xml')
		synsets = WNGlossTag.extract_for_lesk(file_name, synsets=all_synsets, memory_save=memory_save)
		if verbose: t.end("Found %s synsets in file [%s]" % (synsets.count(), file_name))
		
		t.start()
		file_name = os.path.join(root, 'noun.xml')
		synsets = WNGlossTag.extract_for_lesk(file_name, synsets=all_synsets, memory_save=memory_save)
		if verbose: t.end("Found %s synsets in file [%s]" % (synsets.count(), file_name))
		
		return all_synsets

	@staticmethod
	def read_all_glosstag(root=os.path.expanduser('~/wordnet/glosstag/merged'), verbose=False, memory_save=True):
		t = Timer()
		all_synsets = SynsetCollection()

		t.start()
		file_name = os.path.join(root, 'adj.xml')
		synsets = WNGlossTag.read_xml_data(file_name, synsets=all_synsets, memory_save=memory_save)
		if verbose: t.end("Found %s synsets in file [%s]" % (synsets.count(), file_name))

		t.start()
		file_name = os.path.join(root, 'adv.xml')
		synsets = WNGlossTag.read_xml_data(file_name, synsets=all_synsets, memory_save=memory_save)
		if verbose: t.end("Found %s synsets in file [%s]" % (synsets.count(), file_name))

		t.start()
		file_name = os.path.join(root, 'verb.xml')
		synsets = WNGlossTag.read_xml_data(file_name, synsets=all_synsets, memory_save=memory_save)
		if verbose: t.end("Found %s synsets in file [%s]" % (synsets.count(), file_name))
		
		t.start()
		file_name = os.path.join(root, 'noun.xml')
		synsets = WNGlossTag.read_xml_data(file_name, synsets=all_synsets, memory_save=memory_save)
		if verbose: t.end("Found %s synsets in file [%s]" % (synsets.count(), file_name))
		
		return all_synsets

# Demo
def main():
	print ("WordNet glosstag cache demo")
	rootfolder = os.path.expanduser('~/wordnet/glosstag/merged')
	# all_synsets = WNGlossTag.read_all_glosstag(rootfolder, verbose=True, memory_save=True)
	all_synsets = WNGlossTag.build_lelesk_data(rootfolder, verbose=True, memory_save=True)
	print("Total synsets: %s" % all_synsets.count())
	
	if all_synsets.by_sid('r00003483'):
		synset = all_synsets.by_sid('r00003483')
		print(synset.def_gloss)
	
	print ('-' * 80)
	sk = 'at_bottom%4:02:00::'
	if all_synsets.by_sk(sk):
		print(unicode(all_synsets.by_sk(sk)).encode('UTF8'))
	
	# Final gloss
	print ('-'*80)
	ss = all_synsets.by_sid('r00003483')
	if ss:
		main_gloss = []
		to_be_expanded = []
		for token in ss.def_gloss:
			main_gloss.append(token.text)
			if token.sk:
				to_be_expanded.append(token.sk)
		print("Main gloss   : %s" % (main_gloss,))
		print("To be expaned: %s" % (to_be_expanded,))
		
	
	t = Timer()
	t.start('Storing data to file...')
	pickle.dump(all_synsets, open('lelesk.model.dat', 'wb'))
	t.end('stored into file')
	
	# clear memory
	all_synsets = None
	
	t.start('start to load again')
	all_ss = pickle.load(open('lelesk.model.dat', 'rb'))
	t.end('Done!')
	print("Loaded %s synsets from file" % (len(all_ss.synsets),))
	# [TODO] Using pickle doesn't help at all, I'll take a look at this problem later
	raw_input("Press any key to continue ...")
		
if __name__ == "__main__":
	main()
