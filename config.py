# config.py
import RPi.GPIO as GPIO
import os
from dotenv import load_dotenv

# --- API KEYS ---
# REPLACE WITH YOUR ACTUAL KEY
load_dotenv() # Load variables from .env file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- GPIO PIN CONFIGURATION (BCM Mode) ---
PIN_JAW = 22
PIN_NECK = 27
PIN_EYE_UD = 23
PIN_EYE_LR = 17

# --- SERVO SETTINGS ---
SERVO_FREQ = 50

# --- PATHS ---
BEEP_SOUND_PATH = "beep.wav"  # Make sure this file exists in the folder
YOLO_MODEL_PATH = "yolov8n.pt"

# --- VISION SETTINGS ---
CAMERA_INDEX = 0
FRAME_WIDTH = 320
FRAME_HEIGHT = 240