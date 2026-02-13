# modules/motor.py
import time
import threading
import RPi.GPIO as GPIO
import config

class RobotMotor:
    def __init__(self):
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Setup Pins
        GPIO.setup(config.PIN_JAW, GPIO.OUT)
        GPIO.setup(config.PIN_NECK, GPIO.OUT)
        GPIO.setup(config.PIN_EYE_UD, GPIO.OUT)
        GPIO.setup(config.PIN_EYE_LR, GPIO.OUT)

        # Initialize PWM
        self.jaw = GPIO.PWM(config.PIN_JAW, config.SERVO_FREQ)
        self.neck = GPIO.PWM(config.PIN_NECK, config.SERVO_FREQ)
        self.eye_ud = GPIO.PWM(config.PIN_EYE_UD, config.SERVO_FREQ)
        self.eye_lr = GPIO.PWM(config.PIN_EYE_LR, config.SERVO_FREQ)

        # Start PWM at 0 (Off)
        self.jaw.start(0)
        self.neck.start(0)
        self.eye_ud.start(0)
        self.eye_lr.start(0)
        
        self.current_neck_angle = 90

    def set_angle(self, pwm_obj, pin, angle):
        """Moves a servo to a specific angle."""
        duty = 2 + (angle / 18)
        GPIO.output(pin, True)
        pwm_obj.ChangeDutyCycle(duty)
        time.sleep(0.3)
        GPIO.output(pin, False)
        pwm_obj.ChangeDutyCycle(0)

    def move_neck(self, angle):
        self.current_neck_angle = angle
        self.set_angle(self.neck, config.PIN_NECK, angle)

    def move_eyes(self, lr_angle=None, ud_angle=None):
        if lr_angle is not None:
            self.set_angle(self.eye_lr, config.PIN_EYE_LR, lr_angle)
        if ud_angle is not None:
            self.set_angle(self.eye_ud, config.PIN_EYE_UD, ud_angle)

    def flap_jaw(self, stop_event):
        """Oscillates jaw while speaking."""
        try:
            while not stop_event.is_set():
                for angle in [80, 115]:
                    if stop_event.is_set(): break
                    self.set_angle(self.jaw, config.PIN_JAW, angle)
                    time.sleep(0.15)
            self.set_angle(self.jaw, config.PIN_JAW, 100) # Rest
        except Exception as e:
            print(f"Jaw Error: {e}")

    def cleanup(self):
        self.jaw.stop()
        self.neck.stop()
        self.eye_ud.stop()
        self.eye_lr.stop()
        GPIO.cleanup()