import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Ensure working directory is correct

import cv2
import numpy as np
import streamlit as st
import time
import csv
import socket

# Import custom modules
from videoDownloader import download_video, relativeToAbsolute
import main as main_mod  # for downloading video
from video_processing import get_expected_coordinates
from coordinate_overlays import get_pose_coordinates, draw_overlays

ESP_IP = "192.168.72.112"  # wifi dependent
ESP_PORT = 4210
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- Helper functions ---
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

def compute_global_error(expected, live, weights=None):
    errors = []
    for key in expected.keys():
        err = np.linalg.norm(np.array(expected[key]) - np.array(live[key]))
        errors.append(err)
    if weights is None:
        weights = [1] * len(errors)
    weighted_error = sum(e * w for e, w in zip(errors, weights)) / sum(weights)
    return weighted_error

def map_global_error_to_intensity(global_error, max_error=0.1):
    return int(min(global_error / max_error, 1.0) * 100)
st.title("DanticDance: Dual Stream Overlay App")
st.write("Enter a YouTube URL to download the expected dance video. Then view both streams:")
st.write("**Top:** Expected Dance Video with red overlays and diagonal lines (pre-processed).")
st.write("**Bottom:** Live Webcam Feed with green overlays (live) overlaid with red expected markers plus error indicators.")

# Add a slider for playback speed control
playback_speed = st.slider("Playback Speed (FPS)", min_value=1, max_value=120, value=60, step=1)

# --- Section 1: Download Video ---
video_url = st.text_input("Enter YouTube URL", "")
if "downloaded_video_path" not in st.session_state:
    st.session_state.downloaded_video_path = None
if "csv_path" not in st.session_state:
    st.session_state.csv_path = None

download_button = st.button("Download Video")
if download_button and video_url != "":
    st.write("Downloading video, please wait...")
    timestamp = int(time.time())
    relative_video_path = f"/src/videos/video_{timestamp}.mp4"
    st.session_state.downloaded_video_path = main_mod.main(video_url, relative_video_path)
    st.success(f"Video downloaded to {st.session_state.downloaded_video_path}")
    
    # Preprocess the video to extract expected coordinates and write to CSV
    csv_filename = f"/src/csv/coords_{timestamp}.csv"
    abs_csv_path = relativeToAbsolute(csv_filename)
    st.write("Pre-processing video for coordinate extraction...")
    cap_pre = cv2.VideoCapture(st.session_state.downloaded_video_path)
    coords_list = []
    while True:
        ret, frame = cap_pre.read()
        if not ret:
            break
        # Preserve the original aspect ratio (say, fix width to 640)
        frame = resize_with_aspect_ratio(frame, width=640)
        coords = get_expected_coordinates(frame)
        if coords is not None:
            # Round to 4 decimals for speed
            rounded_coords = { k: (round(val[0],4), round(val[1],4)) for k, val in coords.items() }
            coords_list.append([rounded_coords["left_arm"][0], rounded_coords["left_arm"][1],
                                rounded_coords["right_arm"][0], rounded_coords["right_arm"][1],
                                rounded_coords["left_leg"][0], rounded_coords["left_leg"][1],
                                rounded_coords["right_leg"][0], rounded_coords["right_leg"][1]])
        # Optionally, skip frames where detection fails.
    cap_pre.release()
    if coords_list:
        os.makedirs(relativeToAbsolute("/src/csv/"), exist_ok=True)
        with open(abs_csv_path, mode="w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            for row in coords_list:
                csv_writer.writerow(row)
        st.session_state.csv_path = abs_csv_path
        st.success(f"Pre-processed coordinates saved to {abs_csv_path}")
    else:
        st.error("No valid coordinates were extracted. Adjust mediapipe parameters or check video quality.")

# --- Section 2: Set up Video Streams ---
st.header("Expected Dance Video (Downloaded)")
video_placeholder = st.empty()

st.header("Live Webcam Feed")
webcam_placeholder = st.empty()

# Open downloaded video if available.
if st.session_state.downloaded_video_path:
    video_cap = cv2.VideoCapture(st.session_state.downloaded_video_path)
else:
    video_cap = None
    dummy_video_frame = np.zeros((480,640,3), dtype=np.uint8)

# Load pre-processed coordinates from CSV into a list.
csv_coords = []
if st.session_state.csv_path:
    with open(st.session_state.csv_path, mode="r") as csvfile:
        csv_reader = csv.reader(csvfile)
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
if not csv_coords:
    csv_coords = [{"left_arm": (0,0), "right_arm": (0,0), "left_leg": (0,0), "right_leg": (0,0)}]

# Open the webcam.
webcam_cap = cv2.VideoCapture(0)
if not webcam_cap.isOpened():
    st.write("Webcam not found.")
    webcam_cap = None
    dummy_webcam_frame = np.zeros((480,640,3), dtype=np.uint8)

# Initialize frame counter for CSV.
csv_idx = 0
num_csv_frames = len(csv_coords)

# Main loop: update both streams.
while True:
    start_time = time.time()
    
    # --- Top Stream: Expected Video ---
    if video_cap is not None:
        frame_v = video_cap.read()[1]
        if frame_v is None:
            video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            frame_v = video_cap.read()[1]
        # Resize preserving aspect ratio
        frame_v = resize_with_aspect_ratio(frame_v, width=640)
        # Get expected coordinates from CSV (cycled using csv_idx)
        exp_coords = csv_coords[csv_idx % num_csv_frames]
        # Overlay red markers on expected video (using same dict for both parameters)
        frame_v = draw_overlays(frame_v, exp_coords, exp_coords)
        top_frame = cv2.cvtColor(frame_v, cv2.COLOR_BGR2RGB)
        video_placeholder.image(top_frame, channels="RGB")
        csv_idx += 1
    else:
        video_placeholder.image(dummy_video_frame, channels="RGB")
    
    # --- Bottom Stream: Live Webcam ---
    if webcam_cap is not None:
        frame_w = webcam_cap.read()[1]
        if frame_w is None:
            break
        frame_w = resize_with_aspect_ratio(frame_w, width=640)
        live_coords = get_pose_coordinates(frame_w)
        if live_coords is None:
            live_coords = {
                "left_arm": np.array([0.32, 0.52]),
                "right_arm": np.array([0.68, 0.51]),
                "left_leg": np.array([0.36, 0.88]),
                "right_leg": np.array([0.64, 0.91])
            }
        # Use same expected coords from CSV for error comparison.
        exp_coords_for_webcam = csv_coords[csv_idx % num_csv_frames]
        frame_w = draw_overlays(frame_w, live_coords, exp_coords_for_webcam)
        # Compute global error over arms.
        global_error = compute_global_error(exp_coords_for_webcam, live_coords)
        intensity = map_global_error_to_intensity(global_error)
        error_text = f"Global Error: {global_error:.2f} | Intensity: {intensity}%"
        cv2.putText(frame_w, error_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
        bottom_frame = cv2.cvtColor(frame_w, cv2.COLOR_BGR2RGB)
        webcam_placeholder.image(bottom_frame, channels="RGB")
        left_error = np.linalg.norm(np.array(csv_coords[csv_idx % num_csv_frames]["left_arm"]) - np.array(live_coords["left_arm"]))
        right_error = np.linalg.norm(np.array(csv_coords[csv_idx % num_csv_frames]["right_arm"]) - np.array(live_coords["right_arm"]))
        intensity_left = int(min(left_error/0.1,1.0)*100)
        intensity_right = int(min(right_error/0.1,1.0)*100)
        data = f"{intensity_left},{intensity_right}\n"
        sock.sendto(data.encode(), (ESP_IP, ESP_PORT))
    else:
        webcam_placeholder.image(dummy_webcam_frame, channels="RGB")
    
    elapsed = time.time() - start_time
    delay = max(0, (1/playback_speed) - elapsed)
    time.sleep(delay)
    
    # TODO:
    # Networking integration: send [intensity] array to ESP32 via WiFi.
    # The error intensity values (intensity_left, intensity_right) should eventually be packed into an array
    # and transmitted over WiFi (using a NodeMCU/ESP32) to drive the haptic actuators.
