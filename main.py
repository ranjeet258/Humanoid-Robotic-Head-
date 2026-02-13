# main.py
from modules.motor import RobotMotor
from modules.vision import RobotVision
from modules.audio import RobotAudio
from modules.brain import RobotBrain
import time

def main():
    # Initialize Systems
    motor = RobotMotor()
    vision = RobotVision()
    audio = RobotAudio()
    brain = RobotBrain()

    audio.speak("System Online. Waiting for command.", motor)

    try:
        while True:
            text = audio.listen()
            
            if not text:
                continue
            
            print(f"[User]: {text}")

            # --- COMMANDS ---
            if "track me" in text:
                audio.speak("Tracking activated.", motor)
                vision.start_tracking(motor)
                continue

            if "stop tracking" in text:
                vision.stop_tracking()
                audio.speak("Tracking stopped.", motor)
                continue

            if "what do you see" in text:
                vision.stop_tracking() # Pause tracking to take photo
                frame = vision.get_frame()
                if frame is not None:
                    desc = brain.see_and_describe(frame)
                    audio.speak(desc, motor)
                continue

            if "exit" in text or "quit" in text:
                audio.speak("Goodbye.", motor)
                break

            # --- DEFAULT CHAT ---
            response = brain.ask(text)
            audio.speak(response, motor)

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        motor.cleanup()

if __name__ == "__main__":
    main()