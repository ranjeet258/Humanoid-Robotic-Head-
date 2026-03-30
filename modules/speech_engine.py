
import threading
from typing import Optional

import speech_recognition as sr

from config import Config
from utils.logger import get_logger

log = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Full Speech Engine
# ─────────────────────────────────────────────────────────────────────────────

class SpeechEngine:
    """
    Listens on the default microphone and returns recognised text using
    Google Speech-to-Text over HTTPS.
    """

    def __init__(self) -> None:
        self._rec = sr.Recognizer()
        self._rec.energy_threshold         = Config.ENERGY_THRESHOLD
        self._rec.dynamic_energy_threshold = True
        log.info("SpeechEngine ready.")

    def listen(self) -> Optional[str]:
        """
        Block until the user speaks (or *LISTEN_TIMEOUT* elapses).
        Returns lower-cased text, or None on silence / failure.
        """
        try:
            with sr.Microphone() as src:
                self._rec.adjust_for_ambient_noise(
                    src, duration=Config.NOISE_ADJUST_DURATION)
                log.info("🎤  Listening …")
                audio = self._rec.listen(
                    src,
                    timeout=Config.LISTEN_TIMEOUT,
                    phrase_time_limit=Config.PHRASE_TIME_LIMIT,
                )

            text = self._rec.recognize_google(audio)
            log.info("User said: \"%s\"", text)
            return text.lower()

        except sr.WaitTimeoutError:
            log.debug("Listen timeout — no speech detected.")
        except sr.UnknownValueError:
            log.debug("Could not understand audio.")
        except sr.RequestError as exc:
            log.error("Google STT request failed: %s", exc)
        except Exception as exc:
            log.error("Unexpected listen error: %s", exc)

        return None


# ─────────────────────────────────────────────────────────────────────────────
# Interrupt Sensor
# ─────────────────────────────────────────────────────────────────────────────

class InterruptSensor:
    """
    Rapidly polls the microphone for loud sound energy while the robot is
    speaking.  When energy exceeds INTERRUPT_ENERGY, it sets the provided
    threading.Event so the robot stops mid-sentence.

    Usage::
        sensor = InterruptSensor()
        event  = threading.Event()
        sensor.start(event)
        …
        sensor.stop()
    """

    def __init__(self) -> None:
        self._rec = sr.Recognizer()
        self._rec.energy_threshold         = Config.INTERRUPT_ENERGY
        self._rec.dynamic_energy_threshold = False
        self._thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()

    def start(self, interrupt_event: threading.Event) -> None:
        """Begin background polling. Sets *interrupt_event* if speech detected."""
        self._stop_flag.clear()
        self._thread = threading.Thread(
            target=self._poll,
            args=(interrupt_event,),
            daemon=True,
            name="InterruptSensor",
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop polling and wait for the background thread to exit."""
        self._stop_flag.set()
        if self._thread:
            self._thread.join(timeout=1.0)

    # ── private ──────────────────────────────────────────────────────────

    def _poll(self, interrupt_event: threading.Event) -> None:
        while not self._stop_flag.is_set():
            if self._detect_energy():
                log.info("⚠️   Interrupt detected — user is speaking.")
                interrupt_event.set()
                return

    def _detect_energy(self) -> bool:
        """True if the microphone captures speech-level energy briefly."""
        try:
            with sr.Microphone() as src:
                # Very short sample — purely energy-based, not full STT
                audio = self._rec.listen(
                    src, timeout=Config.INTERRUPT_INTERVAL, phrase_time_limit=0.5
                )
            return True
        except (sr.WaitTimeoutError, Exception):
            return False
