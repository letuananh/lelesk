#!/bin/bash

function link_folder {
	FOLDER_PATH=$1
	SYMLINK_NAME=$2
	if [ ! -d ${SYMLINK_NAME} ]; then
		ln -sv ${FOLDER_PATH} ${SYMLINK_NAME}
	else
		echo "Folder ${SYMLINK_NAME} exists."
	fi
}

function link_file {
	FOLDER_PATH=$1
	SYMLINK_NAME=$2
	if [ ! -f ${SYMLINK_NAME} ]; then
		ln -sv ${FOLDER_PATH} ${SYMLINK_NAME}
	else
		echo "File ${SYMLINK_NAME} exists."
	fi
}

link_folder `readlink -f ../chirptext/chirptext` chirptext
link_folder `readlink -f ../puchikarui/puchikarui` puchikarui
link_folder `readlink -f ../yawlib/yawlib` yawlib
link_folder `readlink -f ../nltk/nltk` nltk

git submodule init && git submodule update
