-- SQLite DB for Gloss WordNet

DROP TABLE IF EXISTS meta;
DROP TABLE IF EXISTS synset;
DROP TABLE IF EXISTS term;
DROP TABLE IF EXISTS sensekey;
DROP TABLE IF EXISTS gloss_raw;
DROP TABLE IF EXISTS gloss;
DROP TABLE IF EXISTS glossitem;
DROP TABLE IF EXISTS sensetag;


CREATE TABLE IF NOT EXISTS meta  (
        title TEXT
       ,license TEXT
       ,WNVer TEXT
       ,url
       ,maintainer TEXT
);

INSERT INTO meta (license, title, url, WNVer, maintainer)
SELECT 'CC BY 4.0', 'Gloss WordNet SQLite 3.0', 'http://creativecommons.org/licenses/by/4.0/', '3.0', 'Le Tuan Anh <tuananh.ke@gmail.com>'
WHERE NOT EXISTS(SELECT 1 FROM meta WHERE WNVer = '3.0');

CREATE TABLE IF NOT EXISTS synset (
       id TEXT PRIMARY KEY -- Synset ID
       ,offset TEXT
       ,pos TEXT
);

CREATE TABLE IF NOT EXISTS term (
       sid TEXT
       ,term TEXT
       ,FOREIGN KEY (sid) REFERENCES synset(sid) 
);

CREATE TABLE IF NOT EXISTS sensekey (
       sid TEXT
       ,sensekey TEXT
       ,FOREIGN KEY (sid) REFERENCES synset(sid) 
);

CREATE TABLE IF NOT EXISTS gloss_raw (
       sid TEXT
       ,cat TEXT -- type orig/text (See Gloss WordNet DTD)
       ,gloss TEXT
       ,FOREIGN KEY (sid) REFERENCES synset(sid)
);

CREATE TABLE IF NOT EXISTS gloss (
       id INTEGER PRIMARY KEY -- Gloss ID
       ,origid TEXT -- Original ID
       ,sid TEXT    -- fkey to synsetid
       ,cat TEXT    -- category (def/ex)
       ,FOREIGN KEY (sid) REFERENCES synset(sid) 
);

CREATE TABLE IF NOT EXISTS glossitem (
       id INTEGER PRIMARY KEY -- item ID
       ,ord INTEGER -- item order
       ,gid INTEGER  -- fkey to gloss id
       ,tag TEXT
       ,lemma TEXT
       ,pos TEXT
       ,cat TEXT     -- category (type in original DTD)
       ,coll TEXT  -- collocation group ID
       ,rdf TEXT 
       ,sep TEXT
       ,text TEXT
       ,origid TEXT -- Original ID
       ,FOREIGN KEY (gid) REFERENCES gloss(gid) 
);

CREATE TABLE IF NOT EXISTS sensetag (
        id INTEGER PRIMARY KEY
       ,cat TEXT        -- Type (date/range/coll/etc.)
       ,tag TEXT        -- from glob tag
       ,glob TEXT       -- from glob tag
       ,glob_lemma TEXT -- from glob tag
       ,glob_id    TEXT -- from glob tag
       ,coll TEXT       
       ,sid TEXT        -- Synset ID
       ,gid INTEGER     -- ref to gloss id
       ,sk TEXT         -- sk from id tag
       ,origid TEXT     -- Original ID from id tag
       ,lemma TEXT      -- from id tag
       ,itemid INTEGER  -- ref to glossitem id
       ,FOREIGN KEY (itemid) REFERENCES glossitem(id) 
       ,FOREIGN KEY (gid) REFERENCES gloss(gid) 
);



CREATE INDEX IF NOT EXISTS synset_id ON synset (id);
CREATE INDEX IF NOT EXISTS synset_ofs ON synset (offset);
CREATE INDEX IF NOT EXISTS synset_pos ON synset (pos);

CREATE INDEX IF NOT EXISTS term_sid ON term (sid);
CREATE INDEX IF NOT EXISTS term_term ON term (term);

CREATE INDEX IF NOT EXISTS gloss_raw_sid ON gloss_raw (sid);

CREATE INDEX IF NOT EXISTS sensekey_sid ON sensekey (sid);
CREATE INDEX IF NOT EXISTS sensekey_sensekey ON sensekey (sensekey);

CREATE INDEX IF NOT EXISTS gloss_id ON gloss (id);
CREATE INDEX IF NOT EXISTS gloss_sid ON gloss (sid);

CREATE INDEX IF NOT EXISTS glossitem_id ON glossitem (id);
CREATE INDEX IF NOT EXISTS glossitem_gid ON glossitem (gid);

CREATE INDEX IF NOT EXISTS sensetag_id ON sensetag (id);
CREATE INDEX IF NOT EXISTS sensetag_itemid ON sensetag (itemid);
CREATE INDEX IF NOT EXISTS sensetag_gid ON sensetag (gid);

