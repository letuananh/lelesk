#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import lxml
from lxml import etree
import xml.etree.ElementTree as ET
from le_utile import *
from collections import namedtuple
from bs4 import BeautifulSoup

TokenInfo = namedtuple("TokenInfo", ['text', 'sk'])

SEMCOR_ROOT=os.path.expanduser('~/semcor/')
DATA_DIR_1=os.path.join(SEMCOR_ROOT, 'brown1', 'tagfiles')
DATA_DIR_2=os.path.join(SEMCOR_ROOT, 'brown2', 'tagfiles')
DATA_DIR_V=os.path.join(SEMCOR_ROOT, 'brownv', 'tagfiles')
DATA_DIRS = [ DATA_DIR_1, DATA_DIR_2, DATA_DIR_V ]
XML_DIR = os.path.expanduser('./data/')
SEMCOR_TXT = os.path.expanduser('./semcor_wn30.txt')

def fix_malformed_xml_file(file_name, postfix='.xml'):
	print('Fixing the file: %s' %file_name)
	soup = BeautifulSoup(open(file_name).read())
	open(file_name+postfix, 'w').write(soup.prettify())

def convert_file(file_name, semcor_txt):
	print('Loading %s' %file_name)
	#root = ET.parse(file_name).getroot()

	tree = etree.iterparse(file_name)
	for event, element in tree:
		if event == 'end' and element.tag == 's':
			# print("Found a sentence. Length = %s" % len(element))
			tokens = []
			for token in element:
				if token.tag == 'wf':
					lemma = StringTool.strip(token.get('lemma'))
					lexsn = StringTool.strip(token.get('lexsn'))
					sk = lemma + '%' + lexsn if lemma and lexsn else ''
					sk = StringTool.strip(sk.replace('\t', ' ').replace('|', ' '))
					text = StringTool.strip(token.text.replace('\t', ' ').replace('|', ' '))
					tokens.append(TokenInfo(text, sk))
			element.clear()
			
			#sentence_text = ' '.join([ x.text for x in tokens ])
			tokens_text = '\t'.join([ x.text + '|' + x.sk for x in tokens])
			semcor_txt.write(tokens_text + '\n')
			#print(sentence_text)
			#for token in tokens:
			#	if token.text and token.sk:
					#semcor_txt.write('%s\t%s\t%s\n' % (token.text, token.sk, sentence_text))
	
				
def main():
	print("Semcor to Le's Lesk test format")
	
	t = Timer()
	c = Counter()
	
	#fix_data()
	
	semcor_txt = open(SEMCOR_TXT, 'w')
	
	all_files = [ os.path.join(XML_DIR, x) for x in os.listdir(XML_DIR) if os.path.isfile(os.path.join(XML_DIR, x)) ]
	for file_name in all_files:
		convert_file(file_name, semcor_txt)
	
	semcor_txt.flush()
	semcor_txt.close()
		
def fix_data():
	for data_dir in DATA_DIRS:
		all_files = [ os.path.join(data_dir, x) for x in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, x)) ]
		for a_file in all_files:
			fix_malformed_xml_file(a_file)
			c.count('file')
if __name__ == "__main__":
	main()
