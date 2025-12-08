# I2C Address Mapping & Wiring Guide

**Date:** 2024-12-08  
**System:** PKM PLTN Simulator - 2 ESP Architecture  
**Multiplexer:** 2x TCA9548A (8-channel I2C multiplexer)

---

## 📡 I2C System Overview

### Architecture:
```
Raspberry Pi 4 (Master)
    │
    ├─── I2C Bus 1 (GPIO 2/3 - SDA/SCL)
    │
    ├─── TCA9548A #1 (0x70) ────┐
    │    ├─ Channel 0: ESP-BC    │
    │    ├─ Channel 1: OLED #1   │
    │    ├─ Channel 2: OLED #2   │
    │    ├─ Channel 3: OLED #3   │
    │    ├─ Channel 4: OLED #4   │
    │    ├─ Channel 5: OLED #5   │
    │    ├─ Channel 6: OLED #6   │
    │    └─ Channel 7: OLED #7   │
    │                             │
    └─── TCA9548A #2 (0x71) ────┘
         ├─ Channel 0: ESP-E
         ├─ Channel 1: OLED #8
         ├─ Channel 2: OLED #9
         └─ Channel 3-7: (Reserved)
```

---

## 🔌 I2C Address Table

### **TCA9548A Multiplexers:**

| Device | I2C Address | Notes |
|--------|-------------|-------|
| TCA9548A #1 | **0x70** | Main multiplexer (ESP-BC + 7 OLEDs) |
| TCA9548A #2 | **0x71** | Secondary multiplexer (ESP-E + 2 OLEDs) |

### **ESP32 Slaves:**

| Device | I2C Address | Connected To | Function |
|--------|-------------|--------------|----------|
| **ESP-BC** | **0x08** | TCA9548A #1, Ch 0 | Control Rods + Turbine + Humidifier + Pumps |
| **ESP-E** | **0x0A** | TCA9548A #2, Ch 0 | 3-Flow LED Visualizer (48 LEDs) |

### **OLED Displays (9 units):**

All OLEDs use the **same I2C address: 0x3C** (standard SSD1306)

| Display | I2C Address | Connected To | Display Content |
|---------|-------------|--------------|-----------------|
| **OLED #1** | 0x3C | TCA9548A #1, Ch 1 | **Pressurizer** (Pressure bar) |
| **OLED #2** | 0x3C | TCA9548A #1, Ch 2 | **Pump Primary** (Status + PWM) |
| **OLED #3** | 0x3C | TCA9548A #1, Ch 3 | **Pump Secondary** (Status + PWM) |
| **OLED #4** | 0x3C | TCA9548A #1, Ch 4 | **Pump Tertiary** (Status + PWM) |
| **OLED #5** | 0x3C | TCA9548A #1, Ch 5 | **Safety Rod** (Position 0-100%) |
| **OLED #6** | 0x3C | TCA9548A #1, Ch 6 | **Shim Rod** (Position 0-100%) |
| **OLED #7** | 0x3C | TCA9548A #1, Ch 7 | **Regulating Rod** (Position 0-100%) |
| **OLED #8** | 0x3C | TCA9548A #2, Ch 1 | **Thermal Power** (kW) |
| **OLED #9** | 0x3C | TCA9548A #2, Ch 2 | **System Status** (State info) |

---

## 🔧 TCA9548A Channel Mapping

### **TCA9548A #1 (Address: 0x70)**

| Channel | Device | I2C Address | Purpose |
|---------|--------|-------------|---------|
| **0** | ESP-BC | 0x08 | Main ESP32 (Control + Pumps + Turbine + Humidifiers) |
| **1** | OLED #1 | 0x3C | Pressurizer Display |
| **2** | OLED #2 | 0x3C | Pump Primary Display |
| **3** | OLED #3 | 0x3C | Pump Secondary Display |
| **4** | OLED #4 | 0x3C | Pump Tertiary Display |
| **5** | OLED #5 | 0x3C | Safety Rod Display |
| **6** | OLED #6 | 0x3C | Shim Rod Display |
| **7** | OLED #7 | 0x3C | Regulating Rod Display |

### **TCA9548A #2 (Address: 0x71)**

| Channel | Device | I2C Address | Purpose |
|---------|--------|-------------|---------|
| **0** | ESP-E | 0x0A | LED Visualizer (3 Flow Animations) |
| **1** | OLED #8 | 0x3C | Thermal Power Display |
| **2** | OLED #9 | 0x3C | System Status Display |
| **3** | - | - | Reserved (Future expansion) |
| **4** | - | - | Reserved |
| **5** | - | - | Reserved |
| **6** | - | - | Reserved |
| **7** | - | - | Reserved |

---

## 📋 Wiring Checklist

### **Raspberry Pi Connections:**

```
Raspberry Pi 4 GPIO Header:
├─ GPIO 2 (Pin 3)  → I2C SDA (Common bus for both TCA9548A)
├─ GPIO 3 (Pin 5)  → I2C SCL (Common bus for both TCA9548A)
├─ 3.3V (Pin 1)    → Power for I2C devices
└─ GND (Pin 6)     → Common ground
```

### **TCA9548A #1 (0x70) Wiring:**

**Main connections:**
- VCC → 3.3V (Raspberry Pi)
- GND → GND (Raspberry Pi)
- SDA → GPIO 2 (Raspberry Pi)
- SCL → GPIO 3 (Raspberry Pi)
- A0, A1, A2 → GND (Address = 0x70)

**Channel connections:**
- SD0/SC0 → ESP-BC (SDA/SCL)
- SD1/SC1 → OLED #1 (SDA/SCL)
- SD2/SC2 → OLED #2 (SDA/SCL)
- SD3/SC3 → OLED #3 (SDA/SCL)
- SD4/SC4 → OLED #4 (SDA/SCL)
- SD5/SC5 → OLED #5 (SDA/SCL)
- SD6/SC6 → OLED #6 (SDA/SCL)
- SD7/SC7 → OLED #7 (SDA/SCL)

### **TCA9548A #2 (0x71) Wiring:**

**Main connections:**
- VCC → 3.3V (Raspberry Pi)
- GND → GND (Raspberry Pi)
- SDA → GPIO 2 (Raspberry Pi) - Same bus as #1
- SCL → GPIO 3 (Raspberry Pi) - Same bus as #1
- A0 → 3.3V, A1 → GND, A2 → GND (Address = 0x71)

**Channel connections:**
- SD0/SC0 → ESP-E (SDA/SCL)
- SD1/SC1 → OLED #8 (SDA/SCL)
- SD2/SC2 → OLED #9 (SDA/SCL)
- SD3-SD7 → Not connected (Reserved)

### **ESP32 Connections:**

**ESP-BC (0x08):**
```
ESP32 Pin 21 (SDA) → TCA9548A #1, Channel 0 (SD0)
ESP32 Pin 22 (SCL) → TCA9548A #1, Channel 0 (SC0)
ESP32 GND → Common GND
ESP32 5V → Power supply (separate from I2C)
```

**ESP-E (0x0A):**
```
ESP32 Pin 21 (SDA) → TCA9548A #2, Channel 0 (SD0)
ESP32 Pin 22 (SCL) → TCA9548A #2, Channel 0 (SC0)
ESP32 GND → Common GND
ESP32 5V → Power supply (separate from I2C)
```

### **OLED Display Connections:**

Each OLED (128x64, SSD1306, 0x3C):
```
VCC → 3.3V (from TCA9548A power rail)
GND → Common GND
SDA → Respective TCA9548A channel SDx
SCL → Respective TCA9548A channel SCx
```

---

## 💻 Software Configuration

### **Python Code (raspi_config.py):**

```python
# TCA9548A Multiplexer Addresses
MUX_ADDRESS_1 = 0x70  # Main multiplexer
MUX_ADDRESS_2 = 0x71  # Secondary multiplexer

# ESP I2C Addresses
ESP_BC_ADDRESS = 0x08  # Control Rods + Turbine + Humidifier + Pumps
ESP_E_ADDRESS = 0x0A   # 3-Flow LED Visualizer

# OLED Display Address (same for all)
OLED_ADDRESS = 0x3C

# TCA9548A #1 (0x70) Channel Mapping
ESP_BC_CHANNEL = 0
OLED_PRESSURIZER_CHANNEL = 1
OLED_PUMP_PRIMARY_CHANNEL = 2
OLED_PUMP_SECONDARY_CHANNEL = 3
OLED_PUMP_TERTIARY_CHANNEL = 4
OLED_SAFETY_ROD_CHANNEL = 5
OLED_SHIM_ROD_CHANNEL = 6
OLED_REGULATING_ROD_CHANNEL = 7

# TCA9548A #2 (0x71) Channel Mapping
ESP_E_CHANNEL = 0
OLED_THERMAL_CHANNEL = 1
OLED_STATUS_CHANNEL = 2
```

### **Channel Selection Function:**

```python
def select_mux_channel(mux_address, channel):
    """
    Select a channel on TCA9548A multiplexer
    
    Args:
        mux_address: 0x70 or 0x71
        channel: 0-7
    """
    if channel > 7:
        return False
    
    bus.write_byte(mux_address, 1 << channel)
    return True
```

### **Usage Example:**

```python
# Communicate with ESP-BC
select_mux_channel(0x70, 0)  # Select TCA9548A #1, Channel 0
i2c_master.update_esp_bc(...)

# Update OLED #1 (Pressurizer)
select_mux_channel(0x70, 1)  # Select TCA9548A #1, Channel 1
oled_manager.update_pressurizer(...)

# Communicate with ESP-E
select_mux_channel(0x71, 0)  # Select TCA9548A #2, Channel 0
i2c_master.update_esp_e(...)

# Update OLED #8 (Thermal Power)
select_mux_channel(0x71, 1)  # Select TCA9548A #2, Channel 1
oled_manager.update_thermal(...)
```

---

## 🧪 Testing & Verification

### **I2C Device Detection:**

```bash
# Check main I2C bus
i2cdetect -y 1

# Expected output:
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 10:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 20:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 30:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 40:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 50:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 60:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 70: 70 71 -- -- -- -- -- --
```

### **TCA9548A #1 Channel Test:**

```python
import smbus2

bus = smbus2.SMBus(1)

# Test each channel on TCA9548A #1 (0x70)
for channel in range(8):
    bus.write_byte(0x70, 1 << channel)
    time.sleep(0.1)
    
    # Scan for devices
    devices = []
    for addr in range(3, 128):
        try:
            bus.read_byte(addr)
            devices.append(hex(addr))
        except:
            pass
    
    print(f"Channel {channel}: {devices}")

# Expected output:
# Channel 0: ['0x08']  # ESP-BC
# Channel 1: ['0x3c']  # OLED #1
# Channel 2: ['0x3c']  # OLED #2
# Channel 3: ['0x3c']  # OLED #3
# Channel 4: ['0x3c']  # OLED #4
# Channel 5: ['0x3c']  # OLED #5
# Channel 6: ['0x3c']  # OLED #6
# Channel 7: ['0x3c']  # OLED #7
```

### **TCA9548A #2 Channel Test:**

```python
# Test each channel on TCA9548A #2 (0x71)
for channel in range(3):
    bus.write_byte(0x71, 1 << channel)
    time.sleep(0.1)
    
    devices = []
    for addr in range(3, 128):
        try:
            bus.read_byte(addr)
            devices.append(hex(addr))
        except:
            pass
    
    print(f"Channel {channel}: {devices}")

# Expected output:
# Channel 0: ['0x0a']  # ESP-E
# Channel 1: ['0x3c']  # OLED #8
# Channel 2: ['0x3c']  # OLED #9
```

---

## 📊 Communication Protocol Summary

### **ESP-BC (0x08):**

**Send (12 bytes):**
```
Byte 0-2:   Control rod targets (uint8, 0-100%)
Byte 3:     Reserved
Byte 4-7:   Reserved (float)
Byte 8:     Humidifier commands (6 relays bit-packed)
Byte 9-11:  Reserved
```

**Receive (20 bytes):**
```
Byte 0-2:   Control rod actual positions (uint8)
Byte 3:     Reserved
Byte 4-7:   Thermal power (float, kW)
Byte 8-11:  Turbine power level (float, %)
Byte 12-15: Turbine state (uint32)
Byte 16-17: Generator/turbine status (uint8)
Byte 18-19: Humidifier status (6 relays bit-packed)
```

### **ESP-E (0x0A):**

**Send (16 bytes):**
```
Byte 0:     Register address (0x00)
Byte 1-4:   Primary pressure (float)
Byte 5:     Primary pump status (uint8)
Byte 6-9:   Secondary pressure (float)
Byte 10:    Secondary pump status (uint8)
Byte 11-14: Tertiary pressure (float)
Byte 15:    Tertiary pump status (uint8)
```

**Receive (2 bytes):**
```
Byte 0:     Animation speed (uint8)
Byte 1:     LED count (uint8)
```

### **OLED Displays (0x3C):**

Standard SSD1306 I2C protocol:
- Resolution: 128x64 pixels
- Driver: SSD1306
- Library: Adafruit_SSD1306 or luma.oled
- Updates: Write framebuffer then display

---

## ⚠️ Important Notes

### **Address Conflicts:**
- ✅ All 9 OLEDs use same address (0x3C) - **100% AMAN!**
- ✅ ESP-BC (0x08) and ESP-E (0x0A) are different - OK
- ✅ TCA9548A #1 (0x70) and #2 (0x71) are different - OK

### **❓ Kenapa OLED dengan Alamat Sama AMAN?**

**Penjelasan TCA9548A Channel Isolation:**

TCA9548A adalah **I2C multiplexer dengan isolasi channel**. Ini berarti:

1. **Hanya 1 Channel Aktif dalam 1 Waktu:**
   ```
   Saat Raspberry Pi select Channel 1:
   → Hanya OLED #1 yang "terlihat" di bus I2C
   → OLED #2-#9 TERPUTUS dari bus (isolated)
   → Tidak ada konflik!
   ```

2. **Sequential Access (Satu per Satu):**
   ```python
   # Update OLED #1
   select_channel(0x70, 1)  # Aktifkan Channel 1
   oled.display()           # Update OLED #1
   
   # Update OLED #2  
   select_channel(0x70, 2)  # Aktifkan Channel 2, Channel 1 MATI
   oled.display()           # Update OLED #2
   
   # Dan seterusnya...
   ```

3. **Physical Isolation:**
   - TCA9548A memiliki **switch hardware** untuk setiap channel
   - Saat channel tidak dipilih → SDA/SCL fisik **TERPUTUS**
   - Seperti saklar ON/OFF untuk setiap OLED

**Analogi Sederhana:**
```
Bayangkan 9 lampu (OLED) dengan saklar terpisah.
- Kamu hanya bisa nyalakan 1 saklar dalam 1 waktu
- Walaupun semua lampu sama tipenya (alamat 0x3C)
- Tidak akan bentrok karena hanya 1 yang aktif!
```

### **Update Speed & Performance:**

**Q: Apakah lambat karena update satu-per-satu?**

**A: TIDAK! Sangat cepat:**

```python
# Update 9 OLED secara sequential
for channel in range(9):
    select_channel(mux_address, channel)  # ~0.1ms
    update_oled(data)                     # ~20ms per OLED
    
# Total time: 9 × 20ms = 180ms = 0.18 detik
# Refresh rate: ~5.5 FPS (cukup untuk monitoring data!)
```

**Timing Breakdown:**
- Channel selection: ~0.1 ms (sangat cepat)
- OLED update: ~20 ms per display
- Total for 9 OLEDs: ~180 ms
- **Hasil: Smooth, tidak terasa delay!**

### **Kenapa Tidak Pakai Alamat Berbeda?**

**Masalah dengan alamat berbeda:**
1. ❌ OLED SSD1306 hanya support 2 alamat: 0x3C dan 0x3D
2. ❌ Butuh solder/jumper untuk ubah alamat
3. ❌ Maksimal hanya 2 OLED per bus (kita butuh 9!)
4. ❌ Ribet dan error-prone

**Keuntungan pakai TCA9548A:**
1. ✅ Bisa pakai unlimited OLED dengan alamat sama
2. ✅ Tidak perlu modifikasi hardware OLED
3. ✅ Plug-and-play
4. ✅ Professional solution
5. ✅ Mudah troubleshoot (test per channel)

### **Power Considerations:**
- OLEDs: 3.3V only (do NOT use 5V!)
- ESP32: 5V power + 3.3V I2C logic
- TCA9548A: 3.3V or 5V (use 3.3V for OLED compatibility)
- Pull-up resistors: 4.7kΩ on SDA/SCL (usually built into TCA9548A)

### **Cable Length:**
- I2C max recommended length: 1-2 meters
- Use shielded cable for longer runs
- Consider I2C extender for >2 meters

### **Troubleshooting:**
- If device not detected: Check wiring, power, and ground
- If communication fails: Check TCA9548A channel selection
- If OLED blank: Check 3.3V power and address 0x3C
- If ESP not responding: Check I2C address (0x08 or 0x0A)

---

## 🔗 References

- **Main Code:** `raspi_central_control/raspi_i2c_master.py`
- **Config File:** `raspi_central_control/raspi_config.py`
- **TCA9548A Manager:** `raspi_central_control/raspi_tca9548a.py`
- **OLED Manager:** `raspi_central_control/raspi_oled_manager.py`
- **Architecture:** `ARCHITECTURE_2ESP.md`
- **Hardware Update:** `HARDWARE_UPDATE_SUMMARY.md`

---

**Status:** ✅ Ready for Hardware Implementation  
**Last Updated:** 2024-12-08  
**Version:** 3.1
