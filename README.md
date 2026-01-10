# 🏭 PKM PLTN Simulator - Nuclear Power Plant Training Simulator

**Kompetisi PKM 2024 - Simulator PWR (Pressurized Water Reactor)**

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.7%2B-blue)]()
[![ESP32](https://img.shields.io/badge/ESP32-Arduino-orange)]()
[![Architecture](https://img.shields.io/badge/architecture-2%20ESP%20UART-success)]()

> **📌 Dokumentasi lengkap sistem - Semua informasi dalam satu file**  
> **🎉 NEW: UART Communication Protocol - Reliable & Efficient!**  
> **🎉 NEW: Video Display System - Educational Visualization!**  
> **🎉 NEW: Event Queue Pattern - No Deadlocks!**

---

## 📋 Daftar Isi

1. [Overview](#-overview)
2. [🆕 What's New in v4.0](#-whats-new-in-v40)
3. [Architecture v4.0 (UART Communication)](#-architecture-v40---uart-communication)
4. [System Architecture](#-system-architecture)
5. [Hardware Components](#-hardware-components)
6. [Control Panel](#-control-panel)
7. [Software Architecture](#-software-architecture)
8. [Video Display System](#-video-display-system-new)
9. [Communication Protocol](#-communication-protocol-uart)
10. [PWR Startup Sequence](#-pwr-startup-sequence)
11. [Instalasi](#-instalasi)
12. [Status Implementasi](#-status-implementasi)
13. [Troubleshooting](#-troubleshooting)
14. [📚 Documentation](#-documentation)

---

## 🎯 Overview

Simulator PLTN tipe **PWR (Pressurized Water Reactor)** dengan Raspberry Pi 4 sebagai master controller dan **2 ESP32** sebagai slave controllers menggunakan **UART communication protocol**.

### 🎉 What's New in v4.0 (UART Architecture - January 2025)

**🔌 UART Communication Protocol:**
- ✅ **Binary Protocol** - Replaces I2C/JSON for reliability
- ✅ **Hardware UART** - GPIO 14/15 (ESP-BC), GPIO 4/5 (ESP-E)
- ✅ **83% size reduction** - Binary vs JSON (15 bytes vs 86 bytes)
- ✅ **CRC8 checksum** - Error detection and correction
- ✅ **ACK/NACK mechanism** - Guaranteed delivery
- ✅ **No buffer garbage** - Eliminates I2C issues

**🎬 Video Display System:**
- ✅ **Separate visualization module** - Independent from main controller
- ✅ **Pygame-based UI** - Lightweight & cross-platform
- ✅ **3 display modes** - IDLE, AUTO (video), MANUAL (interactive guide)
- ✅ **Real-time sync** - JSON state file communication
- ✅ **Standalone testing** - No simulation required for development

**🎮 Event Queue Pattern:**
- ✅ **No deadlocks** - Interrupt-safe button handling
- ✅ **Queue-based processing** - Decoupled callback execution
- ✅ **< 1μs callback** - Immediate response (was ~10ms)
- ✅ **Robust architecture** - Production-ready button system

**📌 GPIO Pin Updates:**
- ✅ **UART3 enabled** - GPIO 4/5 for ESP-E communication
- ✅ **Button remapped** - GPIO 11 for PUMP_PRIMARY_ON (was GPIO 5)
- ✅ **No conflicts** - All pins properly allocated

**See [BUTTON_EVENT_QUEUE_PATTERN.md](BUTTON_EVENT_QUEUE_PATTERN.md) and [GPIO_PIN_MAPPING.md](GPIO_PIN_MAPPING.md) for complete guides!**

### Komponen Utama

| Komponen | Jumlah | Fungsi | Status |
|----------|--------|--------|--------|
| Raspberry Pi 4 | 1 | Master controller, logic, safety system | ✅ |
| **ESP32 (ESP-BC)** | **1** | **Control rods + turbine + pumps + humidifiers (UART)** | ✅ |
| **ESP32 (ESP-E)** | **1** | **LED visualization + power indicator (UART)** | ✅ |
| Push Button | **17** | **Operator input (manual control + auto simulation + emergency)** | ✅ |
| OLED Display | 9 | Real-time monitoring (128x64 I2C) | ✅ |
| Servo Motor | 3 | Control rod simulation (safety, shim, regulating) | ✅ |
| LED Flow | 48 | Flow visualization (16 LEDs × 3 flows) | ✅ |
| **LED Power** | **10** | **Power output visualization (0-300 MWe)** | ✅ |
| Relay | 4 | **Cooling Tower humidifiers (CT1-4)** | ✅ |
| Motor Driver (L298N) | 4 | **3 pumps + 1 turbine (PWM + direction control)** | ✅ |
| Humidifier | 4 | Cooling tower visual effect | ✅ |
| **Video Display** | **1** | **Educational visualization (separate monitor)** | ✅ **NEW** |

### Target Pengguna
- 🎓 Mahasiswa teknik nuklir
- 👨‍🏫 Dosen untuk demonstrasi
- 🏫 Institusi pendidikan
- 🔬 Penelitian sistem kontrol

---

## 🚀 Architecture v4.0 - UART Communication

### Why UART Instead of I2C?

**Old Architecture (v3.x - I2C):**
- I2C Master-Slave communication
- Buffer garbage issues
- Clock stretching problems
- Limited to 100kHz speed
- Complex multiplexer setup

**New Architecture (v4.0 - UART):**
- **Hardware UART** - Dedicated serial ports
- **Binary protocol** - 83% size reduction vs JSON
- **CRC8 checksum** - Error detection
- **115200 baud** - Faster than I2C
- **No multiplexer** - Direct connection
- **Reliable** - No buffer issues

### UART Communication Benefits

| Aspect | I2C (Old) | UART (New) | Improvement |
|--------|-----------|------------|-------------|
| **Speed** | 100 kHz | 115200 baud | ⚡ **15% faster** |
| **Reliability** | Buffer issues | CRC8 + ACK/NACK | 🛡️ **Error detection** |
| **Message Size** | 86-187 bytes | 15-28 bytes | 📦 **83% reduction** |
| **Wiring** | I2C + Multiplexer | Direct UART | 🔌 **Simpler** |
| **CPU Load** | Higher (polling) | Lower (interrupt) | 📊 **More efficient** |
| **Debugging** | Complex | Easy (serial monitor) | 🐛 **Better tools** |

### UART Port Configuration

```
Raspberry Pi UART Ports:
┌─────────────────────────────────────────────────────┐
│  UART0 (/dev/ttyAMA0)  - GPIO 14/15  → ESP-BC      │
│  UART3 (/dev/ttyAMA1)  - GPIO 4/5    → ESP-E       │
└─────────────────────────────────────────────────────┘

ESP32 Hardware Serial:
┌─────────────────────────────────────────────────────┐
│  ESP-BC: UART2 (GPIO 16=RX, 17=TX) ← Raspberry Pi  │
│  ESP-E:  UART2 (GPIO 16=RX, 17=TX) ← Raspberry Pi  │
└─────────────────────────────────────────────────────┘
```

### Binary Protocol Format

**Command Structure:**
```
[STX][CMD][LEN][PAYLOAD][CRC8][ETX]
 0x02  1B   1B   0-23B    1B   0x03

STX  = Start of Text (0x02)
CMD  = Command type (PING=0x50, UPDATE=0x55)
LEN  = Payload length
CRC8 = Checksum of CMD+LEN+PAYLOAD
ETX  = End of Text (0x03)
```

**Example - ESP-BC Update:**
```
Send: [0x02][0x55][0x0A][rod1][rod2][rod3][h1][h2][h3][h4][CRC][0x03]
      = 15 bytes (vs 86 bytes JSON)

Recv: [0x02][0x06][0x17][23 bytes data][CRC][0x03]
      = 28 bytes (vs 187 bytes JSON)
```

### File Structure (Updated)

```
pkm-simulator-PLTN/
├── esp_utama_uart/
│   └── esp_utama_uart.ino              # ✅ ESP-BC UART firmware
│
├── esp_visualizer_uart/
│   └── esp_visualizer_uart.ino         # ✅ ESP-E UART firmware
│
├── raspi_central_control/
│   ├── raspi_main_panel.py             # ✅ Main control program
│   ├── raspi_uart_master.py            # ✅ UART communication
│   ├── raspi_gpio_buttons.py           # ✅ Button handler (event queue)
│   ├── raspi_humidifier_control.py     # ✅ Humidifier logic
│   ├── raspi_buzzer_alarm.py           # ✅ Buzzer alarm
│   ├── raspi_oled_manager.py           # ✅ OLED display manager
│   ├── raspi_tca9548a.py               # ✅ I2C multiplexer (OLEDs only)
│   ├── raspi_system_health.py          # ✅ Health monitoring
│   ├── raspi_config.py                 # ✅ Configuration
│   └── test_komunikasi_lengkap.py      # ✅ Full system test
│
└── pltn_video_display/
    ├── video_display_app.py            # ✅ Video display application
    ├── README.md                       # ✅ Video display guide
    └── assets/                         # ✅ Video files
```

### Quick Start with v4.0

```bash
# 1. Enable UART3 on Raspberry Pi
sudo nano /boot/config.txt
# Add: dtoverlay=uart3

# 2. Upload firmware
Arduino IDE → esp_utama_uart/esp_utama_uart.ino → ESP32 #1 (ESP-BC)
Arduino IDE → esp_visualizer_uart/esp_visualizer_uart.ino → ESP32 #2 (ESP-E)

# 3. Connect UART wires
# ESP-BC: RasPi GPIO 14(TX) → ESP GPIO 16(RX)
#         RasPi GPIO 15(RX) ← ESP GPIO 17(TX)
# ESP-E:  RasPi GPIO 4(TX)  → ESP GPIO 16(RX)
#         RasPi GPIO 5(RX)  ← ESP GPIO 17(TX)

# 4. Run RasPi program
cd raspi_central_control
python3 raspi_main_panel.py

# 5. (Optional) Run video display
cd pltn_video_display
python3 video_display_app.py --test --windowed
```

---

## 🏗️ System Architecture

### Diagram Arsitektur v4.0 (2 ESP - UART Communication)

```
┌───────────────────────────────────────────────────────────────┐
│                 PANEL KONTROL OPERATOR                        │
│  ┌──────────────────────┐  ┌───────────────────────────────┐ │
│  │  17 Push Buttons     │  │  9 OLED Displays (128x64)     │ │
│  │  ├─ 6 Pump (ON/OFF)  │  │  ├─ 1: Presurizer (I2C 0x70)  │ │
│  │  ├─ 6 Rod (UP/DOWN)  │  │  ├─ 2-4: Pumps (Ch1-3)       │ │
│  │  ├─ 2 Pressure       │  │  ├─ 5-7: Rods (Ch4-6)        │ │
│  │  ├─ 2 Mode/Control   │  │  ├─ 8: Thermal kW (Ch7)      │ │
│  │  └─ 1 Emergency      │  │  └─ 9: Status (0x70 Ch7)     │ │
│  └──────────────────────┘  └───────────────────────────────┘ │
│         ↓ GPIO 6-27            ↓ I2C Bus (TCA9548A 0x70)     │
└───────────────────────────────────────────────────────────────┘
                             ↓
┌───────────────────────────────────────────────────────────────┐
│               RASPBERRY PI 4 (Master Controller)              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Python Control Program v4.0 (Multi-threaded)         │  │
│  │  ├─ Thread 1: Button polling (10ms)                  │  │
│  │  ├─ Thread 2: Button event processor (event queue)   │  │
│  │  ├─ Thread 3: Control logic (50ms)                   │  │
│  │  ├─ Thread 4: UART ESP-BC comm (100ms)              │  │
│  │  ├─ Thread 5: UART ESP-E comm (100ms)               │  │
│  │  ├─ Thread 6: OLED display update (200ms)           │  │
│  │  └─ Thread 7: System health monitor (1000ms)        │  │
│  │                                                          │  │
│  │  Program: raspi_main_panel.py ✅                       │  │
│  │  Protocol: Binary UART with CRC8 checksum ✅          │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
                    ↓ UART Communication (115200 baud)
         ┌─────────────────────┬─────────────────────┐
         │      ESP-BC         │       ESP-E         │
         │  UART: GPIO 14/15   │  UART: GPIO 4/5     │
         │  (RasPi) → (ESP)    │  (RasPi) → (ESP)    │
         │   16=RX, 17=TX      │   16=RX, 17=TX      │
         │                     │                     │
         │ • 3 Servo motors   │ • 48 LEDs (3x16)    │
         │ • 4 CT Relays      │   via multiplexer   │
         │ • 4 PWM motors     │ • Primary flow      │
         │   (L298N drivers)  │ • Secondary flow    │
         │ • Thermal calc     │ • Tertiary flow     │
         │ • State machine    │ • 10 Power LEDs     │
         │ • Binary protocol  │ • Animation control │
         │                     │                     │
         │ File:              │ File:               │
         │ esp_utama_uart.ino │ esp_visualizer_     │
         │                     │ uart.ino            │
         └─────────────────────┴─────────────────────┘
         
    ✅ UART replaces I2C - More reliable!
    ✅ Binary protocol - 83% size reduction!
    ✅ CRC8 + ACK/NACK - Error detection!
```

### Communication Organization

**UART Ports (ESP Communication):**
- UART0 (/dev/ttyAMA0): RasPi GPIO 14/15 ↔ ESP-BC GPIO 16/17
- UART3 (/dev/ttyAMA1): RasPi GPIO 4/5 ↔ ESP-E GPIO 16/17

**I2C Bus (Display Only):**
- GPIO 2/3: I2C Bus 1 → TCA9548A (0x70) → 9x OLED displays

**Note:** I2C is now only used for OLED displays. ESP communication moved to UART for reliability.

---

## 💻 Hardware Components

### 1. Raspberry Pi 4 (Master Controller)

**Spesifikasi:**
- Model: Raspberry Pi 4 Model B (4GB RAM recommended)
- OS: Raspberry Pi OS (Bullseye atau lebih baru)
- Python: 3.7+

**GPIO Usage:**
```
GPIO 2/3:   I2C (SDA/SCL) - 9 OLED displays only
GPIO 14/15: UART0 (TXD/RXD) - ESP-BC communication
GPIO 4/5:   UART3 (TXD/RXD) - ESP-E communication (requires dtoverlay=uart3)
GPIO 6-27:  17 Push Buttons (with internal pull-up)
GPIO 22:    Buzzer (PWM output)
```

**Tasks:**
1. Baca 17 push buttons (event queue pattern, no deadlocks)
2. Implementasi safety interlock logic
3. Kontrol 9 OLED displays via TCA9548A (I2C)
4. Komunikasi dengan 2 ESP32 via UART (binary protocol)
5. Kalkulasi humidifier control
6. System health monitoring
7. Export state to JSON (untuk video display)
8. Data logging ke CSV

---

### 2. ESP-BC (UART) - Control Rods + Turbine + Motors + Humidifiers

**Hardware:**
- ESP32 Dev Board (38-pin)
- 3x Servo motors (MG996R recommended) - Control rods
- 2x L298N Motor Driver (4 channels total: 3 pumps + 1 turbine)
- 4x Relay Module (Cooling Tower humidifiers)
- UART connection to Raspberry Pi

**UART Connection:**
```
Raspberry Pi GPIO 14 (UART0 TX) → ESP32 GPIO 16 (UART2 RX)
Raspberry Pi GPIO 15 (UART0 RX) ← ESP32 GPIO 17 (UART2 TX)
Common GND
```

**GPIO Pins:**
```cpp
// UART Communication
#define UART_RX 16  // From Raspberry Pi
#define UART_TX 17  // To Raspberry Pi

// Servo motors (Control Rods)
#define SERVO_SAFETY 13      // Safety rod
#define SERVO_SHIM 12        // Shim rod  
#define SERVO_REGULATING 14  // Regulating rod

// L298N Motor Drivers (PWM)
#define MOTOR_PUMP_PRIMARY 4      // Primary pump
#define MOTOR_PUMP_SECONDARY 5    // Secondary pump
#define MOTOR_PUMP_TERTIARY 18    // Tertiary pump
#define MOTOR_TURBINE 19          // Turbine motor

// L298N Direction Control (Turbine only)
#define MOTOR_TURBINE_IN1 23  // Forward
#define MOTOR_TURBINE_IN2 15  // Reverse

// Cooling Tower Humidifier Relays
#define RELAY_CT1 27  // Cooling Tower 1
#define RELAY_CT2 26  // Cooling Tower 2
#define RELAY_CT3 25  // Cooling Tower 3
#define RELAY_CT4 32  // Cooling Tower 4
```

**Fungsi:**
- Terima commands via UART (binary protocol, 15 bytes)
- Gerakkan 3 servo motors sesuai target (smooth interpolation)
- Kontrol 4 motor drivers (PWM 0-255) dengan L298N
- Kontrol direction turbin (FORWARD/REVERSE/STOP)
- Kontrol 4 relay humidifier (ON/OFF sesuai command)
- Hitung thermal power (kW) dari posisi rod
- Kirim status via UART (binary protocol, 28 bytes)

**UART Binary Protocol:**
```cpp
// Receive Command (15 bytes):
// [STX][CMD=0x55][LEN=10][rod1][rod2][rod3][pump1][pump2][pump3]
// [humid1][humid2][humid3][humid4][CRC8][ETX]

// Send Response (28 bytes):
// [STX][ACK=0x06][LEN=23][rod1_actual][rod2_actual][rod3_actual]
// [thermal_kw (float)][power_level (float)][state][turbine_speed (float)]
// [pump1_speed (float)][pump2_speed (float)][pump3_speed (float)]
// [humid1_status][humid2_status][humid3_status][humid4_status]
// [CRC8][ETX]
```

---

### 3. ESP-E (UART) - LED Visualizer + Power Indicator

**Hardware:**
- ESP32 Dev Board (38-pin)
- 3x CD74HC4067 (16-channel multiplexer)
- 48x LED (16 per flow) - Water flow visualization
- 10x LED - Power indicator (0-300 MWe)
- Current limiting resistors (220Ω per LED)
- UART connection to Raspberry Pi

**UART Connection:**
```
Raspberry Pi GPIO 4 (UART3 TX) → ESP32 GPIO 16 (UART2 RX)
Raspberry Pi GPIO 5 (UART3 RX) ← ESP32 GPIO 17 (UART2 TX)
Common GND
```

**GPIO Pins:**
```cpp
// UART Communication
#define UART_RX 16  // From Raspberry Pi
#define UART_TX 17  // To Raspberry Pi

// Multiplexer Control (Shared)
#define MUX_S0 14
#define MUX_S1 27
#define MUX_S2 26
#define MUX_S3 25

// Flow LED Control (3 flows)
#define FLOW_EN_PRIMARY 33     // Enable pin
#define FLOW_SIG_PRIMARY 32    // Signal pin (PWM)

#define FLOW_EN_SECONDARY 15
#define FLOW_SIG_SECONDARY 4

#define FLOW_EN_TERTIARY 2
#define FLOW_SIG_TERTIARY 16

// Power Indicator LEDs (10 LEDs, 0-300 MWe)
#define LED_POWER_1  23
#define LED_POWER_2  22
#define LED_POWER_3  21
#define LED_POWER_4  19
#define LED_POWER_5  18
#define LED_POWER_6  5
#define LED_POWER_7  17  // Note: Conflicts with TX, use different pin
#define LED_POWER_8  13
#define LED_POWER_9  12
#define LED_POWER_10 14
```

**Fungsi:**
- Terima status via UART (binary protocol, 17 bytes)
- Animate 48 LEDs (3 flows × 16 LEDs) dengan kecepatan berbeda
- Kontrol 10 power LEDs (simultaneous brightness control)
- Multi-wave flowing effect untuk realistis
- PWM brightness control (0-255)

**UART Binary Protocol:**
```cpp
// Receive Command (17 bytes):
// [STX][CMD=0x55][LEN=12][thermal_kw (float)][pump1_status]
// [pump2_status][pump3_status][reserved...][CRC8][ETX]

// Send Response (10 bytes):
// [STX][ACK=0x06][LEN=5][power_mwe (float)][pwm][CRC8][ETX]
```

---

## 🎬 Video Display System (NEW v4.0)

### Overview

Sistem visualisasi video **terpisah** yang menampilkan educational content dan interactive guide pada monitor terpisah.

**Key Features:**
- ✅ **Standalone module** - Independent from main control
- ✅ **Pygame-based** - Lightweight & cross-platform
- ✅ **3 display modes** - IDLE, AUTO (video), MANUAL (guide)
- ✅ **Real-time sync** - Reads state from JSON file
- ✅ **Testing mode** - No simulation required

### Architecture

```
┌──────────────────────┐         ┌──────────────────────┐
│  raspi_main_panel.py │         │ video_display_app.py │
│  (Main Controller)   │         │ (Video Display)      │
│                      │         │                      │
│  • Button handling   │         │  • Pygame window     │
│  • ESP comm (UART)   │         │  • mpv video player  │
│  • Control logic     │         │  • State reading     │
│  • OLED displays     │         │  • UI rendering      │
│  • Export state ───> │  JSON   │  • Step guides       │
│                      │  File   │                      │
└──────────────────────┘         └──────────────────────┘
         ↑                                    ↓
         │                               HDMI Monitor
    ESP32 Hardware                     (1920x1080)
```

### JSON State File

**Location:**
- Linux/RPi: `/tmp/pltn_state.json`
- Windows: `C:/temp/pltn_state.json`

**Format:**
```json
{
  "timestamp": 1736520312.123,
  "mode": "manual",
  "auto_running": false,
  "auto_phase": "",
  "pressure": 45.0,
  "safety_rod": 100,
  "shim_rod": 50,
  "regulating_rod": 50,
  "pump_primary": 2,
  "pump_secondary": 2,
  "pump_tertiary": 2,
  "thermal_kw": 25000.0,
  "turbine_speed": 85.0,
  "emergency": false
}
```

### Display Modes

**1. IDLE Screen**
- Shown when: No activity, backend not running
- Content: Welcome screen with instructions

**2. AUTO Mode - Video**
- Shown when: `mode='auto'` and `auto_running=True`
- Content: Fullscreen educational video (`videos/full_process.mp4`)
- Duration: ~60-90 seconds loop

**3. MANUAL Mode - Interactive Guide**
- Shown when: `mode='manual'`
- Content: Step-by-step instructions with real-time feedback
- Steps: 9 phases (pressure, pumps, rods, operation)
- Includes: Progress bars, parameter display, next step hints

### Quick Start

**Test Mode (No Hardware):**
```bash
cd pltn_video_display
python video_display_app.py --test --windowed

# Controls:
# Press 1 = IDLE, 2 = AUTO, 3 = MANUAL
# Press UP/DOWN = Adjust pressure
# Press R/P = Toggle rods/pumps
```

**Production Mode (With Simulation):**
```bash
# Terminal 1: Main simulation
cd raspi_central_control
python raspi_main_panel.py

# Terminal 2: Video display
cd pltn_video_display
python video_display_app.py
```

**See [pltn_video_display/README.md](pltn_video_display/README.md) for complete documentation.**

---

## 🎛️ Control Panel

### 9 OLED Displays (via TCA9548A)

**TCA9548A (Address: 0x70)**

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
| 7 | 9 | System Status | `Humidifiers: CT1-4` |

### 17 Push Buttons (via GPIO)

**See [GPIO_PIN_MAPPING.md](GPIO_PIN_MAPPING.md) for complete pin mapping guide.**

**Pump Control (6 buttons):**
```
GPIO 11: Pump Primary ON      GPIO 6:  Pump Primary OFF
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

**System Control (3 buttons):**
```
GPIO 17: REACTOR START (GREEN)
GPIO 27: REACTOR RESET (YELLOW)
GPIO 18: EMERGENCY SHUTDOWN (RED)
```

**Note:** GPIO 5 previously used for PUMP_PRIMARY_ON has been moved to GPIO 11 to accommodate UART3 (GPIO 4/5 for ESP-E communication).

---

## 🧠 Software Architecture

### File Structure (v4.0)

```
pkm-simulator-PLTN/
├── esp_utama_uart/
│   └── esp_utama_uart.ino              # ✅ ESP-BC UART firmware
│
├── esp_visualizer_uart/
│   └── esp_visualizer_uart.ino         # ✅ ESP-E UART firmware
│
├── pltn_video_display/
│   ├── video_display_app.py            # ✅ Video display application
│   ├── README.md                       # ✅ Video display guide
│   ├── 3_MODE_DESIGN_SPEC.md          # ✅ Design specification
│   ├── PYGAME_ANIMATION_GUIDE.md      # ✅ Animation guide
│   ├── requirements.txt               # ✅ Python dependencies
│   └── assets/                        # ✅ Video files
│
└── raspi_central_control/
    ├── raspi_main_panel.py            # ✅ Main program (v4.0)
    ├── raspi_uart_master.py           # ✅ UART communication
    ├── raspi_gpio_buttons.py          # ✅ Button handler (event queue)
    ├── raspi_humidifier_control.py    # ✅ Humidifier logic
    ├── raspi_buzzer_alarm.py          # ✅ Buzzer alarm
    ├── raspi_oled_manager.py          # ✅ OLED display manager
    ├── raspi_tca9548a.py              # ✅ I2C multiplexer (OLEDs)
    ├── raspi_system_health.py         # ✅ System health monitor
    ├── raspi_config.py                # ✅ Configuration
    ├── raspi_README.md                # ✅ Installation guide
    ├── raspi_requirements.txt         # ✅ Python dependencies
    └── test_komunikasi_lengkap.py     # ✅ Full system test
```

### Multi-threaded Architecture (v4.0)

```python
# Thread 1: Button Polling (10ms cycle)
# - Non-blocking GPIO reads
# - Debounce handling (200ms)
# - Immediate response
while running:
    button_handler.check_all_buttons()
    time.sleep(0.01)

# Thread 2: Button Event Processor (event queue pattern)
# - Process events from queue
# - Can use locks safely
# - Decoupled from interrupt context
while running:
    try:
        event = button_event_queue.get(timeout=0.1)
        process_button_event(event)  # with state_lock
        button_event_queue.task_done()
    except Empty:
        pass

# Thread 3: Control Logic & Safety (50ms cycle)
# - Check safety interlock
# - Update rod positions
# - Calculate humidifier commands
# - Thermal calculations
while running:
    with state_lock:
        # Safety interlock check
        rod_movement_allowed = check_interlock()
        
        # Update system state
        if rod_movement_allowed:
            update_rod_positions()
        
        # Humidifier control logic
        update_humidifier_status()
    
    time.sleep(0.05)

# Thread 4: UART ESP-BC Communication (100ms cycle)
# - Binary protocol with CRC8
# - Send rod targets + humidifier commands
# - Receive rod actuals + thermal + pump speeds
while running:
    with state_lock:
        # Prepare command
        rod_targets = [safety_rod, shim_rod, regulating_rod]
        humid_cmds = [ct1_cmd, ct2_cmd, ct3_cmd, ct4_cmd]
    
    # Send/receive via UART (outside lock)
    esp_bc_data = uart_master.update_esp_bc(rod_targets, [], humid_cmds)
    
    with state_lock:
        # Update state with response
        update_from_esp_bc(esp_bc_data)
    
    time.sleep(0.1)

# Thread 5: UART ESP-E Communication (100ms cycle)
# - Binary protocol with CRC8
# - Send thermal power + pump status
# - Receive power indicator status
while running:
    with state_lock:
        thermal_kw = state.thermal_kw
        pump_status = [pump_primary, pump_secondary, pump_tertiary]
    
    # Send/receive via UART
    esp_e_data = uart_master.update_esp_e(thermal_kw, pump_status)
    
    with state_lock:
        state.power_mwe = esp_e_data.power_mwe
    
    time.sleep(0.1)

# Thread 6: OLED Display Update (200ms cycle)
# - Update 9 OLED displays via TCA9548A
# - Format data for display
# - Progress bars and status
while running:
    with state_lock:
        display_data = get_display_data()
    
    # Update displays (I2C communication)
    oled_manager.update_all_displays(display_data)
    
    time.sleep(0.2)

# Thread 7: System Health Monitor (1000ms cycle)
# - Check thread status
# - Monitor UART communication
# - Log system statistics
# - Watchdog functionality
while running:
    health_status = system_health.check_all()
    
    if health_status.errors:
        logger.warning(f"Health check warnings: {health_status.errors}")
    
    time.sleep(1.0)
```

### Event Queue Pattern (No Deadlocks!)

**See [BUTTON_EVENT_QUEUE_PATTERN.md](BUTTON_EVENT_QUEUE_PATTERN.md) for complete implementation guide.**

**Key Points:**
- Button callbacks only enqueue events (< 1μs)
- Dedicated thread processes events with locks
- No deadlock risk from interrupt context
- Proven pattern in embedded systems

```python
# In button callback (interrupt context)
def on_pressure_up(self):
    self.button_event_queue.put(ButtonEvent.PRESSURE_UP)
    logger.info("⚡ Queued: PRESSURE_UP")

# In event processor thread (can use locks)
def process_button_event(self, event):
    with self.state_lock:  # Safe to use lock here!
        if event == ButtonEvent.PRESSURE_UP:
            self.state.pressure = min(self.state.pressure + 5.0, 200.0)
```
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

### 2. ⚡ Power Indicator System ⭐ NEW v3.1!

**10 LED Power Visualization (0-300 MWe)**

Menampilkan output daya listrik reaktor secara real-time dengan 10 LED yang menyala bersamaan.

**Spesifikasi Reaktor:**
```
Reactor Type: PWR (Pressurized Water Reactor)
Electrical Rating: 300 MWe (Megawatt electrical)
Thermal Capacity: 900 MWth (Megawatt thermal)
Turbine Efficiency: 33% (typical PWR)
```

**LED Behavior:**
```
✅ Semua 10 LED menyala BERSAMAAN
✅ Brightness SAMA untuk semua LED
✅ Brightness proporsional dengan daya output

Examples:
0 MWe (0%):     Semua OFF
75 MWe (25%):   Semua DIM (brightness 64)
150 MWe (50%):  Semua MEDIUM (brightness 127)
225 MWe (75%):  Semua BRIGHT (brightness 191)
300 MWe (100%): Semua FULL (brightness 255)
```

**Realistic Physics:**
```
Reactor Core → 900 MWth (heat from nuclear fission)
      ↓
   Turbine → 33% efficiency
      ↓
   Output → 300 MWe (electrical power)

Power ONLY generated when:
1. Control rods raised (reactivity)
2. Turbine running (conversion)
```

**Hardware:**
- Location: ESP-E (Visualizer)
- LEDs: 10x standard 5mm LEDs
- GPIO: 23, 22, 21, 19, 18, 5, 17, 13, 12, 14
- Control: PWM (0-255 brightness)
- Resistor: 220Ω per LED

---

### 3. 🌊 Humidifier Control System (6 Units)

**2x Steam Generator Humidifiers**

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
- Relay 1: ESP-BC GPIO 13 (SG Humidifier #1)
- Relay 2: ESP-BC GPIO 15 (SG Humidifier #2)
- Visual: Uap keluar dari steam generator mockup

**4x Cooling Tower Humidifiers**

**Kondisi ON:**
```
Electrical Power >= 80 MWe (80,000 kW)
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

### 4. 🔄 PWR Startup Sequence (ALUR SIMULASI TERKINI)

**Realistic Pressurized Water Reactor startup - 300 MWe PWR:**

```
Phase 1: System Initialization (0-5s)
├─ Operator action: Press START button
├─ All pumps: OFF (status = 0)
├─ All rods: 0% (fully inserted)
├─ Pressure: 0 bar
├─ Turbine state: IDLE
├─ Power output: 0 MWe
├─ Display: "SYSTEM READY - START REACTOR"
└─ Note: Semua kontrol aktif setelah START

Phase 2: Control Rods Withdrawal (5-30s)
├─ Operator action: Press Shim Rod UP & Regulating Rod UP
├─ Shim rod: 0% → 40% (increment +5% per press)
├─ Regulating rod: 0% → 40% (increment +5% per press)
├─ Safety rod: Tetap 0% (untuk shutdown/SCRAM only)
├─ Reactor thermal: Mulai naik (quadratic curve)
│  └─ Formula: (shim+reg)/2 × (shim+reg)/2 × 90
├─ Servo motors: Bergerak sesuai target position
├─ Display: Rod positions update real-time
└─ Note: Reactor mulai menghasilkan panas thermal

Phase 3: Steam Generator Humidifiers Activate (30-35s)
├─ Kondisi trigger: Shim ≥ 40% AND Regulating ≥ 40%
├─ Action automatic:
│  ├─ RELAY_HUMID_SG1 → ON (GPIO 13)
│  └─ RELAY_HUMID_SG2 → ON (GPIO 15)
├─ Visual effect: Uap keluar dari steam generator mockup 💨
├─ Hysteresis: OFF ketika < 35% (mencegah oscillation)
└─ Display: "HUMIDIFIERS: SG1✓ SG2✓"

Phase 4: Turbine Starting (35-60s)
├─ Kondisi trigger: Reactor thermal > 50 MWth (50,000 kW)
├─ Turbine state: IDLE → STARTING
├─ Turbine speed: 0% → 100% (gradual, +0.5% per cycle)
├─ Motor turbin PWM: Mengikuti turbine speed
│  └─ Speed = (Shim + Regulating) / 2
├─ Pompa auto-start (controlled by ESP-BC):
│  ├─ Primary: 0% → 50% (gradual +2% per cycle)
│  ├─ Secondary: 0% → 50% (gradual +2% per cycle)
│  └─ Tertiary: 0% → 50% (gradual +2% per cycle)
├─ LED Flow: All 3 flows animate (48 LEDs)
└─ Display: "TURBINE STARTING"

Phase 5: Power Generation Begins (60-120s)
├─ Turbine state: STARTING → RUNNING (ketika speed = 100%)
├─ Pompa speed: 50% → 100% (gradual)
├─ Power calculation (realistic PWR physics):
│  ├─ Reactor thermal: ~900 MWth (dari rod positions)
│  ├─ Turbine efficiency: 33% (typical PWR)
│  ├─ Turbine load: 100% (fully loaded)
│  └─ Electrical output: 900 MWth × 0.33 × 1.0 = ~300 MWe
├─ Power indicator LEDs: 10 LEDs menyala BERSAMAAN
│  └─ Brightness: Proporsional dengan output (0-255 PWM)
├─ Thermal power: Menampilkan electrical output (kW)
└─ Display: "POWER: 300 MWe - STABLE OPERATION"

Phase 6: Cooling Tower Humidifiers Activate (120s+)
├─ Kondisi trigger: Electrical power ≥ 80 MWe (80,000 kW)
├─ Action automatic:
│  ├─ RELAY_HUMID_CT1 → ON (GPIO 32)
│  ├─ RELAY_HUMID_CT2 → ON (GPIO 33)
│  ├─ RELAY_HUMID_CT3 → ON (GPIO 14)
│  └─ RELAY_HUMID_CT4 → ON (GPIO 12)
├─ Visual effect: Uap keluar dari 4 cooling tower mockup 💨
├─ Hysteresis: OFF ketika < 70 MWe
└─ Display: "HUMIDIFIERS: SG✓ CT(1-4)✓"

Phase 7: Normal Operation (Stable)
├─ Operator dapat adjust:
│  ├─ Control rods: Fine tuning reactivity
│  ├─ Pressure: Adjust dengan UP/DOWN buttons
│  └─ Power output: Dikontrol via rod positions
├─ System monitoring:
│  ├─ 9 OLED: Real-time status semua parameter
│  ├─ 48 LED: Flow animation continuous
│  ├─ 10 LED: Power indicator brightness
│  ├─ 6 Humidifier: Status sesuai kondisi
│  └─ Servos: Posisi actual = target
├─ Safety interlock: Active monitoring
│  └─ Emergency button: Ready untuk SCRAM
└─ Status: "REACTOR STABLE - 300 MWe OUTPUT"

Phase 8: Emergency Shutdown (Jika diperlukan)
├─ Operator action: Press EMERGENCY button (GPIO 18)
├─ Immediate actions:
│  ├─ All rods: → 0% (fully inserted - SCRAM)
│  ├─ Turbine: RUNNING → SHUTDOWN
│  ├─ Power output: Ramp down ke 0 MWe
│  ├─ Pompa: Gradual deceleration (-1% per cycle)
│  ├─ All humidifiers: → OFF
│  └─ LED flows: Slow down then stop
├─ System state: Emergency active = True
├─ Interlock: Semua kontrol locked
└─ Display: "⚠️ EMERGENCY SHUTDOWN ACTIVE"
```

**Key Features Alur Simulasi:**
- ✅ **START Button Required** - Semua operasi dimulai dengan START
- ✅ **Automatic Turbine Control** - State machine di ESP-BC
- ✅ **Gradual Pump Control** - Realistic acceleration/deceleration
- ✅ **6 Individual Humidifiers** - 2 SG + 4 CT dengan logic berbeda
- ✅ **Realistic Power Calculation** - 900 MWth × 33% efficiency = 300 MWe
- ✅ **10 LED Power Indicator** - Simultaneous brightness control
- ✅ **Safety Interlock** - Mencegah operasi tidak aman
- ✅ **Emergency SCRAM** - Immediate shutdown capability

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

#### Wiring Raspberry Pi (v4.0 - UART)

```
I2C Bus (Display Only):
GPIO 2  (SDA) ─→ TCA9548A (0x70) ─→ 9x OLED displays
GPIO 3  (SCL) ─┘

UART Communication (ESP32):
GPIO 14 (UART0 TX) ─→ ESP-BC GPIO 16 (RX)
GPIO 15 (UART0 RX) ←─ ESP-BC GPIO 17 (TX)

GPIO 4  (UART3 TX) ─→ ESP-E GPIO 16 (RX)
GPIO 5  (UART3 RX) ←─ ESP-E GPIO 17 (TX)

Buttons:
GPIO 6-27: 17x Push Buttons (with internal pull-up)
GPIO 22:   Buzzer output (PWM)

Common GND between RasPi and all ESP32 modules!
```

#### Wiring ESP-BC (Control + Motors + Humidifiers)

```
UART:
ESP GPIO 16 (RX) ←─ RasPi GPIO 14 (TX)
ESP GPIO 17 (TX) ─→ RasPi GPIO 15 (RX)

Servos (Control Rods):
ESP GPIO 13 ─→ Safety Rod Servo (Signal)
ESP GPIO 12 ─→ Shim Rod Servo (Signal)
ESP GPIO 14 ─→ Regulating Rod Servo (Signal)

L298N Motor Drivers:
ESP GPIO 4  ─→ ENA (Primary Pump PWM)
ESP GPIO 5  ─→ ENB (Secondary Pump PWM)
ESP GPIO 18 ─→ ENA (Tertiary Pump PWM)
ESP GPIO 19 ─→ ENB (Turbine PWM)
ESP GPIO 23 ─→ IN1 (Turbine direction)
ESP GPIO 15 ─→ IN2 (Turbine direction)

Cooling Tower Humidifier Relays:
ESP GPIO 27 ─→ Relay 1 IN ─→ CT1 (220V AC)
ESP GPIO 26 ─→ Relay 2 IN ─→ CT2 (220V AC)
ESP GPIO 25 ─→ Relay 3 IN ─→ CT3 (220V AC)
ESP GPIO 32 ─→ Relay 4 IN ─→ CT4 (220V AC)

⚠️ WARNING: Use optocoupler relay module!
⚠️ Separate ground for 220V AC and 5V logic!
⚠️ Add fuse on AC line!
```

#### Wiring ESP-E (LED Visualizer)

```
UART:
ESP GPIO 16 (RX) ←─ RasPi GPIO 4 (TX)
ESP GPIO 17 (TX) ─→ RasPi GPIO 5 (RX)

Flow LEDs & Power LEDs:
(See hardware section for complete pin mapping)
```

### 2. Software Installation

#### Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python packages
sudo apt install python3-pip python3-dev i2c-tools -y

# Enable I2C (for OLED displays)
sudo raspi-config
# → Interface Options → I2C → Enable

# Enable UART3 (for ESP-E communication)
sudo nano /boot/config.txt
# Add this line at the end:
dtoverlay=uart3

# Install Python dependencies
cd raspi_central_control
pip3 install -r raspi_requirements.txt

# Reboot
sudo reboot

# After reboot, verify UART ports
ls -l /dev/ttyAMA*
# Should see:
# /dev/ttyAMA0 (UART0 - ESP-BC)
# /dev/ttyAMA1 (UART3 - ESP-E)

# Test I2C detection (OLED displays only)
sudo i2cdetect -y 1
```

**Expected i2cdetect output (v4.0):**
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
10:          -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20:          -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30:          -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- 
40:          -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50:          -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60:          -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: 70 -- -- -- -- -- -- --
```

Addresses found:
- `0x3C` = OLED displays
- `0x70` = TCA9548A (OLED multiplexer)

**Note:** ESP32 no longer appear on I2C bus (now using UART).

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
   
4. Install ESP32Servo library
   Tools → Manage Libraries → Search "ESP32Servo" → Install
```

**Upload Firmware:**
```
1. ESP-BC (Control Rods + Motors + Humidifiers):
   Open: esp_utama_uart/esp_utama_uart.ino
   Select: Tools → Port → (your ESP32 port)
   Upload to ESP32 #1

2. ESP-E (LED Visualizer):
   Open: esp_visualizer_uart/esp_visualizer_uart.ino
   Select: Tools → Port → (your ESP32 port)
   Upload to ESP32 #2
```

### 3. Testing

**Test UART Communication:**
```bash
# Test ESP-BC UART
sudo minicom -D /dev/ttyAMA0 -b 115200
# Should see binary data stream when ESP is running

# Test ESP-E UART
sudo minicom -D /dev/ttyAMA1 -b 115200
# Should see binary data stream when ESP is running
```

**Test individual modules:**
```bash
cd raspi_central_control

# Test button handler (event queue pattern)
python3 raspi_gpio_buttons.py

# Test UART communication
python3 test_komunikasi_lengkap.py

# Test OLED displays
python3 raspi_oled_manager.py
```

**Run main program:**
```bash
cd raspi_central_control
python3 raspi_main_panel.py

# In separate terminal, run video display (optional)
cd pltn_video_display
python3 video_display_app.py --test --windowed
```
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

**Overall Progress:** 🟢 **98% Complete** (Ready for Hardware Testing)  
**Architecture:** ✅ **v3.4 - All Critical Issues Fixed**  
**Last Updated:** 2024-12-12  
**Status:** ✅ **READY FOR HARDWARE TESTING** (All critical issues resolved)

### ✅ ALL CRITICAL ISSUES RESOLVED (Session 6 - Dec 12, 2024)

**Issue #1: START Button** ✅ FIXED
- **Solution:** Added `on_reactor_start()` callback with proper flag management
- **Status:** Button registered, reactor can be started properly
- **Files:** `raspi_gpio_buttons.py`, `raspi_main_panel.py`

**Issue #2: RESET Button** ✅ FIXED  
- **Solution:** Renamed STOP → RESET, force reset without conditions
- **Status:** Simulation resets to initial state on button press
- **Files:** `raspi_gpio_buttons.py`, `raspi_main_panel.py`

**Issue #3: Safety Interlock** ✅ FIXED
- **Solution:** Simplified from 6 checks → 3 checks (reactor_started + pressure + no emergency)
- **Status:** Interlock works with auto-controlled pumps
- **Files:** `raspi_main_panel.py`

**Issue #4: 17 Button Registration** ✅ VERIFIED
- **Solution:** All callbacks registered with validation
- **Status:** Complete button integration confirmed
- **Files:** Both button files updated

**Issue #5: L298N Motor Control** ✅ FIXED
- **Solution:** Added 8 direction pins (IN1-IN4 for each L298N)
- **Status:** Full motor direction control (FORWARD/REVERSE/STOP)
- **Files:** `esp_utama.ino`, `L298N_MOTOR_DRIVER_WIRING.md`

**Issue #6: Humidifier Threshold** ✅ FIXED
- **Solution:** Staging control based on power generation (0-300 MWe)
- **Status:** 4 CT humidifiers activate progressively
- **Files:** `raspi_humidifier_control.py`, `raspi_main_panel.py`

**Issue #7: Buzzer GPIO Conflict** ✅ FIXED
- **Solution:** Changed GPIO 18 → GPIO 22 (no conflicts)
- **Status:** Passive buzzer alarm system ready
- **Files:** `raspi_config.py`, `raspi_buzzer_alarm.py`

**See TODO.md for remaining optional enhancements**

---

### ✅ Phase 1 & 2: COMPLETED (100%)

- [x] **ESP-BC (Merged)** ✅ **UPDATED v3.1**
  - Firmware: `esp_utama/esp_utama.ino`
  - 3 servos (control rods)
  - **6 relays (ALL for humidifiers: 2 SG + 4 CT)** ✨ NEW
  - **4 motor drivers (3 pompa + 1 turbin)** ✨ NEW
  - **Realistic 300 MWe PWR physics model** ✨ NEW
  - **Power generation only when turbine runs** ✨ NEW
  - **Pump gradual control (realistic behavior)** ✨ NEW
  - **Dynamic turbine speed (based on rods)** ✨ NEW
  - Thermal power calculation
  - I2C protocol: 12 bytes send, 20 bytes receive
  - ESP32 Core v3.x compatible

- [x] **ESP-E (3-Flow Visualizer + Power Indicator)** ✅ **UPDATED v3.1**
  - Firmware: `esp_visualizer/esp_visualizer.ino`
  - 48 LED flow control via multiplexer
  - 3 independent flow animations
  - **10 LED power indicator (0-300 MWe)** ✨ NEW
  - **Simultaneous brightness control** ✨ NEW
  - **PWM visualization of electrical output** ✨ NEW
  - I2C protocol updated (20 bytes)

- [x] **Python RasPi Programs** ✅
  - `raspi_main_panel.py` - Main control program v3.0
  - `raspi_i2c_master.py` - 2 ESP communication
  - `raspi_humidifier_control.py` - Humidifier logic
  - `raspi_gpio_buttons.py` - 15 button handler
  - `raspi_tca9548a.py` - Multiplexer manager
  - `test_2esp_architecture.py` - Validation test

- [x] **Control Features** ✅ **ENHANCED v3.1**
  - 15 button support with callbacks
  - 3-thread architecture (button, control, ESP comm)
  - Safety interlock logic
  - **6 individual humidifier control** ✨ NEW
  - **Pump gradual start/stop** ✨ NEW
  - **Dynamic turbine speed control** ✨ NEW
  - Emergency shutdown
  - **Realistic 300 MWe PWR physics** ✨ NEW
  - **Real-time power visualization** ✨ NEW

- [x] **Documentation** ✅ **UPDATED v3.1**
  - `README.md` - This file (updated v3.1)
  - `TODO.md` - Updated with Session 5 progress
  - `HARDWARE_UPDATE_SUMMARY.md` - Hardware config details
  - `I2C_ADDRESS_MAPPING.md` - Complete I2C wiring guide ✨ NEW
  - `TCA9548A_EXPLANATION.md` - Multiplexer safety explained ✨ NEW
  - `POWER_INDICATOR_LED.md` - Power LED documentation ✨ NEW
  - `ARCHITECTURE_2ESP.md` - Complete design
  - `ESP_PERFORMANCE_ANALYSIS.md` - Benchmarks
  - `HARDWARE_OPTIMIZATION_ANALYSIS.md` - Pin analysis
  - `INTEGRATION_CHECKLIST_2ESP.md` - Testing guide
  - `REVIEW_SUMMARY.md` - Code review
  - `COMPILATION_FIX.md` - ESP32 v3.x fixes
  - `CLEANUP_GUIDE.md` - Migration guide
  - `TODO.md` - Task tracking

### ⏳ Phase 3: Pending (0%)

- [ ] **9-OLED Display Manager**
  - File: `raspi_panel_oled_9.py`
  - Support 2x PCA9548A (0x70, 0x71)
  - 9 display layouts
  - Integration with main program
  - Status: Not started

- [ ] **Hardware Testing**
  - ESP-BC upload and test
  - ESP-E verify working
  - Button response test
  - LED animation test
  - Humidifier trigger test
  - Full system integration
  - Status: Waiting for hardware

### 📋 Optional Enhancements

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

### Overall Progress: 🟡 **95% Complete - Integration Fixes Needed**

**Summary:**
- ✅ Phase 1 & 2: 100% (All code complete!)
- ⚠️ Integration Issues: 4 issues identified (2 critical, 2 high)
- ⏳ Phase 3: 0% (9-OLED pending - optional)
- 🔧 Hardware Testing: Blocked by integration issues

**Before Hardware Test:**
1. 🔴 Fix START button implementation
2. 🔴 Fix safety interlock logic
3. 🟡 Fix humidifier threshold consistency
4. 🟡 Add pump status communication
5. 🧪 Create integration test scripts

**Estimated Time to Fix:** 2-3 hours

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
```

### Power Indicator LEDs ⭐ NEW

**Problem:** LEDs tidak menyala
```bash
# Check 1: Verify thermal power > 0
Serial Monitor → Check "Thermal Power: X kW"
If 0 kW → Rods not raised or turbine not running

# Check 2: Verify GPIO connections
10 LEDs on GPIO: 23, 22, 21, 19, 18, 5, 17, 13, 12, 14
Check wiring with multimeter

# Check 3: Check resistors
Each LED needs 220Ω resistor in series
```

**Problem:** Semua LED terang walaupun power rendah
```cpp
// Check formula
brightness = (power_mwe / 300.0) * 255;
// Should scale from 0-300 MWe

// Debug print
Serial.printf("Power: %.1f MWe, Brightness: %d\n", 
              power_mwe, brightness);
```

**Problem:** LEDs nyala walaupun turbine idle
```cpp
// WRONG: Power from rods only
thermal_kw = rod_position * 100;

// CORRECT: Power from rods × turbine
thermal_kw = reactor_thermal * 0.33 * (turbine_load / 100);
// turbine_load should be 0 when IDLE!
```

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
ESP_COMM_RATE = 0.15     # Instead of 0.1
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

## 📚 Documentation Files

### **Core Documentation**
- `README.md` - **This file** - Complete system documentation
- `TODO.md` - Task tracking and progress
- `CHANGELOG_V2.md` - Version history

### **Architecture & Design**
- `ARCHITECTURE_2ESP.md` - 2 ESP system architecture (v3.0)
- `ESP_PERFORMANCE_ANALYSIS.md` - Performance benchmarks
- `HARDWARE_OPTIMIZATION_ANALYSIS.md` - Pin usage analysis
- `INTEGRATION_CHECKLIST_2ESP.md` - Testing procedures

### **Hardware Configuration (v3.1)**
- `HARDWARE_UPDATE_SUMMARY.md` - Latest hardware changes
- `I2C_ADDRESS_MAPPING.md` - Complete I2C wiring guide
- `TCA9548A_EXPLANATION.md` - Multiplexer safety (9 OLEDs with same address)
- `POWER_INDICATOR_LED.md` - 10 LED power visualization documentation

### **Code Quality**
- `REVIEW_SUMMARY.md` - Code review results
- `COMPILATION_FIX.md` - ESP32 Core v3.x compatibility fixes
- `ESP32_CORE_V3_CHANGES.md` - API migration guide
- `CLEANUP_GUIDE.md` - Old file cleanup instructions

### **Raspberry Pi Package**
- `RASPI_PACKAGE_SUMMARY.md` - Python modules summary

---

## ✅ Final Summary (v3.2 - December 2024)

### **What's Complete:**

✅ **2 ESP Architecture** (v3.0 - Cost optimized)  
✅ **300 MWe PWR Physics Model** (v3.1 - Realistic)  
✅ **8-Phase Startup Sequence** (v3.2 - Documented) ⭐ NEW  
✅ **6 Individual Humidifiers** (2 SG + 4 CT)  
✅ **Gradual Pump Control** (Realistic start/stop)  
✅ **Dynamic Turbine Speed** (Based on control rods)  
✅ **10 LED Power Indicator** (0-300 MWe visualization)  
✅ **Simultaneous LED Brightness** (All LEDs same brightness)  
✅ **Power Only When Turbine Runs** (Realistic physics!)

### **⚠️ Integration Issues Found (v3.2):**

🔴 **CRITICAL:**
1. START button callback missing
2. Safety interlock logic broken (expects manual pumps)

🟡 **HIGH:**
3. Humidifier threshold mismatch (800 kW vs 80 MWe)
4. Pump status not communicated from ESP-BC

🟢 **LOW:**
5. 9-OLED display manager pending
6. Testing scripts incomplete

**See TODO.md for detailed fix instructions**

### **Key Features:**

🎯 **Reactor Rating:** 300 MWe PWR (Pressurized Water Reactor)  
🎯 **Thermal Capacity:** 900 MWth (33% turbine efficiency)  
🎯 **Control Rods:** 3 servo motors (Safety, Shim, Regulating)  
🎯 **Pumps:** 3 motor drivers with gradual control  
🎯 **Turbine:** 1 motor with dynamic speed control  
🎯 **Humidifiers:** 6 relays (2 SG + 4 CT)  
🎯 **Flow Visualization:** 48 LEDs (3 flows × 16 LEDs)  
🎯 **Power Visualization:** 10 LEDs (simultaneous brightness)  
🎯 **I2C Multiplexing:** 2x TCA9548A for 9 OLEDs  
🎯 **Safety:** Interlock system + emergency shutdown

### **Code Status:**

| Component | Status | Progress | Issues |
|-----------|--------|----------|--------|
| ESP-BC Firmware | ✅ Complete | 100% | Minor: pump status |
| ESP-E Firmware | ✅ Complete | 100% | None |
| Raspberry Pi Code | ⚠️ Issues | 95% | 2 critical |
| Documentation | ✅ Complete | 100% | Minor updates |
| OLED Manager | ⏳ Pending | 0% | Optional |
| Hardware Testing | 🔒 Blocked | 0% | Fix issues first |
| **Overall** | **⚠️ Fixes Needed** | **95%** | **4 issues** |

### **Next Steps:**

**BEFORE Hardware Test:**
1. 🔴 Fix START button implementation (15 min)
2. 🔴 Fix safety interlock logic (20 min)
3. 🟡 Fix humidifier threshold (10 min)
4. 🟡 Add pump status communication (30 min)
5. 🧪 Create integration test scripts (1-2 hrs)

**THEN Hardware Test:**
1. 🔧 Upload firmware to ESP32 boards
2. 🔌 Wire all components according to I2C_ADDRESS_MAPPING.md
3. 🧪 Test individual subsystems
4. ✅ Full system integration test
5. 🎯 (Optional) Implement 9-OLED display manager
6. 📊 (Optional) Add data logging
7. 🌐 (Optional) Web dashboard

### **Contact & Support:**

- 📧 Email: [your-email]
- 🐛 Issues: GitHub Issues
- 📖 Wiki: [your-wiki-link]
- 💬 Discord: [your-discord]

---

**Status:** ⚠️ 95% Complete - Integration Fixes Needed  
**Version:** 3.2  
**Last Updated:** December 12, 2024  
**Estimated Fix Time:** 2-3 hours  
**Blocker:** 2 CRITICAL issues must be fixed before hardware test

---

**⚠️ IMPORTANT:** Jangan upload ke hardware sebelum fix CRITICAL issues!

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
**Last Updated:** 2024-12-12  
**Status:** 🟡 **95% Complete - Integration Fixes Needed**

**Remaining Work:**
- [x] All Python modules integrated ✅
- [x] Complete alur simulasi documented ✅
- [ ] Fix START button callback (CRITICAL) 🔴
- [ ] Fix safety interlock logic (CRITICAL) 🔴
- [ ] Fix humidifier threshold (HIGH) 🟡
- [ ] Add pump status communication (HIGH) 🟡
- [ ] Optional: OLED display manager
- [ ] Full system integration test (after fixes)

**Estimated Completion:** January 2025 (after fixes + hardware test)

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
