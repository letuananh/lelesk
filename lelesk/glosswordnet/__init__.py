# -*- coding: utf-8 -*-

'''
Gloss WordNet XML Data Access Object - Access Gloss WordNet in either 
XML or SQLite format
Latest version can be found at https://github.com/letuananh/lelesk

Usage:

from glosswordnet import XMLGWordNet
xmlwn = XMLGWordNet()
xmlwn.read(xml_file)    
for ss in xmlwn.synsets:
    print(ss)

or 
from glosswordnet import SQLiteGWordNet
[TODO] WIP

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
from .models import SynsetCollection, Synset, GlossRaw, SenseKey, Term, Gloss, GlossGroup, SenseTag, GlossItem
from .xmldao import XMLGWordNet
from .sqlitedao import SQLiteGWordNet



