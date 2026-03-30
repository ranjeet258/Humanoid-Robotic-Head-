

import threading
import time
from typing import Optional, Tuple

import cv2
from ultralytics import YOLO

from config import Config
from modules.servo_controller import ServoController
from utils.logger import get_logger

log = get_logger(__name__)


class VisionTracker:
    """Real-time person-tracking via YOLOv8-Nano and neck servo."""

    def __init__(self, servo: ServoController) -> None:
        log.info("Loading YOLOv8 model '%s' …", Config.YOLO_MODEL)
        self._model   = YOLO(Config.YOLO_MODEL)
        self._servo   = servo
        self._cap:    Optional[cv2.VideoCapture] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._frame_lock = threading.Lock()
        self._latest_frame = None
        log.info("VisionTracker ready.")

    # ──────────────────────────────────────────────────────────────────────
    # Public interface
    # ──────────────────────────────────────────────────────────────────────

    def start_tracking(self) -> None:
        """Open camera and begin the background tracking loop."""
        if self._running:
            return
        self._cap = self._open_camera()
        if self._cap is None:
            log.error("Cannot start tracking — camera unavailable.")
            return
        self._running = True
        self._thread  = threading.Thread(
            target=self._tracking_loop, daemon=True, name="VisionTracker"
        )
        self._thread.start()
        log.info("Tracking started.")

    def stop_tracking(self) -> None:
        """Stop the tracking loop and release the camera."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._cap:
            self._cap.release()
            self._cap = None
        log.info("Tracking stopped.")

    def get_frame(self) -> Optional[object]:
        """
        Return the most recent camera frame (OpenCV BGR ndarray), or None.
        Safe to call from any thread.
        """
        with self._frame_lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None

    def capture_snapshot(self) -> Optional[object]:
        """
        Capture a fresh single frame directly from the camera (bypasses
        the tracking loop — safe to call even when tracking is stopped).
        """
        cap = self._cap or self._open_camera()
        if cap is None:
            return None
        ok, frame = cap.read()
        if not self._cap:          # we opened it here, close it
            cap.release()
        return frame if ok else None

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    def _tracking_loop(self) -> None:
        frame_interval = 1.0 / Config.TRACK_FPS_TARGET

        while self._running and self._cap and self._cap.isOpened():
            t0 = time.monotonic()

            ok, frame = self._cap.read()
            if not ok:
                log.warning("Camera read failed — retrying …")
                time.sleep(0.1)
                continue

            # Store latest frame for snapshots
            with self._frame_lock:
                self._latest_frame = frame

            # Run YOLO inference
            person_cx = self._detect_person(frame)
            if person_cx is not None:
                self._servo.track_user(person_cx, frame.shape[1])

            # Throttle to target FPS
            elapsed = time.monotonic() - t0
            sleep_t = frame_interval - elapsed
            if sleep_t > 0:
                time.sleep(sleep_t)

    def _detect_person(self, frame) -> Optional[float]:
        """
        Run YOLOv8 on *frame*.
        Returns the X-centroid of the first detected person, or None.
        """
        try:
            results = self._model(frame, stream=True, verbose=False)
            for r in results:
                for box in r.boxes:
                    if int(box.cls[0]) == Config.PERSON_CLASS_ID:
                        x1, _, x2, _ = box.xyxy[0]
                        return float((x1 + x2) / 2)
        except Exception as exc:
            log.error("YOLO inference error: %s", exc)
        return None

    @staticmethod
    def _open_camera() -> Optional[cv2.VideoCapture]:
        cap = cv2.VideoCapture(Config.CAMERA_INDEX)
        if not cap.isOpened():
            log.error("Could not open camera at index %d.", Config.CAMERA_INDEX)
            return None
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  Config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.FRAME_HEIGHT)
        return cap
