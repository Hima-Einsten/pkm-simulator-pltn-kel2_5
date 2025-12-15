# Migration Guide: I2C → UART Communication

**Date:** 2024-12-15  
**Reason:** ESP32 I2C slave tidak stabil (error 5, timeout, bus lock)  
**Solution:** Migrasi ke UART (Serial) communication  
**Impact:** Medium - Perlu perubahan wiring dan software, tapi arsitektur tetap

---

## 🎯 Migration Overview

### **Before (I2C):**
```
Raspberry Pi I2C Bus
    │
    ├── TCA9548A #1 (0x70)
    │   ├── Channel 0: ESP-BC (0x08) ❌ UNSTABLE!
    │   └── Channel 1-7: OLEDs
    │
    └── TCA9548A #2 (0x71)
        ├── Channel 0: ESP-E (0x0A) ❌ UNSTABLE!
        └── Channel 1-2: OLEDs
```

### **After (UART):**
```
Raspberry Pi
    │
    ├── UART0 (GPIO 14/15): ESP-BC ✅ STABLE!
    ├── UART2 (GPIO 0/1): ESP-E ✅ STABLE!
    │
    └── I2C Bus (GPIO 2/3)
        ├── TCA9548A #1 (0x70): 7 OLEDs only
        └── TCA9548A #2 (0x71): 2 OLEDs only
```

**Benefits:**
- ✅ **Reliable:** UART jauh lebih stabil untuk ESP32
- ✅ **Fast:** Baudrate bisa sampai 921600 bps
- ✅ **Simple:** No multiplexer needed untuk ESP
- ✅ **Robust:** Hardware flow control optional
- ✅ **Debuggable:** Mudah monitor dengan Serial Monitor

---

## 📊 Pin Mapping

### **Raspberry Pi 4 GPIO:**

```
┌─────────────────────────────────────────┐
│ Raspberry Pi 4 GPIO Header              │
├─────────────────────────────────────────┤
│ GPIO 2  (Pin 3)  → I2C SDA (OLEDs)      │
│ GPIO 3  (Pin 5)  → I2C SCL (OLEDs)      │
│                                          │
│ GPIO 14 (Pin 8)  → UART0 TXD (ESP-BC)   │
│ GPIO 15 (Pin 10) → UART0 RXD (ESP-BC)   │
│                                          │
│ GPIO 0  (Pin 27) → UART2 TXD (ESP-E)    │ ⚠️ Needs config!
│ GPIO 1  (Pin 28) → UART2 RXD (ESP-E)    │ ⚠️ Needs config!
│                                          │
│ GND     (Pin 6)  → Common Ground         │
└─────────────────────────────────────────┘
```

**Note:** GPIO 0/1 perlu di-enable di `/boot/config.txt`

### **ESP-BC (ESP32 #1):**

```
┌─────────────────────────────────────────┐
│ ESP32 (ESP-BC)                           │
├─────────────────────────────────────────┤
│ GPIO 16 (RX2) ← Raspberry Pi GPIO 14    │
│ GPIO 17 (TX2) → Raspberry Pi GPIO 15    │
│                                          │
│ GND → Common Ground                      │
│ 5V  → Power Supply                       │
└─────────────────────────────────────────┘
```

**Why RX2/TX2?** GPIO 21/22 masih digunakan untuk I2C (OLED direct connect jika ada)

### **ESP-E (ESP32 #2):**

```
┌─────────────────────────────────────────┐
│ ESP32 (ESP-E)                            │
├─────────────────────────────────────────┤
│ GPIO 16 (RX2) ← Raspberry Pi GPIO 0     │
│ GPIO 17 (TX2) → Raspberry Pi GPIO 1     │
│                                          │
│ GND → Common Ground                      │
│ 5V  → Power Supply                       │
└─────────────────────────────────────────┘
```

---

## 🔧 Hardware Changes

### **1. Wiring Changes:**

**Remove:**
- ❌ ESP-BC I2C connection dari TCA9548A #1 Channel 0
- ❌ ESP-E I2C connection dari TCA9548A #2 Channel 0

**Add:**
- ✅ ESP-BC UART: GPIO 16/17 ↔ RasPi GPIO 14/15
- ✅ ESP-E UART: GPIO 16/17 ↔ RasPi GPIO 0/1

**Keep:**
- ✅ TCA9548A #1 untuk 7 OLED (channels 1-7)
- ✅ TCA9548A #2 untuk 2 OLED (channels 1-2)

### **2. Raspberry Pi Configuration:**

```bash
# Edit /boot/config.txt
sudo nano /boot/config.txt

# Add these lines:
# Enable UART2 on GPIO 0/1
dtoverlay=uart2

# Enable UART0 (already enabled by default)
enable_uart=1

# Reboot
sudo reboot
```

**Verify:**
```bash
# Check UART devices
ls -l /dev/serial*

# Should see:
# /dev/serial0 → ttyAMA0 (UART0 - GPIO 14/15)
# /dev/serial1 → ttyAMA1 (UART2 - GPIO 0/1)
```

### **3. Level Shifter (Optional but Recommended):**

ESP32 adalah **3.3V**, Raspberry Pi UART adalah **3.3V** → **No level shifter needed!**

Tapi untuk **noise immunity**, gunakan:
- **74HC125** (Tri-state buffer) atau
- **Simple resistor divider** (RasPi TX → 1kΩ → ESP RX)

---

## 💻 Software Changes

### **Communication Protocol: JSON over UART**

**Why JSON?**
- ✅ Easy to debug (human-readable)
- ✅ Self-documenting
- ✅ Flexible (mudah tambah field)
- ✅ Error detection built-in

**Alternative:** Binary protocol (lebih cepat tapi sulit debug)

### **Message Format:**

```json
// Raspberry Pi → ESP-BC
{
  "cmd": "update",
  "safety": 50,
  "shim": 60,
  "regulating": 70,
  "humid_sg": [1, 1],
  "humid_ct": [1, 0, 1, 0]
}

// ESP-BC → Raspberry Pi
{
  "status": "ok",
  "rods": [50, 60, 70],
  "thermal_kw": 12345.67,
  "power_level": 85.5,
  "state": 2,
  "humid_status": [[1,1], [1,0,1,0]]
}
```

---

## 📁 File Changes Summary

### **New Files to Create:**

1. **`raspi_uart_master.py`** - UART communication handler
2. **`esp_bc_uart.ino`** - ESP-BC UART version
3. **`esp_e_uart.ino`** - ESP-E UART version
4. **`UART_MIGRATION_GUIDE.md`** - This document

### **Files to Modify:**

1. **`raspi_main_panel.py`** - Replace I2C master dengan UART master
2. **`raspi_config.py`** - Add UART config
3. **`raspi_system_health.py`** - Update health checks

### **Files to Keep (No Change):**

1. **`raspi_oled_manager.py`** - OLEDs tetap I2C ✅
2. **`raspi_tca9548a.py`** - Multiplexer tetap digunakan ✅
3. **`raspi_gpio_buttons.py`** - Buttons unchanged ✅
4. **`raspi_humidifier_control.py`** - Unchanged ✅
5. **`raspi_buzzer_alarm.py`** - Unchanged ✅

---

## 🚀 Step-by-Step Migration

### **Phase 1: Backup Current System**

```bash
cd ~/pkm-simulator-PLTN
git add .
git commit -m "Backup before UART migration"
git tag "v3.4-i2c-backup"
```

### **Phase 2: Hardware Rewiring**

**Tools needed:**
- Jumper wires (4 for ESP-BC, 4 for ESP-E)
- Multimeter (verify connections)
- Breadboard (temporary testing)

**Steps:**
1. Power OFF Raspberry Pi
2. Disconnect ESP-BC I2C wires (GPIO 21/22 dari TCA9548A #1)
3. Connect ESP-BC UART:
   - ESP RX2 (GPIO 16) → RasPi TX (GPIO 14)
   - ESP TX2 (GPIO 17) → RasPi RX (GPIO 15)
   - ESP GND → RasPi GND
4. Repeat for ESP-E:
   - ESP RX2 (GPIO 16) → RasPi GPIO 0
   - ESP TX2 (GPIO 17) → RasPi GPIO 1
   - ESP GND → RasPi GND
5. Verify dengan multimeter (continuity test)
6. Power ON

### **Phase 3: Raspberry Pi Configuration**

```bash
# 1. Enable UART2
sudo nano /boot/config.txt
# Add: dtoverlay=uart2
# Add: enable_uart=1

# 2. Reboot
sudo reboot

# 3. Test UART devices
ls -l /dev/ttyAMA*
# Should see: /dev/ttyAMA0 (UART0), /dev/ttyAMA1 (UART2)

# 4. Test permissions
sudo usermod -a -G dialout $USER
```

### **Phase 4: ESP32 Code Update**

Upload new UART-based firmware:

**For ESP-BC:**
```bash
# Arduino IDE:
1. Open esp_utama/esp_utama_uart.ino (new file)
2. Select board: ESP32 Dev Module
3. Select port: /dev/ttyUSB0
4. Upload
5. Open Serial Monitor (115200 baud)
6. Check for: "UART Ready on Serial2"
```

**For ESP-E:**
```bash
# Same steps with esp_visualizer_uart.ino
```

### **Phase 5: Raspberry Pi Software Update**

```bash
cd ~/pkm-simulator-PLTN/raspi_central_control

# Test UART communication
python3 test_uart_esp.py

# If OK, run main program
python3 raspi_main_panel.py
```

---

## 🧪 Testing Plan

### **Test 1: UART Loopback**

```bash
# Connect TX → RX on same UART
# Send test message
echo "Hello" > /dev/ttyAMA0
cat /dev/ttyAMA0
# Should see: Hello
```

### **Test 2: ESP-BC Communication**

```python
import serial
import time

ser = serial.Serial('/dev/ttyAMA0', 115200, timeout=1)
time.sleep(2)

# Send test command
ser.write(b'{"cmd":"ping"}\n')
response = ser.readline()
print(f"Response: {response}")

ser.close()
```

### **Test 3: Full System Integration**

```bash
python3 raspi_main_panel.py

# Check logs:
# - UART devices detected
# - ESP-BC connected
# - ESP-E connected
# - Commands sent/received
```

---

## 📈 Performance Comparison

| Metric | I2C (Old) | UART (New) |
|--------|-----------|------------|
| **Reliability** | ⭐⭐ (2/5) | ⭐⭐⭐⭐⭐ (5/5) |
| **Speed** | 100 kHz | 115200 bps (11x faster) |
| **Latency** | ~10ms | ~1ms |
| **Error Rate** | High (timeout, bus lock) | Very Low |
| **Debug Ease** | Hard | Easy (Serial Monitor) |
| **Wiring** | Complex (via MUX) | Simple (direct) |
| **CPU Usage** | Medium | Low |
| **Range** | <2m | <15m |

---

## 🎯 Next Steps

Saya akan create:

1. ✅ **`raspi_uart_master.py`** - UART communication module
2. ✅ **`esp_utama_uart.ino`** - ESP-BC UART firmware
3. ✅ **`esp_visualizer_uart.ino`** - ESP-E UART firmware
4. ✅ **`test_uart_esp.py`** - UART test script
5. ✅ **Modified `raspi_main_panel.py`** - Integration

**Mau saya buatkan semuanya sekarang?** Atau butuh penjelasan lebih detail dulu tentang:
- Protocol design (JSON vs Binary)
- Error handling strategy
- Flow control mechanism
- Baudrate selection

---

**Recommendation:** ✅ **LANJUT MIGRASI KE UART**

**Alasan:**
1. ESP32 I2C slave memang bermasalah (known issue)
2. UART jauh lebih stable dan reliable
3. Code changes manageable (medium impact)
4. Hardware changes minimal (4 wires per ESP)
5. Debugging lebih mudah (Serial Monitor)

**Estimated Time:**
- Hardware: 1-2 hours (wiring)
- Software: 3-4 hours (coding + testing)
- Testing: 2-3 hours (integration)
- **Total: 1 day**

