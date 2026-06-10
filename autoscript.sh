#!/bin/bash

# Auto install last version of youtube-dl and chat-downloader for docker image
# Force reinstall yt-dlp from a fork to fix error "No video formats found!" when use --live-from-start with cookies.
# Will remove this after the merge complete.
# https://github.com/yt-dlp/yt-dlp/pull/16771
# https://github.com/yt-dlp/yt-dlp/issues/15274
pip install --no-cache-dir --upgrade --quiet "yt-dlp[pin] @ git+https://github.com/dreammu/yt-dlp@live-adaptive-formats" yt-dlp-ejs

# Run main script
bash /usr/src/app/config/auto.sh

# Run Youtube-dl Web GUI
python -u /usr/src/app/youtube-dl-server.py
