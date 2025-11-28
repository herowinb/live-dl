#!/bin/bash

# Auto install last version of youtube-dl and chat-downloader for docker image
pip install --no-cache-dir --upgrade --quiet yt-dlp yt-dlp-ejs

# Run main script
bash /usr/src/app/config/auto.sh

# Run Youtube-dl Web GUI
python -u /usr/src/app/youtube-dl-server.py
