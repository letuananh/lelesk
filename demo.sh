#!/bin/bash

# Disambiguate a sentence
python3 -m lelesk wsd "I go to the bank to get money."

# Disambiguate a text file and write output to demo_wsd.json in TTL/JSON format
python3 -m lelesk file data/demo.txt data/demo_wsd.json --ttl json
