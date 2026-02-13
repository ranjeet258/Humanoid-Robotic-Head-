#!/bin/bash
# Setup script for Humanoid Robot

echo "======================================"
echo "Humanoid Robot Setup Script"
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
    espeak

# Install Python packages
echo -e "${GREEN}Installing Python packages...${NC}"
pip3 install -r requirements.txt --break-system-packages

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
        echo -e "${YELLOW}sox not found. Please create beep.wav manually${NC}"
    fi
fi

# Set up systemd service (optional)
read -p "Create systemd service for auto-start? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo tee /etc/systemd/system/humanoid-robot.service > /dev/null <<EOF
[Unit]
Description=Humanoid Robot Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="GEMINI_API_KEY=$api_key"
ExecStart=/usr/bin/python3 $(pwd)/humanoid_robot_optimized.py
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
python3 -c "
import speech_recognition
import pygame
import RPi.GPIO
from google import genai
from gtts import gTTS
print('All modules imported successfully!')
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Setup completed successfully!${NC}"
    echo ""
    echo "To run the robot:"
    echo "  python3 humanoid_robot_optimized.py"
    echo ""
    echo "To set API key manually:"
    echo "  export GEMINI_API_KEY='your-key-here'"
else
    echo -e "${RED}✗ Setup failed. Please check error messages above.${NC}"
    exit 1
fi
