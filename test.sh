#!/usr/bin/bash

python3 -m lelesk.wsdtk -s "01828736-v" -r ~/tmp/lelesk-synset-01828736-v.txt
python3 -m lelesk.wsdtk -t "love" -r ~/tmp/lelesk-synset-love.txt
python3 -m lelesk.wsdtk -k "love%2:37:02::" -r ~/tmp/lelesk-synset-love-2-37-02.txt
python3 -m lelesk.wsdtk -c "love" -p "v" -r ~/tmp/lelesk-candidate-love-v.txt
python3 -m lelesk.wsdtk -W "love" -x "I love cooking." -r ~/tmp/lelesk-wsd-i-love-cooking.txt
python3 -m lelesk.wsdtk -b data/test.txt -o data/test_report.txt -r data/test_debug.txt
