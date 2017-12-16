Le's Lesk
======

An attempt to improve extended LESK using glosstag WordNet

# REQUIRED PACKAGES
----------------------

1. Princeton WordNet Gloss Corpus [WNG]
  - Download URL: http://wordnetcode.princeton.edu/glosstag-files/WordNet-3.0-glosstag.tar.bz2
  - Homepage    : http://wordnet.princeton.edu/glosstag.shtml

2. Princeton WordNet 3.0 SQLite [WNSqlite]
  - Download URL : http://downloads.sourceforge.net/project/wnsql/wnsql3/sqlite/3.0/sqlite-30.db.zip
  - Home page    : http://wnsqlbuilder.sourceforge.net/

3. NLTK version 3.0
  - Home page    : http://nltk.org/

# INSTALLATION
----------------------
1. Install NLTK & download all data
2. Install Yawlib & wordnet databases

# USING LeLESK
----------------------
To make a single WSD call, execute the following command:
```
python3 wsdtk.py -W YOUR_WORD -x YOUR_SENTENCE
```
For example, if you want to disambiguate the word "bank" in the sentence "I go to the bank to withdraw money", use:
```
python3 wsdtk.py -W "bank" -x "I go to the bank to withdraw money"
```

To run WSD in batch mode, execute the following command:
```
python3 wsdtk.py -b data/datafile.txt -o data/datafile_summary.txt > data/datafile_details.txt
```

# RESULT

On a decent PC with quadcore i7 and 4 GB RAM, it takes ~13 minutes to process annotated document "The Adventure of the Speckled Band" in NTU-MC. This is the result you should be able to get with the latest version:

| Information                         |    Stat |
|:------------------------------------|--------:|
| Sentences                           |     599 |
| Correct sense ranked the first      |    2544 |
| Correct sense ranked the 2nd or 3rd |    1328 |
| Wrong                               |   1325  |
| NoSense                             |    122  |
| TotalSense                          |    5319 |

Development test result (a subset of speckled.txt)

LELESK

| Information                         |    Instance | Classes |
|:------------------------------------|--------:|-----------:
| Correct sense ranked the first      |     190 |   139 |
| Correct sense ranked the 2nd or 3rd |     105 |   100 |
| Wrong                               |      96 |    83 |
| NoSense                             |       9 |     5 |
| TotalSense                          |     400 |   - |

MFS

| Information                         |    Instance | Classes |
|:------------------------------------|--------:|-----------:
| Correct sense ranked the first      |     211 |   147 |
| Correct sense ranked the 2nd or 3rd |      93 |    86 |
| Wrong                               |      87 |    73 |
| NoSense                             |       9 |     5 |
| TotalSense                          |     400 |  -  |



