#!/usr/bin/sh

python3 wsdtk.py -b 'data/specall.txt' -o 'data/specall_ll_summary.txt' > 'data/specall_ll_details.txt'
python3 wsdtk.py -b 'data/specall.txt' -o 'data/specall_mfs_summary.txt' -m mfs > 'data/specall_mfs_details.txt'


echo '-------------------------------------------------------'
echo 'LELESK'
tail -n 7 data/specall_ll_summary.txt
echo '-------------------------------------------------------'
echo 'MFS'
tail -n 7 data/specall_mfs_summary.txt

