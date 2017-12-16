#!/bin/bash

python3 -m lelesk.wsdtk -W "love" -x "I love cooking." -r ~/tmp/lelesk-wsd-i-love-cooking.txt
python3 -m lelesk.wsdtk -b data/test.txt -o data/test_report.txt -r data/test_debug.txt
