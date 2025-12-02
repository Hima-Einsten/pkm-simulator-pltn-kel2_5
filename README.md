# 🏭 PLTN Simulator v2.0 - Nuclear Power Plant Training Simulator

**Version 2.0** - Full I2C Architecture with Raspberry Pi Central Control

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.7%2B-blue)]()
[![ESP32](https://img.shields.io/badge/ESP32-Arduino-orange)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

---

## 📋 Project Overview

Simulator pembangkit listrik tenaga nuklir (PLTN) tipe PWR (Pressurized Water Reactor) yang menggunakan **Raspberry Pi sebagai master controller** dan **3 ESP32 sebagai I2C slaves** untuk mengontrol berbagai komponen simulator.

> **V2.0 Update:** Sistem disederhanakan dari 5 ESP menjadi 3 ESP dengan menggunakan multiplexer untuk kontrol LED yang lebih efisien!

### 🎯 Key Features

- ✅ **Centralized Control** - Raspberry Pi sebagai I2C Master
- ✅ **Multi-threaded Architecture** - Non-blocking I2C communication
- ✅ **Real-time Monitoring** - 4 OLED displays + data logging
- ✅ **Safety Systems** - Interlock logic + emergency shutdown
- ✅ **Flow Visualization** - 48 LED animation (3 pumps)
- ✅ **State Machine** - Automated startup/shutdown sequence
- ✅ **Data Logging** - CSV export untuk analysis

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 4                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Main Control Program (Python)               │  │
│  │  - Button Input (8 buttons)                          │  │
│  │  - Pump Control (3 motors PWM)                       │  │
│  │  - Alarm System (buzzer)                             │  │
│  │  - Data Logging (CSV)                                │  │
│  └─────┬────────────────────┬───────────────────────────┘  │
│        │                    │                               │
│  ┌─────▼─────┐       ┌─────▼─────┐                        │
│  │  I2C Bus  │       │  I2C Bus  │                        │
│  │   #0      │       │   #1      │                        │
│  └─────┬─────┘       └─────┬─────┘                        │
└────────┼───────────────────┼─────────────────────────────┘
         │                   │
   ┌─────▼──────┐      ┌─────▼──────┐
   │ TCA9548A   │      │ TCA9548A   │
   │  (0x70)    │      │  (0x71)    │
   │ 4x OLEDs   │      │ 5x ESP32   │
   └────────────┘      └─────┬──────┘
                             │
         ┌───────────────────┼─────────────────┐
         │           │       │        │        │
      ESP-B       ESP-C   ESP-E   ESP-F    ESP-G
      (0x08)      (0x09)  (0x0A)  (0x0B)   (0x0C)
```

---

## 📦 Components

### 1. Raspberry Pi Central Control
**Folder:** `raspi_central_control/`

**Role:** Master controller dengan I2C Master protocol

**Features:**
- 8x Button input (pressure & pump control)
- 3x Motor PWM output (pump simulation)
- 1x Buzzer (alarm system)
- 4x OLED display manager (via TCA9548A #1)
- CSV data logging
- Multi-threaded communication

**Files:**
- `raspi_main.py` - Main control program
- `raspi_config.py` - Configuration
- `raspi_i2c_master.py` - I2C Master
- `raspi_oled_manager.py` - Display manager
- `raspi_tca9548a.py` - Multiplexer driver

### 2. ESP-B - Control Rod Controller
**Folder:** `ESP_B_Rev_1/`  
**I2C Address:** `0x08`

**Role:** Control rod & reactor core simulation

**Features:**
- 3x Servo motors (control rods)
- 4x OLED displays (rod positions + thermal power)
- Interlock safety system
- Emergency shutdown button
- kwThermal calculation

### 3. ESP-C - Turbine & Generator
**Folder:** `esp_c/`  
**I2C Address:** `0x09`

**Role:** Power generation system

**Features:**
- 4x Relay (Steam Gen, Turbine, Condenser, Cooling)
- 4x Motor/Fan PWM control
- State machine (IDLE → STARTING → RUNNING → SHUTTING_DOWN)
- Power level calculation

### 4. ESP-E - 3-Flow Visualizer ⭐ NEW IN V2.0
**Folder:** `ESP_E_Aliran_Primer/`  
**I2C Address:** `0x0A`

**Role:** All 3 coolant loops visualization (Primary, Secondary, Tertiary)

**Features:**
- **48x LED** total (16 per flow)
- **3x CD74HC4067 multiplexers** for efficient control
- **Independent animations** for each flow
- **Multi-wave effect** - looks like real flowing water!
- **12 GPIO pins** only (was 48 with direct control)
- Speed based on each pump status independently

**Hardware:**
- Shared selector pins (S0-S3) for all multiplexers
- Individual EN & SIG per flow
- PWM brightness control for smooth animation

**What happened to ESP-F and ESP-G?**
> ❌ **REMOVED** - Merged into ESP-E for better efficiency
> - ESP-F (Secondary) → Now multiplexer #2 in ESP-E
> - ESP-G (Tertiary) → Now multiplexer #3 in ESP-E
> - See `DEPRECATED_FILES.md` for details

---

## 🚀 Quick Start

### Prerequisites

**Hardware:**
- 1x Raspberry Pi 4 (or 3B+)
- 5x ESP32 DevKit
- 2x TCA9548A I2C Multiplexer
- 4x OLED 128x32 (SSD1306)
- Various sensors, buttons, motors, LEDs

**Software:**
- Raspbian OS (Bookworm/Bullseye)
- Python 3.7+
- Arduino IDE (for ESP32)

### Installation

#### 1. Upload ESP Modules

```bash
# For each ESP:
1. Open Arduino IDE
2. Open ESP_X_I2C.ino from respective folder
3. Select Board: ESP32 Dev Module
4. Upload
5. Verify Serial Monitor shows "Ready!"
```

#### 2. Setup Raspberry Pi

```bash
# Clone repository
cd ~
git clone <your-repo-url>
cd pkm-simulator-PLTN/raspi_central_control

# Install dependencies
pip3 install -r raspi_requirements.txt

# Enable I2C
sudo raspi-config
# Interface Options → I2C → Enable

# Reboot
sudo reboot
```

#### 3. Test I2C Communication

```bash
# Check if all devices detected
sudo i2cdetect -y 1

# Expected:
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- 08 09 0a 0b 0c -- -- -- 
# 70: 70 71 -- -- -- -- -- --
```

#### 4. Run System

```bash
cd raspi_central_control
python3 raspi_main.py
```

---

## 🎮 Operation Guide

### Normal Startup Sequence

1. **Increase Pressure** (ESP-A buttons)
   - Press BTN_PRES_UP until pressure reaches 150 bar

2. **Start Pumps** (ESP-A buttons)
   - Press BTN_PUMP_PRIM_ON → wait for status "ON"
   - Press BTN_PUMP_SEC_ON → wait for status "ON"
   - Press BTN_PUMP_TER_ON → wait for status "ON"

3. **Check Visualizers** (ESP-E/F/G)
   - LED animations should be running fast

4. **Operate Control Rods** (ESP-B buttons)
   - Interlock released, rods can now move
   - Press UP buttons to withdraw rods
   - Monitor kwThermal on OLED

5. **Monitor Power Generation** (ESP-C)
   - State machine: STARTING_UP → RUNNING
   - Turbine and generator activate
   - Power level increases

### Emergency Shutdown

- Press **Emergency Button** on ESP-B
- All rods drop to 0%
- Buzzer sounds for 1 second
- Turbine shuts down automatically

### Normal Shutdown

1. Lower all control rods to 0% (ESP-B)
2. Wait for turbine shutdown (ESP-C)
3. Stop all pumps (Raspberry Pi)
4. Lower pressure to 0 bar

---

## 📊 Data Logging

### CSV Log
**File:** `pltn_data.csv`

**Columns:**
- Timestamp
- Pressure (bar)
- Pump statuses
- Rod positions
- Thermal power
- Generated power

**Update Rate:** 1 Hz (every second)

### Application Log
**File:** `pltn_control.log`

**Contains:**
- System events
- I2C communication status
- Error messages
- State transitions

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| `PROJECT_COMPLETE.md` | Complete project summary |
| `RASPI_PACKAGE_SUMMARY.md` | Raspberry Pi details |
| `raspi_central_control/README.md` | RasPi installation |
| `ESP_*/README.md` | Individual ESP guides |

---

## 🔧 Maintenance

### Check System Health
```bash
# View logs
tail -f raspi_central_control/pltn_control.log

# Monitor I2C
sudo i2cdetect -y 1

# View data
cat raspi_central_control/pltn_data.csv
```

### Backup Data
```bash
tar -czf pltn_backup_$(date +%Y%m%d).tar.gz \
    raspi_central_control/*.csv \
    raspi_central_control/*.log
```

---

## 🐛 Troubleshooting

### ESP Not Detected
```bash
sudo i2cdetect -y 1
```
- Check wiring (SDA/SCL)
- Verify I2C address in code
- Check pull-up resistors (4.7kΩ)

### Communication Timeout
- Shorten I2C cables (<20cm)
- Reduce I2C clock speed
- Check power supply stability

### Display Issues
- Verify OLED address (0x3C)
- Check TCA9548A channel
- Test OLED separately

---

## 🎯 Future Enhancements

- [ ] Web dashboard (Flask/Django)
- [ ] Database integration (InfluxDB)
- [ ] Real-time graphs (Grafana)
- [ ] Mobile app
- [ ] AI predictive maintenance
- [ ] Cloud data sync

---

## 📝 Version History

### v2.0 (2024-11)
- ✅ Complete I2C architecture
- ✅ Raspberry Pi central control
- ✅ Multi-threaded communication
- ✅ All ESP modules converted to I2C Slave

### v1.0 (2024-10)
- Original UART-based system
- ESP-A as master controller

---

## 👥 Contributors

- Nur Ihsanudin - Initial work & v2.0 migration

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

- ESP32 Arduino Framework
- Raspberry Pi Foundation
- Adafruit Libraries

---

## 📞 Contact & Support

For questions or issues:
1. Check documentation in `docs/` folder
2. Review `PROJECT_COMPLETE.md`
3. Check logs: `pltn_control.log`

---

**Status:** ✅ **Production Ready**  
**Last Updated:** 2024-11-11

🎉 **Ready to simulate nuclear power!** 🏭⚡
