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
import itertools
#-----------------------------------------------------------------------

class GWordNetSchema(Schema):
    def __init__(self, data_source=None):
        Schema.__init__(self, data_source)
        self.add_table('meta', 'title license WNVer url maintainer'.split())
        self.add_table('synset', 'id offset pos'.split())
        
        self.add_table('term', 'sid term'.split())
        self.add_table('gloss_raw', 'sid cat gloss'.split())
        self.add_table('sensekey', 'sid sensekey'.split())
        
        self.add_table('gloss', 'id origid sid cat'.split())
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
        ''' Helper method for storing a single synset
        '''
        self.insert_synsets([synset])
    
    def insert_synsets(self, synsets):
        ''' Store synsets with related information (sensekeys, terms, gloss, etc.)
        '''
        with Execution(self.schema) as exe:
            # synset;
            glossid_seed = itertools.count()
            glossitemid_seed = itertools.count()
            sensetagid_seed = itertools.count()
            for synset in synsets:
                exe.schema.synset.insert([synset.sid, synset.ofs, synset.pos])
                # term;
                for term in synset.terms:
                    exe.schema.term.insert([synset.sid, term.term])
                # sensekey;
                for sk in synset.keys:
                    exe.schema.sensekey.insert([synset.sid, sk.sensekey])
                # gloss_raw;
                for gloss_raw in synset.raw_glosses:
                    exe.schema.gloss_raw.insert([synset.sid, gloss_raw.cat, gloss_raw.gloss])
                # gloss; DB: id origid sid cat | OBJ: gid origid cat
                for gloss in synset.glosses:
                    gloss.gid = next(glossid_seed)
                    exe.schema.gloss.insert([gloss.gid, gloss.origid, synset.sid, gloss.cat])
                    # glossitem;
                    # OBJ | gloss, order, tag, lemma, pos, cat, coll, rdf, origid, sep, text
                    # DB  | id ord gid tag lemma pos cat coll rdf sep text origid
                    itemid_map = {}
                    for item in gloss.items:
                        item.itemid = next(glossitemid_seed)
                        itemid_map[item.origid] = item.itemid
                        exe.schema.glossitem.insert([item.itemid, item.order, gloss.gid, item.tag, item.lemma, item.pos
                        , item.cat, item.coll, item.rdf, item.sep, item.text, item.origid])
                    # sensetag;
                    for tag in gloss.tags:
                        # OBJ: tagid cat, tag, glob, glemma, gid, coll, origid, sid, sk, lemma
                        # DB: id cat tag glob glob_lemma glob_id coll sid gid sk origid lemma itemid
                        tag.tagid = next(sensetagid_seed)
                        exe.schema.sensetag.insert([tag.tagid, tag.cat, tag.tag, tag.glob, tag.glemma, 
                        tag.glob_id, tag.coll, '', gloss.gid, tag.sk, tag.origid, tag.lemma, itemid_map[tag.item.origid] ])
            exe.ds.commit()
        pass

    def results_to_synsets(self, results, exe):
        synsets = SynsetCollection()
        for result in results:
            ss = Synset(result.id, result.offset, result.pos)
            # term;
            terms = exe.schema.term.select(where='sid=?', values=[ss.sid])
            for term in terms:
                ss.add_term(term.term)
            # sensekey;
            sks = exe.schema.sensekey.select(where='sid=?', values=[ss.sid])
            for sk in sks:
                ss.add_sensekey(sk.sensekey)
            # gloss_raw | sid cat gloss
            rgs = exe.schema.gloss_raw.select(where='sid=?', values=[ss.sid])
            for rg in rgs:
                ss.add_raw_gloss(rg.cat, rg.gloss)
            # gloss; DB: id origid sid cat | OBJ: gid origid cat
            glosses = exe.schema.gloss.select(where='sid=?', values=[ss.sid])
            for gl in glosses:
                gloss = ss.add_gloss(gl.origid, gl.cat, gl.id)  
                # glossitem;
                # OBJ | gloss, order, tag, lemma, pos, cat, coll, rdf, origid, sep, text
                # DB  | id ord gid tag lemma pos cat coll rdf sep text origid
                glossitems = exe.schema.glossitem.select(where='gid=?', values=[gl.id])
                item_map = {}
                for gi in glossitems:
                    item = gloss.add_gloss_item(gi.tag, gi.lemma, gi.pos, gi.cat, gi.coll, gi.rdf, gi.origid, gi.sep, gi.text, gi.id)
                    item_map[item.itemid] = item
                # sensetag;
                # OBJ: tagid cat, tag, glob, glemma, gid, coll, origid, sid, sk, lemma
                # DB: id cat tag glob glob_lemma glob_id coll sid gid sk origid lemma itemid
                tags = exe.schema.sensetag.select(where='gid=?', values=[gl.id])
                for tag in tags:
                    gloss.tag_item(item_map[tag.itemid], tag.cat, tag.tag, tag.glob, tag.glob_lemma
                        , tag.glob_id, tag.coll, tag.origid, tag.sid, tag.sk, tag.lemma, tag.id)
            synsets.add(ss)
        return synsets

    def get_synset_by_id(self, synsetid):
        with Execution(self.schema) as exe:
            # synset;
            results = exe.schema.synset.select(where='id = ?', values=[synsetid])
            if results:
                return self.results_to_synsets(results, exe)
            else:
                return None
        pass

    def get_synset_by_sk(self, sensekey):
        with Execution(self.schema) as exe:
            # synset;
            results = exe.schema.synset.select(where='id IN (SELECT sid FROM sensekey where sensekey=?)', values=[sensekey])
            if results:
                return self.results_to_synsets(results, exe)
            else:
                return None
        pass
        
