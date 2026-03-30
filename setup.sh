#!/bin/bash
# =============================================================================
# setup.sh — One-shot setup for the Humanoid Robotic Head
# NIT Jamshedpur | Developer: Ranjeet Kumar Gupta
# =============================================================================
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  ✓  $*${NC}"; }
warn() { echo -e "${YELLOW}  ⚠  $*${NC}"; }
err()  { echo -e "${RED}  ✗  $*${NC}"; }

echo "============================================================"
echo "  Humanoid Robot Setup — NIT Jamshedpur"
echo "  Developer: Ranjeet Kumar Gupta"
echo "============================================================"

# ── Raspberry Pi check ────────────────────────────────────────────────────────
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    warn "This does not appear to be a Raspberry Pi."
    read -r -p "  Continue anyway? [y/N] " reply
    [[ "${reply,,}" == "y" ]] || exit 1
fi

# ── System packages ───────────────────────────────────────────────────────────
echo; echo "[ 1/6 ]  Installing system packages …"
sudo apt-get update -qq
sudo apt-get install -y \
    python3-pip python3-dev python3-smbus \
    portaudio19-dev python3-pyaudio \
    i2c-tools ffmpeg espeak sox libopencv-dev \
    libcamera-apps
ok "System packages installed."

# ── Enable I2C ────────────────────────────────────────────────────────────────
echo; echo "[ 2/6 ]  Enabling I2C interface …"
sudo raspi-config nonint do_i2c 0
sudo usermod -a -G i2c "$USER"
ok "I2C enabled.  (Will take effect after reboot.)"

# ── Python packages ───────────────────────────────────────────────────────────
echo; echo "[ 3/6 ]  Installing Python packages …"
pip3 install -r requirements.txt --break-system-packages -q
ok "Python packages installed."

# ── Beep sound ────────────────────────────────────────────────────────────────
echo; echo "[ 4/6 ]  Creating beep sound …"
mkdir -p /home/ranjeet
if command -v sox &>/dev/null; then
    sox -n /home/ranjeet/beep.wav synth 0.2 sine 880 vol 0.5
    ok "beep.wav created at /home/ranjeet/beep.wav"
else
    warn "sox not found — beep.wav not created.  Robot will run without beep."
fi

# ── Gemini API key ────────────────────────────────────────────────────────────
echo; echo "[ 5/6 ]  Configuring Gemini API key …"
if grep -q "GEMINI_API_KEY" ~/.bashrc 2>/dev/null; then
    warn "GEMINI_API_KEY already in ~/.bashrc — skipping."
else
    read -r -p "  Enter your Gemini API key: " api_key
    echo "export GEMINI_API_KEY=\"${api_key}\"" >> ~/.bashrc
    export GEMINI_API_KEY="${api_key}"
    ok "Key saved to ~/.bashrc"
fi

# ── Optional: systemd service ─────────────────────────────────────────────────
echo; echo "[ 6/6 ]  Optional auto-start service …"
read -r -p "  Create systemd auto-start service? [y/N] " reply
if [[ "${reply,,}" == "y" ]]; then
    API_KEY_VAL="${GEMINI_API_KEY:-}"
    sudo tee /etc/systemd/system/humanoid-robot.service > /dev/null <<EOF
[Unit]
Description=Humanoid Robot — NIT Jamshedpur
After=network.target sound.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=$(pwd)
Environment="GEMINI_API_KEY=${API_KEY_VAL}"
ExecStart=/usr/bin/python3 $(pwd)/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable humanoid-robot.service
    ok "Service created.  Use: sudo systemctl start humanoid-robot"
fi

# ── I2C device scan ───────────────────────────────────────────────────────────
echo; echo "  Scanning I2C bus …"
sudo i2cdetect -y 1 || true
warn "PCA9685 should appear at address 0x40.  If not — check wiring."

# ── Done ──────────────────────────────────────────────────────────────────────
echo
echo "============================================================"
echo -e "${GREEN}  Setup complete!${NC}"
echo "============================================================"
echo
echo "  IMPORTANT: Reboot required for I2C to activate."
echo "             sudo reboot"
echo
echo "  After reboot:"
echo "    1.  python3 test_hardware.py    ← verify all hardware"
echo "    2.  python3 main.py             ← start the robot"
echo
echo "  Logs:  /home/ranjeet/robot.log"
echo "============================================================"
