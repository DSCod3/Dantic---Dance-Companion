# video_processing.py
import numpy as np

def get_dummy_expected_coordinates():
    """
    Returns a dictionary with dummy expected normalized coordinates for:
      - left_arm (forearm, near hand)
      - right_arm (forearm, near hand)
      - left_leg (slightly above the ankle)
      - right_leg (slightly above the ankle)
    (Coordinates are in normalized [0,1] range relative to the frame size.)
    """
    expected_coords = {
        "left_arm": np.array([0.30, 0.50]),
        "right_arm": np.array([0.70, 0.50]),
        "left_leg": np.array([0.35, 0.90]),
        "right_leg": np.array([0.65, 0.90])
    }
    return expected_coords
