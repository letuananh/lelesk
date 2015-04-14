#!/usr/bin/sh

python3 main.py batch -i data/speckled_lldev.txt -o data/speckled_lldev_summary.txt > data/speckled_lldev_details.txt
python3 main.py batch -i data/speckled_lldev.txt -o data/speckled_lldevpre_summary.txt -t > data/speckled_lldevpre_details.txt
python3 main.py batch -i data/speckled_lldev.txt -o data/speckled_lldevpos_summary.txt -p > data/speckled_lldevpos_details.txt
python3 main.py batch -i data/speckled_lldev.txt -o data/speckled_lldevpospre_summary.txt -p -t > data/speckled_lldevpospre_details.txt
python3 main.py batch -i data/speckled_lldev.txt -o data/speckled_lldevPPOS_summary.txt -p -P -t > data/speckled_lldevPPOS_details.txt
python3 main.py batch -i data/speckled_lldev.txt -o data/speckled_lldevPPOSpre_summary.txt -p -P -t > data/speckled_lldevPPOSpre_details.txt

python3 main.py batch -i data/speckled_lldev.txt -o data/speckled_lldevmfs_summary.txt -m "mfs" -t > data/speckled_lldevmfs_details.txt
python3 main.py batch -i data/speckled_lldev.txt -o data/speckled_lldevmfspos_summary.txt -m "mfs" -p -t > data/speckled_lldevmfspos_details.txt
python3 main.py batch -i data/speckled_lldev.txt -o data/speckled_lldevmfsPPOS_summary.txt -m "mfs" -p -P -t > data/speckled_lldevmfsPPOS_details.txt

echo '-------------------------------------------------------'
echo 'LELESK+MFS'
tail -n 7 data/speckled_lldev_details.txt
echo '-------------------------------------------------------'
echo 'LELESK+MFS+Pretokenized'
tail -n 7 data/speckled_lldevpre_details.txt
echo '-------------------------------------------------------'
echo 'LELESK+MFS+POS'
tail -n 7 data/speckled_lldevpos_details.txt
echo '-------------------------------------------------------'
echo 'LELESK+MFS+POS+Pretokenized'
tail -n 7 data/speckled_lldevpospre_details.txt
echo '-------------------------------------------------------'
echo 'LELESK+MFS+PerfectPOS'
tail -n 7 data/speckled_lldevPPOS_details.txt
echo '-------------------------------------------------------'
echo 'LELESK+MFS+PerfectPOS+Pretokenized'
tail -n 7 data/speckled_lldevPPOSpre_details.txt

echo '-------------------------------------------------------'
echo 'MFS'
tail -n 7 data/speckled_lldevmfs_details.txt
echo '-------------------------------------------------------'
echo 'MFS+POS'
tail -n 7 data/speckled_lldevmfspos_details.txt
echo '-------------------------------------------------------'
echo 'MFS+PerfectPOS'
tail -n 7 data/speckled_lldevmfsPPOS_details.txt