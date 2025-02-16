# video_processing.py
import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose

def get_expected_coordinates(frame):
    """
    Process a frame from the YouTube video using MediaPipe Pose (static mode)
    to extract expected normalized coordinates for:
      - left_arm: point along the forearm (30% left elbow + 70% left wrist).
      - right_arm: point along the forearm (30% right elbow + 70% right wrist).
      - left_leg: point slightly above the left ankle.
      - right_leg: point slightly above the right ankle.
    
    Returns a dictionary of normalized (0–1) coordinates or None if any required
    landmark is not confidently detected.
    """
    with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)
        if not results.pose_landmarks:
            return None
        landmarks = results.pose_landmarks.landmark
        # Required landmarks: left elbow (13), left wrist (15),
        # right elbow (14), right wrist (16), left ankle (27), right ankle (28)
        required_indices = [13, 15, 14, 16, 27, 28]
        for idx in required_indices:
            if landmarks[idx].visibility < 0.5:
                return None
        left_elbow = landmarks[13]
        left_wrist = landmarks[15]
        right_elbow = landmarks[14]
        right_wrist = landmarks[16]
        left_arm_x = 0.3 * left_elbow.x + 0.7 * left_wrist.x
        left_arm_y = 0.3 * left_elbow.y + 0.7 * left_wrist.y
        right_arm_x = 0.3 * right_elbow.x + 0.7 * right_wrist.x
        right_arm_y = 0.3 * right_elbow.y + 0.7 * right_wrist.y
        left_ankle = landmarks[27]
        right_ankle = landmarks[28]
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
