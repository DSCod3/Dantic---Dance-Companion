import cv2
import numpy as np
import streamlit as st
import time
# import serial  # Uncomment this if you have a Bluetooth serial device connected

# ========================================================
# Bluetooth Setup (Simulation for macOS)
# ========================================================
# On macOS, your Bluetooth port might look like '/dev/tty.HC-05-DevB'
# Uncomment the following line to use the actual device:
# bt_serial = serial.Serial(port='/dev/tty.HC-05-DevB', baudrate=9600, timeout=1)

# For testing without a Bluetooth device, we simulate the connection:
class DummySerial:
    def write(self, data):
        print("Simulated Bluetooth Send:", data.decode())
        
bt_serial = DummySerial()

# ========================================================
# Error Processing Functions
# ========================================================
def compute_error(expected, current):
    """Compute distance between expected and current hand/leg coordinates."""
    return np.linalg.norm(current - expected)

def map_error_to_intensity(error, max_error=0.5):
    """
    Map error (0 to max_error) to an intensity value between 0 and 100.
    If error exceeds max_error, intensity saturates at 100.
    """
    intensity = int(min(error / max_error, 1.0) * 100)
    return intensity

def map_error_to_color(error, max_error=0.5):
    """
    Map error to an RGB color: green for low error, red for high error.
    At error=0, return green (0,255,0); at error=max_error, return red (255,0,0).
    """
    ratio = min(error / max_error, 1.0)
    red = int(255 * ratio)
    green = int(255 * (1 - ratio))
    blue = 0
    return (red, green, blue)

def send_bluetooth_command(command):
    """
    Send command over Bluetooth.
    Still have to code this out fully, but for now, just printing it.
    """
    bt_serial.write(command.encode())

def process_hand_errors(expected_left, current_left, expected_right, current_right):
    """
    Compute errors for left and right hand positions, map them to intensity,
    and form a command string to be sent to the Arduino.
    Returns a tuple: (command_string, left_intensity, right_intensity, left_color, right_color)
    """
    error_left = compute_error(expected_left, current_left)
    error_right = compute_error(expected_right, current_right)
    
    intensity_left = map_error_to_intensity(error_left)
    intensity_right = map_error_to_intensity(error_right)
    
    left_color = map_error_to_color(error_left)
    right_color = map_error_to_color(error_right)
    
    # Format command: e.g., "L:<intensity_left>;R:<intensity_right>"
    command = f"L:{intensity_left};R:{intensity_right}"
    
    # Transmit command over Bluetooth
    send_bluetooth_command(command)
    
    return command, intensity_left, intensity_right, left_color, right_color

# ========================================================
# Streamlit GUI & Main Loop
# ========================================================

st.title("Dantic: Error Processing Test")
st.write("This app simulates error processing and Bluetooth transmission for haptic feedback.")

# Create a placeholder for the video frame
frame_placeholder = st.empty()

# For testing purposes, we use dummy hand coordinates (normalized: x and y between 0 and 1)
# In the final system, these will be obtained from the video processing module.
dummy_expected_left = np.array([0.3, 0.5])
dummy_expected_right = np.array([0.7, 0.5])
# Simulate current hand positions with a small error (you can adjust these to test different intensities)
dummy_current_left = np.array([0.35, 0.55])
dummy_current_right = np.array([0.65, 0.52])

# Try to open the webcam; if not available, use a dummy black image.
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    st.write("Webcam not found. Using dummy image.")
    cap = None
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

# Main loop to update the GUI
while True:
    # Capture frame from webcam if available; else use dummy image.
    if cap:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (640, 480))
    else:
        frame = dummy_frame.copy()
    
    # Process errors using dummy values
    command, intensity_left, intensity_right, left_color, right_color = process_hand_errors(
        dummy_expected_left, dummy_current_left, dummy_expected_right, dummy_current_right)
    
    # Overlay the computed error information on the frame
    overlay_text_left = f"Left Intensity: {intensity_left}%"
    cv2.putText(frame, overlay_text_left, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, left_color, 2)
    
    overlay_text_right = f"Right Intensity: {intensity_right}%"
    cv2.putText(frame, overlay_text_right, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, right_color, 2)
    
    cv2.putText(frame, f"Command Sent: {command}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    
    # Convert BGR to RGB for Streamlit display
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Update the Streamlit image
    frame_placeholder.image(frame_rgb, channels="RGB")
    
    # Sleep to simulate a frame rate (~30 FPS)
    time.sleep(0.033)
