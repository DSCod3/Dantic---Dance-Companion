# app.py
import cv2
import numpy as np
import streamlit as st
import time

# Import our custom modules
from coordinate_overlays import get_pose_coordinates, draw_overlays
from video_processing import get_dummy_expected_coordinates  # For expected coordinates

# ========================================================
# Bluetooth Setup for macOS (Simulated)
# ========================================================
# On macOS, a real Bluetooth port might look like '/dev/tty.HC-05-DevB'.
# Uncomment and adjust the line below if you have the actual device:
# import serial
# bt_serial = serial.Serial(port='/dev/tty.HC-05-DevB', baudrate=9600, timeout=1)

# For now, we simulate Bluetooth communication:
class DummySerial:
    def write(self, data):
        print("Simulated Bluetooth Send:", data.decode())

bt_serial = DummySerial()

# ========================================================
# Error Processing Functions
# ========================================================
def compute_error(expected, current):
    """Compute Euclidean distance between expected and current coordinates."""
    return np.linalg.norm(current - expected)

def map_error_to_intensity(error, max_error=0.1):
    """
    Map error (0 to max_error) to an intensity value between 0 and 100.
    If error exceeds max_error, intensity saturates at 100.
    """
    intensity = int(min(error / max_error, 1.0) * 100)
    return intensity

def send_bluetooth_command(command):
    """Simulate sending a command via Bluetooth."""
    bt_serial.write(command.encode())

def process_error_and_command(expected_coords, actual_coords):
    """
    Compute errors for left and right arms, map errors to intensities,
    form a command string, and send it over Bluetooth.
    Returns the command and error/intensity data.
    """
    error_left = compute_error(expected_coords["left_arm"], actual_coords["left_arm"])
    error_right = compute_error(expected_coords["right_arm"], actual_coords["right_arm"])
    
    intensity_left = map_error_to_intensity(error_left)
    intensity_right = map_error_to_intensity(error_right)
    
    command = f"L:{intensity_left};R:{intensity_right}"
    send_bluetooth_command(command)
    
    return command, intensity_left, intensity_right, error_left, error_right

# ========================================================
# Streamlit GUI Setup
# ========================================================
st.title("HaptiDance: Coordinate Overlay & Error Processing Test")
st.write("This app overlays coordinate markers and diagonal lines on the webcam feed,")
st.write("computes errors between dummy expected and actual dance positions, and simulates Bluetooth transmission.")

# Placeholder for video feed
frame_placeholder = st.empty()

# Get expected coordinates from the dummy video_processing module
expected_coords = get_dummy_expected_coordinates()
# For testing, define dummy actual coordinates that differ slightly from expected.
dummy_actual_coords = {
    "left_arm": np.array([0.32, 0.52]),
    "right_arm": np.array([0.68, 0.51]),
    "left_leg": np.array([0.36, 0.88]),
    "right_leg": np.array([0.64, 0.91])
}

# Attempt to open the webcam; if not available, use a dummy black image.
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    st.write("Webcam not found. Using a dummy image.")
    cap = None
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

# Main loop to update the GUI.
while True:
    # 1. Grab a frame from the webcam (or use dummy image)
    if cap:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (640, 480))
    else:
        frame = dummy_frame.copy()
    
    # === STEP A: Extract live pose coordinates ===
    # Call get_pose_coordinates to extract live coordinates from the current frame.
    # This will use MediaPipe Holistic internally (THANK GOD IT WORKS)
    live_coords = get_pose_coordinates(frame)
    
    # For testing, if live_coords is None (i.e., no pose detected), use dummy actual coordinates.
    if live_coords is None:
        live_coords = {
            "left_arm": np.array([0.32, 0.52]),
            "right_arm": np.array([0.68, 0.51]),
            "left_leg": np.array([0.36, 0.88]),
            "right_leg": np.array([0.64, 0.91])
        }
    
    # === STEP B: Draw overlays ===
    # This function uses both live_coords and expected_coords.
    frame = draw_overlays(frame, live_coords, expected_coords)
    
    # === STEP C: Process Errors & Send Commands ===
    # Compute error between expected and live positions (for arms in this case)
    command, intensity_left, intensity_right, error_left, error_right = process_error_and_command(expected_coords, live_coords)
    
    # Overlay error and command information on the frame.
    overlay_text = (f"Left Error: {error_left:.2f} Intensity: {intensity_left}% | "
                    f"Right Error: {error_right:.2f} Intensity: {intensity_right}%")
    cv2.putText(frame, overlay_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"Command: {command}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Convert the frame from BGR to RGB for displaying in Streamlit.
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_placeholder.image(frame_rgb, channels="RGB")
    
    # Sleep to simulate ~30 FPS.
    time.sleep(0.0166)
