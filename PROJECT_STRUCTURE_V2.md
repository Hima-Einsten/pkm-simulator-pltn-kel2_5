# PLTN Simulator Project Structure V2.0

## 📁 Directory Structure

```
pkm-simulator-PLTN/
│
├── 📄 README.md                           # Main project documentation
├── 📄 SYSTEM_ARCHITECTURE_V2.md           # System design & architecture
├── 📄 CHANGELOG_V2.md                     # Version history & changes
├── 📄 DEPRECATED_FILES.md                 # Removed files documentation
├── 📄 PROJECT_STRUCTURE_V2.md            # This file
├── 📄 .gitignore                          # Git ignore rules
│
├── 📂 ESP_B/                              # ESP-B: Batang Kendali & Reaktor
│   ├── ESP_B_I2C/
│   │   └── ESP_B_I2C.ino                 # Firmware for control rods
│   ├── README.md
│   └── WIRING.md
│
├── 📂 ESP_C/                              # ESP-C: Turbin & Generator
│   ├── ESP_C_I2C/
│   │   └── ESP_C_I2C.ino                 # Firmware for turbine
│   ├── README.md
│   └── WIRING.md
│
├── 📂 ESP_E_Aliran_Primer/                # ESP-E: 3-Flow Visualizer ⭐ NEW
│   ├── ESP_E_I2C/
│   │   └── ESP_E_I2C.ino                 # Firmware for 3 flows
│   ├── WIRING_3_FLOWS.md                 # Wiring guide
│   ├── REACTOR_FLOW_LOGIC.md             # PWR operation theory
│   ├── FIX_SUMMARY.md                    # Bug fixes
│   └── README.md
│
├── 📂 raspi_central_control/              # Raspberry Pi Control System
│   ├── 📄 raspi_main.py                  # Main control program
│   ├── 📄 raspi_config.py                # Configuration
│   ├── 📄 raspi_i2c_master.py            # I2C communication
│   ├── 📄 raspi_oled_manager.py          # OLED display control
│   ├── 📄 raspi_tca9548a.py              # Multiplexer driver
│   ├── 📄 raspi_video_player.py          # Video system
│   ├── 📄 raspi_video_integration.py     # Video integration
│   │
│   ├── 🧪 test_pca9548a_esp.py           # ESP communication test
│   ├── 🧪 test_reactor_flow_sequence.py  # Startup sequence test ⭐ NEW
│   ├── 🧪 test_visualizer_interactive.py # Interactive visualizer test
│   │
│   ├── 📄 raspi_requirements.txt         # Python dependencies
│   ├── 📄 raspi_README.md                # Raspberry Pi setup
│   ├── 📄 VIDEO_SYSTEM_GUIDE.md          # Video system docs
│   └── 📄 VIDEO_CONTENT_GUIDE.md         # Video content guide
│
├── 🔧 cleanup_v2.bat                     # Cleanup script (Windows)
└── 🔧 cleanup_v2.sh                      # Cleanup script (Linux/Mac)

```

---

## 📊 File Count by Category

### Firmware (ESP32):
- **ESP-B:** 1 file (ESP_B_I2C.ino)
- **ESP-C:** 1 file (ESP_C_I2C.ino)
- **ESP-E:** 1 file (ESP_E_I2C.ino)
- **Total:** 3 firmware files

### Raspberry Pi Python:
- **Core:** 6 files (main, config, i2c, oled, tca, video)
- **Tests:** 3 files
- **Total:** 9 Python files

### Documentation:
- **Main docs:** 5 files (README, Architecture, Changelog, etc.)
- **ESP docs:** 9 files (per module)
- **Raspi docs:** 4 files
- **Total:** 18 documentation files

### Scripts:
- **Cleanup:** 2 files (bat, sh)
- **Setup:** 1 file (video setup)
- **Total:** 3 scripts

---

## 🎯 Key Files Overview

### Core System Files:

#### 1. System Documentation
| File | Purpose |
|------|---------|
| `README.md` | Project overview & quick start |
| `SYSTEM_ARCHITECTURE_V2.md` | Complete system design |
| `CHANGELOG_V2.md` | Version history |
| `PROJECT_STRUCTURE_V2.md` | This file |

#### 2. ESP Firmware (3 modules)
| Module | File | Function |
|--------|------|----------|
| ESP-B | `ESP_B_I2C.ino` | Control rods & reactor |
| ESP-C | `ESP_C_I2C.ino` | Turbine & generator |
| ESP-E | `ESP_E_I2C.ino` | 3-flow visualizer ⭐ |

#### 3. Raspberry Pi Core
| File | Purpose |
|------|---------|
| `raspi_main.py` | Main control loop |
| `raspi_config.py` | System configuration |
| `raspi_i2c_master.py` | I2C communication |
| `raspi_oled_manager.py` | Display management |
| `raspi_tca9548a.py` | Multiplexer control |

#### 4. Test Scripts
| File | Purpose |
|------|---------|
| `test_pca9548a_esp.py` | Test all ESP modules |
| `test_reactor_flow_sequence.py` | PWR startup demo ⭐ |
| `test_visualizer_interactive.py` | Manual visualizer test |

---

## 🆕 New in V2.0

### Added Files:
- ✅ `ESP_E_I2C.ino` - 3-flow version
- ✅ `WIRING_3_FLOWS.md` - Multi-flow wiring
- ✅ `REACTOR_FLOW_LOGIC.md` - PWR theory
- ✅ `test_reactor_flow_sequence.py` - Educational test
- ✅ `SYSTEM_ARCHITECTURE_V2.md` - New architecture
- ✅ `CHANGELOG_V2.md` - Change history
- ✅ `DEPRECATED_FILES.md` - Removed files record
- ✅ `PROJECT_STRUCTURE_V2.md` - This file
- ✅ `cleanup_v2.bat/sh` - Cleanup scripts

### Removed Folders:
- ❌ `ESP_F_Aliran_Sekunder/` → Merged into ESP-E
- ❌ `ESP_G_Aliran_Tersier/` → Merged into ESP-E

---

## 📦 Dependencies

### ESP32 (Arduino):
```
Wire.h          # I2C communication
Servo.h         # (ESP-B, ESP-C only)
```

### Raspberry Pi (Python):
```
smbus2          # I2C communication
RPi.GPIO        # GPIO control
Adafruit-SSD1306  # OLED displays
PIL             # Image processing
opencv-python   # Video processing
```

---

## 🔄 Typical Workflow

### 1. Development:
```
Edit firmware → Upload to ESP → Test with Python scripts
```

### 2. Testing:
```bash
# Test individual ESP
python3 test_pca9548a_esp.py

# Test flow sequence
python3 test_reactor_flow_sequence.py

# Run full system
python3 raspi_main.py
```

### 3. Deployment:
```
Wire hardware → Flash firmware → Configure Raspi → Run
```

---

## 📈 Project Statistics

### Code Metrics:
- **Total lines of code:** ~4,500 (was ~5,200)
- **Documentation lines:** ~3,000
- **Test code lines:** ~1,200
- **Arduino files:** 3
- **Python files:** 9
- **Markdown docs:** 18

### Hardware:
- **ESP32 modules:** 3 (was 5)
- **CD74HC4067 MUX:** 3 (new)
- **OLED displays:** 4
- **LEDs:** 48+
- **Servo motors:** 5

---

## 🎓 Learning Resources

### For Students:
1. **PWR Operation:** `REACTOR_FLOW_LOGIC.md`
2. **I2C Communication:** `SYSTEM_ARCHITECTURE_V2.md`
3. **Multiplexing:** `WIRING_3_FLOWS.md`
4. **System Integration:** `raspi_main.py` + comments

### For Developers:
1. **API Reference:** Code comments in Python files
2. **Protocol Specs:** `raspi_i2c_master.py` docstrings
3. **Test Examples:** `test_*.py` files
4. **Hardware Setup:** `WIRING_*.md` files

---

## 🔧 Maintenance

### Regular Tasks:
- Update firmware when logic changes
- Test I2C communication periodically
- Check LED animations
- Verify sensor readings
- Review log files

### Files to Update:
- `CHANGELOG_V2.md` - When making changes
- `README.md` - For major features
- Test scripts - When adding features
- Documentation - Keep in sync with code

---

## 📞 Quick Reference

### Most Used Files:
```
Upload firmware:      ESP_*/ESP_*_I2C/*.ino
Run simulator:        raspi_main.py
Test system:          test_pca9548a_esp.py
Configure:            raspi_config.py
Read theory:          REACTOR_FLOW_LOGIC.md
Check wiring:         WIRING_3_FLOWS.md
```

### Most Edited Files:
```
raspi_main.py         # Control logic
raspi_config.py       # Parameters
ESP_E_I2C.ino        # LED animations
```

---

**Version:** 2.0.0  
**Last Updated:** 2024-12-02  
**Total Files:** ~35 (was ~42)  
**Status:** Production Ready

✅ **Simplified, documented, and organized!**
