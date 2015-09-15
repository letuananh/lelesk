#!/usr/bin/sh

python3 lelesk/wsdtk.py -b 'data/specall.txt' -o 'data/specall_ll_report.txt' -r 'data/specall_ll_debug.txt'
python3 lelesk/wsdtk.py -b 'data/specall.txt' -o 'data/specall_mfs_report.txt' -m mfs -r 'data/specall_mfs_debug.txt'


echo '-------------------------------------------------------'
echo 'LELESK'
echo ''
tail -n 7 data/specall_ll_report.txt
echo ''
echo '-------------------------------------------------------'
echo 'MFS'
echo ''
tail -n 7 data/specall_mfs_report.txt

