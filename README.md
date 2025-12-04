# 🏭 PKM PLTN Simulator - Nuclear Power Plant Training Simulator

**Kompetisi PKM 2024 - Simulator PWR (Pressurized Water Reactor)**

[![Status](https://img.shields.io/badge/status-in%20development-yellow)]()
[![Python](https://img.shields.io/badge/python-3.7%2B-blue)]()
[![ESP32](https://img.shields.io/badge/ESP32-Arduino-orange)]()

> **📌 Dokumentasi lengkap sistem - Semua informasi dalam satu file**

---

## 📋 Daftar Isi

1. [Overview](#-overview)
2. [System Architecture](#-system-architecture)
3. [Hardware Components](#-hardware-components)
4. [Control Panel](#-control-panel)
5. [Software Architecture](#-software-architecture)
6. [Fitur Utama](#-fitur-utama)
7. [Humidifier Control](#-humidifier-control-new)
8. [Data Flow](#-data-flow-lengkap)
9. [PWR Startup Sequence](#-pwr-startup-sequence)
10. [Instalasi](#-instalasi)
11. [Status Implementasi](#-status-implementasi)
12. [Troubleshooting](#-troubleshooting)

---

## 🎯 Overview

Simulator PLTN tipe **PWR (Pressurized Water Reactor)** dengan Raspberry Pi 4 sebagai master controller dan 3 ESP32 sebagai slave controllers.

### Komponen Utama

| Komponen | Jumlah | Fungsi |
|----------|--------|--------|
| Raspberry Pi 4 | 1 | Master controller, logic, safety system |
| ESP32 | 3 | Control rods, turbine, LED visualization |
| Push Button | 15 | Operator input (pump, rod, pressure, emergency) |
| OLED Display | 9 | Real-time monitoring (128x64 I2C) |
| Servo Motor | 3 | Control rod simulation |
| LED | 48 | Flow visualization (16 per flow) |
| Relay | 6 | Turbine, generator, 2x humidifier |
| Humidifier | 2 | Steam generator & cooling tower visual effect |

### Target Pengguna
- 🎓 Mahasiswa teknik nuklir
- 👨‍🏫 Dosen untuk demonstrasi
- 🏫 Institusi pendidikan
- 🔬 Penelitian sistem kontrol

---

## 🏗️ System Architecture

### Diagram Arsitektur Lengkap

```
┌───────────────────────────────────────────────────────────────┐
│                 PANEL KONTROL OPERATOR                        │
│  ┌──────────────────────┐  ┌───────────────────────────────┐ │
│  │  15 Push Buttons     │  │  9 OLED Displays (128x64)     │ │
│  │  ├─ 6 Pump (ON/OFF)  │  │  ├─ 1: Presurizer (0x70 Ch0) │ │
│  │  ├─ 6 Rod (UP/DOWN)  │  │  ├─ 2-4: Pumps (Ch1-3)       │ │
│  │  ├─ 2 Pressure       │  │  ├─ 5-7: Rods (Ch4-6)        │ │
│  │  └─ 1 Emergency      │  │  ├─ 8: Thermal kW (Ch7)      │ │
│  └──────────────────────┘  │  └─ 9: Status (0x71 Ch0)     │ │
│         ↓ GPIO 5-25        └───────────────────────────────┘ │
│                                  ↓ I2C (2x PCA9548A)         │
└───────────────────────────────────────────────────────────────┘
                             ↓
┌───────────────────────────────────────────────────────────────┐
│               RASPBERRY PI 4 (Master Controller)              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Python Control Program (Multi-threaded)              │  │
│  │  ├─ Thread 1: Button polling (10ms)                  │  │
│  │  ├─ Thread 2: Interlock & safety logic (50ms)       │  │
│  │  ├─ Thread 3: OLED display update (200ms)           │  │
│  │  ├─ Thread 4: ESP communication (100ms)             │  │
│  │  └─ Thread 5: Data logging (1s)                     │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
                   ↓ I2C via PCA9548A (0x72)
┌──────────────────┬────────────────────┬─────────────────────┐
│     ESP-B        │      ESP-C         │       ESP-E         │
│   (0x08 Ch0)     │    (0x09 Ch1)      │     (0x0A Ch2)      │
│                  │                    │                     │
│ • 3 Servo motors │ • 4 Main relays    │ • 48 LEDs (3x16)    │
│ • Temp sensor    │ • 2 Humid relays   │   via multiplexer   │
│ • Calculate      │ • 4 PWM motors     │ • Primary flow      │
│   thermal kW     │ • State machine    │ • Secondary flow    │
│                  │                    │ • Tertiary flow     │
└──────────────────┴────────────────────┴─────────────────────┘
```

### I2C Bus Organization

**Bus 1 - Display (GPIO 2/3):**
- PCA9548A #1 (0x70): 8x OLED channels
- PCA9548A #2 (0x71): 1x OLED channel

**Bus 2 - ESP Communication (GPIO 2/3 - same physical bus):**
- PCA9548A #3 (0x72): 3x ESP32 channels

---

## 💻 Hardware Components

### 1. Raspberry Pi 4 (Master Controller)

**Spesifikasi:**
- Model: Raspberry Pi 4 Model B (4GB RAM recommended)
- OS: Raspberry Pi OS (Bullseye atau lebih baru)
- Python: 3.7+

**GPIO Usage:**
```
GPIO 2/3:   I2C (SDA/SCL) - 9 OLED + 3 ESP
GPIO 5-26:  15 Push Buttons (with internal pull-up)
(Optional: GPIO untuk buzzer, status LED)
```

**Tasks:**
1. Baca 15 push buttons (dengan debouncing 200ms)
2. Implementasi safety interlock logic
3. Kontrol 9 OLED displays via 2x PCA9548A
4. Komunikasi dengan 3 ESP32 via PCA9548A
5. Kalkulasi humidifier control
6. Data logging ke CSV
7. (Optional) Web dashboard

---

### 2. ESP-B (0x08) - Control Rods & Reactor Core

**Hardware:**
- ESP32 Dev Board
- 3x Servo motors (MG996R recommended)
- Sensor suhu (optional)

**GPIO Pins:**
```cpp
// Servo motors
#define SERVO_ROD1 27  // Safety rod
#define SERVO_ROD2 14  // Shim rod  
#define SERVO_ROD3 12  // Regulating rod

// I2C
#define SDA 21
#define SCL 22
```

**Fungsi:**
- Terima target positions dari Raspberry Pi (3 bytes)
- Gerakkan 3 servo motors sesuai target
- Hitung thermal power (kW) dari posisi rod
- Kirim actual positions + thermal kW (16 bytes)

**I2C Protocol:**
```cpp
// Receive (3 bytes):
// - Byte 0: Safety rod target (0-100%)
// - Byte 1: Shim rod target (0-100%)
// - Byte 2: Regulating rod target (0-100%)

// Send (16 bytes):
// - Byte 0: Safety rod actual
// - Byte 1: Shim rod actual
// - Byte 2: Regulating rod actual
// - Byte 3: Reserved
// - Byte 4-7: Thermal power kW (float)
// - Byte 8-15: Reserved for future
```

---

### 3. ESP-C (0x09) - Turbine, Generator & Humidifier

**Hardware:**
- ESP32 Dev Board
- 4x Relay module (main components)
- 2x Relay module (humidifiers) ⭐ **NEW**
- 4x Motor/Fan (PWM control)

**GPIO Pins:**
```cpp
// Main component relays
#define RELAY_STEAM_GEN 25
#define RELAY_TURBINE 26
#define RELAY_CONDENSER 27
#define RELAY_COOLING_TOWER 14

// Humidifier relays (NEW!)
#define RELAY_HUMIDIFIER_STEAM_GEN 32    // ⭐ Steam Generator
#define RELAY_HUMIDIFIER_COOLING_TOWER 33 // ⭐ Cooling Tower

// Motor PWM
#define MOTOR_STEAM_GEN_PIN 12
#define MOTOR_TURBINE_PIN 13
#define MOTOR_CONDENSER_PIN 15
#define MOTOR_COOLING_PIN 4

// I2C
#define SDA 21
#define SCL 22
```

**Fungsi:**
- Kontrol relay untuk komponen utama (based on power level)
- **Kontrol 2 humidifier relay (based on RasPi command)**
- State machine: IDLE → STARTING → RUNNING → SHUTDOWN
- PWM control untuk motor speeds

**I2C Protocol (UPDATED):**
```cpp
// Receive (12 bytes):
// - Byte 0: Register (0x00)
// - Byte 1: Safety rod position
// - Byte 2: Shim rod position  
// - Byte 3: Regulating rod position
// - Byte 4-7: Thermal power kW (float)
// - Byte 8: Humidifier Steam Gen command (0/1) ⭐
// - Byte 9: Humidifier Cooling Tower command (0/1) ⭐

// Send (12 bytes):
// - Byte 0-3: Power level (float, 0-100%)
// - Byte 4-7: State (uint32)
// - Byte 8: Generator status
// - Byte 9: Turbine status
// - Byte 10: Humidifier SG status ⭐
// - Byte 11: Humidifier CT status ⭐
```

---

### 4. ESP-E (0x0A) - 3-Flow LED Visualizer

**Hardware:**
- ESP32 Dev Board
- 3x CD74HC4067 (16-channel multiplexer)
- 48x LED (16 per flow)
- Current limiting resistors

**GPIO Pins:**
```cpp
// Shared selector (all 3 multiplexers)
#define S0 14
#define S1 27
#define S2 26
#define S3 25

// Flow 1: Primary
#define EN_PRIMARY 33
#define SIG_PRIMARY 32

// Flow 2: Secondary
#define EN_SECONDARY 15
#define SIG_SECONDARY 4

// Flow 3: Tertiary
#define EN_TERTIARY 2
#define SIG_TERTIARY 16

// I2C
#define SDA 21
#define SCL 22
```

**Fungsi:**
- Terima status 3 pump dari Raspberry Pi
- Animate 48 LEDs (16 per flow) dengan kecepatan berbeda
- Multi-wave flowing effect (looks realistic!)

**I2C Protocol:**
```cpp
// Receive (16 bytes):
// - Byte 0: Register (0x00)
// - Byte 1-5: Primary (pressure float + pump status)
// - Byte 6-10: Secondary (pressure float + pump status)
// - Byte 11-15: Tertiary (pressure float + pump status)

// Send (2 bytes):
// - Byte 0: Animation speed
// - Byte 1: LED count (16)
```

---

## 🎛️ Control Panel

### 9 OLED Displays (via 2x PCA9548A)

**PCA9548A #1 (Address: 0x70)**

| Channel | OLED | Content | Example Display |
|---------|------|---------|-----------------|
| 0 | 1 | Presurizer Pressure | `155.0 bar` + bar graph |
| 1 | 2 | Pump Primary Status | `ON` / `OFF` / `STARTING` |
| 2 | 3 | Pump Secondary Status | `ON` / `OFF` / `STARTING` |
| 3 | 4 | Pump Tertiary Status | `ON` / `OFF` / `STARTING` |
| 4 | 5 | Safety Rod Position | `75%` + bar graph |
| 5 | 6 | Shim Rod Position | `60%` + bar graph |
| 6 | 7 | Regulating Rod Position | `45%` + bar graph |
| 7 | 8 | Thermal Power | `1250 kW` |

**PCA9548A #2 (Address: 0x71)**

| Channel | OLED | Content | Example Display |
|---------|------|---------|-----------------|
| 0 | 9 | System Status | `Humidifiers: SG✓ CT✓` |

### 15 Push Buttons (via GPIO)

**Pump Control (6 buttons):**
```
GPIO 5:  Pump Primary ON      GPIO 6:  Pump Primary OFF
GPIO 13: Pump Secondary ON    GPIO 19: Pump Secondary OFF
GPIO 26: Pump Tertiary ON     GPIO 21: Pump Tertiary OFF
```

**Rod Control (6 buttons):**
```
GPIO 20: Safety Rod UP        GPIO 16: Safety Rod DOWN
GPIO 12: Shim Rod UP          GPIO 7:  Shim Rod DOWN
GPIO 8:  Regulating Rod UP    GPIO 25: Regulating Rod DOWN
```

**Pressurizer Control (2 buttons):**
```
GPIO 24: Pressure UP          GPIO 23: Pressure DOWN
```

**Emergency (1 button):**
```
GPIO 18: EMERGENCY SHUTDOWN (RED BUTTON)
```

---

## 🧠 Software Architecture

### File Structure

```
pkm-simulator-PLTN/
├── ESP_B/
│   └── ESP_B_I2C/
│       └── ESP_B_I2C.ino              # Control rods
│
├── ESP_C/
│   ├── ESP_C_I2C.ino                  # Old version
│   └── ESP_C_HUMIDIFIER.ino           # ⭐ NEW with humidifier
│
├── ESP_E_Aliran_Primer/
│   └── ESP_E_I2C/
│       └── ESP_E_I2C.ino              # 3-flow visualizer
│
└── raspi_central_control/
    ├── raspi_main_panel.py            # ⏳ Main program (TODO)
    ├── raspi_gpio_buttons.py          # ✅ Button handler
    ├── raspi_panel_oled.py            # ⏳ 9-OLED manager (TODO)
    ├── raspi_humidifier_control.py    # ✅ Humidifier logic
    ├── raspi_interlock.py             # ⏳ Safety logic (TODO)
    ├── raspi_i2c_master.py            # ⏳ ESP communication (TODO)
    ├── raspi_config.py                # Configuration
    ├── test_esp_e_quick.py            # ✅ ESP-E test
    └── test_pca9548a_esp.py           # ✅ Full test
```

### Multi-threaded Architecture

```python
# Thread 1: Button Polling (10ms cycle)
while running:
    button_handler.check_all_buttons()  # Non-blocking
    time.sleep(0.01)

# Thread 2: Control Logic & Safety (50ms cycle)
while running:
    # Check interlock
    rod_movement_allowed = check_interlock()
    
    # Update rod positions
    if rod_movement_allowed:
        update_rod_positions()
    
    # Calculate humidifier commands
    sg_cmd, ct_cmd = humidifier.update_all(
        safety_rod, shim_rod, regulating_rod, thermal_kw
    )
    
    time.sleep(0.05)

# Thread 3: OLED Update (200ms cycle)
while running:
    for i in range(9):
        select_oled_channel(i)
        update_oled_display(i, data)
    time.sleep(0.2)

# Thread 4: ESP Communication (100ms cycle)
while running:
    # ESP-B
    send_rod_targets()
    rod_data = receive_from_esp_b()
    
    # ESP-C  
    send_to_esp_c(rod_data, thermal_kw, sg_cmd, ct_cmd)
    
    # ESP-E
    send_to_esp_e(flow_data)
    
    time.sleep(0.1)

# Thread 5: Data Logging (1s cycle)
while running:
    log_data_to_csv(timestamp, all_data)
    time.sleep(1.0)
```

---

## ⚡ Fitur Utama

### 1. 🔐 Safety Interlock System

**Rod Movement Interlock:**

Rod hanya bisa bergerak jika **SEMUA kondisi terpenuhi:**

```python
✅ Pressure Primary >= 40 bar
✅ Pump Primary Status = ON
✅ Pump Secondary Status = ON
✅ Emergency Flag = False
```

Jika salah satu kondisi tidak terpenuhi:
- ❌ Rod tidak bisa bergerak (servo locked)
- ⚠️ Warning di OLED: "INTERLOCK NOT SATISFIED"
- 🔊 Buzzer bunyi (optional)

**Pump Startup Sequence:**

Pompa **HARUS** dinyalakan dengan urutan:

```
1. Tertiary Pump ON   (Cooling path ready)
   ↓
2. Secondary Pump ON  (Heat exchanger ready)
   ↓  
3. Primary Pump ON    (Main loop ready)
```

Jika urutan salah:
- ❌ Command ditolak
- ⚠️ Warning: "START TERTIARY FIRST"

---

### 2. 🌊 Humidifier Control System ⭐ NEW!

#### Steam Generator Humidifier

**Kondisi ON:**
```
Shim Rod >= 40% AND Regulating Rod >= 40%
```

**Logic dengan Hysteresis:**
```python
if currently_off:
    turn_on_when: shim >= 40% AND reg >= 40%
    
if currently_on:
    turn_off_when: shim < 35% OR reg < 35%  # 5% hysteresis
```

**Hardware:**
- Relay: ESP-C GPIO 32
- Humidifier: 220V AC (via relay)
- Visual: Uap keluar dari steam generator mockup

#### Cooling Tower Humidifier

**Kondisi ON:**
```
Thermal Power >= 800 kW
```

**Logic dengan Hysteresis:**
```python
if currently_off:
    turn_on_when: thermal >= 800 kW
    
if currently_on:
    turn_off_when: thermal < 700 kW  # 100kW hysteresis
```

**Hardware:**
- Relay: ESP-C GPIO 33
- Humidifier: 220V AC (via relay)
- Visual: Uap keluar dari cooling tower mockup

#### Configuration

```python
# Default config
HUMIDIFIER_CONFIG = {
    'sg_shim_rod_threshold': 40.0,      # Shim rod >= 40%
    'sg_reg_rod_threshold': 40.0,       # Reg rod >= 40%
    'sg_hysteresis': 5.0,               # OFF when < 35%
    
    'ct_thermal_threshold': 800.0,      # Thermal >= 800kW
    'ct_hysteresis': 100.0,             # OFF when < 700kW
}

# Conservative (higher threshold)
HUMIDIFIER_CONFIG_CONSERVATIVE = {
    'sg_shim_rod_threshold': 50.0,
    'sg_reg_rod_threshold': 50.0,
    'sg_hysteresis': 10.0,
    'ct_thermal_threshold': 1000.0,
    'ct_hysteresis': 150.0,
}
```

---

### 3. 💡 48-LED Flow Visualization

**ESP-E** mengontrol 3 aliran dengan **multiplexer** (efisien!):

| Flow | LEDs | Animation | Condition |
|------|------|-----------|-----------|
| Primary | 16 | Fast (40ms) | Pump Primary ON |
| Secondary | 16 | Fast (40ms) | Pump Secondary ON |
| Tertiary | 16 | Fast (40ms) | Pump Tertiary ON |

**Animation Speeds:**
- **OFF:** No animation (all dark)
- **STARTING:** Slow (80ms interval)
- **ON:** Fast (40ms interval)
- **SHUTTING_DOWN:** Very slow (120ms interval)

**Multi-wave Effect:**
- 4 gelombang per aliran
- 3 LED per gelombang (bright → medium → dim → off)
- Continuous flowing effect (looks like real water!)

---

### 4. 🔄 PWR Startup Sequence

**Realistic Pressurized Water Reactor startup:**

```
Phase 1: System Check (0-5s)
├─ All pumps: OFF
├─ All rods: 0%
├─ Pressure: 0 bar
└─ Display: "SYSTEM INITIALIZING"

Phase 2: Start Tertiary Cooling (5-15s)
├─ Operator press: "Pump Tertiary ON"
├─ Pressure ramp: 0 → 55 bar (gradual)
├─ LEDs: Tertiary flow animate (slow → fast)
└─ Display: "TERTIARY COOLING ACTIVE"

Phase 3: Start Secondary Cooling (15-25s)
├─ Interlock check: Tertiary = ON ✅
├─ Operator press: "Pump Secondary ON"
├─ Pressure ramp: 55 → 105 bar
├─ LEDs: Secondary flow animate
└─ Display: "SECONDARY COOLING ACTIVE"

Phase 4: Start Primary Loop (25-35s)
├─ Interlock check: Secondary = ON ✅
├─ Operator press: "Pump Primary ON"
├─ Pressure ramp: 105 → 155 bar
├─ LEDs: Primary flow animate
├─ Rod control: NOW ENABLED 🔓
└─ Display: "PRIMARY LOOP ACTIVE - READY"

Phase 5: Insert Control Rods (35-50s)
├─ Operator press: Rod UP buttons
├─ Rods move: 0% → target%
├─ Servo motors actuate
├─ Thermal power increases: 0 → XXX kW
└─ Display: Rod positions + thermal kW

Phase 6: Humidifiers Activate (40-60s)
├─ IF Shim >= 40% AND Reg >= 40%
│  └─ Steam Gen Humidifier: ON 🌊
│
├─ IF Thermal >= 800 kW
│  └─ Cooling Tower Humidifier: ON 🌊
│
└─ Display: "HUMIDIFIERS: SG✓ CT✓"

Phase 7: Power Generation (50s+)
├─ ESP-C calculates power level
├─ Power ramps: 0% → target%
├─ Turbine: ON
├─ Generator: ON
├─ System: STABLE OPERATION
└─ Display: "GENERATING POWER: XX MW"
```

---

## 🔄 Data Flow Lengkap

### End-to-End Flow (dari Button Press sampai Visualisasi)

```
1. USER INPUT
   └─ Operator tekan "Shim Rod UP"
      └─ GPIO 12 reads LOW (button pressed)
         └─ Debounce 200ms
            └─ Callback triggered

2. RASPBERRY PI PROCESSING
   ├─ shim_rod_position += 1  # Increment 1%
   │
   ├─ Check interlock:
   │  ├─ Pressure >= 40 bar? ✅
   │  ├─ Pump Primary ON? ✅
   │  ├─ Pump Secondary ON? ✅
   │  └─ Emergency? ❌
   │  → Interlock satisfied, allow movement
   │
   ├─ Calculate humidifier commands:
   │  ├─ Shim (45%) >= 40%? YES ✅
   │  ├─ Reg (45%) >= 40%? YES ✅
   │  └─ → Steam Gen Humid = ON (cmd=1)
   │
   └─ Update OLED 6: "Shim Rod: 45%"

3. SEND TO ESP-B
   └─ I2C packet (3 bytes):
      [0x08][safety_target][shim_target][reg_target]
      Example: [0x08][50][45][45]

4. ESP-B EXECUTION
   ├─ Servo motor 2 moves to 45%
   ├─ Read actual position: 45%
   ├─ Calculate thermal:
   │  thermal_kW = (safety + shim + reg)/3 * 20
   │  = (50 + 45 + 45)/3 * 20 = 933 kW
   │
   └─ I2C response (16 bytes):
      [50][45][45][0][thermal_kW_float]...

5. RASPBERRY PI RECEIVES
   ├─ Parse: safety=50%, shim=45%, reg=45%
   ├─ Parse: thermal=933 kW
   │
   ├─ Update humidifier logic:
   │  ├─ SG: Shim+Reg both >= 40% → ON ✅
   │  └─ CT: Thermal 933kW >= 800kW → ON ✅
   │
   └─ Prepare ESP-C command

6. SEND TO ESP-C
   └─ I2C packet (12 bytes):
      [0x00][50][45][45][thermal_933.0][1][1]
      (rod positions, thermal kW, humid cmds)

7. ESP-C EXECUTION
   ├─ Power level = (50+45+45)/3 = 46.7%
   │
   ├─ Relay control:
   │  ├─ Steam Gen: ON (power > 20%)
   │  ├─ Turbine: ON (power > 30%)
   │  ├─ Condenser: ON (power > 20%)
   │  └─ Cooling Tower: ON (power > 15%)
   │
   ├─ Humidifier control:
   │  ├─ GPIO 32 = HIGH → SG Humid ON 🌊
   │  └─ GPIO 33 = HIGH → CT Humid ON 🌊
   │
   └─ I2C response (12 bytes):
      [power_46.7][state_RUNNING][gen_ON][turb_ON][sg_ON][ct_ON]

8. SEND TO ESP-E
   └─ I2C packet (16 bytes):
      [0x00][primary_data][secondary_data][tertiary_data]
      (pressure floats + pump status for each)

9. ESP-E VISUALIZATION
   ├─ Primary: Pump ON → Fast animation (40ms)
   ├─ Secondary: Pump ON → Fast animation (40ms)
   └─ Tertiary: Pump ON → Fast animation (40ms)
   → 48 LEDs flowing beautifully! 💡

10. OUTPUT VISUALIZATION
    ├─ OLED 5: "Safety Rod: 50%"  [▓▓▓▓▓░░░░░]
    ├─ OLED 6: "Shim Rod: 45%"    [▓▓▓▓░░░░░░]
    ├─ OLED 7: "Reg Rod: 45%"     [▓▓▓▓░░░░░░]
    ├─ OLED 8: "Thermal: 933 kW"
    ├─ OLED 9: "Humidifiers: SG✓ CT✓"
    │
    ├─ LEDs: All 3 flows animating
    │  ●●●○○○○○○○○○○○●●  Primary
    │  ○○○●●●○○○○○○○○○○  Secondary
    │  ○○○○○○●●●○○○○○○○  Tertiary
    │
    └─ Physical humidifiers:
       ├─ Steam Gen: UAPS KELUAR 💨
       └─ Cooling Tower: UAPS KELUAR 💨
```

**Total Latency:** < 250ms (button → visualisasi)

---

## 📥 Instalasi

### 1. Hardware Assembly

#### Wiring Raspberry Pi

```
GPIO 2  (SDA) ─┬─ PCA9548A #1 (0x70) ─ 8x OLED
GPIO 3  (SCL) ─┤
               ├─ PCA9548A #2 (0x71) ─ 1x OLED
               └─ PCA9548A #3 (0x72) ─┬─ ESP-B (0x08)
                                       ├─ ESP-C (0x09)
                                       └─ ESP-E (0x0A)

GPIO 5-26: 15x Push Buttons (with 10kΩ pull-up to 3.3V)
```

#### Wiring ESP-C Humidifier

```
ESP-C GPIO 32 ─→ Relay Module IN1 ─→ Humidifier #1 (220V AC)
ESP-C GPIO 33 ─→ Relay Module IN2 ─→ Humidifier #2 (220V AC)

⚠️ WARNING: Use optocoupler relay module!
⚠️ Separate ground for 220V AC and 5V logic!
⚠️ Add fuse on AC line!
```

### 2. Software Installation

#### Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python packages
sudo apt install python3-pip python3-smbus i2c-tools -y

# Install dependencies
cd raspi_central_control
pip3 install -r requirements.txt

# Enable I2C
sudo raspi-config
# → Interface Options → I2C → Enable

# Reboot
sudo reboot

# Test I2C detection
sudo i2cdetect -y 1
```

**Expected i2cdetect output:**
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- 08 09 0a -- -- -- -- -- 
10:          -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20:          -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30:          -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- 
40:          -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50:          -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60:          -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: 70 71 72 -- -- -- -- --
```

Addresses found:
- `0x08` = ESP-B
- `0x09` = ESP-C
- `0x0A` = ESP-E
- `0x3C` = OLED displays
- `0x70` = PCA9548A #1 (OLED 1-8)
- `0x71` = PCA9548A #2 (OLED 9)
- `0x72` = PCA9548A #3 (ESP comm)

#### ESP32 (Arduino IDE)

**Setup Arduino IDE:**
```
1. Install ESP32 board support
   File → Preferences → Additional Board URLs:
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

2. Install ESP32 boards
   Tools → Board → Boards Manager → Search "ESP32" → Install

3. Select board
   Tools → Board → ESP32 Dev Module
```

**Upload Firmware:**
```
1. ESP-B:
   Open: ESP_B/ESP_B_I2C/ESP_B_I2C.ino
   Upload to ESP32 #1

2. ESP-C (with humidifier support):
   Open: ESP_C/ESP_C_HUMIDIFIER.ino
   Upload to ESP32 #2

3. ESP-E:
   Open: ESP_E_Aliran_Primer/ESP_E_I2C/ESP_E_I2C.ino
   Upload to ESP32 #3
```

### 3. Testing

**Test individual modules:**
```bash
# Test button handler
python3 raspi_gpio_buttons.py

# Test humidifier logic
python3 raspi_humidifier_control.py

# Test ESP-E LED visualization
python3 test_esp_e_quick.py

# Test full ESP communication
python3 test_pca9548a_esp.py
```

**Run main program:**
```bash
python3 raspi_main_panel.py
```

---

## 📊 Status Implementasi

### ✅ Completed (Ready to Use)

- [x] **ESP-E** (3-Flow Visualizer)
  - 48 LED control via multiplexer
  - 3 independent flow animations
  - Fast/slow animation modes
  - I2C communication tested

- [x] **ESP-C** (Humidifier Support)
  - Hardware pins configured (GPIO 32, 33)
  - I2C protocol updated (12 bytes)
  - Relay control logic implemented
  - Code: `ESP_C_HUMIDIFIER.ino` ready

- [x] **Humidifier Control Logic**
  - Python module: `raspi_humidifier_control.py`
  - Steam Gen logic (Shim + Reg rod)
  - Cooling Tower logic (Thermal kW)
  - Hysteresis implemented
  - Tested with fake data

- [x] **Button Handler**
  - Python module: `raspi_gpio_buttons.py`
  - 15 button support
  - Debouncing (200ms)
  - Callback system

- [x] **Documentation**
  - All info consolidated in README.md
  - Clear diagrams
  - Installation guide
  - Troubleshooting guide

### ⏳ In Progress (80% Complete)

- [ ] **9-OLED Display Manager**
  - Need: `raspi_panel_oled.py`
  - Support 2x PCA9548A
  - Display layouts designed
  - TODO: Implementation

- [ ] **Main Program Integration**
  - Need: `raspi_main_panel.py`
  - Multi-threaded architecture
  - Integrate all modules
  - TODO: Implementation

- [ ] **ESP-B Simplification**
  - Remove button handling
  - Remove OLED display code
  - Keep servo control only
  - Update protocol
  - TODO: Code update

- [ ] **Safety Interlock**
  - Need: `raspi_interlock.py`
  - Rod movement conditions
  - Pump sequence checking
  - Emergency handling
  - TODO: Implementation

### 📋 Todo (Not Started)

- [ ] **PWR Startup Sequence**
  - Need: `raspi_startup_sequence.py`
  - Automated startup
  - Step-by-step guide
  - TODO: Implementation

- [ ] **Data Logging**
  - CSV export
  - Real-time graphs
  - Historical data
  - TODO: Implementation

- [ ] **Web Dashboard** (Optional)
  - Flask web app
  - Real-time monitoring
  - Remote control
  - TODO: Design & implementation

### Overall Progress: 🟡 **75% Complete**

---

## 🔧 Troubleshooting

### I2C Communication

**Problem:** Device tidak terdeteksi di i2cdetect
```bash
# Solution 1: Check wiring
- SDA → GPIO 2
- SCL → GPIO 3
- GND → Common ground
- VCC → 3.3V or 5V (check device)

# Solution 2: Check I2C enabled
sudo raspi-config
# Interface Options → I2C → Enable

# Solution 3: Try different I2C speed
sudo nano /boot/config.txt
# Add: dtparam=i2c_arm_baudrate=50000
# (default is 100000)
```

**Problem:** Data corruption / checksum error
```bash
# Add pull-up resistors
- 4.7kΩ from SDA to 3.3V
- 4.7kΩ from SCL to 3.3V

# Shorten cable length
- Use <20cm twisted pair cable
- Star topology for ground

# Check power supply
- Stable 5V (use quality power supply)
- Add capacitors near ESP32 (100μF + 0.1μF)
```

### Humidifier

**Problem:** Humidifier tidak nyala
```bash
# Check 1: GPIO output
voltmeter GPIO 32/33 → Should be 3.3V when ON

# Check 2: Relay clicking
Listen for "click" sound when command sent

# Check 3: Relay output
voltmeter relay COM-NO → Should be 220V when ON

# Check 4: Humidifier power
Check humidifier plugged in & switched on

# Check 5: Water level
Check humidifier has enough water
```

**Problem:** Humidifier oscillating (ON-OFF-ON-OFF)
```python
# Solution: Increase hysteresis
HUMIDIFIER_CONFIG = {
    'sg_hysteresis': 10.0,      # Was 5.0
    'ct_hysteresis': 150.0,     # Was 100.0
}

# Or reduce update frequency
time.sleep(0.2)  # Instead of 0.1
```

**Problem:** Humidifier delay response
```python
# Normal - hysteresis prevents fast switching
# If delay too long:
# - Check I2C communication speed
# - Check Raspberry Pi CPU usage
# - Reduce other thread load
```

### Push Buttons

**Problem:** Button tidak responsif
```bash
# Check wiring
Button pin 1 → GPIO
Button pin 2 → GND
(Internal pull-up enabled in code)

# Test dengan multimeter
- Continuity test: should beep when pressed
- Voltage test: 3.3V (not pressed), 0V (pressed)

# Check code
GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Button pressed = GPIO.LOW
```

**Problem:** Button bouncing (multiple triggers)
```python
# Solution: Increase debounce time
ButtonHandler(debounce_time=0.3)  # Was 0.2
```

**Problem:** Button stuck/no response
```bash
# Hardware issue
- Check button not mechanically jammed
- Check solder joints
- Replace button if defective

# Software issue
- Check GPIO not used by other program
- Check button callback registered
- Add debug print in callback
```

### LED Animation

**Problem:** LED tidak nyala
```bash
# Check power
- 48 LEDs need ~2A at 5V
- Use proper power supply (5V 3A recommended)
- Check common ground with ESP32

# Check multiplexer
- EN pin LOW = enabled
- Check S0-S3 connections
- Test each channel individually

# Check LED polarity
- Long leg = Anode (+)
- Short leg = Cathode (-)
- Check correct orientation
```

**Problem:** LED flickering
```cpp
// Solution: Increase PWM frequency
const int PWM_FREQ = 10000;  // Was 5000

// Or reduce brightness
int brightness = 200;  // Instead of 255

// Or add delay
delayMicroseconds(100);  // After each LED
```

**Problem:** Animation too fast/slow
```cpp
// Adjust animation interval in ESP-E code
flow.animationInterval = 60;  // Adjust value
```

### OLED Display

**Problem:** OLED tidak tampil
```bash
# Check I2C address
sudo i2cdetect -y 1
# Should see 0x3C

# Check wiring via multiplexer
- PCA9548A channel select correct?
- OLED connected to correct channel?

# Test OLED directly (bypass multiplexer)
python3 -c "
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
i2c = busio.I2C(SCL, SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
oled.fill(1)
oled.show()
"
```

**Problem:** OLED garbled display
```python
# Reset OLED before use
oled.fill(0)
oled.show()
time.sleep(0.1)

# Use smaller font if text cut off
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 10)
```

### System Performance

**Problem:** Raspberry Pi CPU 100%
```bash
# Check with top command
top

# Reduce thread update rates
BUTTON_POLL_RATE = 0.02  # Instead of 0.01
OLED_UPDATE_RATE = 0.3   # Instead of 0.2

# Use nicer priority for non-critical threads
os.nice(10)  # Lower priority
```

**Problem:** I2C timeout
```python
# Increase timeout
bus = smbus2.SMBus(1, timeout=0.5)  # 500ms timeout

# Add retry logic
for retry in range(3):
    try:
        data = bus.read_i2c_block_data(addr, reg, length)
        break
    except:
        if retry == 2:
            raise
        time.sleep(0.01)
```

---

## 📚 Referensi

### Hardware Datasheets
- [ESP32 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf)
- [PCA9548A Datasheet](https://www.ti.com/lit/ds/symlink/pca9548a.pdf)
- [CD74HC4067 Datasheet](https://www.ti.com/lit/ds/symlink/cd74hc4067.pdf)
- [SSD1306 OLED Datasheet](https://cdn-shop.adafruit.com/datasheets/SSD1306.pdf)

### PWR (Pressurized Water Reactor) Reference
- [NRC - Pressurized Water Reactor](https://www.nrc.gov/reading-rm/basic-ref/students/for-educators/04.pdf)
- [IAEA - Nuclear Power Reactors](https://www.iaea.org/topics/nuclear-power-reactors)

### Python Libraries
- [smbus2 Documentation](https://smbus2.readthedocs.io/)
- [RPi.GPIO Documentation](https://sourceforge.net/p/raspberry-gpio-python/wiki/Home/)
- [Adafruit CircuitPython](https://circuitpython.org/)

---

## 📞 Support & Contact

**Project:** PKM PLTN Simulator 2024  
**Purpose:** Educational nuclear power plant simulator  
**Target:** Kompetisi PKM (Program Kreativitas Mahasiswa)

**For Questions:**
1. Read this README thoroughly
2. Check inline code documentation
3. Test individual components before full system
4. Review troubleshooting section

---

## 📄 License

MIT License - Free to use for educational purposes

Copyright (c) 2024 PKM PLTN Simulator Team

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.

---

## 🎓 Educational Value

Sistem ini mengajarkan konsep:

1. **System Integration** - Multiple hardware modules working together
2. **Real-time Control** - Multi-threaded embedded systems
3. **Safety Systems** - Interlock logic & emergency shutdown
4. **Communication Protocols** - I2C master-slave architecture
5. **PWR Operation** - Realistic nuclear reactor startup sequence
6. **Conditional Logic** - Humidifier control with hysteresis
7. **Hardware Interfacing** - GPIO, I2C, PWM, Relay, Servo
8. **Visualization** - LED animation & OLED displays
9. **Control Theory** - PID-like control with feedback
10. **Instrumentation** - Sensors, actuators, displays

---

## 🎉 Acknowledgments

- **Pembimbing:** [Nama Dosen Pembimbing]
- **Institusi:** [Nama Universitas]
- **Team Members:** [Nama Anggota Tim]
- **Sponsor:** [Jika ada sponsor]

Special thanks to:
- Raspberry Pi Foundation
- Espressif (ESP32)
- Arduino Community
- Open source contributors

---

**Version:** 2.0  
**Last Updated:** 2024-12-04  
**Status:** 🟡 **In Development (75% complete)**

**Remaining Work:**
- [ ] Integrate all Python modules
- [ ] Complete OLED display manager
- [ ] Full system testing
- [ ] Physical assembly
- [ ] Documentation finalization

**Estimated Completion:** January 2025

---

🎉 **Semua dokumentasi sekarang dalam satu file README.md!**

**File lain yang bisa dihapus:**
- `SYSTEM_ARCHITECTURE_V2.md`
- `ESP_MODULES_SUMMARY.md`
- `GAP_ANALYSIS.md`
- `PANEL_CONTROL_ARCHITECTURE.md`
- `HUMIDIFIER_SYSTEM_SUMMARY.md`
- `PROJECT_COMPLETE.md`
- `PROJECT_STRUCTURE_V2.md`
- `DEPRECATED_FILES.md`

**Keep only:**
- ✅ `README.md` (this file - complete documentation)
- ✅ `CHANGELOG_V2.md` (version history)
- ✅ ESP-specific READMEs in each ESP folder
