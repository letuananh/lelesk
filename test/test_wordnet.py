#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
A tool for converting Gloss WordNet into SQLite
Latest version can be found at https://github.com/letuananh/lelesk

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

#-------------------------------------------------------------------
import os.path
import unittest
import lelesk.glosswordnet
from lelesk.glosswordnet import XMLGWordNet, SQLiteGWordNet
from lelesk.wordnetsql import WordNetNTUMC, WordNetSQL

WN_NTUMC_FILE     = os.path.abspath(os.path.expanduser('~/wordnet/wn-ntumc.db'))
WNSQL_FILE        = os.path.abspath(os.path.expanduser('~/wordnet/sqlite-30.db'))
TEST_GWN_XML_FILE = os.path.abspath(os.path.expanduser('./data/unittest/test.xml'))

class TestXMLGWordNet(unittest.TestCase):

    def test_upper(self):
        xmlwn = XMLGWordNet()
        xmlwn.read(TEST_GWN_XML_FILE)
        for ss in xmlwn.synsets[:5]:
            # print(ss)
            self.assertIsNotNone(ss)

class TestNTUMCWordNet(unittest.TestCase):
    
    def test_get_all_synsets(self):
        wn = WordNetNTUMC(WN_NTUMC_FILE)
        ss = wn.get_all_synsets()
        print("WordNet-NTUMC synset count: %s " % (len(ss),))
        self.assertTrue(len(ss) > 0)
        
class TestWordNetSQL(unittest.TestCase):
    
    def test_get_all_synsets(self):
        wn = WordNetSQL(WNSQL_FILE)
        ss = wn.get_all_synsets()
        print("WordNet 3.0 synset count: %s " % (len(ss),))
        self.assertTrue(len(ss) > 0)

if __name__ == '__main__':
    unittest.main()
