# Raspberry Pi Central Control - Installation & Usage Guide

## 🎯 Overview

Complete Python control system for PLTN Simulator dengan arsitektur I2C Master-Slave.

**Raspberry Pi sebagai I2C Master** mengontrol:
- 4x OLED Display (via TCA9548A #1)
- 5x ESP32 Slaves (via TCA9548A #2)
- 8x Button input
- 3x Motor PWM output
- 1x Buzzer alarm

## 📁 File Structure

```
RasPi_Central_Control/
├── raspi_main.py           # Main program (run this)
├── raspi_config.py         # Configuration parameters
├── raspi_tca9548a.py       # TCA9548A multiplexer driver
├── raspi_i2c_master.py     # I2C Master communication
├── raspi_oled_manager.py   # OLED display manager
├── raspi_requirements.txt  # Python dependencies
└── README.md               # This file
```

## 🔧 Hardware Requirements

### 1. Raspberry Pi
- Raspberry Pi 3B/3B+/4/Zero 2W
- Raspbian OS (Bookworm atau Bullseye)
- Minimum 1GB RAM
- 8GB SD card

### 2. I2C Multiplexers
- 2x TCA9548A 1-to-8 I2C Multiplexer
  - TCA9548A #1 (0x70) - untuk OLED displays
  - TCA9548A #2 (0x71) - untuk ESP32 slaves

### 3. Peripherals
- 4x OLED 128x32 (SSD1306, address 0x3C)
- 8x Push buttons (for control)
- 1x Buzzer (untuk alarm)
- 3x Motor driver L298N atau equivalent
- Breadboard & jumper wires

### 4. ESP32 Modules
- ESP-B (I2C Slave 0x08) - Batang Kendali
- ESP-C (I2C Slave 0x09) - Turbin & Generator
- ESP-E (I2C Slave 0x0A) - Visualizer Primer
- ESP-F (I2C Slave 0x0B) - Visualizer Sekunder
- ESP-G (I2C Slave 0x0C) - Visualizer Tersier

## 📌 Pin Connections

### I2C Buses
```
I2C Bus 0 (GPIO 0/1):
  GPIO0 (SDA0) → TCA9548A #1 SDA
  GPIO1 (SCL0) → TCA9548A #1 SCL

I2C Bus 1 (GPIO 2/3):
  GPIO2 (SDA1) → TCA9548A #2 SDA
  GPIO3 (SCL1) → TCA9548A #2 SCL
```

### Button Inputs
```
GPIO5  → BTN_PRES_UP
GPIO6  → BTN_PRES_DOWN
GPIO4  → BTN_PUMP_PRIM_ON
GPIO17 → BTN_PUMP_PRIM_OFF
GPIO27 → BTN_PUMP_SEC_ON
GPIO22 → BTN_PUMP_SEC_OFF
GPIO10 → BTN_PUMP_TER_ON
GPIO9  → BTN_PUMP_TER_OFF
```

### PWM Outputs
```
GPIO18 → Buzzer (Hardware PWM0)
GPIO12 → Motor Primary (Hardware PWM0)
GPIO13 → Motor Secondary (Hardware PWM1)
GPIO19 → Motor Tertiary (Hardware PWM1)
```

## 🚀 Installation

### Step 1: Update Raspberry Pi OS
```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
```

### Step 2: Enable I2C
```bash
sudo raspi-config
# Navigate to:
# 3 Interface Options → I4 I2C → Enable
# Reboot when prompted
```

### Step 3: Install Python Dependencies
```bash
cd ~/
git clone <your-repo-url> pltn_simulator
cd pltn_simulator/RasPi_Central_Control

# Install system packages
sudo apt install -y python3-pip python3-dev python3-pil i2c-tools

# Install Python packages
pip3 install -r raspi_requirements.txt
```

### Step 4: Test I2C Bus
```bash
# Test I2C bus 0 (Display multiplexer)
sudo i2cdetect -y 0

# Test I2C bus 1 (ESP multiplexer)
sudo i2cdetect -y 1

# You should see:
#   0x70 (TCA9548A #1 on bus 0)
#   0x71 (TCA9548A #2 on bus 1)
```

### Step 5: Test Individual Components
```bash
# Test TCA9548A
python3 raspi_tca9548a.py

# Test I2C Master (requires ESP to be connected)
python3 raspi_i2c_master.py

# Test OLED Manager
python3 raspi_oled_manager.py
```

## ▶️ Running the System

### Manual Start
```bash
cd ~/pltn_simulator/RasPi_Central_Control
python3 raspi_main.py
```

### Auto-Start on Boot (Optional)
```bash
# Create systemd service
sudo nano /etc/systemd/system/pltn-control.service
```

Add this content:
```ini
[Unit]
Description=PLTN Simulator Central Control
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/pltn_simulator/RasPi_Central_Control
ExecStart=/usr/bin/python3 raspi_main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pltn-control.service
sudo systemctl start pltn-control.service

# Check status
sudo systemctl status pltn-control.service

# View logs
sudo journalctl -u pltn-control.service -f
```

## 🎮 Operating Instructions

### 1. System Startup
1. Power on Raspberry Pi
2. Wait for system to boot (~30 seconds)
3. OLED displays show startup screen
4. System ready when "NORMAL" appears on pressurizer display

### 2. Pressure Control
- Press BTN_PRES_UP to increase pressure (+5 bar)
- Press BTN_PRES_DOWN to decrease pressure (-5 bar)
- Target: 150 bar for normal operation

### 3. Pump Operation
**Primary Pump:**
- Requires pressure ≥ 40 bar
- Press BTN_PUMP_PRIM_ON to start
- Press BTN_PUMP_PRIM_OFF to stop

**Secondary & Tertiary Pumps:**
- Can start at any pressure
- Press respective ON/OFF buttons

### 4. Operating Sequence
1. Increase pressure to 150 bar
2. Start Primary pump → wait for "ON" status
3. Start Secondary pump → wait for "ON" status
4. Start Tertiary pump → wait for "ON" status
5. ESP-B interlock will release
6. Control rods can now be operated
7. ESP-C will start turbin sequence

### 5. Emergency Shutdown
- Press ESP-B emergency button
- All control rods drop to 0%
- Turbin will shutdown
- Stop all pumps manually

### 6. Normal Shutdown
1. Lower all control rods to 0% (at ESP-B)
2. Wait for ESP-C turbin shutdown
3. Stop Primary pump
4. Stop Secondary pump
5. Stop Tertiary pump
6. Lower pressure to 0 bar

## 📊 Data Logging

### CSV Data Log
- File: `pltn_data.csv` (in same directory)
- Interval: 1 second
- Columns: timestamp, pressure, pump status, PWM, rod positions, power level

### Application Log
- File: `pltn_control.log`
- Level: INFO (configurable in config.py)
- Contains system events, errors, communication status

## 🔍 Troubleshooting

### I2C Device Not Detected
```bash
# Check bus 0
sudo i2cdetect -y 0

# Check bus 1
sudo i2cdetect -y 1

# If nothing appears:
# - Check wiring (SDA/SCL)
# - Check pull-up resistors (4.7kΩ)
# - Verify I2C is enabled in raspi-config
```

### ESP Not Responding
```bash
# Check logs
tail -f pltn_control.log

# Look for:
# "ESP 0x08 not responding"
# "I2C timeout"

# Solutions:
# - Verify ESP is powered on
# - Check ESP I2C slave code is running
# - Verify correct I2C address in ESP code
# - Check cable connections
```

### Display Not Working
```bash
# Test OLED directly
sudo i2cdetect -y 0

# Should see 0x3C on one of channels 0-3
# If not:
# - Check TCA9548A channel selection
# - Verify OLED address (0x3C or 0x3D)
# - Test OLED on breadboard separately
```

### GPIO Permission Error
```bash
# Add user to gpio group
sudo usermod -a -G gpio pi

# Or run with sudo (not recommended for production)
sudo python3 raspi_main.py
```

## ⚙️ Configuration

Edit `raspi_config.py` to customize:

### I2C Addresses
```python
TCA9548A_DISPLAY_ADDRESS = 0x70
TCA9548A_ESP_ADDRESS = 0x71
ESP_B_ADDRESS = 0x08
ESP_C_ADDRESS = 0x09
# ... etc
```

### Timing
```python
I2C_UPDATE_INTERVAL_FAST = 0.05   # ESP-B polling (50ms)
I2C_UPDATE_INTERVAL_NORMAL = 0.1  # ESP-C polling (100ms)
OLED_UPDATE_INTERVAL = 0.2        # Display update (200ms)
```

### System Parameters
```python
PRESS_NORMAL_OPERATION = 150.0
PRESS_WARNING_ABOVE = 160.0
PRESS_CRITICAL_HIGH = 180.0
PWM_STARTUP_STEP = 10
```

## 🧪 Testing Mode

Run without GPIO hardware:
```python
# In raspi_main.py, GPIO_AVAILABLE will be False
# System runs in simulation mode
# No actual GPIO control, but I2C communication works
```

## 📈 Performance

- I2C Bus Speed: 100 kHz (standard mode)
- Main Loop: ~100 Hz (10ms cycle)
- I2C ESP-B: 20 Hz (50ms)
- I2C ESP-C: 10 Hz (100ms)
- I2C Visualizers: 5 Hz (200ms)
- Display Update: 5 Hz (200ms)

## 🆘 Support

Check logs:
```bash
tail -f pltn_control.log
```

Monitor I2C traffic:
```bash
sudo i2cdump -y 1 0x08  # Dump ESP-B data
```

Test components individually using test functions in each module.

## 📝 Version History

- v2.0 (2024-11) - Full I2C architecture with dual TCA9548A
- v1.0 (2024-10) - Original UART-based system (ESP-A)

---

**Ready to Run!** 🚀

For questions or issues, check `pltn_control.log` or refer to `MIGRATION_PLAN.md` for detailed architecture documentation.
