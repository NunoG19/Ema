#!/bin/sh

PUBLISH_FOLDER=../www/

if [ -f version.py ]
then
    python2 libs/kypatcher.py create
    cd ..
    rsync -azv --delete-after --exclude=".*/" Ema $PUBLISH_FOLDER/
else
    echo "Please run this script on Ema/ folder"
fi
