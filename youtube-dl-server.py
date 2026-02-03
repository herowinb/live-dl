from __future__ import unicode_literals
import json
import os
import subprocess
from queue import Queue
from bottle import route, run, Bottle, request, static_file, template, auth_basic
from threading import Thread
from yt_dlp import YoutubeDL
from pathlib import Path
from collections import ChainMap

app = Bottle()

BASE_DIR = "./config"
# Whitelisted files ONLY
ALLOWED_FILES = [
    "auto.sh",
    "config.yml",
]

# Default Credentials
AUTH_USER = os.getenv("EDITOR_USER", "admin")
AUTH_PASS = os.getenv("EDITOR_PASS", "live-dl")

def check_auth(user, pw):
    return user == AUTH_USER and pw == AUTH_PASS

app_defaults = {
    'YDL_FORMAT': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
    'YDL_EXTRACT_AUDIO_FORMAT': None,
    'YDL_EXTRACT_AUDIO_QUALITY': '192',
    'YDL_RECODE_VIDEO_FORMAT': None,
    'YDL_OUTPUT_TEMPLATE': '/youtube-dl/%(title)s [%(id)s].%(ext)s',
    'YDL_ARCHIVE_FILE': None,
    'YDL_SERVER_HOST': '0.0.0.0',
    'YDL_SERVER_PORT': 8080,
}


@app.route('/')
def dl_queue_list():
    return static_file('index.html', root='./')

@app.route("/editor", method=["GET", "POST"])
@auth_basic(check_auth)
def editor():
    saved = False
    filename = request.forms.get("filename") or ALLOWED_FILES[0]

    if request.method == "POST":
        if request.forms.get("save"):
            content = request.forms.get("content", "")
            write_file(filename, content)
            saved = True

    content = read_file(filename)

    return template(
        "editor.html",
        files=ALLOWED_FILES,
        current=filename,
        content=content,
        saved=saved
    )

@app.route('/static/:filename#.*#')
def server_static(filename):
    return static_file(filename, root='./static')


@app.route('/q', method='GET')
def q_size():
    return {"success": True, "size": json.dumps(list(dl_q.queue))}


@app.route('/q', method='POST')
def q_put():
    url = request.forms.get("url")
    options = {
        'format': request.forms.get("format")
    }

    if not url:
        return {"success": False, "error": "/q called without a 'url' in form data"}

    dl_q.put((url, options))
    print("Added url " + url + " to the download queue")
    return {"success": True, "url": url, "options": options}

@app.route("/update", method="GET")
def dl_worker():
    while not done:
        url, options = dl_q.get()
        download(url, options)
        dl_q.task_done()


def get_ydl_options(request_options):
    request_vars = {
        'YDL_EXTRACT_AUDIO_FORMAT': None,
        'YDL_RECODE_VIDEO_FORMAT': None,
    }

    requested_format = request_options.get('format', 'bestvideo')

    if requested_format in ['aac', 'flac', 'mp3', 'm4a', 'opus', 'vorbis', 'wav']:
        request_vars['YDL_EXTRACT_AUDIO_FORMAT'] = requested_format
    elif requested_format == 'bestaudio':
        request_vars['YDL_EXTRACT_AUDIO_FORMAT'] = 'best'
    elif requested_format in ['mp4', 'flv', 'webm', 'ogg', 'mkv', 'avi']:
        request_vars['YDL_RECODE_VIDEO_FORMAT'] = requested_format

    ydl_vars = ChainMap(request_vars, os.environ, app_defaults)

    postprocessors = []

    if(ydl_vars['YDL_EXTRACT_AUDIO_FORMAT']):
        postprocessors.append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': ydl_vars['YDL_EXTRACT_AUDIO_FORMAT'],
            'preferredquality': ydl_vars['YDL_EXTRACT_AUDIO_QUALITY'],
        })

    if(ydl_vars['YDL_RECODE_VIDEO_FORMAT']):
        postprocessors.append({
            'key': 'FFmpegVideoConvertor',
            'preferedformat': ydl_vars['YDL_RECODE_VIDEO_FORMAT'],
        })

    return {
        'format': ydl_vars['YDL_FORMAT'],
        'postprocessors': postprocessors,
        'outtmpl': ydl_vars['YDL_OUTPUT_TEMPLATE'],
        'download_archive': ydl_vars['YDL_ARCHIVE_FILE'],
        'cookiefile': '/usr/src/app/config/cookies.txt',
        'ignoreerrors': True,
        'nopart': True
    }


def download(url, request_options):
    with YoutubeDL(get_ydl_options(request_options)) as ydl:
        ydl.download([url])

def safe_path(filename):
    if filename not in ALLOWED_FILES:
        return None
    return os.path.join(BASE_DIR, filename)

def read_file(filename):
    path = safe_path(filename)
    if not path or not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(filename, content):
    path = safe_path(filename)
    if not path:
        return
    # Normalize to LF explicitly
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


dl_q = Queue()
done = False
dl_thread = Thread(target=dl_worker)
dl_thread.start()


print("Started download thread")

app_vars = ChainMap(os.environ, app_defaults)

app.run(host=app_vars['YDL_SERVER_HOST'], port=app_vars['YDL_SERVER_PORT'], debug=True)
done = True
dl_thread.join()
