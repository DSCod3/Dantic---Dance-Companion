# coordinate_overlays.py
import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)

def get_pose_coordinates(frame):
    """
    Process the frame (BGR image) using MediaPipe Pose (video mode) to extract normalized coordinates.
    Returns a dictionary with keys 'left_arm', 'right_arm', 'left_leg', 'right_leg' or None.
    """
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)
    if not results.pose_landmarks:
        return None
    landmarks = results.pose_landmarks.landmark
    left_elbow = landmarks[13]
    left_wrist = landmarks[15]
    right_elbow = landmarks[14]
    right_wrist = landmarks[16]
    left_ankle = landmarks[27]
    right_ankle = landmarks[28]
    left_arm_x = 0.3 * left_elbow.x + 0.7 * left_wrist.x
    left_arm_y = 0.3 * left_elbow.y + 0.7 * left_wrist.y
    right_arm_x = 0.3 * right_elbow.x + 0.7 * right_wrist.x
    right_arm_y = 0.3 * right_elbow.y + 0.7 * right_wrist.y
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
    Draw overlay dots and diagonal lines on the frame.
    - For the expected video, if you pass the same dictionary for actual and expected, the dots will be red.
    - For the live webcam, actual (live) coordinates are drawn in green and expected (from video) in red.
    Diagonal lines (cyan) connect left_arm to right_leg and right_arm to left_leg for both.
    """
    height, width, _ = frame.shape
    def norm_to_pix(coord):
        return (int(coord[0] * width), int(coord[1] * height))
    if actual_coords is None or expected_coords is None:
        return frame
    actual_positions = {k: norm_to_pix(v) for k, v in actual_coords.items()}
    expected_positions = {k: norm_to_pix(v) for k, v in expected_coords.items()}
    # Draw actual positions (green)
    for pos in actual_positions.values():
        cv2.circle(frame, pos, 8, (0, 255, 0), -1)
    # Draw expected positions (red)
    for pos in expected_positions.values():
        cv2.circle(frame, pos, 8, (0, 0, 255), -1)
    cyan = (255, 255, 0)
    cv2.line(frame, actual_positions["left_arm"], actual_positions["right_leg"], cyan, 2)
    cv2.line(frame, actual_positions["right_arm"], actual_positions["left_leg"], cyan, 2)
    cv2.line(frame, expected_positions["left_arm"], expected_positions["right_leg"], cyan, 2)
    cv2.line(frame, expected_positions["right_arm"], expected_positions["left_leg"], cyan, 2)
    return frame
