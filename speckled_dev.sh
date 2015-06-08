#!/usr/bin/sh

python3 wsdtk.py -b 'data/specdev.txt' -o 'data/specdev_ll_summary.txt' > 'data/specdev_ll_details.txt'
python3 wsdtk.py -b 'data/specdev.txt' -o 'data/specdev_mfs_summary.txt' -m mfs > 'data/specdev_mfs_details.txt'


echo '-------------------------------------------------------'
echo 'LELESK'
tail -n 25 data/specdev_ll_details.txt
echo '-------------------------------------------------------'
echo 'MFS'
tail -n 25 data/specdev_mfs_details.txt

