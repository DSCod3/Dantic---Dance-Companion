import time
from videoDownloader import download_video, relativeToAbsolute
# from videoInterpreter import interpret_video

model = '/pose models/pose_landmarker_lite.task'
videoURL = str(input("Enter the URL of the video: "))
timestamp = int(time.time())
relativeVideoPath = f'/src/videos/video_{timestamp}.mp4'

def main():
    print("running main")
    print("downloading video")
    download_video(videoURL, relativeVideoPath)
    return

main()