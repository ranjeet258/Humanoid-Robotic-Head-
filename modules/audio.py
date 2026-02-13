# modules/audio.py
import os
import speech_recognition as sr
from gtts import gTTS
import pygame
import threading
import tempfile
import config

class RobotAudio:
    def __init__(self):
        pygame.mixer.init()
        self.recognizer = sr.Recognizer()

    def play_beep(self):
        try:
            if os.path.exists(config.BEEP_SOUND_PATH):
                pygame.mixer.Sound(config.BEEP_SOUND_PATH).play()
        except Exception:
            pass

    def listen(self):
        with sr.Microphone() as source:
            self.play_beep()
            print("[Audio] Listening...")
            self.recognizer.adjust_for_ambient_noise(source)
            try:
                audio = self.recognizer.listen(source, timeout=5)
                text = self.recognizer.recognize_google(audio)
                return text.lower()
            except:
                return None

    def speak(self, text, motor_controller):
        print(f"[Robot]: {text}")
        try:
            tts = gTTS(text=text, lang='en')
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_path = fp.name
                tts.save(temp_path)

            # Start Jaw Movement
            stop_event = threading.Event()
            t = threading.Thread(target=motor_controller.flap_jaw, args=(stop_event,))
            t.start()

            # Play Audio
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            # Stop Jaw
            stop_event.set()
            t.join()
            os.remove(temp_path)
        except Exception as e:
            print(f"TTS Error: {e}")