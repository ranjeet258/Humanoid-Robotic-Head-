
import os


class Config:
    # ─────────────────────────────────────────────────────────────────────
    # API / Model
    # ─────────────────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL:   str = "models/gemini-2.5-flash"

    # ─────────────────────────────────────────────────────────────────────
    # PCA9685 — I2C PWM Servo Driver
    # ─────────────────────────────────────────────────────────────────────
    PCA9685_CHANNELS: int = 16          # Total channels on the board

    # Servo channel assignments  (0 – 15)
    JAW_CH:    int = 0
    NECK_CH:   int = 1
    EYE_UD_CH: int = 2   # Up / Down
    EYE_LR_CH: int = 3   # Left / Right

    # ─────────────────────────────────────────────────────────────────────
    # Servo Angles  (degrees, 0 – 180)
    # ─────────────────────────────────────────────────────────────────────
    JAW_OPEN:   int = 115
    JAW_CLOSED: int = 80
    JAW_REST:   int = 100

    NECK_LEFT:    int = 70
    NECK_RIGHT:   int = 110
    NECK_CENTER:  int = 90

    EYE_UP:     int = 70
    EYE_DOWN:   int = 110
    EYE_LEFT:   int = 70
    EYE_RIGHT:  int = 110
    EYE_CENTER: int = 90

    # ─────────────────────────────────────────────────────────────────────
    # Timing  (seconds)
    # ─────────────────────────────────────────────────────────────────────
    SERVO_SETTLE:    float = 0.20   # Time after angle command
    JAW_STEP_DELAY:  float = 0.15   # Jaw open/close cycle half-period
    BLINK_SPEED:     float = 0.10   # Eye blink half-period
    BEEP_DURATION:   float = 0.30   # Duration to wait after beep

    # ─────────────────────────────────────────────────────────────────────
    # Speech Recognition
    # ─────────────────────────────────────────────────────────────────────
    LISTEN_TIMEOUT:       float = 6.0   # Max seconds waiting for speech to begin
    PHRASE_TIME_LIMIT:    float = 12.0  # Max seconds for a single utterance
    ENERGY_THRESHOLD:     int   = 4000  # Ambient-noise calibration baseline
    NOISE_ADJUST_DURATION: float = 0.3  # Ambient-noise sample duration

    # Interrupt detection
    INTERRUPT_ENERGY:   int   = 1000   # Lower = more sensitive
    INTERRUPT_INTERVAL: float = 0.25   # Poll interval while robot speaks

    # ─────────────────────────────────────────────────────────────────────
    # AI Response
    # ─────────────────────────────────────────────────────────────────────
    MAX_RESPONSE_CHARS: int = 200       # Hard-trim after this many characters
    SIMILARITY_THRESHOLD: float = 0.60  # Fuzzy-match threshold for commands

    # ─────────────────────────────────────────────────────────────────────
    # Vision / YOLOv8
    # ─────────────────────────────────────────────────────────────────────
    YOLO_MODEL:      str = "yolov8n.pt"   # Nano model — fastest on Pi 5
    CAMERA_INDEX:    int = 0
    FRAME_WIDTH:     int = 320
    FRAME_HEIGHT:    int = 240
    TRACK_FPS_TARGET: float = 15.0       # Target tracking loop FPS
    PERSON_CLASS_ID: int = 0             # COCO class index for "person"

    # ─────────────────────────────────────────────────────────────────────
    # Audio Paths
    # ─────────────────────────────────────────────────────────────────────
    BEEP_PATH: str = "/home/ranjeet/beep.wav"

    # ─────────────────────────────────────────────────────────────────────
    # TTS Personalities
    # ─────────────────────────────────────────────────────────────────────
    # Each entry: trigger_keyword → (greeting, lang_code, tld)
    PERSONALITIES: dict = {
        "krishna": ("Hi, I'm Krishna. Ask me anything!", "en", "co.in"),
        "maya":    ("Hi, I'm Maya. How can I help you today?", "en", "co.uk"),
        "alex":    ("Hey! I'm Alex. What's on your mind?",    "en", "com.au"),
    }

    # ─────────────────────────────────────────────────────────────────────
    # Default TTS voice
    # ─────────────────────────────────────────────────────────────────────
    DEFAULT_LANG: str = "en"
    DEFAULT_TLD:  str = "com"

    # ─────────────────────────────────────────────────────────────────────
    # Logging
    # ─────────────────────────────────────────────────────────────────────
    LOG_LEVEL:  str = "INFO"
    LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
    LOG_FILE:   str = "/home/ranjeet/robot.log"     # Set "" to disable file log
