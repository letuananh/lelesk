Le's Lesk
======

An attempt to improve extended LESK using glosstag WordNet

#REQUIRED PACKAGES
----------------------

1. Princeton WordNet Gloss Corpus [WNG]
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
To run WSD on semcor test data (annotated with WordNet 3.0), execute the following command:
```
python main.py semcor semcor_wn30.txt > semcor_wn30.txt.output.txt
```
Or run the prepared shell script:
```
bash test.sh
```

#RESULT

On a decent PC with quadcore i7 and 4 GB RAM, it takes ~30 mins to process the whole Semcor test data. This is the result you should be able to get with the latest version:

| Information                  |    Stat |
|:-----------------------------|--------:|
| Sentence count               |  37,176 |
| Words (Lemmatized wrongly)   |  60,458 |
| Words (No sense found)       |  79,329 |
| Word (Lemmatized correctly)  | 112,226 |
| Word (total)                 | 252,013 |
| Correct sense found in top 3 |  65,928 |
| Tagged with correct sense    |  32,967 |
| Accuracy                     |  29.37% |
| Accurary (top 3)             |  58.74% |


