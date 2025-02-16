# app.py
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Ensure working directory is correct

import cv2
import numpy as np
import streamlit as st
import time

# Import custom modules
from videoDownloader import download_video, relativeToAbsolute
import main as main_mod  # To use the download functionality from main.py
from video_processing import get_expected_coordinates
from coordinate_overlays import get_pose_coordinates, draw_overlays

st.title("DanticDance: Dual Stream Overlay App")
st.write("Enter a YouTube URL to download the expected dance video. Then view both streams:")
st.write("**Top:** Expected Dance Video with red overlays and diagonal lines.")
st.write("**Bottom:** Live Webcam Feed with green overlays (live) overlaid with red expected markers plus error indicators.")

# --- Section 1: Download Video ---
video_url = st.text_input("Enter YouTube URL", "")
if "downloaded_video_path" not in st.session_state:
    st.session_state.downloaded_video_path = None

download_button = st.button("Download Video")
if download_button and video_url != "":
    st.write("Downloading video, please wait...")
    timestamp = int(time.time())
    relative_video_path = f"/src/videos/video_{timestamp}.mp4"
    # Call main.py's download function
    st.session_state.downloaded_video_path = main_mod.main(video_url, relative_video_path)
    st.success(f"Video downloaded to {st.session_state.downloaded_video_path}")

# --- Section 2: Set up Video Streams ---
st.header("Expected Dance Video (Downloaded)")
video_placeholder = st.empty()

st.header("Live Webcam Feed")
webcam_placeholder = st.empty()

# Open downloaded video if available; otherwise, show a dummy frame.
if st.session_state.downloaded_video_path:
    video_cap = cv2.VideoCapture(st.session_state.downloaded_video_path)
else:
    video_cap = None
    dummy_video_frame = np.zeros((480,640,3), dtype=np.uint8)

# Open the webcam.
webcam_cap = cv2.VideoCapture(0)
if not webcam_cap.isOpened():
    st.write("Webcam not found.")
    webcam_cap = None
    dummy_webcam_frame = np.zeros((480,640,3), dtype=np.uint8)

# For error processing on the webcam feed, we need to compare live (green) vs expected (red).
# Use the expected coordinates extracted from the expected video.
expected_coords_global = None

# Main loop: update both streams.
while True:
    # --- Top Stream: Expected Video ---
    if video_cap is not None:
        ret_v, frame_v = video_cap.read()
        if not ret_v:
            # Restart video if ended.
            video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret_v, frame_v = video_cap.read()
        frame_v = cv2.resize(frame_v, (640,480))
        # Extract expected coordinates from the video frame.
        expected_coords = get_expected_coordinates(frame_v)
        if expected_coords is not None:
            expected_coords_global = expected_coords  # Save for later use in webcam stream.
            # For the expected video, overlay red markers by passing the same dict for both parameters.
            frame_v = draw_overlays(frame_v, expected_coords, expected_coords)
        video_frame_rgb = cv2.cvtColor(frame_v, cv2.COLOR_BGR2RGB)
        video_placeholder.image(video_frame_rgb, channels="RGB")
    else:
        video_placeholder.image(dummy_video_frame, channels="RGB")
    
    # --- Bottom Stream: Live Webcam ---
    if webcam_cap is not None:
        ret_w, frame_w = webcam_cap.read()
        if not ret_w:
            break
        frame_w = cv2.resize(frame_w, (640,480))
        live_coords = get_pose_coordinates(frame_w)
        if live_coords is None:
            # If live pose is not detected, use a fallback dummy.
            live_coords = {
                "left_arm": np.array([0.32, 0.52]),
                "right_arm": np.array([0.68, 0.51]),
                "left_leg": np.array([0.36, 0.88]),
                "right_leg": np.array([0.64, 0.91])
            }
        # If we have expected coordinates (from the video), overlay them on the webcam feed.
        if expected_coords_global is not None:
            frame_w = draw_overlays(frame_w, live_coords, expected_coords_global)
            # Compute error (for arms) and overlay error/intensity indicators.
            left_error = np.linalg.norm(np.array(expected_coords_global["left_arm"]) - np.array(live_coords["left_arm"]))
            right_error = np.linalg.norm(np.array(expected_coords_global["right_arm"]) - np.array(live_coords["right_arm"]))
            intensity_left = int(min(left_error/0.1,1.0)*100)
            intensity_right = int(min(right_error/0.1,1.0)*100)
            error_text = f"Left Error: {left_error:.2f} Intensity: {intensity_left}% | Right Error: {right_error:.2f} Intensity: {intensity_right}%"
            cv2.putText(frame_w, error_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
        else:
            # If expected coordinates not available, just overlay live coordinates.
            frame_w = draw_overlays(frame_w, live_coords, live_coords)
        webcam_frame_rgb = cv2.cvtColor(frame_w, cv2.COLOR_BGR2RGB)
        webcam_placeholder.image(webcam_frame_rgb, channels="RGB")
    else:
        webcam_placeholder.image(dummy_webcam_frame, channels="RGB")
    
    # Adjust sleep for roughly 30 FPS.
    time.sleep(0.033)
