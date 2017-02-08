-- DROP TABLE IF EXISTS tokens;
-- DROP TABLE IF EXISTS synset;
-- DROP TABLE IF EXISTS sensekey;
-- DROP TABLE IF EXISTS term;

-- synset: synsetid offset pos synsetid_wn30 freq
CREATE TABLE IF NOT EXISTS synset  (
   synsetid TEXT
   ,offset  TEXT
   ,pos     TEXT
   ,synsetid_gwn TEXT
   ,freq    TEXT
);

-- sensekey: synsetid sensekey
CREATE TABLE IF NOT EXISTS sensekey (
	synsetid TEXT
	,sensekey TEXT
);

-- term: synsetid term
CREATE TABLE IF NOT EXISTS term (
	synsetid TEXT
	,term TEXT
);

-- tokens: synsetid token
CREATE TABLE IF NOT EXISTS tokens  (
    synsetid TEXT
   ,token    TEXT
);



CREATE INDEX IF NOT EXISTS tokens_synsetid ON tokens (synsetid);

CREATE INDEX IF NOT EXISTS synset_synsetid ON synset (synsetid);
CREATE INDEX IF NOT EXISTS synset_offset ON synset (offset);
CREATE INDEX IF NOT EXISTS synset_synsetid_gwn ON synset (synsetid_gwn);

CREATE INDEX IF NOT EXISTS sensekey_sensekey ON sensekey (sensekey);
CREATE INDEX IF NOT EXISTS sensekey_synsetid ON sensekey (synsetid);

CREATE INDEX IF NOT EXISTS term_synsetid ON term (synsetid);
CREATE INDEX IF NOT EXISTS term_term ON term (term);

