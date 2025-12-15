# UART Wiring Guide - Raspberry Pi ↔ ESP32

**Date:** 2024-12-15  
**Communication:** UART (Serial) instead of I2C  
**Baudrate:** 115200 bps, 8N1  

---

## 📊 Complete Wiring Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      RASPBERRY PI 4                              │
│                                                                  │
│  GPIO 2  (Pin 3)  ────────────┐                                 │
│  GPIO 3  (Pin 5)  ────────────┼───── I2C Bus (OLEDs only)       │
│                               │                                  │
│  GPIO 14 (Pin 8)  ─────┐      │                                 │
│  GPIO 15 (Pin 10) ─────┼──────┼─── UART0 (ESP-BC)               │
│                        │      │                                  │
│  GPIO 0  (Pin 27) ─────┼──────┼─── UART2 (ESP-E) ⚠️ Enable!     │
│  GPIO 1  (Pin 28) ─────┼──────┼─── UART2                        │
│                        │      │                                  │
│  GND     (Pin 6,14,20) ┴──────┴─── Common Ground                │
└───────────────────────┬┬┬──────────────────────────────────────┘
                        │││
        ┌───────────────┘││
        │    ┌────────────┘│
        │    │    ┌────────┘
        │    │    │
        ▼    ▼    ▼
┌───────────────────┐        ┌───────────────────┐
│    ESP-BC         │        │    ESP-E          │
│    (ESP32 #1)     │        │    (ESP32 #2)     │
├───────────────────┤        ├───────────────────┤
│ GPIO 16 (RX2) ◄───┼────────┼─ RasPi GPIO 14    │
│ GPIO 17 (TX2) ────┼───────►│   (UART0 TX)      │
│                   │        │                   │
│ GPIO 16 (RX2) ◄───┼────────┼─ RasPi GPIO 0     │
│ GPIO 17 (TX2) ────┼───────►│   (UART2 TX)      │
│                   │        │                   │
│ GND ──────────────┼────────┼─ RasPi GND        │
│ 5V ───────────────┼────────┼─ Power Supply     │
└───────────────────┘        └───────────────────┘
```

---

## 🔌 ESP-BC Wiring (Control Rods + Turbine)

### **UART Connection:**
```
ESP32 (ESP-BC)          Raspberry Pi 4
────────────────────    ─────────────────────────
GPIO 16 (RX2)    ◄────  GPIO 14 (TX, Pin 8)
GPIO 17 (TX2)    ─────► GPIO 15 (RX, Pin 10)
GND              ────── GND (Pin 6, 14, or 20)
5V               ────── 5V Power Supply
```

### **Important Notes:**
- ✅ **RX ↔ TX crossed** (ESP RX ← RasPi TX, ESP TX → RasPi RX)
- ✅ **Common ground** required
- ✅ **No level shifter needed** (both 3.3V logic)
- ⚠️ **Do NOT connect GPIO 21/22** (reserved for future use)

### **Other Peripherals (Same as before):**
```
Servos:
- GPIO 13: Safety Rod
- GPIO 12: Shim Rod
- GPIO 14: Regulating Rod

Humidifier Relays:
- GPIO 25: Steam Generator 1
- GPIO 26: Steam Generator 2
- GPIO 27: Cooling Tower 1
- GPIO 32: Cooling Tower 2
- GPIO 33: Cooling Tower 3
- GPIO 34: Cooling Tower 4
```

---

## 🔌 ESP-E Wiring (LED Visualizer)

### **UART Connection:**
```
ESP32 (ESP-E)           Raspberry Pi 4
────────────────────    ─────────────────────────
GPIO 16 (RX2)    ◄────  GPIO 0 (TX, Pin 27) ⚠️
GPIO 17 (TX2)    ─────► GPIO 1 (RX, Pin 28) ⚠️
GND              ────── GND (Pin 6, 14, or 20)
5V               ────── 5V Power Supply
```

### **⚠️ IMPORTANT: Enable UART2 on Raspberry Pi!**

GPIO 0 and 1 need to be enabled as UART2:

```bash
# Edit config file
sudo nano /boot/config.txt

# Add this line at the end:
dtoverlay=uart2

# Save and reboot
sudo reboot
```

### **Other Peripherals (Same as before):**
```
LED Multiplexers:
- GPIO 14, 27, 26, 25: Selector (S0-S3)
- GPIO 33, 15, 2: Enable (EN)
- GPIO 32, 4, 16: PWM Signal

Power Indicator LEDs:
- GPIO 23, 19, 18: 3 LED groups
```

---

## 📋 Step-by-Step Wiring

### **Materials Needed:**
- [ ] 8 x Jumper wires (male-to-female)
- [ ] 1 x Breadboard (optional, for prototyping)
- [ ] 1 x Multimeter (for testing continuity)
- [ ] 2 x ESP32 Dev Boards
- [ ] 1 x Raspberry Pi 4
- [ ] Power supply (5V, 3A minimum)

### **Step 1: Power OFF Everything**
```bash
# Shutdown Raspberry Pi
sudo shutdown -h now

# Wait for complete shutdown
# Disconnect power from all devices
```

### **Step 2: Disconnect Old I2C Wiring**
```
Remove these connections:
❌ ESP-BC GPIO 21 (I2C SDA) from TCA9548A #1
❌ ESP-BC GPIO 22 (I2C SCL) from TCA9548A #1
❌ ESP-E GPIO 21 (I2C SDA) from TCA9548A #2
❌ ESP-E GPIO 22 (I2C SCL) from TCA9548A #2

Keep these connections:
✅ All OLED I2C connections (unchanged)
✅ TCA9548A multiplexers (for OLEDs only)
✅ All other ESP peripherals (servos, relays, LEDs)
```

### **Step 3: Connect ESP-BC UART**
```
1. ESP-BC GPIO 16 (RX2) → Raspberry Pi Pin 8 (GPIO 14, TX)
2. ESP-BC GPIO 17 (TX2) → Raspberry Pi Pin 10 (GPIO 15, RX)
3. ESP-BC GND → Raspberry Pi Pin 6 (GND)
4. Verify with multimeter (continuity test)
```

### **Step 4: Connect ESP-E UART**
```
1. ESP-E GPIO 16 (RX2) → Raspberry Pi Pin 27 (GPIO 0, TX)
2. ESP-E GPIO 17 (TX2) → Raspberry Pi Pin 28 (GPIO 1, RX)
3. ESP-E GND → Raspberry Pi Pin 14 (GND)
4. Verify with multimeter (continuity test)
```

### **Step 5: Enable UART2 on Raspberry Pi**
```bash
# Power ON Raspberry Pi only (not ESPs yet)

# Edit config
sudo nano /boot/config.txt

# Add at the end:
enable_uart=1
dtoverlay=uart2

# Save (Ctrl+O, Enter, Ctrl+X)

# Reboot
sudo reboot

# After reboot, verify:
ls -l /dev/ttyAMA*

# Should see:
# /dev/ttyAMA0 (UART0 - GPIO 14/15)
# /dev/ttyAMA1 (UART2 - GPIO 0/1)
```

### **Step 6: Upload ESP Firmware**
```bash
# Using Arduino IDE:

# For ESP-BC:
1. Open: esp_utama/esp_utama_uart.ino
2. Select Board: ESP32 Dev Module
3. Select Port: /dev/ttyUSB0 (or your ESP's port)
4. Upload
5. Open Serial Monitor (115200 baud)
6. Check for: "✅ UART2 initialized at 115200 baud"

# For ESP-E:
1. Open: esp_visualizer/esp_visualizer_uart.ino
2. Same steps as above
3. Check Serial Monitor for confirmation
```

### **Step 7: Test UART Communication**
```bash
cd ~/pkm-simulator-PLTN/raspi_central_control

# Make test script executable
chmod +x test_uart_esp.py

# Run test
python3 test_uart_esp.py

# Expected output:
# ✅ ESP-BC: PASS
# ✅ ESP-E: PASS
```

### **Step 8: Run Main Program**
```bash
python3 raspi_main_panel.py

# Check log for:
# ✅ UART Master initialized
# ✅ ESP-BC connected
# ✅ ESP-E connected
```

---

## 🔍 Troubleshooting

### **Problem: /dev/ttyAMA1 not found**

**Solution:**
```bash
# Check if UART2 overlay loaded
dtoverlay -l | grep uart

# If not found, add to /boot/config.txt:
dtoverlay=uart2

# Reboot
sudo reboot
```

### **Problem: Permission denied on /dev/ttyAMA0**

**Solution:**
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Logout and login again, or reboot
sudo reboot
```

### **Problem: ESP not responding**

**Solution:**
```bash
# Check ESP Serial Monitor
# Should see: "✅ UART2 initialized"

# If not:
1. Re-upload firmware
2. Check wiring (RX↔TX must be crossed)
3. Check GND connection
4. Press RESET button on ESP
```

### **Problem: Garbled data**

**Solution:**
```bash
# Check baudrate matches on both sides:
# ESP: UART_BAUD 115200
# RasPi: baudrate=115200

# Check wiring quality (loose connections)
# Use shorter wires (< 30cm)
```

---

## ✅ Verification Checklist

Before running main program:

- [ ] All old I2C wires removed from ESPs
- [ ] ESP-BC UART wired (GPIO 16/17 ↔ RasPi GPIO 14/15)
- [ ] ESP-E UART wired (GPIO 16/17 ↔ RasPi GPIO 0/1)
- [ ] Common GND connected
- [ ] /boot/config.txt has `dtoverlay=uart2`
- [ ] `/dev/ttyAMA0` and `/dev/ttyAMA1` exist
- [ ] User in `dialout` group
- [ ] ESP-BC firmware uploaded (uart version)
- [ ] ESP-E firmware uploaded (uart version)
- [ ] Serial Monitor shows "UART Ready"
- [ ] `test_uart_esp.py` passes
- [ ] OLED connections unchanged (still working)

---

## 📸 Wiring Photos Reference

**Raspberry Pi GPIO Header (Looking at board from above):**
```
    3V3  (1) (2)  5V
  GPIO2  (3) (4)  5V
  GPIO3  (5) (6)  GND
  GPIO4  (7) (8)  GPIO14 ← UART0 TX (ESP-BC)
    GND  (9) (10) GPIO15 ← UART0 RX (ESP-BC)
...
  GPIO0 (27) (28) GPIO1   ← UART2 (ESP-E)
```

**ESP32 Dev Board:**
```
[USB Port]
    ↓
┌───────────┐
│ GPIO 16   │ ← UART2 RX (connect to RasPi TX)
│ GPIO 17   │ ← UART2 TX (connect to RasPi RX)
│ GND       │ ← Common GND
│ 3V3       │ (not used, use external 5V)
│ 5V/VIN    │ ← External 5V power
└───────────┘
```

---

**Status:** ✅ **READY FOR IMPLEMENTATION**

**Next:** Upload firmware dan test dengan `test_uart_esp.py`

