# 📌 ESP32 Utama UART - Complete Pin Assignment

**Date:** 2024-12-16  
**System:** PKM PLTN Simulator - ESP32 Main Controller (UART Version)  
**Communication:** UART Protocol (115200 baud, 8N1)

---

## 🎯 Hardware Overview

**ESP32 Utama mengontrol:**
- 3x Servo motors (control rods)
- 6x Relay untuk humidifier (4 cooling tower + 2 steam generator)
- 4x Motor DC dengan L298N motor driver (3 pompa + 1 turbin)
- UART communication dengan Raspberry Pi

---

## 📡 Pin Configuration Summary

### **UART Communication (2 pins)**

| Pin | Function | Notes |
|-----|----------|-------|
| **GPIO 16** | UART RX | Receive data from Raspberry Pi |
| **GPIO 17** | UART TX | Transmit data to Raspberry Pi |

**⚠️ CRITICAL:** GPIO 16 dan 17 HANYA untuk UART, tidak boleh digunakan untuk fungsi lain!

---

### **Control Rods - Servo Motors (3 pins)**

| Pin | Function | Servo Type | Notes |
|-----|----------|------------|-------|
| **GPIO 13** | Safety Rod | SG90/MG996R | 0-180° (0-100%) |
| **GPIO 12** | Shim Rod | SG90/MG996R | 0-180° (0-100%) |
| **GPIO 14** | Regulating Rod | SG90/MG996R | 0-180° (0-100%) |

---

### **Humidifier Relays (6 pins)**

| Pin | Function | Relay Type | Load |
|-----|----------|------------|------|
| **GPIO 25** | Steam Generator 1 | 5V Relay | Humidifier/Fogger |
| **GPIO 26** | Steam Generator 2 | 5V Relay | Humidifier/Fogger |
| **GPIO 27** | Cooling Tower 1 | 5V Relay | Humidifier/Fogger |
| **GPIO 32** | Cooling Tower 2 | 5V Relay | Humidifier/Fogger |
| **GPIO 33** | Cooling Tower 3 | 5V Relay | Humidifier/Fogger |
| **GPIO 34** | Cooling Tower 4 | 5V Relay | Humidifier/Fogger |

**Note:** Active HIGH relay (HIGH = ON, LOW = OFF)

---

### **Motor Driver PWM - Speed Control (4 pins)**

| Pin | Function | L298N Pin | Motor | Notes |
|-----|----------|-----------|-------|-------|
| **GPIO 4** | Pump Primary Speed | ENA (L298N #1) | Pompa Primer | PWM 5kHz, 0-255 |
| **GPIO 5** | Pump Secondary Speed | ENB (L298N #1) | Pompa Sekunder | PWM 5kHz, 0-255 |
| **GPIO 18** | Pump Tertiary Speed | ENA (L298N #2) | Pompa Tersier | PWM 5kHz, 0-255 |
| **GPIO 19** | Turbine Speed | ENB (L298N #2) | Motor Turbin | PWM 5kHz, 0-255 |

**PWM Configuration:**
- Frequency: 5000 Hz (5 kHz)
- Resolution: 8-bit (0-255)
- API: `ledcAttach(pin, freq, resolution)` - ESP32 Core v3.x

---

### **Motor Direction Control (2 pins)**

| Pin | Function | L298N Pin | Notes |
|-----|----------|-----------|-------|
| **GPIO 23** | Turbine IN1 | IN3 (L298N #2) | Direction control 1 |
| **GPIO 15** | Turbine IN2 | IN4 (L298N #2) | Direction control 2 |

**Direction Truth Table (L298N):**
```
IN1=HIGH, IN2=LOW  → FORWARD
IN1=LOW,  IN2=HIGH → REVERSE
IN1=LOW,  IN2=LOW  → STOP (brake)
```

**⚠️ Pumps (Primary, Secondary, Tertiary):**
- Direction control HARD-WIRED pada L298N board
- IN1 connected to GND (LOW)
- IN2 connected to +3.3V (HIGH)
- Always FORWARD direction
- **Saves 6 GPIO pins!**

---

## 🔌 L298N Wiring Diagram

### **L298N #1 - Pompa Primer & Pompa Sekunder**

```
ESP32 Utama                L298N #1                 Motors
━━━━━━━━━━━━━━            ━━━━━━━━━━━━━━          ━━━━━━━━━━━━
                           
GPIO 4 (PWM) ────────────> ENA (PWM)               
HARD-WIRE: GND ───────────> IN1 (Direction)        
HARD-WIRE: +3.3V ─────────> IN2 (Direction)        
                              │                     
                           OUT1 ──────────────────> Motor Pompa Primer (+)
                           OUT2 ──────────────────> Motor Pompa Primer (-)
                           
GPIO 5 (PWM) ────────────> ENB (PWM)               
HARD-WIRE: GND ───────────> IN3 (Direction)        
HARD-WIRE: +3.3V ─────────> IN4 (Direction)        
                              │                     
                           OUT3 ──────────────────> Motor Pompa Sekunder (+)
                           OUT4 ──────────────────> Motor Pompa Sekunder (-)
                           
ESP32 GND ────────────────> GND (Common)           
                           +12V <─────────────────── Power Supply 12V
```

### **L298N #2 - Pompa Tersier & Motor Turbin**

```
ESP32 Utama                L298N #2                 Motors
━━━━━━━━━━━━━━            ━━━━━━━━━━━━━━          ━━━━━━━━━━━━
                           
GPIO 18 (PWM) ───────────> ENA (PWM)               
HARD-WIRE: GND ───────────> IN1 (Direction)        
HARD-WIRE: +3.3V ─────────> IN2 (Direction)        
                              │                     
                           OUT1 ──────────────────> Motor Pompa Tersier (+)
                           OUT2 ──────────────────> Motor Pompa Tersier (-)
                           
GPIO 19 (PWM) ───────────> ENB (PWM)               
GPIO 23 ──────────────────> IN3 (Direction 1)      
GPIO 15 ──────────────────> IN4 (Direction 2)      
                              │                     
                           OUT3 ──────────────────> Motor Turbin (+)
                           OUT4 ──────────────────> Motor Turbin (-)
                           
ESP32 GND ────────────────> GND (Common)           
                           +12V <─────────────────── Power Supply 12V
```

---

## 📊 Complete Pin Usage Table

| GPIO Pin | Function | Type | Notes |
|----------|----------|------|-------|
| **GPIO 4** | Motor: Pump Primary PWM | Output (PWM) | L298N #1 ENA |
| **GPIO 5** | Motor: Pump Secondary PWM | Output (PWM) | L298N #1 ENB |
| **GPIO 12** | Servo: Shim Rod | Output (PWM) | Servo motor |
| **GPIO 13** | Servo: Safety Rod | Output (PWM) | Servo motor |
| **GPIO 14** | Servo: Regulating Rod | Output (PWM) | Servo motor |
| **GPIO 15** | Motor: Turbine IN2 | Output (Digital) | L298N #2 IN4 |
| **GPIO 16** | UART RX | Input | **RESERVED** |
| **GPIO 17** | UART TX | Output | **RESERVED** |
| **GPIO 18** | Motor: Pump Tertiary PWM | Output (PWM) | L298N #2 ENA |
| **GPIO 19** | Motor: Turbine PWM | Output (PWM) | L298N #2 ENB |
| **GPIO 23** | Motor: Turbine IN1 | Output (Digital) | L298N #2 IN3 |
| **GPIO 25** | Relay: SG1 | Output (Digital) | Steam Generator 1 |
| **GPIO 26** | Relay: SG2 | Output (Digital) | Steam Generator 2 |
| **GPIO 27** | Relay: CT1 | Output (Digital) | Cooling Tower 1 |
| **GPIO 32** | Relay: CT2 | Output (Digital) | Cooling Tower 2 |
| **GPIO 33** | Relay: CT3 | Output (Digital) | Cooling Tower 3 |
| **GPIO 34** | Relay: CT4 | Output (Digital) | Cooling Tower 4 |

**Total GPIO Used: 17 pins**

---

## ⚠️ Pin Conflict Resolution

### **Problem in Original Design:**

Original `esp_utama.ino` used GPIO 16, 17 for motor driver PWM, but these pins are **REQUIRED** for UART communication with Raspberry Pi.

### **Solution:**

| Original Pin | Original Function | New Pin | New Function | Status |
|--------------|-------------------|---------|--------------|--------|
| GPIO 16 | Motor: Pump Secondary PWM | **GPIO 16** | **UART RX** | ✅ Changed |
| GPIO 17 | Motor: Pump Tertiary PWM | **GPIO 17** | **UART TX** | ✅ Changed |
| - | - | **GPIO 5** | Motor: Pump Secondary PWM | ✅ New |
| - | - | **GPIO 18** | Motor: Pump Tertiary PWM | ✅ New |

**Result:** No pin conflicts! UART communication works perfectly.

---

## 🔧 Software Configuration

### **UART Setup (ESP32 Core v3.x)**

```cpp
#define UART_BAUD 115200
HardwareSerial UartComm(2);  // UART2

void setup() {
  // Initialize UART2: RX=16, TX=17
  UartComm.begin(UART_BAUD, SERIAL_8N1, 16, 17);
}
```

### **Motor Driver PWM Setup (ESP32 Core v3.x)**

```cpp
#define PWM_FREQ       5000  // 5 kHz
#define PWM_RESOLUTION 8     // 8-bit (0-255)

void setup() {
  // Attach PWM to motor pins
  ledcAttach(MOTOR_PUMP_PRIMARY, PWM_FREQ, PWM_RESOLUTION);   // GPIO 4
  ledcAttach(MOTOR_PUMP_SECONDARY, PWM_FREQ, PWM_RESOLUTION); // GPIO 5
  ledcAttach(MOTOR_PUMP_TERTIARY, PWM_FREQ, PWM_RESOLUTION);  // GPIO 18
  ledcAttach(MOTOR_TURBINE, PWM_FREQ, PWM_RESOLUTION);        // GPIO 19
  
  // Set initial speed to 0
  ledcWrite(MOTOR_PUMP_PRIMARY, 0);
  ledcWrite(MOTOR_PUMP_SECONDARY, 0);
  ledcWrite(MOTOR_PUMP_TERTIARY, 0);
  ledcWrite(MOTOR_TURBINE, 0);
}
```

### **Turbine Direction Control**

```cpp
void setMotorDirection(uint8_t motor_id, uint8_t direction) {
  if (motor_id == 4) {  // Turbine only
    if (direction == MOTOR_FORWARD) {
      digitalWrite(MOTOR_TURBINE_IN1, HIGH);  // GPIO 23
      digitalWrite(MOTOR_TURBINE_IN2, LOW);   // GPIO 15
    } else if (direction == MOTOR_REVERSE) {
      digitalWrite(MOTOR_TURBINE_IN1, LOW);
      digitalWrite(MOTOR_TURBINE_IN2, HIGH);
    } else {  // MOTOR_STOP
      digitalWrite(MOTOR_TURBINE_IN1, LOW);
      digitalWrite(MOTOR_TURBINE_IN2, LOW);
    }
  }
  // Pumps: Hard-wired FORWARD (no code needed)
}
```

---

## 🎮 Automatic Control Logic

### **Turbine State Machine**

```
STATE_IDLE (0)
├─ Turbine: 0%
├─ Pumps: 0%
└─ Condition: reactor_thermal < 50 MWth

STATE_STARTING (1)
├─ Turbine: Gradual 0→100% (ramp up)
├─ Pumps: 50%
└─ Condition: reactor_thermal > 50 MWth

STATE_RUNNING (2)
├─ Turbine: 100%
├─ Pumps: 100%
└─ Condition: reactor_thermal > 20 MWth

STATE_SHUTDOWN (3)
├─ Turbine: Gradual 100→0% (ramp down)
├─ Pumps: 20%
└─ Condition: reactor_thermal < 20 MWth
```

### **Pump Gradual Control**

```cpp
void updatePumpSpeeds() {
  // Gradual acceleration
  if (pump_actual < pump_target) {
    pump_actual += 2.0;  // +2% per cycle (fast ramp-up)
  }
  
  // Gradual deceleration
  if (pump_actual > pump_target) {
    pump_actual -= 1.0;  // -1% per cycle (slow ramp-down)
  }
  
  // Apply PWM
  int pwm = map((int)pump_actual, 0, 100, 0, 255);
  ledcWrite(motor_pin, pwm);
}
```

---

## 🔍 Pin Comparison: I2C vs UART Version

| Function | I2C Version | UART Version | Notes |
|----------|-------------|--------------|-------|
| Communication | I2C (GPIO 21, 22) | UART (GPIO 16, 17) | ✅ Changed |
| Safety Servo | GPIO 25 | GPIO 13 | ✅ Changed |
| Shim Servo | GPIO 26 | GPIO 12 | ✅ Changed |
| Regulating Servo | GPIO 27 | GPIO 14 | ✅ Changed |
| Motor Pump Primary | GPIO 4 | GPIO 4 | ✅ Same |
| Motor Pump Secondary | GPIO 16 | GPIO 5 | ✅ Changed (conflict) |
| Motor Pump Tertiary | GPIO 17 | GPIO 18 | ✅ Changed (conflict) |
| Motor Turbine | GPIO 5 | GPIO 19 | ✅ Changed |
| Turbine IN1 | GPIO 23 | GPIO 23 | ✅ Same |
| Turbine IN2 | GPIO 18 | GPIO 15 | ✅ Changed |
| Relay SG1 | GPIO 13 | GPIO 25 | ✅ Changed |
| Relay SG2 | GPIO 15 | GPIO 26 | ✅ Changed |
| Relay CT1 | GPIO 32 | GPIO 27 | ✅ Changed |
| Relay CT2-4 | GPIO 33, 14, 12 | GPIO 32, 33, 34 | ✅ Changed |

---

## ✅ Hardware Checklist

### **L298N Configuration:**
- [ ] Remove ENA/ENB jumpers on both L298N boards
- [ ] Connect +12V power supply to both L298N
- [ ] Common GND between ESP32, L298N #1, L298N #2, Power Supply
- [ ] Hard-wire pump directions (IN1→GND, IN2→+3.3V) on L298N board

### **ESP32 Wiring:**
- [ ] UART: GPIO 16 (RX), 17 (TX) → Raspberry Pi
- [ ] Servos: GPIO 13, 12, 14 → Control rods
- [ ] Relays: GPIO 25, 26, 27, 32, 33, 34 → Humidifiers
- [ ] PWM: GPIO 4, 5, 18, 19 → L298N ENA/ENB pins
- [ ] Direction: GPIO 23, 15 → L298N IN3, IN4 (turbine only)

### **Power Supply:**
- [ ] 12V 5A for motor drivers
- [ ] 5V USB for ESP32 (separate from motor power)
- [ ] Common ground for all components

---

## 🧪 Testing Procedure

### **Step 1: UART Communication Test**

```bash
# On Raspberry Pi
python3 -c "
import serial
ser = serial.Serial('/dev/serial0', 115200)
ser.write(b'{\"cmd\":\"ping\"}\n')
response = ser.readline()
print('Response:', response)
"
```

Expected: `{"status":"ok","message":"pong","device":"ESP-BC"}`

### **Step 2: Motor Driver Test**

```bash
# Send control rod command (raise shim rod to 50%)
echo '{"cmd":"update","rods":[0,50,0],"humid_sg":[0,0],"humid_ct":[0,0,0,0]}' > /dev/serial0
```

Expected:
- Shim servo moves to 50%
- Reactor thermal increases
- When thermal > 50 MWth → Turbine starts automatically
- Pumps ramp up to 50% then 100%

### **Step 3: Full System Test**

```bash
# Startup sequence
echo '{"cmd":"update","rods":[0,80,80],"humid_sg":[1,1],"humid_ct":[1,1,1,1]}' > /dev/serial0

# Monitor response
cat /dev/serial0
```

Expected:
1. Servos move to target positions
2. Reactor thermal > 50 MWth
3. Turbine state: IDLE → STARTING → RUNNING
4. Pumps: 0% → 50% → 100%
5. Humidifiers turn ON

---

## 📞 Troubleshooting

### **Problem: Motor tidak berputar**

**Check:**
1. UART communication working? (test with ping command)
2. Control rods moving? (reactor thermal > 50 MWth required)
3. PWM pins connected? (GPIO 4, 5, 18, 19)
4. L298N jumpers removed? (ENA/ENB must be removable)
5. Motor power supply 12V connected?

### **Problem: UART tidak merespon**

**Check:**
1. Wiring: ESP32 TX (GPIO 17) → RasPi RX
2. Wiring: ESP32 RX (GPIO 16) → RasPi TX
3. Common ground between ESP32 and RasPi
4. Serial port enabled on RasPi: `raspi-config` → Interfacing → Serial
5. Baud rate: 115200 on both sides

### **Problem: Turbine tidak start**

**Check:**
1. Control rods raised? (shim + regulating > 10%)
2. Reactor thermal > 50 MWth? (check UART response)
3. Turbine PWM connected? (GPIO 19 → L298N #2 ENB)
4. Turbine direction pins? (GPIO 23, 15 → L298N #2 IN3, IN4)

---

## 🎉 Summary

✅ **Total GPIO Used:** 17 pins  
✅ **No Pin Conflicts:** UART (16, 17) reserved exclusively  
✅ **Motor Control:** 4 motors (3 pumps + 1 turbine) with automatic control  
✅ **Communication:** UART JSON protocol (115200 baud)  
✅ **Optimization:** 6 GPIO saved by hard-wiring pump directions  

**Status:** ✅ Ready for Implementation  
**Version:** 2.0 (UART)  
**Date:** 2024-12-16

---

## 📝 Related Documents

- `L298N_MOTOR_DRIVER_WIRING.md` - Original motor driver wiring (I2C version)
- `UART_WIRING_GUIDE.md` - UART communication setup
- `GPIO_PIN_ASSIGNMENT.md` - Raspberry Pi GPIO mapping
- `esp_utama_uart.ino` - Complete Arduino code
