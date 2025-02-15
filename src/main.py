from videoDownloader import download_video,relativeToAbsolute
# from videoInterpreter import interpret_video

model = '/pose models/pose_landmarker_lite.task'
videoURL = "https://www.youtube.com/watch?v=6WsM9ExX7Bg" # str(input("Enter the URL of the video: "))
relativeVideoPath = r'/src/video.mp4'

def main():
    print("running main")
    print("downloading video")
    download_video(videoURL, relativeVideoPath)
    return

main()