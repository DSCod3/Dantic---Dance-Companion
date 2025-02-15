# coordinate_overlays.py
import cv2
import mediapipe as mp

# Initialize MediaPipe Pose once
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5)

def get_pose_coordinates(frame):
    """
    Process the frame using MediaPipe Pose and extract normalized coordinates for:
      - left_arm: a point along the forearm computed as 30% left elbow + 70% left wrist.
      - right_arm: a point along the forearm computed as 30% right elbow + 70% right wrist.
      - left_leg: a point slightly above the left ankle (subtracting 0.05 from y).
      - right_leg: a point slightly above the right ankle.
    
    Returns a dictionary with keys: 'left_arm', 'right_arm', 'left_leg', 'right_leg'
    (Coordinates are in normalized [0,1] range.)
    """
    # Convert BGR frame to RGB as required by MediaPipe
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)
    
    # If no landmarks detected, return None
    if not results.pose_landmarks:
        return None

    landmarks = results.pose_landmarks.landmark

    # Extract relevant landmarks (indices from MediaPipe Pose)
    left_elbow = landmarks[13]
    left_wrist = landmarks[15]
    right_elbow = landmarks[14]
    right_wrist = landmarks[16]
    left_ankle = landmarks[27]
    right_ankle = landmarks[28]
    
    # Compute a point on the forearm: 30% from elbow, 70% toward wrist
    left_arm_x = 0.3 * left_elbow.x + 0.7 * left_wrist.x
    left_arm_y = 0.3 * left_elbow.y + 0.7 * left_wrist.y

    right_arm_x = 0.3 * right_elbow.x + 0.7 * right_wrist.x
    right_arm_y = 0.3 * right_elbow.y + 0.7 * right_wrist.y

    # For legs, take ankle positions and subtract a small offset from y (but not below 0)
    left_leg_x = left_ankle.x
    left_leg_y = max(0, left_ankle.y - 0.05)
    
    right_leg_x = right_ankle.x
    right_leg_y = max(0, right_ankle.y - 0.05)

    coords = {
        "left_arm": (left_arm_x, left_arm_y),
        "right_arm": (right_arm_x, right_arm_y),
        "left_leg": (left_leg_x, left_leg_y),
        "right_leg": (right_leg_x, right_leg_y)
    }
    return coords

def draw_overlays(frame, actual_coords, expected_coords):
    """
    Draws overlay dots and diagonal connecting lines on the given frame.
    
    Parameters:
      - frame: the input image (BGR).
      - actual_coords: dictionary with normalized coordinates from get_pose_coordinates.
      - expected_coords: dictionary with expected normalized coordinates (e.g., from video_processing.py).
      
    Actual positions are drawn as green circles; expected positions as red circles.
    Diagonal lines (in cyan) connect:
      - actual left_arm to actual right_leg and actual right_arm to actual left_leg.
      - expected left_arm to expected right_leg and expected right_arm to expected left_leg.
      
    Returns:
      The modified frame.
    """
    height, width, _ = frame.shape

    # Helper: Convert normalized coordinate (0-1) to pixel coordinate.
    def norm_to_pix(coord):
        return (int(coord[0] * width), int(coord[1] * height))
    
    if actual_coords is None:
        return frame

    actual_positions = {k: norm_to_pix(v) for k, v in actual_coords.items()}
    expected_positions = {k: norm_to_pix(v) for k, v in expected_coords.items()}
    
    # Draw actual positions in green.
    for pos in actual_positions.values():
        cv2.circle(frame, pos, 8, (0, 255, 0), -1)
        
    # Draw expected positions in red.
    for pos in expected_positions.values():
        cv2.circle(frame, pos, 8, (0, 0, 255), -1)
        
    # Define cyan color (BGR: (255, 255, 0)).
    cyan = (255, 255, 0)
    
    # Draw diagonal lines for actual coordinates.
    cv2.line(frame, actual_positions["left_arm"], actual_positions["right_leg"], cyan, 2)
    cv2.line(frame, actual_positions["right_arm"], actual_positions["left_leg"], cyan, 2)
    
    # Draw diagonal lines for expected coordinates.
    cv2.line(frame, expected_positions["left_arm"], expected_positions["right_leg"], cyan, 2)
    cv2.line(frame, expected_positions["right_arm"], expected_positions["left_leg"], cyan, 2)
    
    return frame
