Le's Lesk
======

An attempt to improve extended LESK using glosstag WordNet

#REQUIRED PACKAGES
----------------------

1. WordNet with Semantically Tagged glosses [STG]
  - Download URL: http://wordnetcode.princeton.edu/glosstag-files/WordNet-3.0-glosstag.tar.bz2
  - Homepage    : http://wordnet.princeton.edu/glosstag.shtml

2. Princeton WordNet 3.0 SQLite [WNSqlite]
  - Download URL : http://downloads.sourceforge.net/project/wnsql/wnsql3/sqlite/3.0/sqlite-30.db.zip
  - Home page    : http://wnsqlbuilder.sourceforge.net/

3. NLTK version 3.0
  - Home page    : http://nltk.org/

#INSTALLATION
----------------------
1. Install NLTK & download all data
2. create folder: ~/wordnet
3. Copy glosstag folder from WordNet STG to ~/wordnet/glosstag
4. Copy sqlite-30.db to ~/wordnet/sqlite-30.db

#USING LeLESK
----------------------
Execute 
```
python main.py
```

