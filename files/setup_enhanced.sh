#!/bin/bash
# Enhanced Setup Script for Humanoid Robot with PCA9685

echo "======================================"
echo "Humanoid Robot Enhanced Setup"
echo "PCA9685 16-Channel Servo Driver"
echo "======================================"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo -e "${YELLOW}Warning: This doesn't appear to be a Raspberry Pi${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo -e "${GREEN}Updating system packages...${NC}"
sudo apt-get update

# Install system dependencies
echo -e "${GREEN}Installing system dependencies...${NC}"
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    portaudio19-dev \
    python3-pyaudio \
    ffmpeg \
    espeak \
    i2c-tools \
    python3-smbus

# Enable I2C
echo -e "${GREEN}Enabling I2C interface...${NC}"
sudo raspi-config nonint do_i2c 0

# Add user to i2c group
sudo usermod -a -G i2c $USER

# Install Python packages
echo -e "${GREEN}Installing Python packages...${NC}"
pip3 install -r requirements_enhanced.txt --break-system-packages

# Verify I2C
echo -e "${GREEN}Checking I2C devices...${NC}"
sudo i2cdetect -y 1

echo -e "${YELLOW}Note: PCA9685 should appear at address 0x40${NC}"
echo -e "${YELLOW}If not detected, check your wiring!${NC}"
echo ""

# Set up API key
echo -e "${YELLOW}Setting up Gemini API key...${NC}"
read -p "Enter your Gemini API key: " api_key

# Add to .bashrc
if ! grep -q "GEMINI_API_KEY" ~/.bashrc; then
    echo "export GEMINI_API_KEY=\"$api_key\"" >> ~/.bashrc
    echo -e "${GREEN}API key added to ~/.bashrc${NC}"
else
    echo -e "${YELLOW}API key already exists in ~/.bashrc${NC}"
fi

# Source .bashrc
source ~/.bashrc

# Create beep sound if it doesn't exist
if [ ! -f "/home/ranjeet/beep.wav" ]; then
    echo -e "${GREEN}Creating beep sound...${NC}"
    mkdir -p /home/ranjeet
    # Generate simple beep using sox (if available)
    if command -v sox &> /dev/null; then
        sox -n /home/ranjeet/beep.wav synth 0.2 sine 800
    else
        echo -e "${YELLOW}sox not found. Installing...${NC}"
        sudo apt-get install -y sox
        sox -n /home/ranjeet/beep.wav synth 0.2 sine 800
    fi
fi

# Create configuration file
echo -e "${GREEN}Creating configuration guide...${NC}"
cat > ~/robot_config.txt << 'EOF'
===========================================
HUMANOID ROBOT - PCA9685 WIRING GUIDE
===========================================

PCA9685 Connections:
-------------------
VCC  -> 5V (Raspberry Pi Pin 2 or 4)
GND  -> GND (Raspberry Pi Pin 6)
SDA  -> GPIO 2 (SDA) (Raspberry Pi Pin 3)
SCL  -> GPIO 3 (SCL) (Raspberry Pi Pin 5)
V+   -> External 5-6V power supply for servos

Servo Channels (Default):
-------------------------
Channel 0: Jaw Servo
Channel 1: Neck Servo (Left/Right)
Channel 2: Eye Up/Down Servo
Channel 3: Eye Left/Right Servo

To Change Channels:
-------------------
Edit these lines in humanoid_robot_enhanced.py:

JAW_CHANNEL = 0
NECK_CHANNEL = 1
EYE_UD_CHANNEL = 2
EYE_LR_CHANNEL = 3

Key Features:
-------------
✓ Interrupt Detection: Robot stops talking when you speak
✓ Concise Responses: 1-2 sentence answers
✓ 16-Channel Support: Can control up to 16 servos
✓ Human-like Behavior: Natural conversation flow

Commands to Try:
----------------
- "Look left/right/up/down"
- "Turn left/right"
- "Center neck"
- "Reset position"
- "Introduce yourself"
- "What can you do?"
- Ask any question (gets concise AI answer)
- "Exit" or "Goodbye" to quit

Troubleshooting:
----------------
1. If servos don't move:
   - Check I2C: sudo i2cdetect -y 1
   - Verify PCA9685 at 0x40
   - Check servo power supply

2. If interrupt not working:
   - Adjust INTERRUPT_ENERGY_THRESHOLD in Config class
   - Default: 1000 (lower = more sensitive)

3. If responses too long:
   - Adjust MAX_RESPONSE_LENGTH in Config class
   - Default: 150 characters

===========================================
EOF

echo -e "${GREEN}Configuration guide saved to ~/robot_config.txt${NC}"

# Set up systemd service (optional)
read -p "Create systemd service for auto-start? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo tee /etc/systemd/system/humanoid-robot.service > /dev/null <<EOF
[Unit]
Description=Humanoid Robot Service (Enhanced)
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="GEMINI_API_KEY=$api_key"
ExecStart=/usr/bin/python3 $(pwd)/humanoid_robot_enhanced.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable humanoid-robot.service
    echo -e "${GREEN}Systemd service created and enabled${NC}"
    echo "Start with: sudo systemctl start humanoid-robot"
    echo "Status: sudo systemctl status humanoid-robot"
    echo "Logs: journalctl -u humanoid-robot -f"
fi

# Test installation
echo -e "${GREEN}Testing installation...${NC}"
python3 << 'PYEOF'
try:
    import speech_recognition
    import pygame
    from adafruit_servokit import ServoKit
    from google import genai
    from gtts import gTTS
    print("✓ All modules imported successfully!")
    print("✓ PCA9685 support ready!")
except ImportError as e:
    print(f"✗ Import error: {e}")
    exit(1)
PYEOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Setup completed successfully!${NC}"
    echo ""
    echo "================================================"
    echo "ENHANCED FEATURES:"
    echo "================================================"
    echo "✓ Interrupt Detection: Stops when you speak"
    echo "✓ Concise Responses: 1-2 sentence answers"
    echo "✓ PCA9685 Support: 16-channel servo driver"
    echo "✓ Human-like: Natural conversation flow"
    echo ""
    echo "To run the robot:"
    echo "  python3 humanoid_robot_enhanced.py"
    echo ""
    echo "Configuration guide:"
    echo "  cat ~/robot_config.txt"
    echo ""
    echo "Test servos:"
    echo "  sudo i2cdetect -y 1"
    echo ""
    echo -e "${YELLOW}NOTE: Reboot required for I2C changes!${NC}"
    echo "      sudo reboot"
else
    echo -e "${RED}✗ Setup failed. Please check error messages above.${NC}"
    exit 1
fi
