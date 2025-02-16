# main.py
import time
from videoDownloader import download_video, relativeToAbsolute

# (If needed, set your model path here)
model = '/pose models/pose_landmarker_lite.task'

def main(videoURL, relativeVideoPath):
    print("Running main.py: downloading video...")
    download_video(videoURL, relativeVideoPath)
    # Return the absolute path to the downloaded video.
    return relativeToAbsolute(relativeVideoPath)

if __name__ == "__main__":
    # For command-line testing only.
    videoURL = input("Enter the URL of the video: ")
    timestamp = int(time.time())
    relativeVideoPath = f'/src/videos/video_{timestamp}.mp4'
    video_path = main(videoURL, relativeVideoPath)
    print("Video downloaded to", video_path)
