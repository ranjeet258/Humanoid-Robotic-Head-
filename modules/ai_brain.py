
import base64
from typing import Optional

import cv2
from google import genai
from google.genai import types

from config import Config
from utils.logger import get_logger

log = get_logger(__name__)

# System instruction injected in every request to keep answers concise
_SYSTEM_INSTRUCTION = (
    "You are a friendly, conversational humanoid robot assistant. "
    "Always reply in ONE or TWO short sentences — direct and human-like. "
    "No bullet points, no headers, no long explanations."
)


class AIBrain:
    """Gemini-powered AI brain with text and vision capability."""

    def __init__(self) -> None:
        if not Config.GEMINI_API_KEY:
            raise EnvironmentError(
                "GEMINI_API_KEY is not set. "
                "Export it:  export GEMINI_API_KEY='your-key'"
            )
        self._client = genai.Client(api_key=Config.GEMINI_API_KEY)
        log.info("AIBrain connected to Gemini (%s).", Config.GEMINI_MODEL)

    # ──────────────────────────────────────────────────────────────────────
    # Public interface
    # ──────────────────────────────────────────────────────────────────────

    def ask(self, user_text: str) -> str:
        """
        Send a text prompt to Gemini and return a concise reply.
        Falls back gracefully on any API error.
        """
        log.debug("AIBrain.ask: %s", user_text)
        try:
            response = self._client.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=user_text,
                config=types.GenerateContentConfig(
                    system_instruction=_SYSTEM_INSTRUCTION,
                    max_output_tokens=120,
                    temperature=0.7,
                ),
            )
            return self._trim(self._extract_text(response))
        except Exception as exc:
            log.error("Gemini ask error: %s", exc)
            return "Sorry, I couldn't process that right now."

    def see_and_respond(self, frame, user_text: str = "Describe what you see.") -> str:
        """
        Send a camera frame (OpenCV BGR ndarray) + user question to Gemini
        and return a concise reply.
        """
        log.debug("AIBrain.see_and_respond: %s", user_text)
        try:
            jpeg_bytes = self._frame_to_jpeg(frame)
            if jpeg_bytes is None:
                return "I couldn't capture a clear image."

            b64_image = base64.b64encode(jpeg_bytes).decode("utf-8")

            response = self._client.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(
                        data=jpeg_bytes,
                        mime_type="image/jpeg",
                    ),
                    user_text,
                ],
                config=types.GenerateContentConfig(
                    system_instruction=_SYSTEM_INSTRUCTION,
                    max_output_tokens=120,
                    temperature=0.7,
                ),
            )
            return self._trim(self._extract_text(response))
        except Exception as exc:
            log.error("Gemini vision error: %s", exc)
            return "I'm having trouble seeing right now."

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_text(response) -> str:
        try:
            return response.text.strip()
        except Exception:
            return "I'm not sure how to answer that."

    @staticmethod
    def _trim(text: str) -> str:
        """
        Enforce MAX_RESPONSE_CHARS — cut at sentence boundary where possible.
        """
        if len(text) <= Config.MAX_RESPONSE_CHARS:
            return text
        # Try to cut at last sentence boundary within limit
        truncated = text[: Config.MAX_RESPONSE_CHARS]
        last_dot  = truncated.rfind(". ")
        if last_dot > 0:
            return truncated[: last_dot + 1]
        return truncated + "…"

    @staticmethod
    def _frame_to_jpeg(frame) -> Optional[bytes]:
        """Encode an OpenCV BGR frame as JPEG bytes."""
        try:
            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            return buf.tobytes() if ok else None
        except Exception as exc:
            log.error("Frame encode error: %s", exc)
            return None
