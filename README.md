# Le's Lesk

A fast Python 3 Word-Sense Disambiguation package (WSD) using the extended LESK algorithm

## Install

`lelesk` is available on [PyPI](https://pypi.org/project/lelesk/) and can be installed using pip

```bash
pip install lelesk
```

Lelesk uses NLTK lemmatizer and yawlib wordnet API.
To install NLTK data, start a Python prompt, `import nltk` and then run the download command (only the `book` package is required)

```python
$ python3
Python 3.6.9 (default, Jan 26 2021, 15:33:00) 
[GCC 8.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import nltk
>>> nltk.download("book")
```

Download `yawlib` [databases](https://osf.io/9udjk/) and extract all the db files to `~/wordnet`.
For more information:

- Installing NLTK data: https://www.nltk.org/data.html
- Installing Yawlib wordnets: https://pypi.org/project/yawlib/

## Command-line tools

To disambiguate a sentence, run this command on the terminal:

```bash
python3 -m lelesk wsd "I go to the bank to get money."
```

To perform word-sense disambiguation on a text file, prepare a text file with each line is a sentence. 

For example here is the content of the file `demo.txt`

```
I go to the bank to withdraw money.
I sat at the river bank.
```

you then can run the following command

```
# output to TTL/JSON (a single file)
python3 -m lelesk file demo.txt demo_wsd_output.json --ttl json

# output to TTL/TSV (multiple TSV files)
python3 -m lelesk file demo.txt demo_wsd_output.json --ttl tsv
```

# Issues

If you have any issue, please report at https://github.com/letuananh/lelesk/issues
