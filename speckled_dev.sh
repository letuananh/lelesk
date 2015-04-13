#!/usr/bin/sh

python3 main.py batch -i data/speckled_lldev.txt -o data/speckled_lldev_summary.txt > data/speckled_lldev_details.txt
python3 main.py batch -i data/speckled_lldev.txt -o data/speckled_lldevmfs_summary.txt -m "mfs" > data/speckled_lldevmfs_details.txt
tail data/speckled_lldev_details.txt
tail data/speckled_lldevmfs_details.txt