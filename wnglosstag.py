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
import os
import sys
from le_utile import *

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
		
class WNGlossTag:
	@staticmethod
	def read_xml_data(file_name, synsets=None):
		tree = etree.iterparse(file_name)
		c = Counter()
		if synsets == None:
			synsets = SynsetCollection()
		for event, element in tree:
			#print("%s, %4s, %s" % (event, element.tag, element.text))
			if event == 'end' and element.tag == 'synset':
				synset = Synset(element.get('id'),element.get('ofs'),element.get('pos'))
				for child in element:
					if child.tag == 'terms':
						for grandchild in child:
							if grandchild.tag == 'term':
								synset.terms.append(grandchild.text)
					elif child.tag == 'keys':
						for grandchild in child:
							if grandchild.tag == 'sk':
								synset.keys.append(grandchild.text)
					elif child.tag == 'gloss' and child.get('desc') == 'orig':
						if child[0].tag == 'orig':
							synset.gloss_orig = child[0].text
					elif child.tag == 'gloss' and child.get('desc') == 'text':
						if child[0].tag == 'text':
							synset.gloss_text = child[0].text
					elif child.tag == 'gloss' and child.get('desc') == 'wsd':
						for grandchild in child:
							if grandchild.tag == 'def':
								for token_elem in grandchild:
									if token_elem.tag == 'wf':
										# Add gloss def
										tk = synset.add_gloss_token(token_elem.get('id'), token_elem.get('lemma'),token_elem.get('pos'),token_elem.get('tag'))
										if len(token_elem) == 1 and token_elem[0].tag == 'id':
											tk.sk = token_elem[0].get('sk')
											tk.text = token_elem[0].text
										else:
											tk.text = token_elem.text
									if token_elem.tag == 'cf':
										tk = synset.add_gloss_token(token_elem.get('id'), token_elem.get('lemma'),token_elem.get('pos'),token_elem.get('tag'))
										if len(token_elem) == 1 and token_elem[0].tag == 'glob' and len(token_elem[0]) == 1 and token_elem[0][0].tag == 'id':
											tk.sk = token_elem[0][0].get('sk')
											tk.text = token_elem[0][0].get('lemma')
										else:
											tk.text = token_elem.text
								# end each def token
							elif grandchild.tag == 'ex' and len(grandchild) > 0:
								# flatten & rip all wf
								example_obj = synset.add_example()
								WNGlossTag.rip_wf_elem(grandchild, example_obj)
								# end each example token
				#print("A synset")
				# print len(element)
				#print ','.join([ '%s (%s)' % (x.tag, ','.join([y.tag for y in x])) for x in element ])
				element.clear()
				synsets.add(synset)
				# print("Synset: [%s]" % synset)
			# end if end-synset
			c.count(element.tag)
			#if c['synset'] > 4:
			#	break
			#element.clear()
		# print r
		# c.summarise()
		return synsets
		pass

	@staticmethod
	def rip_wf_elem(rootnode, example_obj):
		# add examples
		for token_elem in rootnode:
			if token_elem.tag == 'wf':
				tk = example_obj.add_token(token_elem.get('id'),token_elem.get('lemma'),token_elem.get('tag'))
				# Add gloss def
				if len(token_elem) == 1 and token_elem[0].tag == 'id':
					tk.sk = token_elem[0].get('sk')
					tk.text = token_elem[0].text
				else:
					tk.text = token_elem.text
			elif token_elem.tag == 'qf':
				# trip children nodes
				WNGlossTag.rip_wf_elem(token_elem, example_obj)

	@staticmethod
	def read_all_glosstag(root=os.path.expanduser('~/wordnet/glosstag/merged'), verbose=False):
		t = Timer()
		all_synsets = SynsetCollection()

		t.start()
		file_name = os.path.join(root, 'noun.xml')
		synsets = WNGlossTag.read_xml_data(file_name)
		all_synsets.merge(synsets)
		if verbose: t.end("Found %s synsets in file [%s]" % (synsets.count(), file_name))

		t.start()
		file_name = 'adj.xml'
		synsets = WNGlossTag.read_xml_data(file_name)
		all_synsets.merge(synsets)
		if verbose: t.end("Found %s synsets in file [%s]" % (synsets.count(), file_name))

		t.start()
		file_name = 'adv.xml'
		synsets = WNGlossTag.read_xml_data(file_name)
		all_synsets.merge(synsets)
		if verbose: t.end("Found %s synsets in file [%s]" % (synsets.count(), file_name))

		t.start()
		file_name = 'verb.xml'
		synsets = WNGlossTag.read_xml_data(file_name)
		all_synsets.merge(synsets)
		if verbose: t.end("Found %s synsets in file [%s]" % (synsets.count(), file_name))
		
		return all_synsets

# Demo
def main():
	print ("WordNet glosstag cache demo")
	rootfolder = os.path.expanduser('~/wordnet/glosstag/merged')
	all_synsets = WNGlossTag.read_all_glosstag(rootfolder, verbose=True)
	print("Total synsets: %s" % all_synsets.count())
	
	if all_synsets.by_sid('r00003483'):
		synset = all_synsets.by_sid('r00003483')
		print(synset.def_gloss)
		
	sk = 'at_bottom%4:02:00::'
	if all_synsets.by_sk(sk):
		print(unicode(all_synsets.by_sk(sk)).encode('UTF8'))
		
if __name__ == "__main__":
	main()
