
import threading
import time
from typing import Optional

from adafruit_servokit import ServoKit

from config import Config
from utils.logger import get_logger

log = get_logger(__name__)


class ServoController:
    """Thread-safe PCA9685 servo manager."""

    def __init__(self) -> None:
        try:
            self._kit = ServoKit(channels=Config.PCA9685_CHANNELS)
            self._lock = threading.Lock()
            self._reset_all()
            log.info("PCA9685 servo controller ready  (I2C @ 0x40)")
        except Exception as exc:
            log.error("PCA9685 init failed: %s", exc)
            raise

    # ──────────────────────────────────────────────────────────────────────
    # Public interface
    # ──────────────────────────────────────────────────────────────────────

    def set_angle(self, channel: int, angle: int, *, settle: bool = True) -> None:
        """
        Drive a servo to *angle* degrees (0–180).
        If *settle* is True, sleep Config.SERVO_SETTLE to let the motor reach position.
        """
        angle = max(0, min(180, int(angle)))
        with self._lock:
            try:
                self._kit.servo[channel].angle = angle
            except Exception as exc:
                log.error("set_angle ch=%d err: %s", channel, exc)
                return
        if settle:
            time.sleep(Config.SERVO_SETTLE)

    def smooth_move(self, channel: int, start: int, end: int,
                    steps: int = 10, step_delay: float = 0.02) -> None:
        """Interpolate smoothly from *start* to *end* degrees."""
        step_size = (end - start) / max(steps, 1)
        for i in range(steps + 1):
            self.set_angle(channel, int(start + step_size * i), settle=False)
            time.sleep(step_delay)

    def animate_jaw(self, stop_event: threading.Event) -> None:
        """
        Oscillate jaw between OPEN and CLOSED while *stop_event* is not set.
        Resets jaw to JAW_REST on exit — always called in a daemon thread.
        """
        try:
            while not stop_event.is_set():
                for angle in (Config.JAW_OPEN, Config.JAW_CLOSED):
                    if stop_event.is_set():
                        break
                    self.set_angle(Config.JAW_CH, angle, settle=False)
                    time.sleep(Config.JAW_STEP_DELAY)
        finally:
            self.set_angle(Config.JAW_CH, Config.JAW_REST, settle=False)

    def blink(self, times: int = 2) -> None:
        """Simulate an eye blink via the EYE_UD servo (cosmetic)."""
        for _ in range(times):
            self.set_angle(Config.EYE_UD_CH, Config.EYE_DOWN, settle=False)
            time.sleep(Config.BLINK_SPEED)
            self.set_angle(Config.EYE_UD_CH, Config.EYE_CENTER, settle=False)
            time.sleep(Config.BLINK_SPEED)

    def look(self, direction: str) -> None:
        """
        Move neck/eyes to a named direction.
        Valid: 'left', 'right', 'up', 'down', 'center'
        """
        d = direction.lower().strip()
        if d == "left":
            self.set_angle(Config.NECK_CH, Config.NECK_LEFT)
            self.set_angle(Config.EYE_LR_CH, Config.EYE_LEFT)
        elif d == "right":
            self.set_angle(Config.NECK_CH, Config.NECK_RIGHT)
            self.set_angle(Config.EYE_LR_CH, Config.EYE_RIGHT)
        elif d == "up":
            self.set_angle(Config.EYE_UD_CH, Config.EYE_UP)
        elif d == "down":
            self.set_angle(Config.EYE_UD_CH, Config.EYE_DOWN)
        elif d == "center":
            self._reset_all()
        else:
            log.warning("Unknown direction: '%s'", direction)

    def track_user(self, center_x: float, frame_width: float) -> None:
        """
        Adjust neck servo so the robot faces the detected user.
        *center_x* is the bounding-box centroid X in pixels;
        *frame_width* is the total width of the camera frame.
        Dead-band: ±10 % of frame_width → no movement.
        """
        offset = center_x - (frame_width / 2)
        dead_band = frame_width * 0.10

        if abs(offset) < dead_band:
            return

        with self._lock:
            try:
                current = self._kit.servo[Config.NECK_CH].angle or Config.NECK_CENTER
            except Exception:
                current = Config.NECK_CENTER

        step = 5 if offset > 0 else -5
        new_angle = max(Config.NECK_LEFT, min(Config.NECK_RIGHT, int(current) + step))
        self.set_angle(Config.NECK_CH, new_angle, settle=False)

    def cleanup(self) -> None:
        """Return all servos to neutral on shutdown."""
        self._reset_all()
        log.info("Servos reset to neutral.")

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    def _reset_all(self) -> None:
        for ch, angle in (
            (Config.JAW_CH,    Config.JAW_REST),
            (Config.NECK_CH,   Config.NECK_CENTER),
            (Config.EYE_UD_CH, Config.EYE_CENTER),
            (Config.EYE_LR_CH, Config.EYE_CENTER),
        ):
            try:
                self._kit.servo[ch].angle = angle
            except Exception as exc:
                log.warning("reset ch=%d failed: %s", ch, exc)
        time.sleep(0.1)
