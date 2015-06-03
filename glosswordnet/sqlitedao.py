#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Gloss WordNet SQLite Data Access Object - Access Gloss WordNet in SQLite format
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

#-----------------------------------------------------------------------

from glosswordnet.models import SynsetCollection, Synset, GlossRaw, SenseKey, Term, Gloss, GlossGroup, SenseTag, GlossItem
from puchikarui import Schema, Execution#, DataSource, Table
#-----------------------------------------------------------------------

class GWordNetSchema(Schema):
    def __init__(self, data_source=None):
        Schema.__init__(self, data_source)
        self.add_table('meta', 'title license WNVer url maintainer'.split())
        self.add_table('synset', 'id offset pos'.split())
        self.add_table('gloss', 'id origid sid'.split())
        self.add_table('glossitem', 'id ord gid tag lemma pos cat coll rdf sep text origid'.split())
        self.add_table('sensetag', 'id cat tag glob glob_lemma glob_id coll sid gid sk origid lemma itemid'.split())

#-----------------------------------------------------------------------

class SQLiteGWordNet:
    def __init__(self, db_path, verbose=False):
        self.db_path = db_path
        self.schema = GWordNetSchema(self.db_path)
        self.verbose = verbose
        
    def setup(self, script_file):
        with Execution(self.schema) as exe:
            if self.verbose:
                print('Creating database file ...')
            exe.ds.executefile(script_file)
            try:
                for meta in exe.schema.meta.select():
                    print(meta)
            except Exception as e:
                print("Error while setting up database ... e = %s" % e)
        pass # end setup()
    
    def insert_synset(self, synset):
        self.insert_synsets([synset])
    
    def insert_synsets(self, synsets):
        with Execution(self.schema) as exe:
            for synset in synsets:
                exe.schema.synset.insert([synset.sid, synset.ofs, synset.pos])
            exe.ds.commit()
        pass
        
