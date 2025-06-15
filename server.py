from flask import Flask, Response, jsonify
import cv2
import numpy as np
import mediapipe as mp
import time
import threading

from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ───────── 1. GAME STATE ─────────
game_state = {
    "success_count": 0,
    "fail_count": 0,
    "current_pose_idx": 0,
    "pose_start_time": None,
    "evaluation_period": 3,  # seconds
    "is_evaluating": False,
    "current_score": 0,
    "time_left": 0,
    "result": None,
    "frame": None,
    "running": False
}

# ───────── 2. POSE CONFIG ─────────
POSES = [
    {
        "name": "RAISE_HANDS",
        "angles": [
            {"points": ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"),  "target": 180, "weight": 0.5},
            {"points": ("RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"), "target": 180, "weight": 0.5},
        ],
        "threshold": 70
    },
    {
        "name": "SIU",
        "angles": [
            {"points": ("LEFT_ELBOW", "LEFT_SHOULDER", "LEFT_HIP"),  "target": 45, "weight": 0.5},
            {"points": ("RIGHT_ELBOW", "RIGHT_SHOULDER", "RIGHT_HIP"), "target": 45, "weight": 0.5},
        ],
        "threshold": 70
    },
    {
        "name": "DOG_POSE",
        "angles": [
            {"points": ("LEFT_SHOULDER", "LEFT_WRIST", "LEFT_ELBOW"), "target": 180, "weight": 0.5},
            {"points": ("LEFT_SHOULDER", "LEFT_HIP",   "LEFT_KNEE"), "target": 135, "weight": 0.5},
        ],
        "threshold": 70
    },
    {
        "name": "MON_POSE",
        "angles": [
            {"points": ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"), "target": 45, "weight": 0.5},
            {"points": ("RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"), "target": 45, "weight": 0.5},
        ],
        "threshold": 70
    },
    {
        "name": "FLEXING",
        "angles": [
            {"points": ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"), "target": 180, "weight": 0.5},
            {"points": ("RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"), "target": 80,  "weight": 0.5},
        ],
        "threshold": 70
    },
    {
        "name": "ABSOLUTE",
        "angles": [
            {"points": ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"), "target": 90, "weight": 0.5},
            {"points": ("RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"), "target": 90, "weight": 0.5},
        ],
        "threshold": 70
    },
    {
        "name": "DYNAMIC",
        "angles": [
            {"points": ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"), "target": 90, "weight": 0.5},
            {"points": ("RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"), "target": 90, "weight": 0.5},
        ],
        "threshold": 70
    },
    {
        "name": "KAWAII",
        "angles": [
            {"points": ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"), "target": 45, "weight": 0.5},
            {"points": ("RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"), "target": 160, "weight": 0.5},
        ],
        "threshold": 70
    },
    {
        "name": "KHABY_LAME",
        "angles": [
            {"points": ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"), "target": 135, "weight": 0.5},
            {"points": ("RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"), "target": 135, "weight": 0.5},
        ],
        "threshold": 70
    },
    {
        "name": "MON_POSE2",
        "angles": [
            {"points": ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"), "target": 180,  "weight": 0.5},
            {"points": ("RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"), "target": 80,  "weight": 0.5},
        ],
        "threshold": 70
    }
]

# ───────── 3. MEDIAPIPE SETUP ─────────
mp_drawing = mp.solutions.drawing_utils
mp_pose    = mp.solutions.pose


def calculate_angle(a, b, c):
    """
    Compute the interior angle ABC (in degrees), guaranteed in [0, 180].
    """
    a, b, c = np.array(a), np.array(b), np.array(c)
    v1 = a - b
    v2 = c - b
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1)*np.linalg.norm(v2) + 1e-6)
    return np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))


def evaluate_pose(landmarks, pose_cfg):
    """
    Returns a 0–100% score indicating how closely the user's pose matches pose_cfg.
    Normalizes by sum of visible-angle weights and maps angle error → [0…1].
    """
    total_score  = 0.0
    total_weight = 0.0

    for ang in pose_cfg["angles"]:
        A, B, C = ang["points"]
        idxA = getattr(mp_pose.PoseLandmark, A).value
        idxB = getattr(mp_pose.PoseLandmark, B).value
        idxC = getattr(mp_pose.PoseLandmark, C).value

        # skip if any joint is not sufficiently visible
        if (landmarks[idxA].visibility < 0.5 or
            landmarks[idxB].visibility < 0.5 or
            landmarks[idxC].visibility < 0.5):
            continue

        ptA = (landmarks[idxA].x, landmarks[idxA].y)
        ptB = (landmarks[idxB].x, landmarks[idxB].y)
        ptC = (landmarks[idxC].x, landmarks[idxC].y)

        measured = calculate_angle(ptA, ptB, ptC)
        error    = abs(measured - ang["target"])

        # map error [0..180] → score [1..0]
        score_i = max(0.0, 1.0 - error/180.0)
        w       = ang.get("weight", 1.0)

        total_score  += score_i * w
        total_weight += w

    if total_weight == 0:
        return 0.0

    return (total_score / total_weight) * 100.0


def process_frame():
    cap = cv2.VideoCapture(0)
    with mp_pose.Pose(min_detection_confidence=0.5,
                      min_tracking_confidence=0.5) as pose:
        while game_state["running"] and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (640, 480))
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            now = time.time()
            if game_state["is_evaluating"]:
                elapsed = now - game_state["pose_start_time"]
                game_state["time_left"] = max(0,
                    game_state["evaluation_period"] - elapsed)

                # time to finalize this pose
                if elapsed > game_state["evaluation_period"]:
                    game_state["is_evaluating"] = False
                    cfg = POSES[game_state["current_pose_idx"]]

                    if results.pose_landmarks:
                        lm    = results.pose_landmarks.landmark
                        score = evaluate_pose(lm, cfg)
                    else:
                        score = 0.0

                    if score >= cfg["threshold"]:
                        game_state["success_count"] += 1
                        game_state["result"] = "SUCCESS!"
                    else:
                        game_state["fail_count"] += 1
                        game_state["result"] = "FAIL!"

                    # advance to next pose
                    game_state["current_pose_idx"] = (
                        game_state["current_pose_idx"] + 1
                    ) % len(POSES)

                    # Check if we've gone through all poses
                    if game_state["current_pose_idx"] == 0:
                        game_state["running"] = False
                        break

                    game_state["pose_start_time"] = now
                    game_state["is_evaluating"] = True

            # live update of current_score while counting down
            if game_state["is_evaluating"] and results.pose_landmarks:
                lm = results.pose_landmarks.landmark
                cfg = POSES[game_state["current_pose_idx"]]
                game_state["current_score"] = evaluate_pose(lm, cfg)
            else:
                game_state["current_score"] = 0.0

            # draw landmarks
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(245,117,66),
                                           thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(245,66,230),
                                           thickness=2, circle_radius=2)
                )

            _, buf = cv2.imencode('.jpg', image,
                                  [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            game_state["frame"] = buf.tobytes()

    cap.release()


def generate_frames():
    while game_state["running"]:
        if game_state["frame"]:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   game_state["frame"] + b'\r\n')
        time.sleep(0.03)


@app.route('/start_game', methods=['POST'])
def start_game():
    game_state.update({
        "success_count": 0,
        "fail_count": 0,
        "current_pose_idx": 0,
        "pose_start_time": time.time(),
        "is_evaluating": True,
        "current_score": 0,
        "time_left": game_state["evaluation_period"],
        "result": None,
        "running": True
    })
    threading.Thread(target=process_frame, daemon=True).start()
    return jsonify(status="Game started")


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/game_state')
def get_state():
    cfg = POSES[game_state["current_pose_idx"]]
    return jsonify({
        "current_pose":   cfg["name"],
        "current_score":  game_state["current_score"],
        "time_left":      game_state["time_left"],
        "success_count":  game_state["success_count"],
        "fail_count":     game_state["fail_count"],
        "result":         game_state["result"],
        "is_evaluating":  game_state["is_evaluating"]
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
