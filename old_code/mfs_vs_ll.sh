#!/usr/bin/sh

python3 main.py batch -i data/speckled_lldev.txt -o data/speckled_lldev_summary.txt > data/speckled_lldev_details.txt
python3 main.py batch -i data/speckled_lldev.txt -o data/speckled_lldevPPOS_summary.txt -p -P > data/speckled_lldevPPOS_details.txt

python3 main.py batch -i data/speckled_lldev.txt -o data/speckled_lldevmfs_summary.txt -m "mfs" > data/speckled_lldevmfs_details.txt
python3 main.py batch -i data/speckled_lldev.txt -o data/speckled_lldevmfsPPOS_summary.txt -m "mfs" -p -P > data/speckled_lldevmfsPPOS_details.txt

echo '-------------------------------------------------------'
echo 'LELESK+MFS'
tail -n 7 data/speckled_lldev_details.txt
echo '-------------------------------------------------------'
echo 'LELESK+MFS+PerfectPOS'
tail -n 7 data/speckled_lldevPPOS_details.txt
echo '-------------------------------------------------------'
echo 'MFS'
tail -n 7 data/speckled_lldevmfs_details.txt
echo '-------------------------------------------------------'
echo 'MFS+PerfectPOS'
tail -n 7 data/speckled_lldevmfsPPOS_details.txt