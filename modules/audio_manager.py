
import os
import tempfile
import threading
import time
from contextlib import contextmanager
from typing import Optional

import pygame
from gtts import gTTS

from config import Config
from utils.logger import get_logger

log = get_logger(__name__)


class AudioManager:
    """Centralised audio manager: TTS, playback, beep."""

    def __init__(self) -> None:
        pygame.init()
        pygame.mixer.init()
        self._beep: Optional[pygame.mixer.Sound] = self._load_beep()
        log.info("AudioManager ready.")

    # ──────────────────────────────────────────────────────────────────────
    # Public interface
    # ──────────────────────────────────────────────────────────────────────

    def play_beep(self) -> None:
        """Play the pre-loaded beep sound (≈5 ms latency)."""
        if self._beep:
            try:
                self._beep.play()
                time.sleep(Config.BEEP_DURATION)
            except Exception as exc:
                log.warning("Beep playback error: %s", exc)

    def play_audio(self,
                   audio_path: str,
                   interrupt_event: Optional[threading.Event] = None) -> None:
        """
        Play *audio_path* via pygame.
        Stops immediately if *interrupt_event* is set while playing.
        """
        try:
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            clock = pygame.time.Clock()

            while pygame.mixer.music.get_busy():
                if interrupt_event and interrupt_event.is_set():
                    pygame.mixer.music.stop()
                    log.info("Audio interrupted by user.")
                    return
                clock.tick(30)
        except Exception as exc:
            log.error("Audio playback error: %s", exc)

    def stop(self) -> None:
        """Stop whatever is playing right now."""
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def is_playing(self) -> bool:
        """Return True while audio is actively playing."""
        try:
            return bool(pygame.mixer.music.get_busy())
        except Exception:
            return False

    @contextmanager
    def tts_file(self, text: str, lang: str = "", tld: str = ""):
        """
        Context manager that synthesises *text* to a temporary MP3 and
        yields the file path.  The file is deleted on exit — even on error.

        Usage::
            with audio.tts_file("Hello!") as path:
                audio.play_audio(path)
        """
        lang = lang or Config.DEFAULT_LANG
        tld  = tld  or Config.DEFAULT_TLD
        tmp: Optional[str] = None
        try:
            tts = gTTS(text=text, lang=lang, tld=tld)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                tmp = f.name
            tts.save(tmp)
            yield tmp
        except Exception as exc:
            log.error("TTS synthesis error: %s", exc)
            yield None                         # caller must handle None gracefully
        finally:
            if tmp and os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError as exc:
                    log.warning("Could not delete temp MP3: %s", exc)

    def cleanup(self) -> None:
        """Release pygame resources."""
        try:
            pygame.quit()
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    def _load_beep(self) -> Optional[pygame.mixer.Sound]:
        try:
            sound = pygame.mixer.Sound(Config.BEEP_PATH)
            log.debug("Beep sound loaded from '%s'.", Config.BEEP_PATH)
            return sound
        except Exception as exc:
            log.warning("Beep sound not found (%s). Continuing without it.", exc)
            return None
