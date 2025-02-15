import yt_dlp
import os

def relativeToAbsolute(path):
    return os.getcwd() + path
    # return os.path.abspath(path)

def download_video(url, path):
    path = relativeToAbsolute(path)
    print(path)
    ydl_opts = {
        'format': 'bestvideo',
        'merge_output_format': 'mp4',
        'outtmpl': path,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])