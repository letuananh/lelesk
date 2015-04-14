#!/usr/bin/sh

python3 main.py batch -i data/speckled_llall.txt -o data/speckled_llall_summary.txt > data/speckled_llall_details.txt
python3 main.py batch -i data/speckled_llall.txt -o data/speckled_llallmfs_summary.txt -m "mfs" > data/speckled_llallmfs_details.txt
# python3 main.py batch -i data/speckled_llall.txt -o data/speckled_llallpos_summary.txt -p > data/speckled_llallpos_details.txt
# python3 main.py batch -i data/speckled_llall.txt -o data/speckled_llallmfspos_summary.txt -m "mfs" -p > data/speckled_llallmfspos_details.txt
python3 main.py batch -i data/speckled_llall.txt -o data/speckled_llallPPOS_summary.txt -p -P > data/speckled_llallPPOS_details.txt
python3 main.py batch -i data/speckled_llall.txt -o data/speckled_llallmfsPPOS_summary.txt -m "mfs" -p -P > data/speckled_llallmfsPPOS_details.txt

echo '-------------------------------------------------------'
echo 'LELESK+MFS'
tail -n 7 data/speckled_llall_details.txt

echo '-------------------------------------------------------'
echo 'MFS'
tail -n 7 data/speckled_llallmfs_details.txt

# echo '-------------------------------------------------------'
# echo 'LELESK+MFS+POS'
# tail -n 7 data/speckled_llallpos_details.txt

# echo '-------------------------------------------------------'
# echo 'MFS+POS'
# tail -n 7 data/speckled_llallmfspos_details.txt

echo '-------------------------------------------------------'
echo 'LELESK+MFS+PerfectPOS'
tail -n 7 data/speckled_llallPPOS_details.txt

echo '-------------------------------------------------------'
echo 'MFS+PerfectPOS'
tail -n 7 data/speckled_llallmfsPPOS_details.txt
