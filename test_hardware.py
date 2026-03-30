
import sys
import time


# ─── Servo test ───────────────────────────────────────────────────────────────
def test_servos() -> bool:
    print("\n── Servo Test (PCA9685) ──────────────────────────────────")
    try:
        from adafruit_servokit import ServoKit
        kit = ServoKit(channels=16)
        print("✓  PCA9685 detected on I2C bus.")

        channels = {0: "Jaw", 1: "Neck", 2: "Eye UD", 3: "Eye LR"}
        for ch, name in channels.items():
            print(f"   Testing CH {ch}  ({name}) …", end=" ", flush=True)
            for angle in (45, 90, 135, 90):
                kit.servo[ch].angle = angle
                time.sleep(0.5)
            print("✓")

        print("✓  All servo channels OK.\n")
        return True
    except Exception as exc:
        print(f"\n✗  Servo test failed: {exc}")
        print("   Check: i2cdetect -y 1  (expect 0x40)")
        return False


# ─── Audio output test ────────────────────────────────────────────────────────
def test_audio_output() -> bool:
    print("── Audio Output Test ─────────────────────────────────────")
    try:
        import pygame
        pygame.init()
        pygame.mixer.init()

        from gtts import gTTS
        import tempfile, os

        tts = gTTS("Audio output test successful.", lang="en")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            path = f.name
        tts.save(path)

        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        os.remove(path)
        pygame.quit()
        print("✓  Speaker output OK.\n")
        return True
    except Exception as exc:
        print(f"✗  Audio output failed: {exc}\n")
        return False


# ─── Microphone test ──────────────────────────────────────────────────────────
def test_microphone() -> bool:
    print("── Microphone Test ───────────────────────────────────────")
    try:
        import speech_recognition as sr
        rec = sr.Recognizer()
        print("   Say something now (5 s window) …")
        with sr.Microphone() as src:
            rec.adjust_for_ambient_noise(src, duration=0.5)
            audio = rec.listen(src, timeout=5, phrase_time_limit=4)
        text = rec.recognize_google(audio)
        print(f"✓  Heard: \"{text}\"\n")
        return True
    except Exception as exc:
        print(f"✗  Microphone test failed: {exc}\n")
        return False


# ─── Camera test ──────────────────────────────────────────────────────────────
def test_camera() -> bool:
    print("── Camera Test ───────────────────────────────────────────")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("Could not open camera at index 0.")
        ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            raise RuntimeError("Camera opened but failed to read a frame.")
        h, w = frame.shape[:2]
        print(f"✓  Camera OK  ({w}×{h} frame captured).\n")
        return True
    except Exception as exc:
        print(f"✗  Camera test failed: {exc}\n")
        return False


# ─── Gemini connectivity test ─────────────────────────────────────────────────
def test_gemini() -> bool:
    print("── Gemini API Test ───────────────────────────────────────")
    try:
        import os
        from google import genai
        key = os.getenv("GEMINI_API_KEY", "")
        if not key:
            raise EnvironmentError("GEMINI_API_KEY not set.")
        client = genai.Client(api_key=key)
        resp   = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents="Reply with exactly: OK"
        )
        reply = resp.text.strip()
        print(f"✓  Gemini responded: \"{reply}\"\n")
        return True
    except Exception as exc:
        print(f"✗  Gemini test failed: {exc}\n")
        return False


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Hardware Verification — Humanoid Robot")
    print("  NIT Jamshedpur  |  Ranjeet Kumar Gupta")
    print("=" * 60)

    results = {
        "Servos"  : test_servos(),
        "Audio"   : test_audio_output(),
        "Mic"     : test_microphone(),
        "Camera"  : test_camera(),
        "Gemini"  : test_gemini(),
    }

    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    all_ok = True
    for name, ok in results.items():
        status = "✓  PASS" if ok else "✗  FAIL"
        print(f"  {name:<10} {status}")
        if not ok:
            all_ok = False

    print("=" * 60)
    sys.exit(0 if all_ok else 1)
