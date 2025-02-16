# videoDownloader.py
import yt_dlp
import os

def relativeToAbsolute(path):
    return os.getcwd() + path

def download_video(url, path):
    path = relativeToAbsolute(path)
    # print("Downloading to:", path)
    ydl_opts = {
        'format': 'bestvideo',
        'merge_output_format': 'mp4',
        'outtmpl': path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
