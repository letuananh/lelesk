#!/usr/bin/sh

python3 wsdtk.py -b 'data/specdev.txt' -o 'data/specdev_ll_report.txt' -r 'data/specdev_ll_debug.txt'
python3 wsdtk.py -b 'data/specdev.txt' -o 'data/specdev_mfs_report.txt' -m mfs -r 'data/specdev_mfs_debug.txt'


echo '-------------------------------------------------------'
echo 'LELESK'
echo ''
tail -n 7 data/specdev_ll_report.txt
echo ''
echo '-------------------------------------------------------'
echo 'MFS'
echo ''
tail -n 7 data/specdev_mfs_report.txt

