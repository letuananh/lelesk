DROP TABLE IF EXISTS lelesktokens;

CREATE TABLE IF NOT EXISTS lelesktokens  (
        synsetid TEXT
       ,token    TEXT
);

CREATE INDEX IF NOT EXISTS lelesktokens_synsetid ON lelesktokens (synsetid);