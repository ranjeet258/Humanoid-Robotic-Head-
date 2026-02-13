import os
import time
import tempfile
import threading
import logging
from typing import Optional
from contextlib import contextmanager
import speech_recognition as sr
from google import genai
from gtts import gTTS
import pygame
import RPi.GPIO as GPIO

# ========== LOGGING SETUP ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== CONFIGURATION ==========
class Config:
    """Centralized configuration"""
    API_KEY = os.getenv("GEMINI_API_KEY", "AIzaXXXXXXXXXXXXXXXXXXXXXXXX")
    BEEP_SOUND_PATH = "/home/ranjeet/beep.wav"
    MODEL_NAME = "models/gemini-2.5-flash"
    
    # Servo pins
    JAW_SERVO = 22
    NECK_SERVO = 27
    EYE_UD_SERVO = 23
    EYE_LR_SERVO = 17
    SERVO_FREQ = 50
    
    # Servo angles
    JAW_OPEN = 115
    JAW_CLOSED = 80
    JAW_REST = 100
    NEUTRAL_ANGLE = 90
    LEFT_ANGLE = 70
    RIGHT_ANGLE = 110
    
    # Timing
    SERVO_SETTLE_TIME = 0.15
    JAW_ANIMATION_SPEED = 0.15
    BEEP_DURATION = 0.4
    AMBIENT_NOISE_DURATION = 0.3

# ========== HARDWARE MANAGER ==========
class ServoController:
    """Manages servo motor operations"""
    
    def __init__(self):
        self.servos = {}
        self._setup_gpio()
    
    def _setup_gpio(self):
        """Initialize GPIO and servo PWM"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        servo_pins = {
            'jaw': Config.JAW_SERVO,
            'neck': Config.NECK_SERVO,
            'eye_ud': Config.EYE_UD_SERVO,
            'eye_lr': Config.EYE_LR_SERVO
        }
        
        for name, pin in servo_pins.items():
            GPIO.setup(pin, GPIO.OUT)
            pwm = GPIO.PWM(pin, Config.SERVO_FREQ)
            pwm.start(0)
            self.servos[name] = {'pwm': pwm, 'pin': pin}
    
    def set_angle(self, servo_name: str, angle: int, settle: bool = True):
        """Set servo to specific angle"""
        try:
            duty = 2 + (angle / 18)
            self.servos[servo_name]['pwm'].ChangeDutyCycle(duty)
            
            if settle:
                time.sleep(Config.SERVO_SETTLE_TIME)
                self.servos[servo_name]['pwm'].ChangeDutyCycle(0)
        except Exception as e:
            logger.error(f"Servo control error ({servo_name}): {e}")
    
    def animate_jaw(self, stop_event: threading.Event):
        """Animate jaw movement for speaking"""
        try:
            while not stop_event.is_set():
                for angle in (Config.JAW_CLOSED, Config.JAW_OPEN):
                    if stop_event.is_set():
                        break
                    self.set_angle('jaw', angle)
                    time.sleep(Config.JAW_ANIMATION_SPEED)
        finally:
            self.set_angle('jaw', Config.JAW_REST)
    
    def cleanup(self):
        """Clean up GPIO resources"""
        for servo in self.servos.values():
            servo['pwm'].stop()
        GPIO.cleanup()

# ========== AUDIO MANAGER ==========
class AudioManager:
    """Manages audio playback and TTS"""
    
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.beep_sound = self._load_beep()
    
    def _load_beep(self) -> Optional[pygame.mixer.Sound]:
        """Load beep sound file"""
        try:
            return pygame.mixer.Sound(Config.BEEP_SOUND_PATH)
        except Exception as e:
            logger.warning(f"Could not load beep sound: {e}")
            return None
    
    def play_beep(self):
        """Play beep sound"""
        if self.beep_sound:
            try:
                self.beep_sound.play()
                time.sleep(Config.BEEP_DURATION)
            except Exception as e:
                logger.warning(f"Beep playback error: {e}")
    
    @contextmanager
    def temp_audio_file(self, text: str, lang: str = "en", tld: str = "com"):
        """Context manager for temporary audio file"""
        temp_file = None
        try:
            tts = gTTS(text=text, lang=lang, tld=tld)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            tts.save(temp_file)
            yield temp_file
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    logger.warning(f"Could not delete temp file: {e}")
    
    def play_audio(self, audio_file: str):
        """Play audio file"""
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(30)
    
    def cleanup(self):
        """Clean up pygame resources"""
        pygame.quit()

# ========== SPEECH RECOGNITION ==========
class SpeechRecognizer:
    """Handles speech recognition"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Optimize recognizer settings
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
    
    def listen(self) -> Optional[str]:
        """Listen to microphone and return recognized text"""
        try:
            with sr.Microphone() as source:
                logger.info("Listening...")
                self.recognizer.adjust_for_ambient_noise(
                    source, 
                    duration=Config.AMBIENT_NOISE_DURATION
                )
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            text = self.recognizer.recognize_google(audio)
            logger.info(f"User: {text}")
            return text.lower()
            
        except sr.WaitTimeoutError:
            logger.debug("Listening timeout")
            return None
        except sr.UnknownValueError:
            logger.debug("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in speech recognition: {e}")
            return None

# ========== AI MANAGER ==========
class GeminiAI:
    """Handles Gemini AI interactions"""
    
    def __init__(self):
        self.client = genai.Client(api_key=Config.API_KEY)
    
    def generate_response(self, prompt: str) -> str:
        """Generate AI response"""
        logger.info("AI thinking...")
        try:
            response = self.client.models.generate_content(
                model=Config.MODEL_NAME,
                contents=f"{prompt}\nAnswer briefly and conversationally."
            )
            
            if response and response.text:
                return response.text.strip()
            
            return "I couldn't generate a response."
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return "Something went wrong with my AI processing."

# ========== ROBOT CONTROLLER ==========
class HumanoidRobot:
    """Main robot controller"""
    
    def __init__(self):
        self.servo = ServoController()
        self.audio = AudioManager()
        self.speech = SpeechRecognizer()
        self.ai = GeminiAI()
    
    def speak(self, text: str, lang: str = "en", tld: str = "com"):
        """Speak text with jaw animation"""
        logger.info(f"Robot: {text}")
        
        with self.audio.temp_audio_file(text, lang, tld) as audio_file:
            stop_event = threading.Event()
            jaw_thread = threading.Thread(
                target=self.servo.animate_jaw, 
                args=(stop_event,),
                daemon=True
            )
            jaw_thread.start()
            
            try:
                self.audio.play_audio(audio_file)
            finally:
                stop_event.set()
                jaw_thread.join(timeout=1.0)
    
    def handle_personality(self, text: str) -> bool:
        """Handle personality changes"""
        personalities = {
            "krishna": ("Hi, I am Krishna. Ask me anything.", "co.in"),
            "maya": ("Hi, I am Maya. How can I help you today?", "co.uk")
        }
        
        for name, (greeting, tld) in personalities.items():
            if name in text:
                self.speak(greeting, tld=tld)
                return True
        return False
    
    def handle_faq(self, text: str) -> bool:
        """Handle frequently asked questions"""
        faqs = {
            "introduce yourself": (
                "I am a humanoid robotic head developed by Ranjeet Gupta "
                "under mentorship of Doctor Vijay Kumar Dalla at NIT Jamshedpur."
            ),
            "what can you do": "I can listen, talk, and move my head like a human."
        }
        
        for trigger, response in faqs.items():
            if trigger in text:
                self.speak(response)
                return True
        return False
    
    def handle_movements(self, text: str) -> bool:
        """Handle movement commands"""
        movements = {
            ("turn left", "look left"): ('neck', Config.LEFT_ANGLE, "Turning left"),
            ("turn right", "look right"): ('neck', Config.RIGHT_ANGLE, "Turning right"),
            ("look up",): ('eye_ud', Config.LEFT_ANGLE, "Looking up"),
            ("look down",): ('eye_ud', Config.RIGHT_ANGLE, "Looking down"),
            ("look straight",): ('eye_lr', Config.NEUTRAL_ANGLE, "Looking straight"),
            ("center neck",): ('neck', Config.NEUTRAL_ANGLE, "Neck centered"),
            ("center eyes",): (None, None, "Eyes centered")
        }
        
        for triggers, action in movements.items():
            if any(trigger in text for trigger in triggers):
                servo, angle, message = action
                
                if "center eyes" in text:
                    self.servo.set_angle('eye_ud', Config.NEUTRAL_ANGLE)
                    self.servo.set_angle('eye_lr', Config.NEUTRAL_ANGLE)
                elif servo:
                    self.servo.set_angle(servo, angle)
                
                self.speak(message)
                return True
        return False
    
    def run(self):
        """Main loop"""
        self.speak("Hi Ranjeet. How can I assist you? Speak after the beep.")
        
        try:
            while True:
                self.audio.play_beep()
                user_input = self.speech.listen()
                
                if not user_input:
                    continue
                
                # Exit commands
                if any(cmd in user_input for cmd in ["exit", "quit", "goodbye"]):
                    self.speak("Goodbye. Have a great day.")
                    break
                
                # Process commands in priority order
                if (self.handle_personality(user_input) or 
                    self.handle_faq(user_input) or 
                    self.handle_movements(user_input)):
                    continue
                
                # General AI response
                response = self.ai.generate_response(user_input)
                self.speak(response)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up all resources"""
        logger.info("Cleaning up resources...")
        self.servo.cleanup()
        self.audio.cleanup()

# ========== ENTRY POINT ==========
def main():
    """Main entry point"""
    try:
        robot = HumanoidRobot()
        robot.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
