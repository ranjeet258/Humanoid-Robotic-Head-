# modules/vision.py
import cv2
import time
import threading
from ultralytics import YOLO
import config

class RobotVision:
    def __init__(self):
        print("[Vision] Loading YOLOv8 Model...")
        self.model = YOLO(config.YOLO_MODEL_PATH)
        self.is_tracking = False
        self.camera_lock = threading.Lock()
        self.cap = None

    def get_frame(self):
        """Captures a single frame safely."""
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        ret, frame = cap.read()
        cap.release()
        if ret:
            return frame
        return None

    def start_tracking(self, motor_controller):
        """Starts the background tracking thread."""
        if self.is_tracking: return
        self.is_tracking = True
        t = threading.Thread(target=self._tracking_loop, args=(motor_controller,), daemon=True)
        t.start()

    def stop_tracking(self):
        self.is_tracking = False

    def _tracking_loop(self, motor):
        print("[Vision] Tracking Started.")
        while self.is_tracking:
            with self.camera_lock:
                frame = self.get_frame()
            
            if frame is None: continue

            # YOLO Inference
            results = self.model(frame, stream=True, verbose=False)
            
            for r in results:
                for box in r.boxes:
                    # Class 0 = Person
                    if int(box.cls[0]) == 0:
                        x1, y1, x2, y2 = box.xyxy[0]
                        center_x = (x1 + x2) / 2
                        
                        # Logic to turn neck
                        if center_x < 100: # Subject on Left
                            new_angle = max(10, motor.current_neck_angle - 5)
                            motor.move_neck(new_angle)
                        elif center_x > 220: # Subject on Right
                            new_angle = min(170, motor.current_neck_angle + 5)
                            motor.move_neck(new_angle)
                        break 
            time.sleep(0.1)