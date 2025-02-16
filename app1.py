import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Ensure working directory is correct

import cv2
import numpy as np
import streamlit as st
import time
import csv
import socket
import tempfile

# Import custom modules
from videoDownloader import download_video, relativeToAbsolute
import main as main_mod  # for downloading video
from video_processing import get_expected_coordinates
from coordinate_overlays import get_pose_coordinates, draw_overlays

# Socket setup for sending intensity data to NodeMCU/ESP32
ESP_IP = "192.168.72.112"  # update as needed
ESP_PORT = 4210
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- Helper Functions ---

def resize_with_aspect_ratio(frame, width=None, height=None, inter=cv2.INTER_AREA):
    (h, w) = frame.shape[:2]
    if width is None and height is None:
        return frame
    if width is not None:
        r = width / float(w)
        dim = (width, int(h * r))
    else:
        r = height / float(h)
        dim = (int(w * r), height)
    return cv2.resize(frame, dim, interpolation=inter)

def compute_global_error(expected, live):
    # Compute Euclidean error for left and right arms separately.
    left_error = np.linalg.norm(np.array(expected["left_arm"]) - np.array(live["left_arm"]))
    right_error = np.linalg.norm(np.array(expected["right_arm"]) - np.array(live["right_arm"]))
    return left_error, right_error

def map_error_to_intensity(error, max_error=0.4):
    intensity = 100 * (1 - np.exp(-global_error / scale))
    return int(intensity)

# --- Streamlit UI Setup ---

st.title("DanticDance: Dual Stream Overlay App")
st.write("Provide a YouTube URL to download and pre-process the expected dance video, or use existing CSV & MP4 files.")
st.write("The **left column** shows the expected dance video (with red overlays), and the **right column** shows the live webcam feed (with green overlays overlaid with red expected markers plus error indicators).")

# Slider for playback speed control.
playback_speed = st.slider("Playback Speed (FPS)", min_value=1, max_value=120, value=60, step=1)

# --- Option: Use Existing CSV & Video ---
use_existing = st.checkbox("Use existing CSV & MP4 video (skip download/pre-processing)", value=False)
if use_existing:
    uploaded_csv = st.file_uploader("Upload CSV file with coordinates", type="csv")
    uploaded_video = st.file_uploader("Upload MP4 video file (expected video)", type="mp4")
    
    if uploaded_csv is not None and uploaded_video is not None:
        csv_coords = []
        content = uploaded_csv.read().decode('utf-8').splitlines()
        csv_reader = csv.reader(content)
        for row in csv_reader:
            if len(row) == 8:
                row = list(map(float, row))
                coord = {
                    "left_arm": (row[0], row[1]),
                    "right_arm": (row[2], row[3]),
                    "left_leg": (row[4], row[5]),
                    "right_leg": (row[6], row[7])
                }
                csv_coords.append(coord)
        if csv_coords:
            st.session_state.csv_coords = csv_coords
            st.success("CSV loaded successfully.")
        else:
            st.error("Uploaded CSV contains no valid data.")
        # Save the uploaded video to a temporary file.
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_video.read())
        st.session_state.downloaded_video_path = tfile.name
        st.success("Video file loaded successfully.")
else:
    st.session_state.pop("csv_coords", None)
    st.session_state.pop("downloaded_video_path", None)

# --- Section 1: Download Video and Pre-process (if not using existing) ---
video_url = st.text_input("Enter YouTube URL", "")
if not use_existing:
    if "downloaded_video_path" not in st.session_state:
        st.session_state.downloaded_video_path = None
    if "csv_coords" not in st.session_state:
        st.session_state.csv_coords = None

    download_button = st.button("Download Video")
    if download_button and video_url != "":
        st.write("Downloading video, please wait...")
        timestamp = int(time.time())
        relative_video_path = f"/src/videos/video_{timestamp}.mp4"
        st.session_state.downloaded_video_path = main_mod.main(video_url, relative_video_path)
        st.success(f"Video downloaded to {st.session_state.downloaded_video_path}")
        
        # Preprocess video to extract coordinates and write to a CSV file.
        st.write("Pre-processing video for coordinate extraction...")
        cap_pre = cv2.VideoCapture(st.session_state.downloaded_video_path)
        coords_list = []
        while True:
            ret, frame = cap_pre.read()
            if not ret:
                break
            frame = resize_with_aspect_ratio(frame, width=640)
            coords = get_expected_coordinates(frame)
            if coords is not None:
                rounded_coords = { k: (round(val[0],4), round(val[1],4)) for k, val in coords.items() }
                coords_list.append({
                    "left_arm": rounded_coords["left_arm"],
                    "right_arm": rounded_coords["right_arm"],
                    "left_leg": rounded_coords["left_leg"],
                    "right_leg": rounded_coords["right_leg"]
                })
        cap_pre.release()
        if coords_list:
            # Write a new CSV file with headers and coordinate values.
            os.makedirs(relativeToAbsolute("/src/csv/"), exist_ok=True)
            abs_csv_path = relativeToAbsolute(f"/src/csv/coords_{timestamp}.csv")
            with open(abs_csv_path, mode="w", newline="") as csvfile:
                csv_writer = csv.writer(csvfile)
                # Write header row.
                csv_writer.writerow(["left_arm_x","left_arm_y","right_arm_x","right_arm_y","left_leg_x","left_leg_y","right_leg_x","right_leg_y"])
                for row in coords_list:
                    csv_writer.writerow([row["left_arm"][0], row["left_arm"][1],
                                         row["right_arm"][0], row["right_arm"][1],
                                         row["left_leg"][0], row["left_leg"][1],
                                         row["right_leg"][0], row["right_leg"][1]])
            st.session_state.csv_coords = coords_list  # Also store in session state for fast access.
            st.success(f"Pre-processed coordinates extracted from {len(coords_list)} frames and saved to CSV.")
        else:
            st.error("No valid coordinates were extracted. Adjust mediapipe parameters or check video quality.")

# --- Section 2: Set up Video Streams (Side by Side) ---
st.header("Video Streams")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Expected Dance Video")
    expected_placeholder = st.empty()
with col2:
    st.subheader("Live Webcam Feed")
    webcam_placeholder = st.empty()

# Open expected video if available.
if st.session_state.get("downloaded_video_path"):
    video_cap = cv2.VideoCapture(st.session_state.downloaded_video_path)
else:
    video_cap = None
    dummy_video_frame = np.zeros((480,640,3), dtype=np.uint8)

# Load pre-processed coordinates from session state.
if "csv_coords" in st.session_state and st.session_state.csv_coords:
    csv_coords = st.session_state.csv_coords
else:
    csv_coords = [{"left_arm": (0,0), "right_arm": (0,0), "left_leg": (0,0), "right_leg": (0,0)}]
num_csv_frames = len(csv_coords)

# Open the webcam.
webcam_cap = cv2.VideoCapture(0)
if not webcam_cap.isOpened():
    st.write("Webcam not found.")
    webcam_cap = None
    dummy_webcam_frame = np.zeros((480,640,3), dtype=np.uint8)

# Initialize CSV frame counter.
csv_idx = 0

# --- Main Loop: Update Both Streams ---
while True:
    start_time = time.time()
    
    # --- Top Stream: Expected Dance Video ---
    if video_cap is not None:
        frame_v = video_cap.read()[1]
        if frame_v is None:
            video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            frame_v = video_cap.read()[1]
        frame_v = resize_with_aspect_ratio(frame_v, width=640)
        exp_coords = csv_coords[csv_idx % num_csv_frames]
        frame_v = draw_overlays(frame_v, exp_coords, exp_coords)
        top_frame = cv2.cvtColor(frame_v, cv2.COLOR_BGR2RGB)
        expected_placeholder.image(top_frame, channels="RGB")
    else:
        expected_placeholder.image(dummy_video_frame, channels="RGB")
    
    # --- Bottom Stream: Live Webcam Feed ---
    if webcam_cap is not None:
        frame_w = webcam_cap.read()[1]
        if frame_w is None:
            break
        frame_w = resize_with_aspect_ratio(frame_w, width=800)  # Larger display for webcam.
        live_coords = get_pose_coordinates(frame_w)
        # If no person is detected, display raw frame.
        if live_coords is None:
            webcam_placeholder.image(cv2.cvtColor(frame_w, cv2.COLOR_BGR2RGB), channels="RGB")
            csv_idx += 1
            elapsed = time.time() - start_time
            delay = max(0, (1/playback_speed) - elapsed)
            time.sleep(delay)
            continue
        exp_coords_for_webcam = csv_coords[csv_idx % num_csv_frames]
        frame_w = draw_overlays(frame_w, live_coords, exp_coords_for_webcam)
        left_error = np.linalg.norm(np.array(exp_coords_for_webcam["left_arm"]) - np.array(live_coords["left_arm"]))
        right_error = np.linalg.norm(np.array(exp_coords_for_webcam["right_arm"]) - np.array(live_coords["right_arm"]))
        print("Left Error is {left_error} and Right Error is {right_error}")
        intensity_left = int(min(left_error/0.4, 1.0) * 100)
        intensity_right = int(min(right_error/0.4, 1.0) * 100)
        error_text = f"Left Error: {left_error:.2f} | Intensity: {intensity_left}%   Right Error: {right_error:.2f} | Intensity: {intensity_right}%"
        cv2.putText(frame_w, error_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        bottom_frame = cv2.cvtColor(frame_w, cv2.COLOR_BGR2RGB)
        webcam_placeholder.image(bottom_frame, channels="RGB")
        
        # Transmit both intensities via UDP.
        data = f"{intensity_left},{intensity_right}\n"
        sock.sendto(data.encode(), (ESP_IP, ESP_PORT))
    else:
        webcam_placeholder.image(dummy_webcam_frame, channels="RGB")
    
    csv_idx += 1
    elapsed = time.time() - start_time––
    delay = max(0, (1/playback_speed) - elapsed)
    time.sleep(delay)
    
    # TODO: Future work for networking: pack additional data if needed.
