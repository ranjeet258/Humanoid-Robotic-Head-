# Enhanced Humanoid Robot 🤖

An advanced humanoid robot with **interrupt detection**, **concise AI responses**, and **PCA9685 servo driver support**.

## 🌟 Key Features

### 1. **Human-like Interruption**
- Robot stops talking when you start speaking
- Natural conversation flow like talking to a real person
- Configurable sensitivity for interrupt detection

### 2. **Concise Responses**
- AI answers in just 1-2 sentences
- No lengthy explanations
- Quick, conversational replies

### 3. **PCA9685 16-Channel Servo Driver**
- Control up to 16 servos simultaneously
- I2C communication (only 2 GPIO pins needed)
- External power supply support for servos

## 📋 Hardware Requirements

### Components
- Raspberry Pi (any model with GPIO)
- PCA9685 16-Channel PWM Servo Driver
- USB Microphone
- Speaker (3.5mm or USB)
- 4 Servo Motors (SG90 or similar)
- 5-6V Power Supply for servos

### Wiring Diagram

```
PCA9685 -> Raspberry Pi
-----------------------
VCC     -> 5V (Pin 2 or 4)
GND     -> GND (Pin 6)
SDA     -> GPIO 2 (SDA - Pin 3)
SCL     -> GPIO 3 (SCL - Pin 5)
V+      -> External 5-6V Power (+)
GND     -> External Power (-)

Servos -> PCA9685
-----------------
Channel 0: Jaw Servo
Channel 1: Neck Servo (Left/Right)
Channel 2: Eye Up/Down
Channel 3: Eye Left/Right
```

## 🚀 Installation

### Quick Setup

```bash
# 1. Make setup script executable
chmod +x setup_enhanced.sh

# 2. Run setup
./setup_enhanced.sh

# 3. Reboot (required for I2C)
sudo reboot

# 4. Test PCA9685 connection
sudo i2cdetect -y 1
# Should show device at 0x40

# 5. Test servos
python3 test_pca9685.py

# 6. Run the robot
python3 humanoid_robot_enhanced.py
```

### Manual Installation

```bash
# Update system
sudo apt-get update

# Install dependencies
sudo apt-get install -y python3-pip python3-dev portaudio19-dev \
    python3-pyaudio ffmpeg espeak i2c-tools python3-smbus

# Enable I2C
sudo raspi-config nonint do_i2c 0

# Install Python packages
pip3 install -r requirements_enhanced.txt --break-system-packages

# Set API key
export GEMINI_API_KEY="your-api-key-here"
echo 'export GEMINI_API_KEY="your-key"' >> ~/.bashrc
```

## 🎮 Usage

### Starting the Robot

```bash
python3 humanoid_robot_enhanced.py
```

### Voice Commands

**Movement Commands:**
- "Look left" / "Turn left"
- "Look right" / "Turn right"
- "Look up"
- "Look down"
- "Look straight"
- "Center neck"
- "Reset position" / "Neutral position"

**Information Commands:**
- "Introduce yourself"
- "What can you do?"
- "Who made you?"
- "How are you?"

**Personality Changes:**
- "Change to Krishna" (Indian accent)
- "Change to Maya" (British accent)

**General Questions:**
- Ask anything! The robot will answer in 1-2 sentences

**Exit:**
- "Exit" / "Quit" / "Goodbye" / "Bye"

### Interrupt Feature

Simply start speaking while the robot is talking - it will stop immediately and listen to you!

## ⚙️ Configuration

Edit `humanoid_robot_enhanced.py` to customize:

```python
class Config:
    # Servo Channels (0-15)
    JAW_CHANNEL = 0
    NECK_CHANNEL = 1
    EYE_UD_CHANNEL = 2
    EYE_LR_CHANNEL = 3
    
    # Servo Angles
    JAW_OPEN = 115
    JAW_CLOSED = 80
    NEUTRAL_ANGLE = 90
    LEFT_ANGLE = 70
    RIGHT_ANGLE = 110
    
    # Interrupt Sensitivity (lower = more sensitive)
    INTERRUPT_ENERGY_THRESHOLD = 1000
    
    # Response Length (characters)
    MAX_RESPONSE_LENGTH = 150
```

## 🔧 Troubleshooting

### Servos Not Moving

1. **Check I2C Connection:**
```bash
sudo i2cdetect -y 1
# Should show 0x40
```

2. **Check Wiring:**
- Verify SDA → GPIO 2 (Pin 3)
- Verify SCL → GPIO 3 (Pin 5)
- Check power supply to PCA9685

3. **Test Individual Servos:**
```bash
python3 test_pca9685.py
```

### Interrupt Not Working

1. **Adjust Sensitivity:**
```python
# In Config class
INTERRUPT_ENERGY_THRESHOLD = 500  # Lower = more sensitive
```

2. **Check Microphone:**
```bash
# Test microphone
arecord -d 5 test.wav
aplay test.wav
```

### Responses Too Long

1. **Reduce MAX_RESPONSE_LENGTH:**
```python
MAX_RESPONSE_LENGTH = 100  # Shorter responses
```

2. The AI is prompted to give 1-2 sentence answers automatically

### No Audio Output

1. **Check Speaker Connection:**
```bash
speaker-test -t wav -c 2
```

2. **Set Default Audio Device:**
```bash
sudo raspi-config
# System Options → Audio → Select output
```

## 📊 Performance Tips

### Optimize Interrupt Detection

```python
# Faster interrupt checking
INTERRUPT_CHECK_INTERVAL = 0.2  # Check every 200ms

# More sensitive detection
INTERRUPT_ENERGY_THRESHOLD = 800
```

### Reduce Latency

```python
# Faster jaw animation
JAW_ANIMATION_SPEED = 0.10

# Shorter settle time
SERVO_SETTLE_TIME = 0.10
```

## 🔄 Auto-Start on Boot

The setup script can create a systemd service:

```bash
# Check status
sudo systemctl status humanoid-robot

# Start manually
sudo systemctl start humanoid-robot

# Stop
sudo systemctl stop humanoid-robot

# View logs
journalctl -u humanoid-robot -f
```

## 📝 File Structure

```
.
├── humanoid_robot_enhanced.py    # Main robot code
├── requirements_enhanced.txt      # Python dependencies
├── setup_enhanced.sh             # Setup script
├── test_pca9685.py               # Servo test utility
└── README.md                     # This file
```

## 🎯 How It Works

### Interrupt Detection System

```
1. Robot starts speaking
2. Separate thread monitors microphone
3. If speech detected → Interrupt event triggered
4. Robot stops talking immediately
5. Switches to listening mode
```

### Concise Response Generation

```
1. User asks question
2. AI prompt includes: "Answer in 1-2 sentences"
3. Response length checked (max 150 chars)
4. If too long → Cut at sentence boundary
5. Speak concise answer
```

### PCA9685 Servo Control

```
1. I2C communication (SDA/SCL pins)
2. 16 independent PWM channels
3. External power for servos
4. Angle control: 0° - 180°
```

## 🆚 Improvements Over Original

| Feature | Original | Enhanced |
|---------|----------|----------|
| Servo Driver | RPi.GPIO | PCA9685 (16-channel) |
| GPIO Pins Used | 4 pins | 2 pins (I2C) |
| Interrupt Detection | ❌ | ✓ |
| Response Length | Variable (long) | 1-2 sentences |
| Concise Answers | ❌ | ✓ |
| Human-like Behavior | Basic | Advanced |
| Servo Channels | 4 max | 16 max |

## 🔐 Security Note

**Never share your Gemini API key!** The setup script saves it to `.bashrc` for convenience, but ensure your Raspberry Pi is secure.

## 📞 Support

- Check `robot_config.txt` for detailed wiring guide
- Run `test_pca9685.py` to verify servo connections
- Adjust Config class for customization

## 🎉 Credits

- **Developer:** Ranjeet Gupta
- **Mentor:** Dr. Vijay Kumar Dalla
- **Institution:** NIT Jamshedpur
- **AI:** Google Gemini 2.5 Flash

---

**Enjoy your human-like robot! 🤖**
