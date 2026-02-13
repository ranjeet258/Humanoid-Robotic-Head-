import os
import time
import tempfile
import threading
import logging
from typing import Optional, Tuple
from contextlib import contextmanager
import speech_recognition as sr
from google import genai
from gtts import gTTS
import pygame
from adafruit_servokit import ServoKit

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
    
    # PCA9685 Servo channels (0-15)
    JAW_CHANNEL = 0
    NECK_CHANNEL = 1
    EYE_UD_CHANNEL = 2
    EYE_LR_CHANNEL = 3
    
    # Servo angles
    JAW_OPEN = 115
    JAW_CLOSED = 80
    JAW_REST = 100
    NEUTRAL_ANGLE = 90
    LEFT_ANGLE = 70
    RIGHT_ANGLE = 110
    
    # Timing
    SERVO_SETTLE_TIME = 0.15
    JAW_ANIMATION_SPEED = 0.12
    BEEP_DURATION = 0.3
    AMBIENT_NOISE_DURATION = 0.3
    
    # Interrupt detection
    INTERRUPT_CHECK_INTERVAL = 0.3  # Check for speech every 300ms
    INTERRUPT_ENERGY_THRESHOLD = 1000  # Energy threshold for interrupt detection
    
    # Response settings
    MAX_RESPONSE_LENGTH = 150  # Characters

# ========== HARDWARE MANAGER ==========
class ServoController:
    """Manages servo motor operations using PCA9685"""
    
    def __init__(self):
        try:
            # Initialize PCA9685 (16-channel servo driver)
            self.kit = ServoKit(channels=16)
            self._initialize_servos()
            logger.info("PCA9685 servo controller initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PCA9685: {e}")
            raise
    
    def _initialize_servos(self):
        """Set all servos to neutral position"""
        self.set_angle(Config.JAW_CHANNEL, Config.JAW_REST)
        self.set_angle(Config.NECK_CHANNEL, Config.NEUTRAL_ANGLE)
        self.set_angle(Config.EYE_UD_CHANNEL, Config.NEUTRAL_ANGLE)
        self.set_angle(Config.EYE_LR_CHANNEL, Config.NEUTRAL_ANGLE)
    
    def set_angle(self, channel: int, angle: int, settle: bool = True):
        """Set servo to specific angle"""
        try:
            # Clamp angle to valid range
            angle = max(0, min(180, angle))
            self.kit.servo[channel].angle = angle
            
            if settle:
                time.sleep(Config.SERVO_SETTLE_TIME)
        except Exception as e:
            logger.error(f"Servo control error (channel {channel}): {e}")
    
    def animate_jaw(self, stop_event: threading.Event):
        """Animate jaw movement for speaking"""
        try:
            while not stop_event.is_set():
                for angle in (Config.JAW_CLOSED, Config.JAW_OPEN):
                    if stop_event.is_set():
                        break
                    self.set_angle(Config.JAW_CHANNEL, angle, settle=False)
                    time.sleep(Config.JAW_ANIMATION_SPEED)
        finally:
            self.set_angle(Config.JAW_CHANNEL, Config.JAW_REST)
    
    def cleanup(self):
        """Reset servos to neutral position"""
        try:
            self._initialize_servos()
            logger.info("Servos reset to neutral")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

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
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        return pygame.mixer.music.get_busy()
    
    def stop_audio(self):
        """Stop audio playback immediately"""
        pygame.mixer.music.stop()
    
    def play_audio(self, audio_file: str, interrupt_event: threading.Event):
        """Play audio file with interrupt support"""
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy() and not interrupt_event.is_set():
            pygame.time.Clock().tick(30)
        
        if interrupt_event.is_set():
            pygame.mixer.music.stop()
    
    def cleanup(self):
        """Clean up pygame resources"""
        pygame.quit()

# ========== INTERRUPT DETECTOR ==========
class InterruptDetector:
    """Detects when user interrupts the robot"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = Config.INTERRUPT_ENERGY_THRESHOLD
        self.recognizer.dynamic_energy_threshold = False
    
    def check_for_speech(self) -> bool:
        """Quick check if someone is speaking"""
        try:
            with sr.Microphone() as source:
                # Very short listen to detect energy
                audio = self.recognizer.listen(source, timeout=0.1, phrase_time_limit=0.5)
                # If we got here, there was speech detected
                return True
        except (sr.WaitTimeoutError, Exception):
            return False

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
    """Handles Gemini AI interactions with concise responses"""
    
    def __init__(self):
        self.client = genai.Client(api_key=Config.API_KEY)
    
    def generate_response(self, prompt: str) -> str:
        """Generate concise AI response (1-2 sentences)"""
        logger.info("AI thinking...")
        try:
            # Enhanced prompt for concise responses
            enhanced_prompt = (
                f"{prompt}\n\n"
                "IMPORTANT: Answer in just 1-2 short sentences. "
                "Be direct, conversational, and human-like. "
                "No lists, no explanations, just a brief answer."
            )
            
            response = self.client.models.generate_content(
                model=Config.MODEL_NAME,
                contents=enhanced_prompt
            )
            
            if response and response.text:
                text = response.text.strip()
                
                # Ensure response is concise
                if len(text) > Config.MAX_RESPONSE_LENGTH:
                    # Try to cut at sentence boundary
                    sentences = text.split('. ')
                    text = sentences[0] + '.'
                
                return text
            
            return "I'm not sure about that."
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return "Sorry, I had a technical issue."

# ========== ROBOT CONTROLLER ==========
class HumanoidRobot:
    """Main robot controller with human-like features"""
    
    def __init__(self):
        self.servo = ServoController()
        self.audio = AudioManager()
        self.speech = SpeechRecognizer()
        self.ai = GeminiAI()
        self.interrupt_detector = InterruptDetector()
        self.is_speaking = False
        self.interrupt_event = threading.Event()
    
    def _monitor_interrupts(self, stop_event: threading.Event):
        """Monitor for user interruptions while speaking"""
        while not stop_event.is_set():
            if self.interrupt_detector.check_for_speech():
                logger.info("⚠️  Interrupt detected!")
                self.interrupt_event.set()
                break
            time.sleep(Config.INTERRUPT_CHECK_INTERVAL)
    
    def speak(self, text: str, lang: str = "en", tld: str = "com"):
        """Speak text with jaw animation and interrupt detection"""
        logger.info(f"Robot: {text}")
        
        # Reset interrupt event
        self.interrupt_event.clear()
        self.is_speaking = True
        
        with self.audio.temp_audio_file(text, lang, tld) as audio_file:
            # Start jaw animation
            jaw_stop = threading.Event()
            jaw_thread = threading.Thread(
                target=self.servo.animate_jaw, 
                args=(jaw_stop,),
                daemon=True
            )
            jaw_thread.start()
            
            # Start interrupt monitoring
            interrupt_stop = threading.Event()
            interrupt_thread = threading.Thread(
                target=self._monitor_interrupts,
                args=(interrupt_stop,),
                daemon=True
            )
            interrupt_thread.start()
            
            try:
                # Play audio with interrupt support
                self.audio.play_audio(audio_file, self.interrupt_event)
                
                if self.interrupt_event.is_set():
                    logger.info("Speech interrupted by user")
                
            finally:
                # Stop all threads
                interrupt_stop.set()
                jaw_stop.set()
                
                # Wait for threads to finish
                interrupt_thread.join(timeout=0.5)
                jaw_thread.join(timeout=1.0)
                
                self.is_speaking = False
    
    def handle_personality(self, text: str) -> bool:
        """Handle personality changes"""
        personalities = {
            "krishna": ("Hi, I'm Krishna. What's up?", "co.in"),
            "maya": ("Hi, I'm Maya. How can I help?", "co.uk")
        }
        
        for name, (greeting, tld) in personalities.items():
            if name in text:
                self.speak(greeting, tld=tld)
                return True
        return False
    
    def handle_faq(self, text: str) -> bool:
        """Handle frequently asked questions with concise answers"""
        faqs = {
            "introduce yourself": (
                "I'm a humanoid robot developed by Ranjeet Gupta at NIT Jamshedpur."
            ),
            "what can you do": (
                "I can talk, listen, and move my head like a human."
            ),
            "who made you": (
                "Ranjeet Gupta created me under Doctor Vijay Kumar Dalla's mentorship."
            ),
            "how are you": (
                "I'm doing great! Thanks for asking."
            )
        }
        
        for trigger, response in faqs.items():
            if trigger in text:
                self.speak(response)
                return True
        return False
    
    def handle_movements(self, text: str) -> bool:
        """Handle movement commands"""
        movements = {
            ("turn left", "look left"): (Config.NECK_CHANNEL, Config.LEFT_ANGLE, "Turning left"),
            ("turn right", "look right"): (Config.NECK_CHANNEL, Config.RIGHT_ANGLE, "Turning right"),
            ("look up",): (Config.EYE_UD_CHANNEL, Config.LEFT_ANGLE, "Looking up"),
            ("look down",): (Config.EYE_UD_CHANNEL, Config.RIGHT_ANGLE, "Looking down"),
            ("look straight",): (Config.EYE_LR_CHANNEL, Config.NEUTRAL_ANGLE, "Looking straight"),
            ("center neck", "look center"): (Config.NECK_CHANNEL, Config.NEUTRAL_ANGLE, "Centered"),
            ("reset", "neutral position"): (None, None, "Resetting position")
        }
        
        for triggers, action in movements.items():
            if any(trigger in text for trigger in triggers):
                channel, angle, message = action
                
                if "reset" in text or "neutral" in text:
                    self.servo._initialize_servos()
                elif channel is not None:
                    self.servo.set_angle(channel, angle)
                
                self.speak(message)
                return True
        return False
    
    def run(self):
        """Main loop"""
        self.speak("Hi Ranjeet. I'm ready. Speak after the beep.")
        
        try:
            while True:
                self.audio.play_beep()
                user_input = self.speech.listen()
                
                if not user_input:
                    continue
                
                # Exit commands
                if any(cmd in user_input for cmd in ["exit", "quit", "goodbye", "bye"]):
                    self.speak("Goodbye. See you soon!")
                    break
                
                # Process commands in priority order
                if (self.handle_personality(user_input) or 
                    self.handle_faq(user_input) or 
                    self.handle_movements(user_input)):
                    continue
                
                # General AI response (concise)
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
