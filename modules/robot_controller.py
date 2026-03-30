
import threading
import time
from difflib import SequenceMatcher
from typing import Optional, Tuple

from config import Config
from modules.servo_controller  import ServoController
from modules.audio_manager     import AudioManager
from modules.speech_engine     import SpeechEngine, InterruptSensor
from modules.ai_brain          import AIBrain
from modules.vision_tracker    import VisionTracker
from utils.logger              import get_logger

log = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Command routing tables
# ─────────────────────────────────────────────────────────────────────────────

# Movement commands:  list-of-trigger-phrases → (direction, spoken_reply)
_MOVEMENTS: list[Tuple[Tuple[str, ...], str, str]] = [
    (("turn left",   "look left",  "face left"),  "left",   "Turning left."),
    (("turn right",  "look right", "face right"), "right",  "Turning right."),
    (("look up",     "eyes up"),                  "up",     "Looking up."),
    (("look down",   "eyes down"),                "down",   "Looking down."),
    (("look straight", "face forward", "look forward",
      "center",      "reset",       "neutral"),   "center", "Back to center."),
]

# Exit phrases
_EXIT_PHRASES = ("exit", "quit", "goodbye", "bye", "shutdown", "power off")

# FAQ map:  trigger-phrase → reply
_FAQ: dict[str, str] = {
    "introduce yourself":
        "I'm a humanoid robotic head built by Ranjeet Gupta at NIT Jamshedpur.",
    "what can you do":
        "I can talk, answer questions, track faces, and describe what I see.",
    "who made you":
        "I was developed by Ranjeet Gupta under Dr Vijay Kumar Dalla's mentorship.",
    "who created you":
        "Ranjeet Kumar Gupta at NIT Jamshedpur — with a lot of soldering!",
    "how are you":
        "Running great, thanks for asking!",
    "what is your name":
        "I'm a humanoid robot. You can give me any name you like.",
    "stop tracking":
        None,        # handled specially — stops vision thread
}

# Vision triggers
_SEE_TRIGGERS = ("what do you see", "what can you see",
                 "describe what you see", "look around", "what is in front")


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _fuzzy_match(text: str, phrases: Tuple[str, ...]) -> bool:
    """True if any phrase is a substring of text, OR similarity ≥ threshold."""
    for phrase in phrases:
        if phrase in text:
            return True
        if _similarity(text, phrase) >= Config.SIMILARITY_THRESHOLD:
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# HumanoidRobot
# ─────────────────────────────────────────────────────────────────────────────

class HumanoidRobot:
    """Full-stack humanoid robot controller."""

    def __init__(self) -> None:
        log.info("Initialising humanoid robot …")

        self._servo    = ServoController()
        self._audio    = AudioManager()
        self._speech   = SpeechEngine()
        self._ai       = AIBrain()
        self._vision   = VisionTracker(self._servo)
        self._sensor   = InterruptSensor()

        self._lang = Config.DEFAULT_LANG
        self._tld  = Config.DEFAULT_TLD

        log.info("All subsystems online.")

    # ──────────────────────────────────────────────────────────────────────
    # Main loop
    # ──────────────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start vision tracking, greet, then enter the interaction loop."""
        self._vision.start_tracking()
        self.speak("System online. Hi Ranjeet! I'm ready. Speak after the beep.")

        try:
            while True:
                self._audio.play_beep()
                user_text = self._speech.listen()

                if not user_text:
                    continue

                if not self._route(user_text):
                    break   # exit command received

        except KeyboardInterrupt:
            log.info("KeyboardInterrupt — shutting down.")
        finally:
            self.shutdown()

    # ──────────────────────────────────────────────────────────────────────
    # Command router
    # ──────────────────────────────────────────────────────────────────────

    def _route(self, text: str) -> bool:
        """
        Dispatch *text* to the appropriate handler.
        Returns False if the robot should exit, True to continue.
        """
        # ── Exit? ──────────────────────────────────────────────────────
        if any(cmd in text for cmd in _EXIT_PHRASES):
            self.speak("Goodbye! Have a great day.")
            return False

        # ── Personality switch? ────────────────────────────────────────
        for kw, (greeting, lang, tld) in Config.PERSONALITIES.items():
            if kw in text:
                self._lang = lang
                self._tld  = tld
                self.speak(greeting, lang=lang, tld=tld)
                return True

        # ── Movement command? ──────────────────────────────────────────
        for triggers, direction, reply in _MOVEMENTS:
            if _fuzzy_match(text, triggers):
                self._servo.look(direction)
                self.speak(reply)
                return True

        # ── Vision query? ──────────────────────────────────────────────
        if any(t in text for t in _SEE_TRIGGERS):
            frame = self._vision.get_frame()
            if frame is not None:
                reply = self._ai.see_and_respond(frame, text)
            else:
                reply = "I couldn't capture an image right now."
            self.speak(reply)
            return True

        # ── Stop tracking? ─────────────────────────────────────────────
        if "stop tracking" in text:
            self._vision.stop_tracking()
            self.speak("Face tracking stopped.")
            return True

        if "start tracking" in text or "track me" in text:
            self._vision.start_tracking()
            self.speak("Face tracking started.")
            return True

        # ── FAQ? ───────────────────────────────────────────────────────
        for trigger, reply in _FAQ.items():
            if trigger in text:
                if reply:
                    self.speak(reply)
                return True

        # ── General AI question ────────────────────────────────────────
        reply = self._ai.ask(text)
        self.speak(reply)
        return True

    # ──────────────────────────────────────────────────────────────────────
    # Speak  — TTS + jaw animation + interrupt detection
    # ──────────────────────────────────────────────────────────────────────

    def speak(self, text: str,
              lang: Optional[str] = None,
              tld:  Optional[str] = None) -> None:
        """
        Synthesise *text* to speech and play it with:
          • Jaw animation (thread-safe, daemon thread)
          • Interrupt detection (stops audio if user speaks)
        """
        if not text:
            return

        lang = lang or self._lang
        tld  = tld  or self._tld

        log.info("Robot: %s", text)
        interrupt_event = threading.Event()

        with self._audio.tts_file(text, lang=lang, tld=tld) as audio_path:
            if audio_path is None:
                log.error("TTS returned no file — skipping speech.")
                return

            # Start jaw animation
            jaw_stop = threading.Event()
            jaw_thread = threading.Thread(
                target=self._servo.animate_jaw,
                args=(jaw_stop,),
                daemon=True,
                name="JawAnimation",
            )
            jaw_thread.start()

            # Start interrupt sensor
            self._sensor.start(interrupt_event)

            try:
                self._audio.play_audio(audio_path, interrupt_event)
            finally:
                jaw_stop.set()
                self._sensor.stop()
                jaw_thread.join(timeout=1.5)

    # ──────────────────────────────────────────────────────────────────────
    # Shutdown
    # ──────────────────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        """Release all hardware and software resources cleanly."""
        log.info("Shutting down …")
        self._vision.stop_tracking()
        self._servo.cleanup()
        self._audio.cleanup()
        log.info("Shutdown complete.")
