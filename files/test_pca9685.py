#!/usr/bin/env python3
"""
PCA9685 Servo Test Script
Tests individual servo channels and movements
"""

import time
from adafruit_servokit import ServoKit

# Initialize PCA9685
print("Initializing PCA9685...")
kit = ServoKit(channels=16)

# Test configuration
TEST_CHANNELS = [0, 1, 2, 3]  # Jaw, Neck, Eye UD, Eye LR
ANGLES = [0, 45, 90, 135, 180]

def test_servo(channel):
    """Test a single servo channel"""
    print(f"\n{'='*50}")
    print(f"Testing Channel {channel}")
    print(f"{'='*50}")
    
    try:
        for angle in ANGLES:
            print(f"  Setting angle: {angle}°")
            kit.servo[channel].angle = angle
            time.sleep(1)
        
        # Return to neutral
        print(f"  Returning to 90°")
        kit.servo[channel].angle = 90
        time.sleep(0.5)
        
        print(f"✓ Channel {channel} test completed")
        return True
        
    except Exception as e:
        print(f"✗ Error on channel {channel}: {e}")
        return False

def main():
    """Main test function"""
    print("\n" + "="*50)
    print("PCA9685 SERVO TESTER")
    print("="*50)
    print("\nThis will test each servo channel:")
    print("  Channel 0: Jaw Servo")
    print("  Channel 1: Neck Servo")
    print("  Channel 2: Eye Up/Down")
    print("  Channel 3: Eye Left/Right")
    print("\nMake sure servos are connected!")
    
    input("\nPress ENTER to start testing...")
    
    results = {}
    for channel in TEST_CHANNELS:
        results[channel] = test_servo(channel)
        time.sleep(1)
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    for channel, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"Channel {channel}: {status}")
    
    # Interactive mode
    print("\n" + "="*50)
    print("INTERACTIVE MODE")
    print("="*50)
    print("Commands:")
    print("  <channel> <angle>  - Set servo (e.g., '1 90')")
    print("  'reset'            - All servos to 90°")
    print("  'quit'             - Exit")
    
    while True:
        try:
            cmd = input("\nEnter command: ").strip().lower()
            
            if cmd == 'quit':
                break
            elif cmd == 'reset':
                for ch in TEST_CHANNELS:
                    kit.servo[ch].angle = 90
                print("All servos reset to 90°")
            else:
                parts = cmd.split()
                if len(parts) == 2:
                    channel = int(parts[0])
                    angle = int(parts[1])
                    
                    if 0 <= channel <= 15 and 0 <= angle <= 180:
                        kit.servo[channel].angle = angle
                        print(f"Channel {channel} set to {angle}°")
                    else:
                        print("Invalid range! Channel: 0-15, Angle: 0-180")
                else:
                    print("Invalid command format!")
                    
        except ValueError:
            print("Invalid input! Use numbers only.")
        except Exception as e:
            print(f"Error: {e}")
    
    # Reset all servos before exit
    print("\nResetting all servos...")
    for ch in TEST_CHANNELS:
        kit.servo[ch].angle = 90
    
    print("Test completed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted! Resetting servos...")
        kit = ServoKit(channels=16)
        for ch in [0, 1, 2, 3]:
            kit.servo[ch].angle = 90
        print("Done.")
