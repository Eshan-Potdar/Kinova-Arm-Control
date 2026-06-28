import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import socket
import json
import urllib.request
import os

UBUNTU_IP = "192.168.64.6"  # Replace with your Ubuntu VM's IP (run 'hostname -I' on Ubuntu)
PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

model_path = os.path.expanduser('~/hand_landmarker.task')
if not os.path.exists(model_path):
    print("Downloading hand detection model...")
    urllib.request.urlretrieve(
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
        model_path
    )
    print("Downloaded!")

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.IMAGE,
    num_hands=1)

cap = cv2.VideoCapture(0)
print(f"Hand tracker running - sending to Ubuntu at {UBUNTU_IP}:{PORT}")

with HandLandmarker.create_from_options(options) as landmarker:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect(mp_image)

        if result.hand_landmarks:
            landmarks = result.hand_landmarks[0]
            wrist = landmarks[0]
            index_tip = landmarks[8]
            thumb_tip = landmarks[4]

            x = (0.5 - wrist.x) * 0.6
            y = 0.4
            z = (0.5 - wrist.y) * 0.4 + 0.3

            distance = abs(index_tip.x - thumb_tip.x) + abs(index_tip.y - thumb_tip.y)
            grip = distance < 0.05

            data = json.dumps({"x": x, "y": y, "z": z, "grip": grip})
            sock.sendto(data.encode(), (UBUNTU_IP, PORT))
            print(f"Sending: x={x:.2f} z={z:.2f} grip={grip}")

        cv2.imshow("Hand Tracker - Mac", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
